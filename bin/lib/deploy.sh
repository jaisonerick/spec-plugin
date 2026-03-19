#!/usr/bin/env bash
# Git commit, push, CI wait, and plugin update helpers.
# Expects MARKETPLACE_ROOT and MARKETPLACE_JSON to be set by the caller.

# Wait for any in-flight or queued CI bump runs to finish.
wait_for_idle_ci() {
  echo "→ Waiting for CI to be idle..."

  for status in in_progress queued; do
    local run_id
    run_id=$(gh run list --workflow=bump-version.yml --branch=main --limit=1 \
      --status "$status" --json databaseId --jq '.[0].databaseId' 2>/dev/null || true)

    if [[ -n "$run_id" ]]; then
      gh run watch "$run_id" --exit-status &>/dev/null || echo "  ⚠ CI run failed"
    fi
  done
}

# Stage and commit locally (does not push).
commit_local() {
  local message="$1"
  shift
  local files=("$@")

  cd "$MARKETPLACE_ROOT"

  for f in "${files[@]}"; do
    git add -A -- "$f"
  done

  git commit -m "$message"
}

# Wait for the bump-version CI workflow triggered by our push.
wait_for_bump() {
  echo "→ Waiting for CI bump-version workflow..."
  sleep 3

  local run_id
  run_id=$(gh run list --workflow=bump-version.yml --branch=main --limit=1 \
    --json databaseId --jq '.[0].databaseId')

  if [[ -n "$run_id" ]]; then
    if ! gh run watch "$run_id" --exit-status &>/dev/null; then
      echo "  ⚠ CI run failed or was skipped"
    else
      echo "  ✓ CI bump complete"
    fi
  fi

  echo "→ Pulling CI bump commit..."
  git pull --rebase
}

# Read current marketplace version.
get_marketplace_version() {
  jq -r '.metadata.version // "unknown"' "$MARKETPLACE_JSON"
}

# Read a local plugin's version.
get_plugin_version() {
  local plugin_name="$1"
  local manifest="$MARKETPLACE_ROOT/plugins/$plugin_name/.claude-plugin/plugin.json"
  if [[ -f "$manifest" ]]; then
    jq -r '.version // "unknown"' "$manifest"
  else
    echo "n/a"
  fi
}

# Update the locally installed marketplace plugin and report status.
update_local_plugin() {
  echo "→ Updating local installation..."
  local output
  output=$(claude plugin update nexaedge-marketplace 2>&1 || true)

  if echo "$output" | grep -qi "updated\|installed\|up to date"; then
    echo "  ✓ Local plugin updated"
  else
    echo "  ✓ Local plugin refreshed"
  fi
}

# Print a deploy summary.
# Changes are passed as entries with a prefix:
#   +plugin/skill    skill added
#   +plugin          plugin added (external)
#   -plugin/skill    skill removed
#   -plugin          plugin removed
#   ~plugin/skill    skill updated
print_summary() {
  local before_version="$1"
  local after_version="$2"
  shift 2
  local changes=("${@+"$@"}")

  echo ""
  echo "┌─────────────────────────────────────"
  echo "│ Deploy summary"
  echo "├─────────────────────────────────────"

  if [[ "$before_version" != "$after_version" ]]; then
    echo "│ Marketplace: $before_version → $after_version"
  else
    echo "│ Marketplace: $after_version (unchanged)"
  fi

  for entry in "${changes[@]+"${changes[@]}"}"; do
    local action="${entry:0:1}"
    local target="${entry:1}"
    local plugin_name="${target%%/*}"
    local skill_name=""
    [[ "$target" == */* ]] && skill_name="${target#*/}"

    local version
    version=$(get_plugin_version "$plugin_name")

    case "$action" in
      +)
        if [[ -n "$skill_name" ]]; then
          echo "│ + $plugin_name/$skill_name (vendored into $plugin_name $version)"
        else
          echo "│ + $plugin_name (added)"
        fi
        ;;
      -)
        if [[ -n "$skill_name" ]]; then
          echo "│ - $plugin_name/$skill_name (removed)"
        else
          echo "│ - $plugin_name (removed)"
        fi
        ;;
      ~)
        if [[ -n "$skill_name" ]]; then
          echo "│ ↑ $plugin_name/$skill_name (updated in $plugin_name $version)"
        else
          echo "│ ↑ $plugin_name (updated to $version)"
        fi
        ;;
    esac
  done

  echo "└─────────────────────────────────────"
}

# Full deploy pipeline.
# Usage: deploy <commit-message> <stage-paths...> [-- <changed-plugin-names...>]
# Everything before "--" is a path to git add.
# Everything after "--" is a plugin name for the summary.
deploy() {
  local message="$1"
  shift

  local -a files=()
  local -a changed_plugins=()
  local past_separator=0

  for arg in "$@"; do
    if [[ "$arg" == "--" ]]; then
      past_separator=1
    elif [[ $past_separator -eq 1 ]]; then
      changed_plugins+=("$arg")
    else
      files+=("$arg")
    fi
  done

  local version_before
  version_before=$(get_marketplace_version)

  commit_local "$message" "${files[@]}"
  wait_for_idle_ci

  echo "→ Pulling latest..."
  git pull --rebase

  echo "→ Pushing to main..."
  git push

  wait_for_bump
  update_local_plugin

  local version_after
  version_after=$(get_marketplace_version)

  print_summary "$version_before" "$version_after" "${changed_plugins[@]+"${changed_plugins[@]}"}"

  # Offer to install newly added plugins
  local -a seen_plugins=()
  for entry in "${changed_plugins[@]+"${changed_plugins[@]}"}"; do
    [[ "${entry:0:1}" != "+" ]] && continue
    local target="${entry:1}"
    local pname="${target%%/*}"

    # Skip if already prompted for this plugin
    local already=0
    for s in "${seen_plugins[@]+"${seen_plugins[@]}"}"; do
      [[ "$s" == "$pname" ]] && already=1 && break
    done
    [[ $already -eq 1 ]] && continue
    seen_plugins+=("$pname")

    # Check if already installed
    if claude plugin list 2>/dev/null | grep -q "${pname}@nexaedge-marketplace"; then
      continue
    fi

    echo ""
    read -rp "Install '$pname' at user level? [y/N] " answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
      claude plugin install "${pname}@nexaedge-marketplace" --scope user
    fi
  done
}
