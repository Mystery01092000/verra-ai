#!/usr/bin/env bash
# PostToolUse(Write|Edit) check. Non-blocking (exit 0) — surfaces design-system drift as a note.
input="$(cat)"
path="$(printf '%s' "$input" | python3 -c 'import sys,json;
try:
  d=json.load(sys.stdin); print(d.get("tool_input",{}).get("file_path",""))
except Exception:
  print("")' 2>/dev/null)"
case "$path" in
  *.html|*.css|*.jsx|*.tsx)
    # warn on raw hex colors that are not the approved tokens
    if grep -Eoq '#[0-9a-fA-F]{6}' "$path" 2>/dev/null; then
      bad=$(grep -Eo '#[0-9a-fA-F]{6}' "$path" | sort -u | grep -Eiv '5566FF|4F46E5|3A33C9|8A92FF|E0E3FF|111114|5B5B66|F5F5F5|FFFFFF|E8E8EC' | head -5 || true)
      if [ -n "$bad" ]; then
        echo "NOTE (validate-design): non-token colors found in $(basename "$path"): $bad — prefer design tokens (design/design-tokens.css)." >&2
      fi
    fi
  ;;
esac
exit 0
