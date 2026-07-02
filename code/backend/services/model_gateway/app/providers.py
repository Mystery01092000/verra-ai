"""Provider abstraction + health/budget-aware fallback chain (ADR-0006).

Primary: AWS Bedrock (Claude models via AnthropicBedrock SDK).
Fallback: OpenAI GPT-4o family.

Model tier strategy:
  small  → Claude 3.5 Haiku  — guardrails, routing, simple extraction (fast + cheap)
  medium → Claude 3.5 Sonnet v2 — main tax analysis, orchestrator tasks (best perf/cost)
  large  → Claude 3 Opus      — complex multi-step reasoning, final review (highest quality)

Auth priority: AWS_BEARER_TOKEN_BEDROCK (IAM Identity Center) > key/secret pair.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Protocol

logger = logging.getLogger(__name__)

# Per-provider tier → model ID mappings.
_BEDROCK_TIER: dict[str, str] = {
    "small": "anthropic.claude-3-5-haiku-20241022-v1:0",
    "medium": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "large": "anthropic.claude-3-opus-20240229-v1:0",
}

_OPENAI_TIER: dict[str, str] = {
    "small": "gpt-4o-mini",
    "medium": "gpt-4o",
    "large": "gpt-4o",
}


def _nova_tier() -> dict[str, str]:
    """Nova tier map, env-overridable (free-tier accounts may only have Nova Lite)."""
    return {
        "small": os.getenv("NOVA_MODEL_SMALL", "us.amazon.nova-micro-v1:0"),
        "medium": os.getenv("NOVA_MODEL_MEDIUM", "us.amazon.nova-lite-v1:0"),
        "large": os.getenv("NOVA_MODEL_LARGE", "us.amazon.nova-pro-v1:0"),
    }


class Provider(Protocol):
    name: str

    async def complete(
        self,
        messages: list[dict[str, str]],
        system: str | None,
        max_tokens: int,
        model_tier: str,
    ) -> dict[str, Any]: ...


class BedrockProvider:
    """Claude on AWS Bedrock via anthropic[bedrock] SDK (primary provider)."""

    name: str = "bedrock"

    def __init__(self) -> None:
        self._region = os.getenv("AWS_REGION", "us-east-1")
        self._bearer_token = os.getenv("AWS_BEARER_TOKEN_BEDROCK", "")
        # Standard AWS SDK names + user's custom names (AWS_ACCESS_KEY / AWS_ACCESS_TOKEN)
        self._access_key = os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("AWS_ACCESS_KEY", "")
        self._secret_key = os.getenv("AWS_SECRET_ACCESS_KEY") or os.getenv("AWS_SECRET_KEY", "")
        # AWS_ACCESS_TOKEN = session token for temporary credentials (STS / IAM Identity Center)
        self._session_token = os.getenv("AWS_SESSION_TOKEN") or os.getenv("AWS_ACCESS_TOKEN", "")

        if self._bearer_token:
            logger.info("BedrockProvider: bearer token auth (IAM Identity Center).")
        elif self._access_key and self._secret_key:
            mode = "key+secret+session_token" if self._session_token else "key+secret"
            logger.info("BedrockProvider: %s auth.", mode)
        else:
            logger.warning(
                "No Bedrock credentials found "
                "(AWS_BEARER_TOKEN_BEDROCK, or AWS_ACCESS_KEY_ID+AWS_SECRET_ACCESS_KEY); "
                "BedrockProvider will fail on use."
            )

    def _client(self) -> Any:
        from anthropic import AnthropicBedrock

        if self._bearer_token:
            # aws_bearer_token is accepted at runtime but missing from the SDK's type stubs.
            bearer_kwargs: dict[str, Any] = {
                "aws_bearer_token": self._bearer_token,
                "aws_region": self._region,
            }
            return AnthropicBedrock(**bearer_kwargs)
        return AnthropicBedrock(
            aws_access_key=self._access_key or None,
            aws_secret_key=self._secret_key or None,
            aws_session_token=self._session_token or None,
            aws_region=self._region,
        )

    async def complete(
        self,
        messages: list[dict[str, str]],
        system: str | None,
        max_tokens: int,
        model_tier: str,
    ) -> dict[str, Any]:
        model = _BEDROCK_TIER.get(model_tier, _BEDROCK_TIER["medium"])
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        client = self._client()
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.messages.create(**kwargs),
        )
        content_block = response.content[0] if response.content else None
        text = content_block.text if content_block and hasattr(content_block, "text") else ""
        return {
            "content": text,
            "provider": self.name,
            "model": model,
            "usage": {
                "inputTokens": response.usage.input_tokens,
                "outputTokens": response.usage.output_tokens,
            },
        }


class NovaProvider:
    """Amazon Nova on Bedrock via boto3 converse (fallback when Claude access is absent,
    e.g. free-tier accounts that only have Nova model access)."""

    name: str = "nova"

    def __init__(self) -> None:
        self._region = os.getenv("AWS_REGION", "us-east-1")

    def _client(self) -> Any:
        import boto3

        # boto3's default chain picks up env keys, AWS_PROFILE, or instance roles.
        return boto3.client("bedrock-runtime", region_name=self._region)

    async def complete(
        self,
        messages: list[dict[str, str]],
        system: str | None,
        max_tokens: int,
        model_tier: str,
    ) -> dict[str, Any]:
        tier_map = _nova_tier()
        model = tier_map.get(model_tier, tier_map["medium"])
        converse_messages = [
            {"role": m["role"], "content": [{"text": m["content"]}]} for m in messages
        ]
        kwargs: dict[str, Any] = {
            "modelId": model,
            "messages": converse_messages,
            "inferenceConfig": {"maxTokens": max_tokens},
        }
        if system:
            kwargs["system"] = [{"text": system}]

        client = self._client()
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, lambda: client.converse(**kwargs))
        blocks = response.get("output", {}).get("message", {}).get("content", [])
        text = "".join(b.get("text", "") for b in blocks)
        usage = response.get("usage", {})
        return {
            "content": text,
            "provider": self.name,
            "model": model,
            "usage": {
                "inputTokens": int(usage.get("inputTokens", 0)),
                "outputTokens": int(usage.get("outputTokens", 0)),
            },
        }


class OpenAIProvider:
    """OpenAI GPT-4o family (fallback provider)."""

    name: str = "openai"

    def __init__(self) -> None:
        self._api_key = os.getenv("OPENAI_API_KEY", "")
        if not self._api_key:
            logger.warning("OPENAI_API_KEY not set; OpenAIProvider will fail on use.")

    async def complete(
        self,
        messages: list[dict[str, str]],
        system: str | None,
        max_tokens: int,
        model_tier: str,
    ) -> dict[str, Any]:
        import openai

        model = _OPENAI_TIER.get(model_tier, _OPENAI_TIER["medium"])
        oai_messages: list[dict[str, str]] = []
        if system:
            oai_messages.append({"role": "system", "content": system})
        oai_messages.extend(messages)

        client = openai.AsyncOpenAI(api_key=self._api_key)
        response = await client.chat.completions.create(
            model=model,
            messages=oai_messages,
            max_tokens=max_tokens,
        )
        choice = response.choices[0] if response.choices else None
        text = choice.message.content or "" if choice else ""
        usage = response.usage
        return {
            "content": text,
            "provider": self.name,
            "model": model,
            "usage": {
                "inputTokens": usage.prompt_tokens if usage else 0,
                "outputTokens": usage.completion_tokens if usage else 0,
            },
        }


class FallbackChain:
    """primary → fallback → degraded. Tries each provider in order."""

    def __init__(self, providers: list[Any]) -> None:
        self._providers = providers

    @property
    def provider_names(self) -> list[str]:
        return [getattr(p, "name", "unknown") for p in self._providers]

    async def complete(
        self,
        messages: list[dict[str, str]],
        system: str | None,
        max_tokens: int,
        model_tier: str,
    ) -> dict[str, Any]:
        last_error: str = ""
        for provider in self._providers:
            pname = getattr(provider, "name", "unknown")
            try:
                result: dict[str, Any] = await provider.complete(
                    messages=messages,
                    system=system,
                    max_tokens=max_tokens,
                    model_tier=model_tier,
                )
                return result
            except Exception as exc:
                last_error = str(exc)
                logger.warning("Provider %s failed: %s — trying next.", pname, exc)
                continue

        logger.error("All providers failed. Last error: %s", last_error)
        return {
            "content": "",
            "error": "all providers failed",
            "lastError": last_error,
        }
