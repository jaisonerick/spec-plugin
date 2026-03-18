# Spec Plugin

A Claude Code plugin for spec-driven project execution. Provides a complete pipeline from ideation to verified, shipped deliverables — orchestrated by AI agents. Works with any project type: code, business, research, consulting.

## Pipeline

```
/ideate → /architect → /plan → /orchestrate (per version)
```

| Skill | Purpose |
|-------|---------|
| `/ideate` | Build a project specification through conversational refinement |
| `/architect` | Create the implementation approach for the project |
| `/plan` | Design an evolutionary delivery roadmap with version progression |
| `/orchestrate` | Execute a version end-to-end with a coordinated agent team |

The orchestrator runs a simple cycle per version:

```
/architect-version → /build-stories → [ /execute-task → /validate-execution ]* → human signs off
```

A version ships when the human confirms its Definition of Done is met.

## Context-Aware

Skills adapt to the workspace they're in:

- **Code repo** (has package.json, Cargo.toml, etc.) → tech stack decisions, automated tests, build verification
- **Document workspace** (organized by project, client, or topic) → structure-aware placement, document deliverables, criteria-based validation
- **Empty directory** → asks what kind of project this is, adapts accordingly
- **Nested project** (e.g., `clients/acme/billing/`) → respects parent structure, places specs in context

The project spec's **Project Context** section captures what `/ideate` learned about the workspace, so downstream skills don't re-discover it.

## Agents

| Agent | Role |
|-------|------|
| `architect` | Deep-dive version architecture. No Bash — documents only. |
| `product-owner` | Story breakdown and retrospectives. |
| `engineer` | Task execution — new stories and validation fixes. |
| `designer` | Visual UI creation following the design system. |
| `qa` | Writes validation specs and executes them. Reports failures — never fixes. |

All agents call `EnterWorktree` as their first action to work on an isolated copy of the repo.

## All Skills

| Skill | Description |
|-------|-------------|
| `/ideate` | Project spec through conversation — adapts to project type |
| `/architect` | Project-level implementation approach |
| `/plan` | Evolutionary delivery roadmap (version progression) |
| `/architect-version` | Per-version architecture deep-dive |
| `/build-stories` | Version → ordered story files |
| `/execute-task` | Execute one task — code or deliverable |
| `/validate-execution` | Validate against Definition of Done — tests or review |
| `/run-retrospective` | Post-version lessons learned |
| `/orchestrate` | Full version execution with agent team |

## Worktree Isolation

Agents work in isolated git worktrees to avoid conflicts:

1. **Agent definitions** instruct each agent to call `EnterWorktree` before doing any work
2. **Orchestrate skill** provides worktree names in agent prompts
3. **PostToolUse hook** on `EnterWorktree` runs `scripts/setup-worktree.sh` if it exists
4. **Setup script** (optional) copies `.env`, `.tool-versions`, and other gitignored files

## Specs Directory Convention

```
specs/
├── <project-name>.md          # Project specification (from /ideate)
├── architecture.md             # Implementation approach (from /architect)
├── roadmap.md                  # Version progression (from /plan)
├── v0.1-short-name.md          # Version specs (from /plan)
├── v0.2-short-name.md
├── v0.1-short-name/            # Per-version folders (from /orchestrate)
│   ├── architecture.md         # Version architecture (from /architect-version)
│   ├── stories.md              # Story index (from /build-stories)
│   ├── 010-story-slug.md       # Story files
│   └── qa/                     # Validation specs (from /validate-execution)
│       ├── specs.md
│       └── 010-spec-name.md
└── ...
```

The `specs/` directory lives wherever the project lives — repo root, a subdirectory, or within a larger workspace.

## Installation

```
/install jaisonerick/spec-plugin
```

Or add to `.claude/settings.json`:

```json
{
  "plugins": ["jaisonerick/spec-plugin"]
}
```

## Optional Dependencies

- **`/interface-design` plugin** — Required for `designer` agent stories.
- **Chrome DevTools MCP** — Used by `/validate-execution` for browser-based validation.
