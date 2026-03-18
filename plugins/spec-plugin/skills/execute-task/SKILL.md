---
name: execute-task
description: "Execute a single task end-to-end — either a new story or a fix from validation findings. Reads the task context and architecture, then produces working output that meets all acceptance criteria. Adapts to project type: writes code for code projects, writes deliverables for non-code projects."
argument-hint: "[story file path or validation spec path with fix instructions]"
---

Your task: execute ONE task end-to-end, producing output that meets all acceptance criteria. The task is either a new story (from `/build-stories`) or a fix (from `/validate-execution` findings).

## Phase 1 — Load Context

1. Read the task file at the provided path
2. Determine the version from the path (e.g., `specs/v0.1-core-push/001-...` → v0.1-core-push)
3. Read the version architecture doc: `specs/<version>/architecture.md`
4. Read the overall architecture: `specs/architecture.md`
5. **Read the project spec** — find the main spec in `specs/` and check the **Project Context** section to understand the project type
6. Scan existing workspace for patterns, conventions, and what's already built/written
7. Check if the task file already has an `## Execution Log` section — if so, resume from where it left off

### Project Type Detection

The spec's **Project Context → Type** determines your execution approach:
- **code**: Write code, run tests, verify builds
- **business / consulting**: Write documents, verify against criteria
- **research**: Investigate, analyze, produce findings
- **hybrid**: Mix approaches as needed

### If this is a fix task

The orchestrator will include validation findings in the prompt — specific failures that need to be addressed. Read the referenced validation spec to understand what failed and why.

### If this follows a design story

If the task lists a prior `/interface-design` story as a prerequisite, read that story's execution log to find the files it produced. Build on them, don't redesign them.

## Phase 2 — Plan Implementation

Before producing any output:
1. List every file to create or modify
2. Define the order of operations
3. Identify any ambiguities or blockers
4. If the task is complex, present the approach to the user

## Phase 3 — Execute

### For Code Projects

**New stories:**
1. Write the code following the architecture and patterns
2. Write tests alongside the implementation (see Phase 4)
3. Ensure everything compiles/runs

**Fix tasks:**
1. Understand the failure first — read validation findings carefully
2. Write a failing test that reproduces the failure
3. Fix the bug with minimal code change
4. Verify the test passes
5. Run the full suite — ensure no regressions

**Integrating Interface-Design Output:**
- Read the design story's execution log for produced files
- Read `.interface-design/system.md` for design tokens and patterns
- Preserve the visual design — don't restyle or restructure
- Your job is to wire: data fetching, state management, API calls, routing

### For Non-Code Projects

**New stories:**
1. Research and gather inputs needed for the deliverable
2. Write the deliverable following the architecture's delivery structure
3. Check the deliverable against each acceptance criterion
4. If the deliverable references other documents or data, verify those references are accurate

**Fix tasks:**
1. Read the validation findings — understand what's missing or incorrect
2. Address each finding specifically
3. Re-verify the affected acceptance criteria

### For Research Projects

**New stories:**
1. Conduct the investigation described in the task
2. Collect and organize findings
3. Produce the output in the format specified by the architecture
4. Verify findings are supported by sources
5. Flag uncertainties or areas needing deeper investigation

## Phase 4 — Verify (Code Projects)

Write automated tests alongside the implementation. The goal is **pragmatic coverage** — not 100% unit testing, but confidence that key behaviors work.

### Testing Philosophy
- **Complex logic** (engines, validators, state machines, algorithms): thorough test suite
- **Key components** (database layers, providers, API routes): at least one test pass verifying primary behavior
- **Simple glue code** (factories, config loading, re-exports): tested implicitly
- **Integration points**: test that components work together

### Run Tests
After writing tests, run them and ensure they all pass. Tests MUST pass before moving to Phase 5.

## Phase 4 — Verify (Non-Code Projects)

For non-code projects, verification is criteria-based:

1. **Walk through each acceptance criterion** from the task file
2. **Check completeness** — does the deliverable address everything?
3. **Check quality** — is the writing clear? Are claims supported? Is the format correct?
4. **Check language** — verify the output language matches the project's language setting
5. Report what's done and what meets criteria

## Phase 5 — Final Checks

1. Check every acceptance criterion from the task file
2. For code: run all tests, linters, type checks, builds
3. For non-code: re-read deliverable against criteria, verify references and links
4. **Integration check** — verify the output connects properly to what exists
5. Report what's done and what's passing/complete

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

## Phase 7 — Document QA Requirements (Code Projects Only)

After completing a code task, ensure validation can happen without guessing:

1. **Startup commands** — if the task adds or changes how services are started, update `docs/dev-environment.md` with exact commands
2. **Setup prerequisites** — if new seed scripts, migrations, env vars, or config overrides are needed, document them in the execution log under `**QA Setup**`
3. **Architecture updates** — if implementation diverged from the architecture doc, update `specs/<version>/architecture.md`
