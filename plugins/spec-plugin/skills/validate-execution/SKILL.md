---
name: validate-execution
description: "Validate a version's implementation against its Definition of Done. For code projects: runs automated tests against the live application. For non-code projects: reviews deliverables against acceptance criteria. Runs incrementally on re-runs. Ends with human validation guidance."
argument-hint: "[version, e.g. v0.1-core-push]"
---

Your task: validate the version's output and guide the human through final verification.

## Phase 1 — Load Context

1. Read the version spec: `specs/<version>.md` — focus on Definition of Done
2. Read the version architecture: `specs/<version>/architecture.md`
3. Read the stories index: `specs/<version>/stories.md`
4. **Read the project spec** — check **Project Context** for project type
5. Check if validation specs exist at `specs/<version>/qa/`

### If no validation specs exist → Write them first (Phase 1B)

1. Read each story file to understand what was built/delivered and its acceptance criteria
2. Read the overall architecture: `specs/architecture.md`
3. Design validation specs based on the project type (see below)

**For code projects:**
Each Definition of Done item that can be verified programmatically should have test cases.
Keep it lean — ~10-15 test cases per version.

Write specs at `specs/<version>/qa/NNN-spec-name.md`:

```markdown
# QA Spec NNN: Spec Title

**Area**: API | Integration | UI | Health | User Flow
**Prerequisites**: What must be running

## Setup
Steps to prepare the environment.

## Test Cases

### TC-001: Test case title
**Definition of Done item**: (which DoD item this covers)
**Steps**:
1. Concrete action (e.g., "POST /api/resource with body: {...}")
2. Verify result

**Expected**: What should happen
**Severity**: critical | major | minor

## Human Review Checklist
- [ ] Visual/UX items to verify manually
```

**For non-code projects:**
Each Definition of Done item becomes a review criterion. Validation is done by reading and evaluating deliverables.

Write specs at `specs/<version>/qa/NNN-spec-name.md`:

```markdown
# QA Spec NNN: Spec Title

**Area**: Completeness | Quality | Accuracy | Format
**Deliverables to review**: (list of files/documents)

## Review Criteria

### RC-001: Criterion title
**Definition of Done item**: (which DoD item this covers)
**What to check**:
1. Read [document/section]
2. Verify [specific quality or content requirement]

**Expected**: What a passing deliverable looks like
**Severity**: critical | major | minor

## Human Review Checklist
- [ ] Items requiring subjective judgment
```

Write index at `specs/<version>/qa/specs.md`.

### If validation specs exist → Determine mode

Check for prior run results. If specs have `## Run Results`, this is a re-run after fixes.

**Incremental mode:** Only re-run failed/skipped items. Add a `### Re-run: <date>` subsection.

## Phase 2 — Environment Setup (Code Projects)

### Mandatory Pre-Flight Check

Verify ALL required services are up and reachable.
**If ANY service is down, STOP.** Report via SendMessage.

### Documentation Check

Verify startup commands are documented. **If missing, STOP and mark BLOCKED.**

### Start & Verify

1. Start services following documented commands
2. Verify health endpoints respond
3. Seed test data if needed

## Phase 2 — Review Setup (Non-Code Projects)

1. Locate all deliverables referenced by the stories
2. Verify all deliverables exist (report missing ones as failures)
3. Note the language setting from the project spec

## Phase 3 — Execute Validation

### For Code Projects

For each test case:
1. **Execute steps** exactly as written:
   - API calls: `curl` or `httpie` via Bash
   - Browser flows: Chrome DevTools MCP tools
   - CLI commands: run via Bash
   - Database checks: query directly
2. **Compare actual vs expected** — record clearly

### For Non-Code Projects

For each review criterion:
1. **Read the deliverable** referenced by the criterion
2. **Evaluate against the criterion** — does it meet the standard?
3. **Record the finding** — pass, fail (with specific issues), or needs-improvement

## Phase 4 — Report Results

Append or update `## Run Results` in each spec file:

```markdown
## Run Results

### Run: <date>

| ID | Title | Result | Notes |
|----|-------|--------|-------|
| TC-001 | Test title | PASS | |
| TC-002 | Test title | FAIL | Expected X, got Y |

**Summary**: X passed, Y failed, Z skipped
**Failures requiring fixes**:
- TC-002: <clear description of what's wrong>
```

## Phase 5 — Determine Next Step

### If failures exist → Report to orchestrator

Report via SendMessage:
- Which items failed and why
- Suggested fix areas
- Whether failures are CRITICAL (blocking) or MINOR (deferrable)

### If all pass → Guide human validation

Present the human validation guide:

```markdown
## Human Validation Guide

### What was delivered
- Summary of the version's outcomes

### How to review (code projects: how to run it)
- Exact steps to see/use the deliverables

### What to verify
Walk through each Definition of Done item that requires human judgment.

### Quick checks
- [ ] Key deliverables are complete and accessible
- [ ] Quality meets expectations
- [ ] [Project-specific checks]

### Known limitations in this version
- (from "Simplified in this version")
```

The version ships only when the human confirms.

## Phase 6 — Document Findings

Append to the spec file:

```markdown
## Validation Findings

### Issues Found
- What didn't meet criteria

### Missing or Incomplete
- Gaps in deliverables

### Patterns Observed
- Recurring issues
```
