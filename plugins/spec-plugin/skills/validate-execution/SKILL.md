---
name: validate-execution
description: "Validate a version's implementation by running validation specs against the live application. Focuses on real user flows and behaviors faster to verify programmatically than manually. Runs incrementally on re-runs. Ends with human validation guidance."
argument-hint: "[version, e.g. v0.1-core-push]"
---

Your task: validate the version's implementation from the outside and guide the human through final verification.

## Phase 1 — Load Context

1. Read the version spec: `specs/<version>.md` — focus on Definition of Done
2. Read the version architecture: `specs/<version>/architecture.md` — for service details (ports, URLs, auth)
3. Read the stories index: `specs/<version>/stories.md`
4. Check if validation specs exist at `specs/<version>/qa/`

### If no validation specs exist → Write them first (Phase 1B)

Before you can validate, you need specs. Write them now.

1. Read each story file to understand what was built and its acceptance criteria
2. Read the overall architecture: `specs/architecture.md`
3. Design validation specs based on your testing scope (what you test / don't test), then proceed to Phase 2

Each Definition of Done item that can be verified programmatically should have at least one test case.

**Keep it lean** — aim for ~10-15 test cases per version.

Write specs at `specs/<version>/qa/NNN-spec-name.md`:

```markdown
# QA Spec NNN: Spec Title

**Area**: API | Integration | UI | Health | User Flow
**Prerequisites**: What must be running (services, databases, seed data)

## Setup
Steps to prepare the environment before running tests.

## Test Cases

### TC-001: Test case title
**Definition of Done item**: (which DoD item this covers, if applicable)
**Steps**:
1. Concrete action (e.g., "POST /api/resource with body: {...}")
2. Verify in database: query X, expect Y
3. Navigate to URL, verify Z appears

**Expected**: What should happen
**Severity**: critical | major | minor

## Human Review Checklist
Items the human should manually verify (visual quality, UX feel, etc.):
- [ ] Visual item 1
- [ ] Visual item 2
```

Write index at `specs/<version>/qa/specs.md`:

```markdown
# <Version> — Validation Specs

| # | Spec | Area | Test Cases | Status |
|---|------|------|-----------|--------|
| 010 | Service Health | Health | 3 | pending |
| 020 | Core Workflow | User Flow | 5 | pending |
```

### If validation specs exist → Determine mode

1. Read the validation specs: `specs/<version>/qa/*.md`
2. **Check for prior run results** — if specs have `## Run Results` sections, this is a re-run after fixes

### Incremental Mode (re-run after fixes)

1. Read prior `## Run Results` from each spec
2. Identify which test cases FAILED or were SKIPPED
3. **Only re-run those test cases** — skip everything that passed before
4. Add a new `### Re-run: <date>` subsection to the existing Run Results

## Phase 2 — Environment Setup

### Mandatory Pre-Flight Check

Before running ANY test case, verify ALL required services are up and reachable.

**If ANY required service is down, STOP IMMEDIATELY.** Report the environment failure to the team lead via SendMessage with what's broken and what needs fixing.

### Documentation Check

Verify startup commands are documented in `docs/dev-environment.md` or the version architecture. **If missing, STOP and mark as BLOCKED.** Don't guess how to start services.

### Start & Verify

1. Start services following documented commands
2. Verify health endpoints respond
3. Seed test data if needed

## Phase 3 — Execute Validation

For each test case (or only failed ones in incremental mode):

1. **Execute the steps** exactly as written:
   - API calls: `curl` or `httpie` via Bash
   - Browser flows: Chrome DevTools MCP tools (navigate, click, fill, snapshot)
   - CLI commands: run via Bash
   - Database checks: query directly to verify state
   - Combined flows: create via API → verify in DB → check in UI

2. **Compare actual vs expected** — record the result clearly

## Phase 4 — Report Results

Append or update `## Run Results` in each spec file:

```markdown
## Run Results

### Run: <date>

| TC | Title | Result | Notes |
|----|-------|--------|-------|
| TC-001 | Test title | PASS | |
| TC-002 | Test title | FAIL | Expected 200, got 500. Error: "connection refused" |

**Summary**: X passed, Y failed, Z skipped
**Failures requiring fixes**:
- TC-002: <clear description of what's wrong and where to look>
```

For incremental re-runs, append a new subsection:

```markdown
### Re-run: <date> (after fixes)

| TC | Title | Result | Notes |
|----|-------|--------|-------|
| TC-002 | Test title | PASS | Fixed in task-NNN |
```

## Phase 5 — Determine Next Step

After all specs are executed, evaluate the results:

### If failures exist → Report to orchestrator

Report via SendMessage:
- Which test cases failed and why
- Suggested fix areas (file paths, components)
- Whether failures are CRITICAL (blocking) or MINOR (deferrable)

The orchestrator will spawn `/execute-task` to fix issues and then call `/validate-execution` again (incremental mode).

### If all pass → Guide human validation

When all automated validation passes, present the human validation guide:

```markdown
## Human Validation Guide

### What was built
- Summary of the version's capabilities

### How to run it
- Exact commands to start the application
- URLs to open, credentials to use

### What to verify
Walk through each Definition of Done item that requires human judgment:

1. **[DoD item]** — Navigate to X, do Y, verify Z looks/feels right
2. **[DoD item]** — Try doing X, confirm the experience is smooth
3. ...

### Quick checks
- [ ] Application starts without errors
- [ ] [Specific page/feature] loads and is usable
- [ ] [Key workflow] completes successfully
- [ ] Visual design matches expectations

### Known limitations in this version
- (from "Simplified in this version" in the version spec)
```

The version is shipped only when the human confirms.

## Phase 6 — Document Findings

Append to the spec file:

```markdown
## Validation Findings

### Environment Issues
- What didn't work out of the box

### Missing Documentation
- Setup steps that should be documented

### Patterns Observed
- Recurring issues across test cases
```
