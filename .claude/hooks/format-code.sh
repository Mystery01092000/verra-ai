#!/usr/bin/env bash
# PostToolUse(Write|Edit): format code. Never blocks.
input="$(cat)"
path="$(printf '%s' "$input" | python3 -c 'import sys,json
try: print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))
except Exception: print("")' 2>/dev/null)"
case "$path" in
  *.py)
    if command -v ruff >/dev/null 2>&1; then ruff format "$path" >/dev/null 2>&1 || true; ruff check --fix "$path" >/dev/null 2>&1 || true; fi ;;
  *.js|*.jsx|*.ts|*.tsx|*.css|*.json|*.html)
    if command -v npx >/dev/null 2>&1; then npx --yes prettier --write "$path" >/dev/null 2>&1 || true; fi ;;
esac
exit 0
