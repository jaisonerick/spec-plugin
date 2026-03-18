# Claude Marketplace

This is a Claude Code **plugin marketplace** repository. It contains multiple plugins — both local (in `plugins/`) and external (referenced from GitHub or other sources).

## Repository Structure

```
.claude-plugin/
  marketplace.json          # Marketplace catalog (name, owner, plugin list)
.github/
  workflows/
    bump-version.yml        # Auto-bumps versions on merge to main
plugins/
  <plugin-name>/            # Local plugin directory
    .claude-plugin/
      plugin.json           # Plugin manifest (name, version, description, author)
    agents/                 # Agent definitions (.md files)
    skills/                 # Skills (directories with SKILL.md)
    hooks/                  # Hook scripts
    README.md               # Plugin documentation
CHANGELOG.md                # Version history (auto-updated by CI)
README.md                   # Marketplace documentation
```

## Versioning

Versions use sequential format: `v1`, `v2`, `v3`, etc. No semver.

There are two independent versions:

- **Marketplace version** (`metadata.version` in `.claude-plugin/marketplace.json`): Tracks changes to the marketplace itself (adding/removing plugins, changing marketplace metadata).
- **Plugin version** (`version` in `plugins/<name>/.claude-plugin/plugin.json`): Tracks each local plugin's own evolution.

**Do NOT set the plugin version in the marketplace plugins array.** The plugin's own `plugin.json` is the source of truth — the marketplace entry must not set `version` (the manifest always wins silently). For external plugins, the version comes from the plugin's own `plugin.json`.

**Versions are bumped automatically by CI** (`.github/workflows/bump-version.yml`). On every push to main:
- CI detects every subfolder under `plugins/` with changed files and bumps each plugin's version independently
- If files under `.claude-plugin/`, `README.md`, or `CLAUDE.md` changed → marketplace version is bumped
- CHANGELOG.md is updated with the commit message
- The bump commit includes `[skip-bump]` to prevent infinite loops

For manual version changes, include `[skip-bump]` in the commit message.

**Do NOT bump versions manually in regular commits** — let CI handle it.

## Marketplace Format Rules

### marketplace.json

Required fields: `name`, `owner` (with `name`), `plugins` array.

The marketplace uses `pluginRoot` to set the base directory for local plugin paths. With `"pluginRoot": "./plugins"`, local sources use `"./spec-plugin"` instead of `"./plugins/spec-plugin"`.

Each plugin entry has only `name` and `source`:

```json
{
  "plugins": [
    {
      "name": "my-local-plugin",
      "source": "./my-local-plugin"
    },
    {
      "name": "my-external-plugin",
      "source": {
        "source": "github",
        "repo": "owner/repo"
      }
    }
  ]
}
```

### Plugin sources

**Relative path** — for plugins in this repo:
```json
{ "name": "my-plugin", "source": "./my-plugin" }
```
Paths resolve relative to `pluginRoot` (which is `./plugins`). Must start with `./`. Cannot use `../`.

**GitHub repository** — for plugins hosted on GitHub:
```json
{
  "name": "my-plugin",
  "source": {
    "source": "github",
    "repo": "owner/repo",
    "ref": "some-branch-or-tag"
  }
}
```
`ref` (branch/tag) is optional — defaults to the repo's default branch.

**Git URL** — for any git host (GitLab, Bitbucket, self-hosted):
```json
{
  "source": { "source": "url", "url": "https://gitlab.com/team/plugin.git", "ref": "main" }
}
```

**Git subdirectory** — for plugins inside a subdirectory of a git repo (sparse clone):
```json
{
  "source": { "source": "git-subdir", "url": "https://github.com/org/monorepo.git", "path": "tools/plugin", "ref": "main" }
}
```
The `url` field also accepts GitHub shorthand (`owner/repo`) or SSH URLs.

**npm package**:
```json
{
  "source": { "source": "npm", "package": "@acme/claude-plugin", "version": "^2.0.0", "registry": "https://npm.example.com" }
}
```

**pip package**:
```json
{
  "source": { "source": "pip", "package": "claude-plugin", "version": "2.1.0" }
}
```

## Plugin Format Rules

### plugin.json

Located at `plugins/<name>/.claude-plugin/plugin.json`.

Every plugin must have these fields:
- `name` — unique identifier and skill namespace (kebab-case). Skills are invoked as `/<plugin-name>:<skill-name>`.
- `description` — brief explanation of the plugin's purpose.
- `version` — sequential version string (`v1`, `v2`, `v3`...). CI bumps automatically.
- `author` — object with `name` (required), `url` (optional).

Do NOT add extra metadata fields (repository, license, keywords, homepage). Keep the manifest minimal.

### Directory layout

All component directories go at the **plugin root**, NOT inside `.claude-plugin/`. Use standard directory names only — do not customize paths.

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json          ← Only manifest here
├── agents/                  ← Agent definitions
├── skills/                  ← Skills (each is a directory with SKILL.md)
├── hooks/                   ← Hook configurations
│   └── hooks.json
├── .mcp.json                ← MCP server definitions
├── .lsp.json                ← LSP server configurations
├── scripts/                 ← Hook and utility scripts
└── README.md
```

**Do NOT use `commands/`** — it is legacy. All skills must use `skills/` with `SKILL.md`.

- **Skills**: Each skill is a directory under `skills/` containing a `SKILL.md` with YAML frontmatter (`description` required) followed by the skill prompt. Include supporting files (scripts, references) alongside SKILL.md as needed.
- **Agents**: Markdown files in `agents/` with YAML frontmatter (`name`, `description`) defining agent roles, tool restrictions, and behavior.
- **Hooks**: `hooks/hooks.json` for plugin-level event handlers. Available events: `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `UserPromptSubmit`, `Notification`, `Stop`, `SubagentStart`, `SubagentStop`, `SessionStart`, `SessionEnd`, `TeammateIdle`, `TaskCompleted`, `PreCompact`, `PostCompact`. Hook types: `command`, `prompt`, `agent`.
- **MCP Servers**: `.mcp.json` at plugin root.
- **LSP Servers**: `.lsp.json` at plugin root. Required fields: `command`, `extensionToLanguage`.

### Environment variables

- `${CLAUDE_PLUGIN_ROOT}` — absolute path to the plugin's install directory. Changes on update.
- `${CLAUDE_PLUGIN_DATA}` — persistent directory for plugin state that survives updates (`~/.claude/plugins/data/{id}/`). Auto-created on first reference. Deleted on uninstall (use `--keep-data` to preserve).

Both are substituted inline in skill content, agent content, hook commands, and MCP/LSP server configs. Also exported as env vars to hook processes and server subprocesses.

### Plugin caching

When users install a plugin, Claude Code copies the plugin directory to `~/.claude/plugins/cache`. Plugins cannot reference files outside their directory using `../` — those files won't be copied. Symlinks within the plugin directory ARE followed during copying. Use `${CLAUDE_PLUGIN_ROOT}` in hooks and MCP configs to reference files within the plugin's install directory.

### Installation scopes

- `user` (default) — `~/.claude/settings.json` — available across all projects
- `project` — `.claude/settings.json` — shared via version control
- `local` — `.claude/settings.local.json` — project-specific, gitignored
- `managed` — managed settings (read-only, update only)

## Development & Testing

Test locally without installing:
```bash
claude --plugin-dir ./plugins/spec-plugin
```

Load multiple plugins:
```bash
claude --plugin-dir ./plugin-one --plugin-dir ./plugin-two
```

Validate marketplace and plugin structure:
```bash
claude plugin validate .
```

Reload after changes (inside Claude Code):
```
/reload-plugins
```

Debug plugin loading:
```bash
claude --debug
```

## Installation

Users install via:
```
/plugin marketplace add nexaedge-marketplace --source github --repo nexaedge/nexaedge-marketplace
/plugin install spec-plugin@nexaedge-marketplace
```

### CLI commands

```bash
claude plugin install <plugin> [--scope user|project|local]
claude plugin uninstall <plugin> [--scope user|project|local] [--keep-data]
claude plugin enable <plugin> [--scope user|project|local]
claude plugin disable <plugin> [--scope user|project|local]
claude plugin update <plugin> [--scope user|project|local|managed]
```

### Private repo authentication

For background auto-updates, set the appropriate token in your environment:
- GitHub: `GITHUB_TOKEN` or `GH_TOKEN`
- GitLab: `GITLAB_TOKEN` or `GL_TOKEN`
- Bitbucket: `BITBUCKET_TOKEN`
