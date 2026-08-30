# NexaEdge Marketplace

Plugins and skills for coding agents. Works with **Claude Code**, **Codex** and **Antigravity**.

> **If you are an agent and someone asked you to install this: read [INSTALL.md](./INSTALL.md) and follow the branch for whichever agent you are.**

## Install

Point your agent at this repository and name the file it should follow. Something like:

> Leia o INSTALL.md deste repositório e siga as instruções para o seu agente: https://github.com/nexaedge/nexaedge-marketplace

Naming the file matters. Given only a URL, an agent that already knows how to add a plugin catalog will do that from memory and stop there, without ever opening the repository.

The agent installs the `nexaedge` plugin at user scope and explains what you can do next. Nothing is added to whatever repository you happen to be in.

From then on you talk to it normally: "what plugins are available?", "install the html report one", "update my plugins".

## Why one plugin first

The `nexaedge` plugin is the front end for the other ones. It detects which agent is running and translates to that agent's native install path, so a plugin lands once per machine instead of being copied into every project. Bootstrapping just this one keeps the first install small and lets you choose the rest in conversation.

## Plugins

| Plugin | Claude | Codex | Antigravity | What it does |
|---|:-:|:-:|:-:|---|
| nexaedge | ● | ● | ● | Install and manage everything else here, on any agent |
| artifact-publish | ● | ● | ● | Publish a self-contained HTML file and get a link |
| html-report | ● | ● | ● | Turn analysis into an interactive HTML report |
| cloudflare-dns | ● | ● | ● | Manage Cloudflare DNS through Terraform |
| plaud | ● | ● | ● | Bring Plaud.ai recordings and transcripts into a repo |
| vendored-skills | ● | ● | ● | Third-party skills, pinned to their upstream commit |
| spec-plugin | ● | | | Ideation to verified code, on a team of subagents |
| linear-spec-plugin | ● | | | The same pipeline, with Linear as system of record |
| interface-design | ● | | | Craft-first interface design for product UI |
| frontend-design | ● | | | Distinctive visual direction for new UI |
| commit-commands | ● | | | Git commit, push and PR workflows |
| typescript-lsp | ● | | | TypeScript code intelligence |
| pyright-lsp | ● | | | Python code intelligence |
| rust-analyzer-lsp | ● | | | Rust code intelligence |

Claude-only plugins need something the other agents do not expose to plugins: subagents, hooks, LSP servers, or they are referenced from someone else's repository and only carry a Claude manifest. `catalog.json` records the reason per plugin, in its `requires` field.

## How one directory serves three agents

Each plugin is written once against open standards, and each agent's own manifest is generated from it. A format change lands in one generator instead of every plugin.

```
plugins/<name>/
├── plugin.json                  Agent Plugins 1.0.0  ← source, also read by Antigravity
├── skills/<skill>/SKILL.md      Agent Skills         ← source, read by all three
├── .claude-plugin/plugin.json   generated
└── .codex-plugin/plugin.json    generated
```

Both formats are cross-vendor standards: [Agent Skills](https://agentskills.io/specification), adopted by around 45 agent products, and [Agent Plugins 1.0.0](https://github.com/agentplugins/agent-plugins-spec), whose maintainers include Amazon, Cursor, Microsoft, OpenAI, Vercel and Google.

There is no standard for the marketplace layer yet, and the Agent Plugins spec leaves it out on purpose. So `catalog.json` says only which plugins exist and where they come from, and the per-agent catalogs (`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`) are generated from it. Antigravity has no catalog at all: it is pointed at `plugins/` by path.

## Development

Everything except `plugin.json`, `catalog.json` and the skills is generated. Never edit a manifest by hand: it reverts on the next push.

```bash
bin/mkt generate      # rebuild every agent's manifests from catalog.json
bin/mkt list          # what is installed locally
bin/mkt add <url>     # vendor a skill or reference a plugin
bin/mkt update        # check vendored skills for upstream updates
```

The generator refuses to run on an inconsistent catalog, so `bin/mkt generate` doubles as the check. The `nexaedge` plugin also fetches `index.tsv` at runtime to list what is available, which means a wrong entry is user-visible.

Validate before pushing:

```bash
claude plugin validate .
python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/<name>
```

Versions are bumped by CI on merge to main. Do not bump them by hand.

A plugin release bumps the marketplace version along with it. Entries in the
generated catalogs carry only `name` and `source`, so a plugin release leaves
those files otherwise byte-identical: the marketplace version is the only field
in them that moves at all. Whether a given consumer reads it is that consumer's
business — Claude's own ingestion appears to key off pushes to this repository,
not off this field.
