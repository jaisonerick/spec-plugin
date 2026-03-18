---
name: build-stories
description: "Break down a single version into executable story files. Reads the version spec, architecture, and roadmap, then creates ordered stories. Adapts to project type — code stories for engineers, deliverable stories for any project type. Use after /architect-version."
argument-hint: "[version, e.g. v0.1-core-push]"
---

Your task: break a version into ordered story files, each sized for a single AI agent session.

## Phase 1 — Load Context

1. Read the version spec: `specs/<version>.md`
2. Read the version architecture doc: `specs/<version>/architecture.md`
3. Read the overall architecture: `specs/architecture.md`
4. Read the roadmap: `specs/roadmap.md`
5. **Read the project spec** — check **Project Context** for the project type
6. Scan the existing workspace to understand what's already built/written
7. Check for any existing stories in `specs/<version>/`

Pay special attention to the version spec's **Definition of Done** — the final story or stories must directly satisfy these conditions.

## Phase 2 — Decompose into Stories

Break the version into stories following these principles:

### Sizing for AI Agents (NOT human teams)
- **Optimize for AI agent context window**: each story must be completable without overwhelming the agent
- A story that touches 15 files across 3 layers is **too broad**
- A story that creates one config file is **too narrow**
- Sweet spot: **one cohesive concern** per story

### Agent Assignment

Every story must specify its **agent** — the agent type that will execute it:

**For code projects:**
- **`engineer`** — Backend, data layer, API endpoints, integrations, tests, wiring UI. Runs `/execute-task`.
- **`designer`** — Visual UI creation: new pages, components, layouts, design system. Runs `/interface-design`.

**For non-code projects:**
- **`engineer`** — The default executor. Runs `/execute-task` for any deliverable type (documents, analyses, research outputs). Despite the name, this agent handles all execution work.

The orchestrator uses this field directly as `subagent_type` when spawning agents.

#### The Design → Engineer Pipeline (Code Projects Only)

For features with UI, use **paired stories**:
1. **Design story** (`agent: designer`) — Creates visual components/layouts
2. **Integration story** (`agent: engineer`) — Wires design into codebase

Not every UI story needs pairing. Use judgment.

### Testing in Stories (Code Projects)

Each engineer story must include testing acceptance criteria proportional to complexity:
- **Complex logic**: thorough unit tests
- **Key components**: at least one test pass
- **Simple glue**: no dedicated tests
- **Integration stories**: at least one integration test

Include a `## Testing Guidance` section in each code story.

### Verification in Stories (Non-Code Projects)

Each story should include clear acceptance criteria that can be verified by reading/reviewing the output:
- **Completeness**: does the deliverable cover everything specified?
- **Quality**: does it meet the standards described in the architecture?
- **Accuracy**: are facts, references, and claims correct?

### Ordering
- Foundation/prerequisite stories come first
- For code: data layer → API → UI
- Design stories before their integration stories
- Each story produces a **working increment**

### Self-containment
- Include enough context in each story that the executing agent doesn't need to read 10 other documents
- Inline the relevant architecture decisions

## Phase 3 — Write Story Files

Create each story as `specs/<version>/NNN-story-slug.md`:

```markdown
# NNN: Story Title

**Agent**: `engineer` | `designer`

## Summary
One paragraph describing what this story delivers.

## Prerequisites
- What must exist before starting (prior stories, inputs, access)

## Deliverables
- What exists after completion (new files, endpoints, documents, analyses)

## Acceptance Criteria
- [ ] Concrete, verifiable condition 1
- [ ] Concrete, verifiable condition 2

## Implementation Guidance
Specific guidance on how to produce the deliverable. For code: files to create/modify, patterns to follow. For non-code: sources to use, structure to follow, quality standards.

## Testing Guidance (code projects)
What to test, at what level, and any fixtures needed.

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
