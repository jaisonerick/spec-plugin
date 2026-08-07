# nexaedge

One front end for the NexaEdge plugin catalog across Claude Code, Codex and Antigravity.

Ask for things in plain language: "what plugins are available?", "install the html report one", "update my plugins". The skill detects which agent is running and translates to that agent's native install path.

## Why it exists

The three agents install plugins in three different ways, and one of them does not install plugins at all. Without a front end, using this catalog means remembering which commands your current agent understands.

It also enforces one rule: **everything installs at user scope, once per machine.** The alternative, copying skills into each project repository, is what produces the same skill in five places at five different versions.

## What it does per agent

| | Mechanism | Where it lands |
|---|---|---|
| Claude Code | native marketplace | `~/.claude/plugins/cache` |
| Codex | native marketplace | `~/.codex/plugins/cache` |
| Antigravity | symlink per plugin | one clone in `~/.nexaedge/marketplace`, linked from `~/.gemini/config/plugins/` |

Claude and Codex copy into a cache, so an update needs an explicit refresh. Antigravity follows the link into the clone, so a `git pull` is live the next time it starts.

Antigravity also offers `plugins.json`, which registers a whole directory as an extra root. This plugin does not use it. On Antigravity 2.0.6 its `include_only` filter makes an entry load **nothing at all**, silently, so there is no way to select individual plugins through it. Symlinks give exact selection and leave the user's own config alone.

## Staying current

`scripts/nexaedge.sh update --if-stale` is a no-op unless the last update was over 12 hours ago, which is cheap enough to run at session start. On Claude Code that is already wired to a `SessionStart` hook.

On Codex and Antigravity nothing is wired: the format for plugin-provided hooks is not confirmed on either, and guessing it would produce a plugin that fails to load. Run `update` when you want it, or call the script from your own shell startup.

## Configuration

| Variable | Purpose |
|---|---|
| `NEXAEDGE_MKT_PLATFORM` | Force the platform instead of detecting it |
| `NEXAEDGE_MKT_HOME` | Where the Antigravity clone and cache live (default `~/.nexaedge`) |
| `NEXAEDGE_MKT_CLONE` | Use a checkout you already have instead of cloning a second copy |
| `NEXAEDGE_MKT_INDEX` | Use a local `index.json`, for developing the marketplace itself |
| `NEXAEDGE_MKT_STALE_HOURS` | Window for `update --if-stale` (default 12) |
| `ANTIGRAVITY_CONFIG_HOME` | Antigravity global customization root (default `~/.gemini/config`) |
