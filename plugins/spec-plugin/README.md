# Spec Plugin

A Claude Code plugin for spec-driven product development. Provides a complete pipeline from ideation to verified, shipped code — orchestrated by AI agents.

## Pipeline

```
/ideate → /architect → /plan → /orchestrate (per version)
```

| Skill | Purpose |
|-------|---------|
| `/ideate` | Build a product specification through conversational refinement |
| `/architect` | Create high-level technical architecture for the project |
| `/plan` | Design an evolutionary product roadmap with version progression |
| `/orchestrate` | Execute a version end-to-end with a coordinated agent team |

The orchestrator runs a simple cycle per version:

```
/architect-version → /build-stories → [ /execute-task → /validate-execution ]* → human signs off
```

A version ships when the human confirms its Definition of Done is met.

## Agents

| Agent | Role |
|-------|------|
| `architect` | Deep-dive version architecture. No Bash — documents only. |
| `product-owner` | Story breakdown and retrospectives. |
| `engineer` | Task execution — new stories and validation fixes. |
| `designer` | Visual UI creation following the design system. |
| `qa` | Writes validation specs and executes them against the live application. |

All agents call `EnterWorktree` as their first action to work on an isolated copy of the repo.

## All Skills

| Skill | Description |
|-------|-------------|
| `/ideate` | Product spec through conversation |
| `/architect` | Project-level architecture |
| `/plan` | Evolutionary product roadmap (version progression) |
| `/architect-version` | Per-version architecture deep-dive |
| `/build-stories` | Version → ordered story files |
| `/execute-task` | Execute one task (story or fix) with working code |
| `/validate-execution` | Write validation specs (if needed), execute them, guide human review |
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
├── <project-name>.md          # Product specification (from /ideate)
├── architecture.md             # Technical architecture (from /architect)
├── roadmap.md                  # Version progression (from /plan)
├── v0.1-core-push.md           # Version specs (from /plan)
├── v0.2-config-support.md
├── v0.1-core-push/             # Per-version folders (from /orchestrate)
│   ├── architecture.md         # Version architecture (from /architect-version)
│   ├── stories.md              # Story index (from /build-stories)
│   ├── 010-story-slug.md       # Story files
│   └── qa/                     # Validation specs (from /validate-execution)
│       ├── specs.md
│       └── 010-spec-name.md
└── ...
```

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
