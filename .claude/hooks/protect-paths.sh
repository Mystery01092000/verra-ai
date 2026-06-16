#!/usr/bin/env bash
# PreToolUse(Write|Edit): block direct edits to generated artifacts. Regenerate via build scripts.
input="$(cat)"
path="$(printf '%s' "$input" | python3 -c 'import sys,json
try:
  print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))
except Exception:
  print("")' 2>/dev/null)"
case "$path" in
  *.docx)
    echo "BLOCKED by protect-paths: $path is a generated artifact. Edit the source script and regenerate, do not hand-edit the .docx." >&2
    exit 2 ;;
esac
exit 0
