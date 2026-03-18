# Claude Marketplace

This is a Claude Code **plugin marketplace** repository. It can contain multiple plugins.

## Repository Structure

```
.claude-plugin/
  marketplace.json          # Marketplace catalog (name, owner, plugin list)
.github/
  workflows/
    bump-version.yml        # Auto-bumps versions on merge to main
plugins/
  spec-plugin/              # The spec-plugin plugin
    .claude-plugin/
      plugin.json           # Plugin manifest (name, version, description)
    agents/                 # Agent definitions (.md files)
    skills/                 # Skills (directories with SKILL.md)
    hooks/                  # Hook scripts
    README.md               # Plugin documentation
CHANGELOG.md                # Version history (auto-updated by CI)
README.md                   # Marketplace documentation
```

## Versioning

There are two independent versions:

- **Marketplace version** (`metadata.version` in `.claude-plugin/marketplace.json`): Tracks changes to the marketplace itself (adding/removing plugins, changing marketplace metadata). Currently `1.0.0`.
- **Plugin version** (`version` in `plugins/spec-plugin/.claude-plugin/plugin.json`): Tracks the plugin's own evolution (new skills, agent changes, bug fixes). Currently `3.1.0`.

**Do NOT duplicate the plugin version in the marketplace plugins array.** The plugin's own `plugin.json` is the source of truth — the marketplace entry should not set `version` (the manifest always wins silently, so a marketplace version would be ignored anyway).

**Versions are bumped automatically by CI** (`.github/workflows/bump-version.yml`). On every push to main:
- If files under `plugins/spec-plugin/` changed → plugin patch version is bumped
- If files under `.claude-plugin/`, `README.md`, or `CLAUDE.md` changed → marketplace patch version is bumped
- CHANGELOG.md is updated with the commit message
- The bump commit includes `[skip-bump]` to prevent infinite loops

For major/minor bumps, edit the version manually and include `[skip-bump]` in the commit message.

**Do NOT bump versions manually in regular commits** — let CI handle it.

## Marketplace Format Rules

### marketplace.json

Required fields: `name`, `owner` (with `name`), `plugins` array.

Each plugin entry requires: `name`, `source`. Optional: `description`, `author`, `category`, `tags`, `strict`.

The `source` field for plugins in this repo uses relative paths (e.g., `"./plugins/spec-plugin"`). Paths resolve relative to the marketplace root (the directory containing `.claude-plugin/`), NOT relative to `marketplace.json` itself.

Optional metadata goes under `metadata`: `description`, `version`, `pluginRoot`.

### Reserved marketplace names

Do NOT use: `claude-code-marketplace`, `claude-code-plugins`, `claude-plugins-official`, `anthropic-marketplace`, `anthropic-plugins`, `agent-skills`, `life-sciences`, or names impersonating official marketplaces.

## Plugin Format Rules

### plugin.json

Located at `plugins/<name>/.claude-plugin/plugin.json`. Required fields: `name`. Recommended: `description`, `version`, `author`.

The `name` field is the plugin's unique identifier and skill namespace. Skills are invoked as `/spec-plugin:<skill-name>`.

### Directory layout

All component directories (`agents/`, `skills/`, `hooks/`, `scripts/`) go at the **plugin root**, NOT inside `.claude-plugin/`.

- **Skills**: Each skill is a directory under `skills/` containing a `SKILL.md` with YAML frontmatter (`description` required) followed by the skill prompt.
- **Agents**: Markdown files in `agents/` defining agent roles, tool restrictions, and behavior.
- **Hooks**: Shell scripts in `hooks/` referenced by agent frontmatter, or a `hooks/hooks.json` for plugin-level event handlers.

### Plugin caching

When users install a plugin, Claude Code copies the plugin directory to a cache location (`~/.claude/plugins/cache`). Plugins cannot reference files outside their directory using `../` — those files won't be copied. Use `${CLAUDE_PLUGIN_ROOT}` in hooks and MCP configs to reference files within the plugin's install directory.

## Development & Testing

Test locally without installing:
```bash
claude --plugin-dir ./plugins/spec-plugin
```

Validate marketplace and plugin structure:
```bash
claude plugin validate .
```

Reload after changes (inside Claude Code):
```
/reload-plugins
```

## Installation

Users install via:
```
/plugin marketplace add claude-marketplace --source github --repo jaisonerick/spec-plugin
/plugin install spec-plugin@claude-marketplace
```
