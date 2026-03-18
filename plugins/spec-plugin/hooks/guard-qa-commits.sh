#!/usr/bin/env bash
# QA commit guard — blocks commits of files outside specs/*/qa/
# Used as PreToolUse hook on Bash for qa agent
# Exit: 0=allow, 2=block with message
set -euo pipefail

# Read the command from stdin (hook receives tool input as JSON)
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('command',''))" 2>/dev/null || echo "")

# Only intercept git add and git commit commands
case "$COMMAND" in
  git\ add\ *)
    # Extract paths after 'git add'
    PATHS="${COMMAND#git add }"
    for path in $PATHS; do
      # Skip flags
      [[ "$path" == -* ]] && continue
      # Allow specs/*/qa/* paths
      if [[ ! "$path" == specs/*/qa/* ]]; then
        echo "BLOCKED: QA agents can only stage files in specs/*/qa/"
        echo "Attempted to stage: $path"
        echo "If you need source changes, report the issue to the team lead."
        exit 2
      fi
    done
    ;;
  git\ commit\ *)
    # Check what's actually staged
    STAGED=$(git diff --cached --name-only 2>/dev/null || true)
    if [[ -z "$STAGED" ]]; then
      exit 0  # Nothing staged, allow (git will handle the empty commit)
    fi
    while IFS= read -r file; do
      if [[ ! "$file" == specs/*/qa/* ]]; then
        echo "BLOCKED: QA agents can only commit files in specs/*/qa/"
        echo "Staged file outside allowed path: $file"
        echo "Unstage non-spec files before committing."
        exit 2
      fi
    done <<< "$STAGED"
    ;;
esac

# Allow all other commands
exit 0
