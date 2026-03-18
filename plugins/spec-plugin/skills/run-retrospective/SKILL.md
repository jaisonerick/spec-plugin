---
name: run-retrospective
description: "Post-version retrospective that captures lessons learned, fixes documentation drift, and proposes skill improvements. Analyzes PROGRESS.md, story logs, QA results, and commit/change history to identify struggle patterns and knowledge worth preserving. Run after a version is shipped."
argument-hint: "[version, e.g. v0.1-core-push]"
---

Your output: documentation fixes, topic-based lesson files in `docs/`, and proposed skill/CLAUDE.md improvements.

## Phase 1 — Collect Evidence

Gather all sources of truth about what happened during this version:

1. **Read PROGRESS.md** — overall timeline, issues encountered, fix cycles
2. **Read story execution logs** — check each story file in `specs/<version>/` for `## Execution Log` sections (look for "Issues Encountered", "Struggled With", "Decisions Made")
3. **Read QA run results** — check each spec in `specs/<version>/qa/` for `## Run Results`, `## Setup & DX Findings`, and `## Struggles & Patterns` sections
4. **Read the architecture doc** — `specs/<version>/architecture.md`
5. **Read commit history** — `git log --oneline` for the version's timeframe, look for fix commits, reverts, multiple attempts
6. **Read current skills** — `.claude/skills/*/SKILL.md` for context on what agents are told to do
7. **Read CLAUDE.md** — current project conventions

## Phase 2 — Identify Patterns

Categorize findings into four buckets:

### A. Documentation Drift
Architecture doc says X, but the actual code does Y. Examples:
- Port numbers differ between docs and config
- Data model has fields the docs don't mention
- API contracts changed during implementation

### B. Struggle Patterns
Things that took multiple attempts. Sources:
- QA fix cycles (how many rounds? what kept failing?)
- Story execution logs with "Struggled With" or repeated "Issues Encountered"
- Commit history showing fix-after-fix patterns

### C. Agent Autonomy Gaps
Places where agents couldn't proceed without help:
- AskUserQuestion calls (what did agents not know?)
- Tool errors (what tools failed and why?)
- QA DX findings (environment/setup issues agents hit)

### D. Skill Gaps
Recurring issues that skills should prevent:
- Patterns that could be added to engineer/qa/orchestrate skills
- Missing conventions in CLAUDE.md
- Common mistakes agents keep making

**After listing ALL findings across all four categories:**
1. Prioritize by impact (how much time was wasted? how likely to recur?)
2. **Pick the top 3-5 findings** to preserve as lessons. Not everything needs documentation — focus on high-impact, likely-to-recur items.

## Phase 3 — Update Documentation (No Approval Needed)

Fix factual discrepancies between documentation and reality. These are corrections, not opinions:

1. **Architecture doc** (`specs/<version>/architecture.md`) — fix incorrect ports, endpoints, data models, configuration values that don't match the actual code
2. **Story statuses** — update `specs/<version>/stories.md` if any stories have incorrect status
3. **Roadmap** — update `specs/roadmap.md` if the version's status or shipped state changed

Keep changes minimal and factual. Don't rewrite sections — fix specific inaccuracies.

## Phase 4 — Lessons Learned & Skill Improvements (Requires Approval)

For each category below, present findings to the user via `AskUserQuestion` and only proceed with approved changes.

### A. Write Lessons to `docs/` Files

Create or update topic-based files in `docs/`. Each file covers one topic and can contain multiple findings.

**File format:**
```markdown
# <Topic>

## <Finding title>
<What went wrong, 1-2 sentences>
<What works and how to prevent it, 1-2 sentences>

## <Finding title>
...
```

**Rules:**
- **Append to existing files** when the topic already has a `docs/<topic>.md` file
- **Create new files** only when no existing file covers the topic
- Keep each finding to 2 paragraphs max (what went wrong + what works)

**Before writing, ask the user** (via `AskUserQuestion`):
> "I found these lessons worth documenting. Which should I save?"

### B. Propose Skill Changes

Group proposed changes by skill file. For each:
1. Describe what happened (the struggle or gap)
2. Show the proposed addition/change (as a diff or new section)
3. Ask the user via `AskUserQuestion` whether to apply

### C. Propose CLAUDE.md Additions

Only for truly universal conventions that apply across ALL versions. These should be rare.

Present each proposed addition and ask via `AskUserQuestion` before adding.

## Phase 5 — Summary & Commit

1. **Summarize** what was done:
   - Documentation fixes applied (Phase 3)
   - Lessons written to `docs/` (Phase 4A)
   - Skill changes applied (Phase 4B)
   - CLAUDE.md updates (Phase 4C)
2. **Commit** all changes with a descriptive message:
   ```
   Retrospective: <version> — N lessons, M doc fixes, K skill updates
   ```
3. **Report** to the team lead (if running as a team member) via `SendMessage`:
   - Summary of findings
   - Files created/modified
   - Any deferred items that need manual attention
