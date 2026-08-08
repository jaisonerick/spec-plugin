#!/usr/bin/env bash
# Cross-agent front end for the nexaedge marketplace.
#
# Claude Code and Codex each have a native marketplace: this script drives their
# CLIs. Antigravity has none, but discovers customizations by path, so there a
# plugin is one local clone plus a symlink into the global customization root.
set -euo pipefail

REPO_SLUG="nexaedge/nexaedge-marketplace"
REPO_URL="https://github.com/${REPO_SLUG}.git"
MARKETPLACE_NAME="nexaedge-marketplace"
CATALOG_URL="https://raw.githubusercontent.com/${REPO_SLUG}/main/index.json"

MKT_HOME="${NEXAEDGE_MKT_HOME:-$HOME/.nexaedge}"
# One stable command string for every future invocation. Agents that gate shell
# access match on the literal command, so an agent reaching this script by two
# different paths gets asked to approve it twice. Everything routes through the
# launcher instead, and one approval covers the plugin for good.
LAUNCHER="$MKT_HOME/bin/nexaedge"
# Point NEXAEDGE_MKT_CLONE at a checkout you already have instead of cloning a
# second copy. Antigravity reads the plugins from wherever this lands.
CLONE_DIR="${NEXAEDGE_MKT_CLONE:-$MKT_HOME/marketplace}"
CATALOG_CACHE="$MKT_HOME/index.json"
STAMP="$MKT_HOME/last-update"

AG_CONFIG_DIR="${ANTIGRAVITY_CONFIG_HOME:-$HOME/.gemini/config}"
AG_PLUGINS_DIR="$AG_CONFIG_DIR/plugins"

STALE_HOURS="${NEXAEDGE_MKT_STALE_HOURS:-12}"

# ── Output ────────────────────────────────────────────────────────────────────

say()  { printf '%s\n' "$*"; }
warn() { printf '%s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$*" >&2; exit 1; }

# ── Platform detection ────────────────────────────────────────────────────────

# Which agent is running this? Environment markers identify the running agent;
# an installed binary only proves the agent exists on this machine. When markers
# are absent and more than one agent is installed, refuse to guess.
detect_platform() {
  if [[ -n "${NEXAEDGE_MKT_PLATFORM:-}" ]]; then
    printf '%s\n' "$NEXAEDGE_MKT_PLATFORM"; return 0
  fi

  [[ -n "${CLAUDECODE:-}${CLAUDE_CODE_ENTRYPOINT:-}" ]] && { say claude; return 0; }
  [[ -n "${CODEX_HOME:-}${CODEX_SANDBOX:-}${CODEX_THREAD_ID:-}" ]] && { say codex; return 0; }
  [[ -n "${ANTIGRAVITY_SESSION_ID:-}${GEMINI_CLI_SESSION_ID:-}" ]] && { say antigravity; return 0; }

  local -a found=()
  command -v claude >/dev/null 2>&1 && found+=(claude)
  command -v codex  >/dev/null 2>&1 && found+=(codex)
  [[ -d "$AG_CONFIG_DIR" ]] && found+=(antigravity)

  case ${#found[@]} in
    1) printf '%s\n' "${found[0]}" ;;
    0) die "no supported agent found (looked for claude, codex, $AG_CONFIG_DIR)" ;;
    *) die "more than one agent installed here (${found[*]}). Environment markers did not say which one is running — pass --platform <name>." ;;
  esac
}

PLATFORM=""
resolve_platform() {
  [[ -n "$PLATFORM" ]] || PLATFORM="$(detect_platform)"
  case "$PLATFORM" in
    claude|codex|antigravity) ;;
    *) die "unknown platform '$PLATFORM' (expected claude, codex or antigravity)" ;;
  esac
}

# ── Catalog ───────────────────────────────────────────────────────────────────

# The catalog lists what the marketplace offers. It lives in the repo, so it is
# fetched rather than bundled: an installed plugin is a copy frozen at install
# time, and a stale listing is worse than a slow one. Falls back to the last
# good copy when offline.
fetch_catalog() {
  # Point at a working copy's index.json while developing the marketplace itself.
  if [[ -n "${NEXAEDGE_MKT_INDEX:-}" ]]; then
    [[ -f "$NEXAEDGE_MKT_INDEX" ]] || die "NEXAEDGE_MKT_INDEX is set but $NEXAEDGE_MKT_INDEX does not exist"
    printf '%s\n' "$NEXAEDGE_MKT_INDEX"; return 0
  fi

  # A cached listing that is hours old is fine, and going to the network on every
  # `list` costs an approval prompt on agents that gate network access. Refresh
  # only when the cache is missing or stale; `update` always refreshes.
  if [[ "${FORCE_REFRESH:-0}" -eq 0 && -f "$CATALOG_CACHE" ]]; then
    local age_limit=$(( STALE_HOURS * 3600 ))
    local now cached
    now="$(date +%s)"
    cached="$(stat -f %m "$CATALOG_CACHE" 2>/dev/null || stat -c %Y "$CATALOG_CACHE" 2>/dev/null || echo 0)"
    if (( now - cached < age_limit )); then
      printf '%s\n' "$CATALOG_CACHE"; return 0
    fi
  fi

  mkdir -p "$MKT_HOME"
  if curl -fsSL --max-time 10 "$CATALOG_URL" -o "$CATALOG_CACHE.tmp" 2>/dev/null; then
    mv "$CATALOG_CACHE.tmp" "$CATALOG_CACHE"
  else
    rm -f "$CATALOG_CACHE.tmp"
    [[ -f "$CATALOG_CACHE" ]] || die "cannot reach the catalog and no cached copy exists"
    warn "note: could not refresh the catalog, using the cached copy"
  fi
  printf '%s\n' "$CATALOG_CACHE"
}

# Print "name<TAB>summary<TAB>platforms" for entries matching an optional query.
catalog_rows() {
  local query="${1:-}" platform="${2:-}"
  python3 - "$(fetch_catalog)" "$query" "$platform" <<'PY'
import json, sys
path, query, platform = sys.argv[1], sys.argv[2].lower(), sys.argv[3]
plugins = json.load(open(path)).get("plugins", [])
for p in plugins:
    if platform and platform not in p.get("platforms", []):
        continue
    if query:
        haystack = " ".join([
            p.get("name", ""), p.get("tagline", ""), p.get("description", ""),
            " ".join(p.get("keywords", [])),
        ]).lower()
        if query not in haystack:
            continue
    print("\t".join([p.get("name", ""), p.get("tagline", ""), ",".join(p.get("platforms", []))]))
PY
}

catalog_supports() {
  local name="$1" platform="$2"
  python3 - "$(fetch_catalog)" "$name" "$platform" <<'PY'
import json, sys
path, name, platform = sys.argv[1:4]
for p in json.load(open(path)).get("plugins", []):
    if p.get("name") == name:
        sys.exit(0 if platform in p.get("platforms", []) else 1)
sys.exit(2)
PY
}

# ── Claude Code ───────────────────────────────────────────────────────────────

claude_ensure_marketplace() {
  claude plugin marketplace list 2>/dev/null | grep -q "$MARKETPLACE_NAME" && return 0
  claude plugin marketplace add "$REPO_SLUG"
}

claude_install() {
  claude_ensure_marketplace
  local p
  for p in "$@"; do claude plugin install "${p}@${MARKETPLACE_NAME}" --scope user; done
  say ""
  say "Installed. Claude Code loads plugins at startup, so run /reload-plugins or restart to use them now."
}

claude_remove()  { local p; for p in "$@"; do claude plugin uninstall "${p}@${MARKETPLACE_NAME}"; done; }
claude_status()  { claude plugin list 2>/dev/null | grep "$MARKETPLACE_NAME" || say "no plugins installed from $MARKETPLACE_NAME"; }
claude_update()  {
  claude plugin marketplace update "$MARKETPLACE_NAME"
  local p
  for p in $(claude plugin list 2>/dev/null | grep -o "[^ ]*@${MARKETPLACE_NAME}" | sed "s/@${MARKETPLACE_NAME}//"); do
    claude plugin update "${p}@${MARKETPLACE_NAME}" || true
  done
}

# ── Codex ─────────────────────────────────────────────────────────────────────

codex_ensure_marketplace() {
  codex plugin marketplace list 2>/dev/null | grep -q "$MARKETPLACE_NAME" && return 0
  codex plugin marketplace add "$REPO_SLUG" --ref main
}

codex_install() {
  codex_ensure_marketplace
  local p
  for p in "$@"; do codex plugin add "${p}@${MARKETPLACE_NAME}"; done
  say ""
  say "Installed. Start a new Codex thread to pick them up."
}

codex_remove()  { local p; for p in "$@"; do codex plugin remove "${p}@${MARKETPLACE_NAME}"; done; }
codex_status()  { codex plugin list 2>/dev/null | grep "$MARKETPLACE_NAME" || say "no plugins installed from $MARKETPLACE_NAME"; }
codex_update()  { codex plugin marketplace upgrade; }

# ── Antigravity ───────────────────────────────────────────────────────────────
#
# Antigravity has no marketplace. It discovers customizations from roots on
# disk, so installing a plugin means linking it into the global root rather than
# copying anything. One clone serves every project on the machine.

ag_ensure_clone() {
  if [[ -d "$CLONE_DIR/.git" ]]; then
    # Never pull over someone's work: the clone may be a working copy of this
    # very repository, pointed at directly for development.
    if [[ -n "$(git -C "$CLONE_DIR" status --porcelain 2>/dev/null)" ]]; then
      warn "note: $CLONE_DIR has uncommitted changes, leaving it alone"
    else
      git -C "$CLONE_DIR" pull --ff-only --quiet 2>/dev/null || warn "note: could not update the clone at $CLONE_DIR"
    fi
    return 0
  fi
  if [[ -e "$CLONE_DIR" ]]; then
    die "$CLONE_DIR exists but is not a git clone. Move it aside, or point NEXAEDGE_MKT_HOME somewhere else."
  fi
  mkdir -p "$(dirname "$CLONE_DIR")"
  git clone --quiet "$REPO_URL" "$CLONE_DIR"
}

# One symlink per plugin into the global discovery directory.
#
# `plugins.json` can register the whole clone as an extra root, but its
# `include_only` filter is unusable on Antigravity 2.0.6: any entry carrying one
# loads nothing at all, with no error. Measured, not read: an entry filtered to a
# plugin that exists still yielded zero, and the same entry without the filter
# yielded everything. Symlinking into the default root selects exactly what was
# asked for, follows correctly, and leaves the user's own config untouched.

ag_link() { printf '%s\n' "$AG_PLUGINS_DIR/$1"; }

# Only ever remove our own links, never a directory someone put there by hand.
ag_is_ours() {
  local link="$1"
  [[ -L "$link" ]] && [[ "$(readlink "$link")" == "$CLONE_DIR"/* ]]
}

ag_install() {
  ag_ensure_clone
  mkdir -p "$AG_PLUGINS_DIR"

  local name target link
  for name in "$@"; do
    target="$CLONE_DIR/plugins/$name"
    [[ -d "$target" ]] || die "$target does not exist in the clone"
    link="$(ag_link "$name")"
    if [[ -e "$link" && ! -L "$link" ]]; then
      die "$link already exists and is not a symlink. Move it aside first."
    fi
    ln -sfn "$target" "$link"
  done

  say ""
  say "Linked into $AG_PLUGINS_DIR"
  say "Reload the Antigravity window to pick them up."
}

ag_remove() {
  local name link
  for name in "$@"; do
    link="$(ag_link "$name")"
    if ag_is_ours "$link"; then
      rm -f "$link"
    elif [[ -e "$link" ]]; then
      warn "note: $link is not one of ours, leaving it alone"
    fi
  done
}

ag_status() {
  [[ -d "$AG_PLUGINS_DIR" ]] || { say "nothing installed under $AG_PLUGINS_DIR"; return 0; }
  local link found=0
  for link in "$AG_PLUGINS_DIR"/*; do
    ag_is_ours "$link" || continue
    say "$(basename "$link")"
    found=1
  done
  [[ $found -eq 1 ]] || say "no plugins installed from $MARKETPLACE_NAME"
}

ag_update() { ag_ensure_clone; }

# ── Commands ──────────────────────────────────────────────────────────────────

cmd_list() {
  resolve_platform
  local query="${1:-}" rows
  rows="$(catalog_rows "$query" "$PLATFORM")"
  [[ -n "$rows" ]] || { say "nothing in the catalog matches${query:+ \"$query\"} on $PLATFORM"; return 0; }
  printf '%s\n' "$rows" | while IFS=$'\t' read -r name summary _; do
    printf '  %-20s %s\n' "$name" "$summary"
  done
}

cmd_install() {
  [[ $# -gt 0 ]] || die "install needs at least one plugin name (see: nexaedge.sh list)"
  resolve_platform

  local p rc
  for p in "$@"; do
    rc=0
    catalog_supports "$p" "$PLATFORM" || rc=$?
    case $rc in
      0) ;;
      1) die "'$p' does not run on $PLATFORM (see: nexaedge.sh list)" ;;
      *) die "'$p' is not in the catalog (see: nexaedge.sh list)" ;;
    esac
  done

  case "$PLATFORM" in
    claude)      claude_install "$@" ;;
    codex)       codex_install "$@" ;;
    antigravity) ag_install "$@" ;;
  esac
  install_launcher
  mkdir -p "$MKT_HOME"
  date +%s > "$STAMP"
}

# Put the stable command string in place, pointing at wherever this copy lives.
install_launcher() {
  local self
  self="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
  mkdir -p "$(dirname "$LAUNCHER")"
  ln -sfn "$self" "$LAUNCHER"
  say ""
  say "Future work goes through a single command:"
  say "  $LAUNCHER"
  say "Approve it once and the plugin stops asking."
}

cmd_remove() {
  [[ $# -gt 0 ]] || die "remove needs at least one plugin name"
  resolve_platform
  case "$PLATFORM" in
    claude)      claude_remove "$@" ;;
    codex)       codex_remove "$@" ;;
    antigravity) ag_remove "$@" ;;
  esac
}

cmd_status() {
  resolve_platform
  say "platform: $PLATFORM"
  say ""
  case "$PLATFORM" in
    claude)      claude_status ;;
    codex)       codex_status ;;
    antigravity) ag_status ;;
  esac
}

# Refresh the marketplace and everything installed from it. With --if-stale this
# is a cheap no-op most of the time, which is what makes it safe to wire into
# session start.
cmd_update() {
  local if_stale=0
  [[ "${1:-}" == "--if-stale" ]] && if_stale=1

  if [[ $if_stale -eq 1 && -f "$STAMP" ]]; then
    local last now
    last="$(cat "$STAMP" 2>/dev/null || echo 0)"
    now="$(date +%s)"
    (( now - last < STALE_HOURS * 3600 )) && return 0
  fi

  resolve_platform
  FORCE_REFRESH=1
  mkdir -p "$MKT_HOME"
  date +%s > "$STAMP"

  case "$PLATFORM" in
    claude)      claude_update ;;
    codex)       codex_update ;;
    antigravity) ag_update ;;
  esac
}

usage() {
  cat <<EOF
Usage: nexaedge.sh <command> [--platform claude|codex|antigravity] [args]

  list [query]        List plugins available for this agent
  install <name>...   Install plugins for this agent, at user/global scope
  remove <name>...    Remove plugins
  update [--if-stale] Refresh the marketplace and installed plugins
  status              Show the detected platform and what is installed
  detect              Print the detected platform
EOF
  exit 1
}

# ── Dispatch ──────────────────────────────────────────────────────────────────

[[ $# -ge 1 ]] || usage
command="$1"; shift

args=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --platform) PLATFORM="${2:-}"; shift 2 ;;
    --help|-h)  usage ;;
    *)          args+=("$1"); shift ;;
  esac
done
set -- ${args+"${args[@]}"}

case "$command" in
  list|ls|search) cmd_list "$@" ;;
  install|add)    cmd_install "$@" ;;
  remove|rm)      cmd_remove "$@" ;;
  update)         cmd_update "$@" ;;
  status)         cmd_status "$@" ;;
  detect)         resolve_platform; say "$PLATFORM" ;;
  --help|-h)      usage ;;
  *)              die "unknown command '$command'" ;;
esac
