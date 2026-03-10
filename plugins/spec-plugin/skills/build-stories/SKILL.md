---
name: build-stories
description: "Break down a single version into executable story files. Reads the version spec, overall architecture, version-specific architecture, and roadmap, then creates ordered stories for engineers and designers. Use after /architect-version."
argument-hint: "[version, e.g. v0.1-core-push]"
---

Your task: break a version into ordered story files, each sized for a single AI agent session.

## Phase 1 — Load Context

1. Read the version spec: `specs/<version>.md`
2. Read the version architecture doc: `specs/<version>/architecture.md`
3. Read the overall architecture: `specs/architecture.md`
4. Read the roadmap: `specs/roadmap.md`
5. Scan the existing codebase (Glob for source files, read key files) to understand what's already built
6. Check for any existing stories in `specs/<version>/`

Pay special attention to the version spec's **Definition of Done** — the final story or stories must directly satisfy these conditions.

## Phase 2 — Decompose into Stories

Break the version into stories following these principles:

### Sizing for AI Agents (NOT human teams)
- **Optimize for AI agent context window**: each story must be completable without overwhelming the executing agent's context
- A story that touches 15 files across 3 layers is **too broad**
- A story that creates one config file is **too narrow**
- Sweet spot: **one cohesive concern** per story

### Agent Assignment

Every story must specify its **agent** — the agent type that will execute it:

- **`engineer`** — Backend work, data layer, API endpoints, integrations, tests, and wiring UI into the codebase. Runs `/execute-task`.
- **`designer`** — Visual UI creation: new pages, components, layouts, design system work. Runs `/interface-design`.

The orchestrator uses this field directly as `subagent_type` when spawning agents.

#### The Design -> Engineer Pipeline

For features with UI, use **paired stories**:

1. **Design story** (`agent: designer`) — Creates the visual components/layouts
2. **Integration story** (`agent: engineer`) — Wires the design into the codebase (data fetching, state, routing, API calls)

Not every UI story needs pairing. Use judgment:
- New page with significant visual design → paired
- Adding to an existing page using established patterns → single engineer story
- Backend with no UI → engineer story only

### Testing in Stories
Each engineer story must include testing acceptance criteria proportional to complexity:

- **Complex logic**: thorough unit tests
- **Key components**: at least one test pass verifying primary behavior
- **Simple glue**: no dedicated test criteria needed
- **Integration stories**: at least one integration test

Include a `## Testing Guidance` section in each story.

### Ordering
- Infrastructure/foundation stories come first
- Data layer before API layer before UI layer
- Design stories before their paired integration stories
- Each story produces a **working increment** (compiles, passes all tests)

### Self-containment
- Include enough context IN each story that the executing agent doesn't need to read 10 other documents
- Inline the relevant architecture decisions

## Phase 3 — Write Story Files

Create each story as `specs/<version>/NNN-story-slug.md`:

```markdown
# NNN: Story Title

**Agent**: `engineer` | `designer`

## Summary
One paragraph describing what this story delivers.

## Prerequisites
- What must exist before starting (files, services, prior stories)

## Deliverables
- What exists after completion (new files, endpoints, components)

## Acceptance Criteria
- [ ] Concrete, testable condition 1
- [ ] Concrete, testable condition 2

## Implementation Guidance
Specific files to create/modify, patterns to follow, architecture decisions that apply.

## Testing Guidance
What to test, at what level, and any fixtures/mocking needed.

## Architecture Context
Inline the relevant decisions so the executor doesn't need to cross-reference.

## References
- Links to relevant architecture sections for deeper context
```

## Phase 4 — Create Index

Write `specs/<version>/stories.md`:

```markdown
# <Version> — Stories

## Status
| # | Story | Agent | Status |
|---|-------|-------|--------|
| 001 | Story title | engineer | pending |
| 002 | Design: Page X | designer | pending |
| 003 | Integrate: Page X | engineer | pending |

## Dependency Graph
(mermaid diagram showing story dependencies if non-linear)
```
