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
CATALOG_URL="https://raw.githubusercontent.com/${REPO_SLUG}/main/index.tsv"

MKT_HOME="${NEXAEDGE_MKT_HOME:-$HOME/.nexaedge}"
# One stable command string for every future invocation. Agents that gate shell
# access match on the literal command, so an agent reaching this script by two
# different paths gets asked to approve it twice. Everything routes through the
# launcher instead, and one approval covers the plugin for good.
LAUNCHER="$MKT_HOME/bin/nexaedge"
# Point NEXAEDGE_MKT_CLONE at a checkout you already have instead of cloning a
# second copy. Antigravity reads the plugins from wherever this lands.
CLONE_DIR="${NEXAEDGE_MKT_CLONE:-$MKT_HOME/marketplace}"
CATALOG_CACHE="$MKT_HOME/index.tsv"
STAMP="$MKT_HOME/last-update"

AG_CONFIG_DIR="${ANTIGRAVITY_CONFIG_HOME:-$HOME/.gemini/config}"
AG_PLUGINS_DIR="$AG_CONFIG_DIR/plugins"
# Antigravity links we made. On Windows the link is a directory junction, which
# a shell cannot tell apart from a real directory, so ownership is recorded.
AG_RECORD="$MKT_HOME/antigravity-links"

STALE_HOURS="${NEXAEDGE_MKT_STALE_HOURS:-12}"

# ── Output ────────────────────────────────────────────────────────────────────

say()  { printf '%s\n' "$*"; }
warn() { printf '%s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$*" >&2; exit 1; }

# ── Paths ─────────────────────────────────────────────────────────────────────

# A Windows path runs from this shell only once cygpath has made it POSIX.
posix_path() {
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -u "$1" 2>/dev/null || printf '%s\n' "$1"
  else
    printf '%s\n' "$1"
  fi
}

# Where this file really is, with every symlink resolved. Invoked through the
# launcher, $BASH_SOURCE is the launcher, and pointing that at itself is a loop.
resolve_self() {
  local src="${BASH_SOURCE[0]}" dir
  while [[ -L "$src" ]]; do
    dir="$(cd -P "$(dirname "$src")" && pwd)"
    src="$(readlink "$src")"
    [[ "$src" == /* ]] || src="$dir/$src"
  done
  printf '%s\n' "$(cd -P "$(dirname "$src")" && pwd)/$(basename "$src")"
}

# ── The agent's own CLI ───────────────────────────────────────────────────────
#
# Claude Code and Codex install plugins through their own command, and that
# command is routinely missing from the PATH an agent hands to a shell: on
# Windows the installer writes the user PATH, and every process started before
# it keeps the old one. So the binary gets resolved rather than assumed, and
# giving up is the last step rather than the first.

runnable() { [[ -n "$1" && -f "$1" && -x "$1" ]]; }

# Every directory the Windows user PATH names, including what an installer added
# after this process started.
windows_path_dirs() {
  command -v powershell.exe >/dev/null 2>&1 || return 0
  powershell.exe -NoProfile -NonInteractive \
    -Command "[Environment]::GetEnvironmentVariable('Path','User')" 2>/dev/null |
    tr -d '\r' | tr ';' '\n'
}

find_cli() {
  local name="$1" candidate dir found npm_dir
  found="$(command -v "$name" 2>/dev/null || true)"
  runnable "$found" && { printf '%s\n' "$found"; return 0; }

  npm_dir="${APPDATA:+$(posix_path "$APPDATA")/npm}"

  # Claude Code exports the binary it is running as: nothing beats asking the
  # agent itself where it lives.
  if [[ "$name" == claude && -n "${CLAUDE_CODE_EXECPATH:-}" ]]; then
    candidate="$(posix_path "$CLAUDE_CODE_EXECPATH")"
    for candidate in "$candidate" "$candidate.exe"; do
      runnable "$candidate" && { printf '%s\n' "$candidate"; return 0; }
    done
  fi

  for candidate in \
    "$HOME/.local/bin/$name" "$HOME/.local/bin/$name.exe" "$HOME/.local/bin/$name.cmd" \
    "${npm_dir:-$HOME/AppData/Roaming/npm}/$name.cmd" "$HOME/bin/$name" \
    "/usr/local/bin/$name" "/opt/homebrew/bin/$name"; do
    runnable "$candidate" && { printf '%s\n' "$candidate"; return 0; }
  done

  while IFS= read -r dir; do
    [[ -n "$dir" ]] || continue
    dir="$(posix_path "$dir")"
    for candidate in "$dir/$name.exe" "$dir/$name.cmd" "$dir/$name"; do
      runnable "$candidate" && { printf '%s\n' "$candidate"; return 0; }
    done
  done < <(windows_path_dirs)

  return 1
}

cli_for() {
  find_cli "$1" || die "cannot find the '$1' command on this machine. Looked at PATH, \$HOME/.local/bin, the npm global directory and the Windows user PATH. Install $1, or add it to PATH, and run this again."
}

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
  find_cli claude >/dev/null 2>&1 && found+=(claude)
  find_cli codex  >/dev/null 2>&1 && found+=(codex)
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
#
# It arrives as one tab-separated row per plugin — name, tagline, platforms,
# keywords, description — because the only interpreter every supported machine
# has is this shell.
fetch_catalog() {
  # Point at a working copy's index.tsv while developing the marketplace itself.
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

lowercase() { printf '%s' "$*" | tr '[:upper:]' '[:lower:]'; }

# Print "name<TAB>tagline<TAB>platforms" for entries matching an optional query.
# A checkout on Windows can carry CRLF, which would otherwise leave the last cell
# of every row ending in a carriage return.
catalog_rows() {
  local query platform file name tagline platforms keywords description
  query="$(lowercase "${1:-}")"
  platform="${2:-}"
  file="$(fetch_catalog)"
  while IFS=$'\t' read -r name tagline platforms keywords description; do
    [[ -n "$name" ]] || continue
    if [[ -n "$platform" ]]; then
      case ",$platforms," in *",$platform,"*) ;; *) continue ;; esac
    fi
    if [[ -n "$query" ]]; then
      case "$(lowercase "$name $tagline $keywords $description")" in *"$query"*) ;; *) continue ;; esac
    fi
    printf '%s\t%s\t%s\n' "$name" "$tagline" "$platforms"
  done < <(tr -d '\r' < "$file")
}

# 0 supported, 1 known but not here, 2 not in the catalog. Reads a catalog the
# caller already fetched: called as a condition, a failure in here would be read
# as an answer.
catalog_supports() {
  local file="$1" name="$2" platform="$3" row_name row_platforms
  while IFS=$'\t' read -r row_name _ row_platforms _; do
    [[ "$row_name" == "$name" ]] || continue
    case ",$row_platforms," in *",$platform,"*) return 0 ;; *) return 1 ;; esac
  done < <(tr -d '\r' < "$file")
  return 2
}

# ── Claude Code ───────────────────────────────────────────────────────────────

claude_ensure_marketplace() {
  local cli="$1"
  "$cli" plugin marketplace list 2>/dev/null | grep -q "$MARKETPLACE_NAME" && return 0
  "$cli" plugin marketplace add "$REPO_SLUG"
}

claude_install() {
  local cli p
  cli="$(cli_for claude)"
  claude_ensure_marketplace "$cli"
  for p in "$@"; do "$cli" plugin install "${p}@${MARKETPLACE_NAME}" --scope user; done
  say ""
  say "Installed. Claude Code loads plugins at startup, so run /reload-plugins or restart to use them now."
}

claude_remove()  { local cli p; cli="$(cli_for claude)"; for p in "$@"; do "$cli" plugin uninstall "${p}@${MARKETPLACE_NAME}"; done; }
claude_status()  { local cli; cli="$(cli_for claude)"; "$cli" plugin list 2>/dev/null | grep "$MARKETPLACE_NAME" || say "no plugins installed from $MARKETPLACE_NAME"; }
claude_update()  {
  local cli p
  cli="$(cli_for claude)"
  "$cli" plugin marketplace update "$MARKETPLACE_NAME"
  for p in $("$cli" plugin list 2>/dev/null | grep -o "[^ ]*@${MARKETPLACE_NAME}" | sed "s/@${MARKETPLACE_NAME}//"); do
    "$cli" plugin update "${p}@${MARKETPLACE_NAME}" || true
  done
}

# ── Codex ─────────────────────────────────────────────────────────────────────

codex_ensure_marketplace() {
  local cli="$1"
  "$cli" plugin marketplace list 2>/dev/null | grep -q "$MARKETPLACE_NAME" && return 0
  "$cli" plugin marketplace add "$REPO_SLUG" --ref main
}

codex_install() {
  local cli p
  cli="$(cli_for codex)"
  codex_ensure_marketplace "$cli"
  for p in "$@"; do "$cli" plugin add "${p}@${MARKETPLACE_NAME}"; done
  say ""
  say "Installed. Start a new Codex thread to pick them up."
}

codex_remove()  { local cli p; cli="$(cli_for codex)"; for p in "$@"; do "$cli" plugin remove "${p}@${MARKETPLACE_NAME}"; done; }
codex_status()  { local cli; cli="$(cli_for codex)"; "$cli" plugin list 2>/dev/null | grep "$MARKETPLACE_NAME" || say "no plugins installed from $MARKETPLACE_NAME"; }
codex_update()  { local cli; cli="$(cli_for codex)"; "$cli" plugin marketplace upgrade; }

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

ag_record()  { mkdir -p "$(dirname "$AG_RECORD")"; grep -qxF "$1" "$AG_RECORD" 2>/dev/null || printf '%s\n' "$1" >> "$AG_RECORD"; }
ag_forget()  { [[ -f "$AG_RECORD" ]] || return 0; grep -vxF "$1" "$AG_RECORD" > "$AG_RECORD.tmp" || true; mv "$AG_RECORD.tmp" "$AG_RECORD"; }

# Only ever remove our own links, never a directory someone put there by hand.
ag_is_ours() {
  local link="$1"
  [[ -L "$link" && "$(readlink "$link")" == "$CLONE_DIR"/* ]] && return 0
  grep -qxF "$(basename "$link")" "$AG_RECORD" 2>/dev/null
}

# Windows gives an unprivileged user no symlink, and its `ln` copies the
# directory instead of saying so. A junction needs no privilege and Antigravity
# follows it the same way.
ag_make_link() {
  local target="$1" link="$2"
  ln -sfn "$target" "$link" 2>/dev/null && [[ -L "$link" ]] && return 0
  rm -rf "$link"
  command -v cygpath >/dev/null 2>&1 || return 1
  cmd //c mklink //J "$(cygpath -w "$link")" "$(cygpath -w "$target")" >/dev/null 2>&1
}

ag_unlink() {
  local link="$1"
  [[ -L "$link" ]] && { rm -f "$link"; return 0; }
  # A junction goes with rmdir, which unlinks it without following it.
  if [[ -d "$link" ]] && command -v cygpath >/dev/null 2>&1; then
    cmd //c rmdir "$(cygpath -w "$link")" >/dev/null 2>&1 && return 0
  fi
  rm -f "$link"
}

ag_install() {
  ag_ensure_clone
  mkdir -p "$AG_PLUGINS_DIR"

  local name target link
  for name in "$@"; do
    target="$CLONE_DIR/plugins/$name"
    [[ -d "$target" ]] || die "$target does not exist in the clone"
    link="$(ag_link "$name")"
    if [[ -e "$link" ]] && ! ag_is_ours "$link"; then
      die "$link already exists and is not one of ours. Move it aside first."
    fi
    ag_make_link "$target" "$link" || die "could not link $target into $AG_PLUGINS_DIR"
    ag_record "$name"
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
      ag_unlink "$link"
      ag_forget "$name"
    elif [[ -e "$link" ]]; then
      warn "note: $link is not one of ours, leaving it alone"
    fi
  done
}

ag_status() {
  [[ -d "$AG_PLUGINS_DIR" ]] || { say "nothing installed under $AG_PLUGINS_DIR"; return 0; }
  local link listed=0
  for link in "$AG_PLUGINS_DIR"/*; do
    ag_is_ours "$link" || continue
    say "$(basename "$link")"
    listed=1
  done
  [[ $listed -eq 1 ]] || say "no plugins installed from $MARKETPLACE_NAME"
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

  local catalog p rc
  catalog="$(fetch_catalog)"
  for p in "$@"; do
    rc=0
    catalog_supports "$catalog" "$p" "$PLATFORM" || rc=$?
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
# An agent updates its plugin into a new directory, so this is re-pointed on
# every install and every update rather than only when it is missing.
install_launcher() {
  local self
  self="$(resolve_self)"
  # Running as the launcher itself, there is nothing else to point at.
  [[ "$self" == "$LAUNCHER" ]] && return 0

  mkdir -p "$(dirname "$LAUNCHER")"
  if ! ln -sfn "$self" "$LAUNCHER" 2>/dev/null || [[ ! -L "$LAUNCHER" ]]; then
    # Windows has no symlink here, and its `ln` copies instead of saying so. A
    # copy would go stale the next time the plugin updates, so what lands is a
    # shim pointing at wherever this copy lives now.
    rm -rf "$LAUNCHER"
    printf '#!/usr/bin/env bash\nexec "%s" "$@"\n' "$self" > "$LAUNCHER.tmp"
    chmod +x "$LAUNCHER.tmp"
    mv -f "$LAUNCHER.tmp" "$LAUNCHER"
  fi

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
  local cli
  say "platform: $PLATFORM"
  case "$PLATFORM" in
    claude|codex) cli="$(cli_for "$PLATFORM")"; say "command:  $cli" ;;
  esac
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

  # An agent updates a plugin into a new directory and drops the old one, so the
  # launcher is re-pointed at this copy first, stale or not. Wired into session
  # start, this repairs it one session after any update.
  install_launcher >/dev/null

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
