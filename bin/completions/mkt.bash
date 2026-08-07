#!/usr/bin/env bash
# Bash completion for mkt

_mkt_root() {
  echo "${MKT_ROOT:-$(cd "$(dirname "$(command -v mkt)")/.." 2>/dev/null && pwd)}"
}

_mkt_plugins() {
  local root="$(_mkt_root)"
  [[ -d "$root/plugins" ]] || return
  for d in "$root"/plugins/*/; do
    [[ -d "$d" ]] && basename "$d"
  done
}

_mkt_skills() {
  local plugin="$1"
  local root="$(_mkt_root)"
  local skills_dir="$root/plugins/$plugin/skills"
  [[ -d "$skills_dir" ]] || return
  for d in "$skills_dir"/*/; do
    [[ -d "$d" ]] && basename "$d"
  done
}

_mkt_remove_targets() {
  local root="$(_mkt_root)"
  [[ -d "$root/plugins" ]] || return
  for plugin_dir in "$root"/plugins/*/; do
    [[ -d "$plugin_dir" ]] || continue
    local pname
    pname=$(basename "$plugin_dir")
    echo "$pname"
    if [[ -d "$plugin_dir/skills" ]]; then
      for skill_dir in "$plugin_dir"/skills/*/; do
        [[ -d "$skill_dir" ]] || continue
        echo "$pname/$(basename "$skill_dir")"
      done
    fi
  done
}

_mkt() {
  local cur prev words cword
  _init_completion || return

  local commands="add remove update generate completions"

  # Find the subcommand
  local cmd=""
  local i
  for ((i=1; i < cword; i++)); do
    case "${words[i]}" in
      add|remove|update|generate|completions) cmd="${words[i]}"; break ;;
    esac
  done

  # No subcommand yet — complete commands
  if [[ -z "$cmd" ]]; then
    COMPREPLY=($(compgen -W "$commands --help" -- "$cur"))
    return
  fi

  # Complete option values
  case "$prev" in
    --plugin)
      COMPREPLY=($(compgen -W "$(_mkt_plugins)" -- "$cur"))
      return
      ;;
    --skill)
      local plugin=""
      for ((i=1; i < cword; i++)); do
        if [[ "${words[i]}" == "--plugin" && $((i+1)) -lt cword ]]; then
          plugin="${words[i+1]}"
          break
        fi
      done
      if [[ -n "$plugin" ]]; then
        COMPREPLY=($(compgen -W "$(_mkt_skills "$plugin")" -- "$cur"))
      fi
      return
      ;;
  esac

  # Complete options/args per subcommand
  case "$cmd" in
    add)
      COMPREPLY=($(compgen -W "--plugin --help" -- "$cur"))
      ;;
    remove)
      COMPREPLY=($(compgen -W "$(_mkt_remove_targets) --help" -- "$cur"))
      ;;
    update)
      COMPREPLY=($(compgen -W "--dry-run --plugin --skill --help" -- "$cur"))
      ;;
    completions)
      COMPREPLY=($(compgen -W "bash zsh --help" -- "$cur"))
      ;;
  esac
}

complete -F _mkt mkt
