"""Tests for Bedrock + OpenAI provider implementations and FallbackChain."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.providers import BedrockProvider, FallbackChain, OpenAIProvider

# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_anthropic_response(text: str = "hello", in_tok: int = 10, out_tok: int = 5) -> Any:
    block = MagicMock()
    block.text = text
    response = MagicMock()
    response.content = [block]
    response.usage.input_tokens = in_tok
    response.usage.output_tokens = out_tok
    return response


def _make_openai_response(text: str = "hi", in_tok: int = 8, out_tok: int = 4) -> Any:
    choice = MagicMock()
    choice.message.content = text
    response = MagicMock()
    response.choices = [choice]
    response.usage.prompt_tokens = in_tok
    response.usage.completion_tokens = out_tok
    return response


# ── BedrockProvider ───────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_bedrock_provider_complete() -> None:
    mock_response = _make_anthropic_response("The answer is 42.")
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    provider = BedrockProvider()
    with patch.object(provider, "_client", return_value=mock_client):
        result = await provider.complete(
            messages=[{"role": "user", "content": "What is 6×7?"}],
            system=None,
            max_tokens=100,
            model_tier="small",
        )

    assert result["content"] == "The answer is 42."
    assert result["provider"] == "bedrock"
    assert result["usage"]["inputTokens"] == 10
    assert result["usage"]["outputTokens"] == 5
    assert "anthropic.claude-3-5-haiku" in result["model"]


@pytest.mark.anyio
async def test_bedrock_provider_medium_tier_uses_sonnet() -> None:
    mock_response = _make_anthropic_response("Sonnet answer.")
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    provider = BedrockProvider()
    with patch.object(provider, "_client", return_value=mock_client):
        result = await provider.complete(
            messages=[{"role": "user", "content": "draft letter"}],
            system="You are a tax expert.",
            max_tokens=500,
            model_tier="medium",
        )

    assert "sonnet" in result["model"]


# ── OpenAIProvider ────────────────────────────────────────────────────────────


def _mock_openai_module(mock_client: Any) -> Any:
    """Return a sys.modules stub for 'openai' so tests run without the real package."""
    import sys

    mock_mod = MagicMock()
    mock_mod.AsyncOpenAI.return_value = mock_client
    return patch.dict(sys.modules, {"openai": mock_mod})


@pytest.mark.anyio
async def test_openai_provider_complete() -> None:
    mock_response = _make_openai_response("OpenAI says hello.", 12, 6)
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with _mock_openai_module(mock_client):
        provider = OpenAIProvider()
        result = await provider.complete(
            messages=[{"role": "user", "content": "Hello"}],
            system=None,
            max_tokens=200,
            model_tier="small",
        )

    assert result["content"] == "OpenAI says hello."
    assert result["provider"] == "openai"
    assert result["model"] == "gpt-4o-mini"
    assert result["usage"]["inputTokens"] == 12


@pytest.mark.anyio
async def test_openai_injects_system_as_first_message() -> None:
    mock_response = _make_openai_response()
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with _mock_openai_module(mock_client):
        provider = OpenAIProvider()
        await provider.complete(
            messages=[{"role": "user", "content": "question"}],
            system="Be concise.",
            max_tokens=100,
            model_tier="medium",
        )
        call_args = mock_client.chat.completions.create.call_args

    messages_sent = call_args.kwargs["messages"]
    assert messages_sent[0] == {"role": "system", "content": "Be concise."}
    assert messages_sent[1] == {"role": "user", "content": "question"}
    assert call_args.kwargs["model"] == "gpt-4o"


# ── FallbackChain ─────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_fallback_chain_uses_primary_when_ok() -> None:
    primary = AsyncMock()
    primary.name = "bedrock"
    primary.complete.return_value = {"content": "from bedrock", "provider": "bedrock"}

    secondary = AsyncMock()
    secondary.name = "openai"

    chain = FallbackChain(providers=[primary, secondary])
    result = await chain.complete(
        messages=[{"role": "user", "content": "test"}],
        system=None,
        max_tokens=100,
        model_tier="small",
    )

    assert result["content"] == "from bedrock"
    secondary.complete.assert_not_called()


@pytest.mark.anyio
async def test_fallback_chain_falls_back_on_error() -> None:
    primary = AsyncMock()
    primary.name = "bedrock"
    primary.complete.side_effect = RuntimeError("Bedrock unavailable")

    secondary = AsyncMock()
    secondary.name = "openai"
    secondary.complete.return_value = {"content": "from openai", "provider": "openai"}

    chain = FallbackChain(providers=[primary, secondary])
    result = await chain.complete(
        messages=[{"role": "user", "content": "test"}],
        system=None,
        max_tokens=100,
        model_tier="medium",
    )

    assert result["content"] == "from openai"
    assert result["provider"] == "openai"


@pytest.mark.anyio
async def test_fallback_chain_all_fail_returns_error_dict() -> None:
    primary = AsyncMock()
    primary.name = "bedrock"
    primary.complete.side_effect = RuntimeError("Bedrock down")

    secondary = AsyncMock()
    secondary.name = "openai"
    secondary.complete.side_effect = RuntimeError("OpenAI down")

    chain = FallbackChain(providers=[primary, secondary])
    result = await chain.complete(
        messages=[{"role": "user", "content": "x"}],
        system=None,
        max_tokens=10,
        model_tier="small",
    )

    assert result["content"] == ""
    assert "all providers failed" in result["error"]
    assert "OpenAI down" in result["lastError"]


def test_fallback_chain_provider_names() -> None:
    p1 = MagicMock()
    p1.name = "bedrock"
    p2 = MagicMock()
    p2.name = "openai"
    chain = FallbackChain(providers=[p1, p2])
    assert chain.provider_names == ["bedrock", "openai"]


def test_health_reports_providers() -> None:
    from app.main import app
    from fastapi.testclient import TestClient

    resp = TestClient(app).get("/health")
    data = resp.json()
    assert data["status"] == "ok"
    assert "bedrock" in data["providers"]
    assert "nova" in data["providers"]
    assert "openai" in data["providers"]


# ── NovaProvider ──────────────────────────────────────────────────────────────


def _make_converse_response(text: str = "nova says hi", in_tok: int = 12, out_tok: int = 6) -> Any:
    return {
        "output": {"message": {"role": "assistant", "content": [{"text": text}]}},
        "usage": {"inputTokens": in_tok, "outputTokens": out_tok},
    }


@pytest.mark.anyio
async def test_nova_provider_converse_roundtrip() -> None:
    from app.providers import NovaProvider

    mock_client = MagicMock()
    mock_client.converse.return_value = _make_converse_response()

    provider = NovaProvider()
    with patch.object(provider, "_client", return_value=mock_client):
        result = await provider.complete(
            messages=[{"role": "user", "content": "what is 87A?"}],
            system="You are a tax expert.",
            max_tokens=300,
            model_tier="medium",
        )

    assert result["content"] == "nova says hi"
    assert result["provider"] == "nova"
    assert "nova-lite" in result["model"]
    assert result["usage"] == {"inputTokens": 12, "outputTokens": 6}
    call_kwargs = mock_client.converse.call_args.kwargs
    assert call_kwargs["messages"][0]["content"] == [{"text": "what is 87A?"}]
    assert call_kwargs["system"] == [{"text": "You are a tax expert."}]
    assert call_kwargs["inferenceConfig"] == {"maxTokens": 300}


@pytest.mark.anyio
async def test_nova_tier_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.providers import NovaProvider

    monkeypatch.setenv("NOVA_MODEL_LARGE", "us.amazon.nova-lite-v1:0")
    mock_client = MagicMock()
    mock_client.converse.return_value = _make_converse_response()

    provider = NovaProvider()
    with patch.object(provider, "_client", return_value=mock_client):
        result = await provider.complete(
            messages=[{"role": "user", "content": "draft"}],
            system=None,
            max_tokens=100,
            model_tier="large",
        )

    assert result["model"] == "us.amazon.nova-lite-v1:0"


@pytest.mark.anyio
async def test_chain_falls_back_from_bedrock_to_nova() -> None:
    from app.providers import NovaProvider

    failing = AsyncMock()
    failing.name = "bedrock"
    failing.complete.side_effect = RuntimeError("model access denied")

    nova = NovaProvider()
    mock_client = MagicMock()
    mock_client.converse.return_value = _make_converse_response("fallback answer")

    with patch.object(nova, "_client", return_value=mock_client):
        chain = FallbackChain(providers=[failing, nova])
        result = await chain.complete(
            messages=[{"role": "user", "content": "q"}],
            system=None,
            max_tokens=50,
            model_tier="small",
        )

    assert result["content"] == "fallback answer"
    assert result["provider"] == "nova"
