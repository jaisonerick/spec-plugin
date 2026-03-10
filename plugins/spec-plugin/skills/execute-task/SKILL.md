---
name: execute-task
description: "Execute a single task end-to-end — either a new story or a fix from validation findings. Reads the task context, version architecture, and overall architecture, then produces working code that meets all acceptance criteria."
argument-hint: "[story file path or validation spec path with fix instructions]"
---

Your task: execute ONE task end-to-end, producing working code that meets all acceptance criteria. The task is either a new story (from `/build-stories`) or a fix (from `/validate-execution` findings).

## Phase 1 — Load Context

1. Read the task file at the provided path
2. Determine the version from the path (e.g., `specs/v0.1-core-push/001-...` → v0.1-core-push)
3. Read the version architecture doc: `specs/<version>/architecture.md`
4. Read the overall architecture: `specs/architecture.md`
5. Scan existing codebase for patterns, conventions, and what's already built
6. Check if the task file already has an `## Execution Log` section — if so, resume from where it left off

### If this is a fix task

The orchestrator will include validation findings in the prompt — specific failures from `/validate-execution` that need to be addressed. Read the referenced validation spec to understand what failed and why.

### If this follows a design story

If the task lists a prior `/interface-design` story as a prerequisite, read that story's execution log to find the files it produced. Build on them, don't redesign them.

## Phase 2 — Plan Implementation

Before writing any code:
1. List every file to create or modify
2. Define the order of operations
3. Identify any ambiguities or blockers
4. If the task is complex (5+ files, multiple layers), present the approach to the user

## Phase 3 — Implement

### For fix tasks
- **Understand the failure first** — read the validation findings carefully
- **Write a failing test** — before changing application code, write a test that reproduces the failure
- **Fix the bug** — make the minimal code change
- **Verify the test passes** — confirm the fix works
- **Run the full suite** — ensure no regressions

### Integrating Interface-Design Output
When a task follows a `/interface-design` story:
- Read the design story's execution log to find produced files
- Read `.interface-design/system.md` for design tokens and patterns
- **Preserve the visual design** — don't restyle, restructure layouts, or change spacing
- Your job is to wire: data fetching, state management, API calls, routing, event handlers
- If the design output needs structural changes to integrate, make minimal adjustments and note them in the execution log

## Phase 4 — Write Tests

Write automated tests alongside the implementation. The goal is **pragmatic coverage** — not 100% unit testing, but confidence that key behaviors work.

### Testing Philosophy
- **Complex logic** (engines, validators, state machines, algorithms): thorough test suite — happy paths, edge cases, error conditions, boundary values
- **Key components** (database layers, providers, API routes): at least one test pass verifying primary behavior works end-to-end
- **Simple glue code** (factories, config loading, re-exports): tested implicitly through other tests, no dedicated tests needed
- **Integration points**: test that components work together correctly

### What to Check in the Task
1. Read the task's `## Testing Guidance` section (if present) for specific test expectations
2. Read the acceptance criteria — many can be expressed as test assertions
3. If the task has no testing guidance, use your judgment based on the complexity tiers above

### Run Tests
After writing tests, run them and ensure they all pass. Tests MUST pass before moving to Phase 5.

## Phase 5 — Verify

1. Check every acceptance criterion from the task file
2. Run all tests and verify they pass
3. Run any specified verification steps (builds, linters, type checks)
4. Verify that new code compiles/runs without errors
5. **Integration wiring check** — for components that wire to other layers, verify the wiring works end-to-end — not just that the component exists
6. Report what's done and what's passing

## Phase 6 — Update Task File

Append an `## Execution Log` section to the task file:

```markdown
## Execution Log

### Session: <date>

**Status**: completed | in-progress

**Completed:**
- What was done (with file paths)

**Decisions Made:**
- Any implementation decisions not in the original task

**Issues Encountered:**
- Problems hit and how they were resolved

**Struggled With:**
- Things that took multiple attempts
- Process difficulty that future agents should know about

**Pending:** (only if in-progress)
- What's left to do
```

Then update `specs/<version>/stories.md` — mark the task as `completed` ONLY if ALL acceptance criteria pass. Otherwise mark as `in-progress`. After updating, **re-read stories.md** to verify the change was saved.

## Phase 7 — Document QA Requirements

After completing the task, ensure validation can happen without guessing:

1. **Startup commands** — if the task adds or changes how services are started, update `docs/dev-environment.md` with the exact commands. If the file doesn't exist, create it.
2. **Setup prerequisites** — if new seed scripts, migrations, env vars, or config overrides are needed, document them in the execution log under a `**QA Setup**` subsection.
3. **Architecture updates** — if implementation diverged from the architecture doc, update `specs/<version>/architecture.md` with the actual values.
