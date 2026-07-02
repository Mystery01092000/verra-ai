"""
Verra — Bedrock model finder
Reads credentials from the environment (never hardcode keys here).
Run:  AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... python test_bedrock.py
      (or rely on an AWS_PROFILE / default credential chain)
"""

import json
import os

AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.environ.get(
    "AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
)

# Priority order — first working model wins
MODELS = [
    # Amazon Nova (preferred: Amazon's own → always available on free tier)
    {"id": "us.amazon.nova-lite-v1:0", "family": "nova"},
    {"id": "amazon.nova-lite-v1:0", "family": "nova"},
    {"id": "us.amazon.nova-micro-v1:0", "family": "nova"},
    {"id": "amazon.nova-micro-v1:0", "family": "nova"},
    # Anthropic Claude (fallback — confirmed working in ap-south-1)
    {"id": "anthropic.claude-3-haiku-20240307-v1:0", "family": "anthropic"},
    {"id": "anthropic.claude-3-sonnet-20240229-v1:0", "family": "anthropic"},
]


def make_client(region: str) -> object:
    import boto3  # type: ignore

    return boto3.client(
        "bedrock-runtime",
        region_name=region,
        aws_access_key_id=AWS_ACCESS_KEY or None,
        aws_secret_access_key=AWS_SECRET_KEY or None,
    )


def probe_anthropic(client: object, model_id: str) -> bool:
    body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 16,
            "messages": [{"role": "user", "content": "Reply OK only."}],
        }
    )
    try:
        resp = client.invoke_model(  # type: ignore[attr-defined]
            modelId=model_id,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        text = json.loads(resp["body"].read())["content"][0]["text"]
        print(f"  ✅  {model_id}  →  {text!r}")
        return True
    except Exception as e:
        print(f"  ❌  {model_id}  →  {str(e)[:110]}")
        return False


def probe_nova(client: object, model_id: str) -> bool:
    body = json.dumps(
        {
            "messages": [{"role": "user", "content": [{"text": "Reply OK only."}]}],
            "inferenceConfig": {"maxTokens": 16},
        }
    )
    try:
        resp = client.invoke_model(  # type: ignore[attr-defined]
            modelId=model_id,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        data = json.loads(resp["body"].read())
        text = data["output"]["message"]["content"][0]["text"]
        print(f"  ✅  {model_id}  →  {text!r}")
        return True
    except Exception as e:
        print(f"  ❌  {model_id}  →  {str(e)[:110]}")
        return False


def main() -> None:
    print("\n── Bedrock model probe ──────────────────────────────")
    print(f"  Region : {AWS_REGION}")
    print(
        f"  Key    : {'SET (' + AWS_ACCESS_KEY[:8] + '...)' if AWS_ACCESS_KEY else 'NOT SET'}"
    )
    print(f"  Secret : {'SET' if AWS_SECRET_KEY else 'NOT SET'}")
    print("────────────────────────────────────────────────────\n")

    if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
        print(
            "⚠️  No credentials. Set AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY in env."
        )
        return

    try:
        import boto3  # noqa: F401
    except ImportError:
        print("boto3 not installed — run: pip install boto3")
        return

    client = make_client(AWS_REGION)

    print("Probing models...\n")
    working: list[str] = []
    for m in MODELS:
        probe = probe_nova if m["family"] == "nova" else probe_anthropic
        if probe(client, m["id"]):
            working.append(m["id"])

    print("\n── Results ──────────────────────────────────────────")
    if working:
        best = working[0]
        print(f"✅  {len(working)} model(s) work. Best: {best}")
        print(f"\nSet in route.ts:  const bedrockModel = '{best}';")
    else:
        print(
            "❌  No models responded. Check IAM: bedrock:InvokeModel on these model ARNs."
        )


if __name__ == "__main__":
    main()
