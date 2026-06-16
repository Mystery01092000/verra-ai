#!/usr/bin/env bash
# PreToolUse(Bash) guard. Reads the tool call JSON on stdin.
# Blocks (exit 2) destructive commands and anything that could leak secrets.
# Verra is a regulated-data product: be conservative.
input="$(cat)"
cmd="$(printf '%s' "$input" | python3 -c 'import sys,json;
try:
  d=json.load(sys.stdin); print(d.get("tool_input",{}).get("command",""))
except Exception:
  print("")' 2>/dev/null)"

block() { echo "BLOCKED by guard-bash hook: $1" >&2; exit 2; }

case "$cmd" in
  *"rm -rf /"*|*":(){"*|*"mkfs"*|*"dd if="*) block "destructive command" ;;
esac
# Never read or print secret material
if printf '%s' "$cmd" | grep -Eiq '(\.env|secrets?|api[_-]?key|private[_-]?key|password|token)'; then
  if printf '%s' "$cmd" | grep -Eiq '(cat|less|more|print|echo|curl|wget|scp|nc )'; then
    block "possible secret exposure"
  fi
fi
exit 0
