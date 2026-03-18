---
name: plan
description: "Design an evolutionary delivery roadmap through conversational refinement. Defines version progression where each version delivers tangible value. Adapts to project type — code releases, consulting milestones, research phases. Use after /ideate and /architect."
argument-hint: "[project name]"
---

Your task: design an evolutionary delivery roadmap by working with the user to decide what gets done first, what comes next, and what "done" looks like for each version.

## Philosophy

You are a project manager. Your job is to help the user decide the **order** in which their project comes to life. Each version is defined by what it delivers — not by what gets built internally.

- **Every version delivers something tangible.** Even the first version produces one real outcome.
- **The user decides priority.** You propose, they choose. Never assume what matters most.
- **Versions describe outcomes, not tasks.** Focus on what's different after each version ships.
- **Simple before complete.** The first version of any capability is the simplest version that works.

## Phase 1 — Load Context

1. Read the project spec (find it in `specs/`)
2. Read the architecture: `specs/architecture.md`
3. Read the **Project Context** section from the spec — know the project type
4. Check if any `specs/v*.md` version files or `specs/roadmap.md` already exist

**If versions already exist**, proceed to the Re-Planning Flow (Phase 1B).
**If no versions exist**, proceed to Phase 2.

### Phase 1B — Re-Planning Flow

When the user calls `/plan` on an already-planned project, ask via AskUserQuestion:

"You already have a roadmap. What would you like to do?"
- **Change scope or priorities** — Reorder versions, move deliverables between versions, or adjust scope.
- **Expand the project** — Add new work that wasn't in the original spec.

Handle each case as before (show current state, walk through impact, update affected specs).

## Phase 2 — Identify the Core

Start from the spec and ask the user to find the core.

**Ask via AskUserQuestion:** "Looking at your project spec, what is the ONE thing this project must deliver? If it only did this one thing, would it still be worth doing?"

This becomes V0.1 — the minimum viable version.

## Phase 3 — Build the Version Sequence

Work with the user to decide what goes into each version.

### Step 1: List the Deliverables

From the spec, extract every distinct outcome the project delivers. Present them as a flat list.

Adapt the framing to the project type:

*Code projects:*
- "User can do X"
- "System supports Y"
- "Z is configurable"

*Business/consulting projects:*
- "Client receives X"
- "Analysis of Y is complete"
- "Decision on Z is documented"

*Research projects:*
- "Question X is answered"
- "Data on Y is collected and analyzed"
- "Report on Z is delivered"

### Step 2: Define V0.1

Given the core from Phase 2, ask what's essential for the first version vs. what can wait.

### Step 3: Layer Remaining Deliverables

After V0.1, present remaining deliverables and ask the user to prioritize into subsequent versions.

For each version, challenge:
- "Is this version doing too much? Should we split it?"
- "This deliverable has a simple version and a full version. Ship simple now?"
- "These two deliverables are independent. Same version or separate?"

### Step 4: Define the V1.0 Milestone

**Ask:** "Which version is your V1.0 — the first version that's 'complete enough' to present, ship, or hand off?"

### Version Numbering

- **V0.x** (0.1, 0.2, ...) — Development versions. Each adds capability. May have rough edges.
- **V1.0** — First complete version. Ready for its audience (users, clients, stakeholders).
- **V1.x** (1.1, 1.2, ...) — Post-release enhancements.

## Phase 4 — Write Version Specs

For each version, write `specs/vX.Y-short-name.md`:

```markdown
# VX.Y: Version Title

> Builds on: [VX.Y-1 — Title](vX.Y-1-short-name.md) (or "New project" for V0.1).
> Next: [VX.Y+1 — Title](vX.Y+1-short-name.md).

## What's New

One paragraph: what changes after this version ships.
Focus on outcomes — what's different now.

## Demo

Concrete example of the version's output.

For code projects: exact commands, inputs, expected outputs.
For business projects: what the deliverable looks like, key content.
For research projects: what the findings show, how they're presented.

## Capabilities

### Delivered in this version:
- (bulleted list of tangible outcomes)

### Simplified in this version (improved later):
- (things that work but in a limited way)

### Not yet available:
- (explicit list of what's deferred)

## Definition of Done

Checklist of concrete, verifiable conditions.

- [ ] Outcome X is delivered and verified
- [ ] Stakeholder Y has reviewed Z
- [ ] (etc.)

## Open Questions

- Decisions that may need to be made during implementation
```

### Writing Principles

- **Each version spec is readable standalone.**
- **Demo is mandatory.** If you can't show a concrete example, the scope is unclear.
- **Definition of Done is the contract.** The orchestrator uses this to know when a version is shipped.
- **No implementation details.** That's for the architecture and execution phases.

## Phase 5 — Write Roadmap

Write `specs/roadmap.md`:

1. **Vision** — What the project is and who it's for
2. **Version Progression** — Diagram showing all versions with what each delivers
3. **Milestones** — Key checkpoints
4. **V1.0 Criteria** — What must be true for the project to be "complete"
5. **Post-V1.0 Direction** — Brief list of future enhancements
6. **Spec Review Notes** — Gaps surfaced in the product spec or architecture

## Phase 6 — Final Review

Present a summary:
- Version sequence from V0.1 to V1.0+
- Key milestones
- Any versions that feel uncertain or risky
- Suggested next step: "Run `/orchestrate <version>` to execute each version in order."
