#!/usr/bin/env bash
# UserPromptSubmit: non-blocking reminder if the prompt contains PII-like patterns.
input="$(cat)"
text="$(printf '%s' "$input" | python3 -c 'import sys,json
try:
  d=json.load(sys.stdin); print(d.get("prompt","") or d.get("user_prompt",""))
except Exception:
  print("")' 2>/dev/null)"
# US SSN, generic 16-digit card, or obvious secret words
if printf '%s' "$text" | grep -Eq '([0-9]{3}-[0-9]{2}-[0-9]{4})|([0-9]{16})'; then
  echo "[pii-guard] This prompt may contain PII (SSN/card-like digits). Verra minimizes PII in prompts — mask or reference by ID where possible." >&2
fi
exit 0
