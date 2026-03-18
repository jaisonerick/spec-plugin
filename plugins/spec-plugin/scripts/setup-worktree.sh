#!/usr/bin/env bash
# Worktree setup script — runs automatically via PostToolUse hook on EnterWorktree.
#
# This is a TEMPLATE. Customize for your project by:
# 1. Adding project-specific config files to the copy list
# 2. Adding service health checks for your stack
# 3. Adding environment variable checks for your API keys
#
# The script receives JSON on stdin with the tool result context.
# It detects the main repo from `git worktree list` and copies
# untracked/gitignored files that worktrees don't get automatically.
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Detect main repo (first entry in git worktree list)
MAIN_REPO=$(git worktree list --porcelain | head -1 | sed 's/worktree //')
WORKTREE_DIR=$(pwd)

if [ "$MAIN_REPO" = "$WORKTREE_DIR" ]; then
  # Not in a worktree — nothing to do
  exit 0
fi

echo "=== Worktree Setup ==="
echo "Main repo: $MAIN_REPO"
echo "Worktree:  $WORKTREE_DIR"
echo ""

# --- Copy files from main repo ---
# Add your project-specific files here
FILES_TO_COPY=(
  ".tool-versions"
  ".env"
  # ".env.local"
  # "config.yaml"
  # "Procfile.dev"
)

for f in "${FILES_TO_COPY[@]}"; do
  if [ -f "$MAIN_REPO/$f" ] && [ ! -f "$WORKTREE_DIR/$f" ]; then
    cp "$MAIN_REPO/$f" "$WORKTREE_DIR/$f"
    printf "${GREEN}✓${NC} Copied %s\n" "$f"
  elif [ -f "$WORKTREE_DIR/$f" ]; then
    printf "${GREEN}✓${NC} %s already exists\n" "$f"
  else
    printf "${YELLOW}⚠${NC} %s not found in main repo\n" "$f"
  fi
done

echo ""

# --- Environment variable checks ---
# Add your project-specific env vars here
# ENV_VARS=(
#   "DATABASE_URL:Database connection"
#   "API_KEY:External API access"
# )
#
# for entry in "${ENV_VARS[@]}"; do
#   var="${entry%%:*}"
#   desc="${entry#*:}"
#   if [ -n "${!var:-}" ]; then
#     printf "${GREEN}✓${NC} %s set (%s)\n" "$var" "$desc"
#   else
#     printf "${YELLOW}⚠${NC} %s missing (%s)\n" "$var" "$desc"
#   fi
# done

# --- Service health checks ---
# Add your project-specific service checks here
# check_service() {
#   local name="$1" url="$2"
#   if curl -sf "$url" >/dev/null 2>&1; then
#     printf "${GREEN}✓${NC} %s UP\n" "$name"
#   else
#     printf "${RED}✗${NC} %s DOWN\n" "$name"
#   fi
# }
#
# echo ""
# echo "Services:"
# check_service "Backend (8000)" "http://localhost:8000/api/health"
# check_service "Database (5432)" "http://localhost:5432"

echo "=== Setup Complete ==="
exit 0
