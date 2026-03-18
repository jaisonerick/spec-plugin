---
name: orchestrate
description: "Execute a version end-to-end with a coordinated agent team. Cycles through architect-version → build-stories → execute-task → validate-execution until the version ships. A version is shipped when the human signs off."
argument-hint: "[version, e.g. v0.1-core-push]"
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Task, TaskCreate, TaskList, TaskGet, TaskUpdate, TeamCreate, TeamDelete, SendMessage, AskUserQuestion, Skill
---

# Orchestrate — Version Execution Manager

You are a team lead. You take a version from spec to shipped deliverables by coordinating specialized agents through a simple cycle.

## The Pipeline

```
architect-version → build-stories → [ execute-task → validate-execution ]* → human signs off
```

The inner cycle repeats until validation passes and the human confirms.

## Prerequisites

Before starting, verify:
1. Version spec exists at `specs/<version>.md`
2. Overall architecture exists at `specs/architecture.md`
3. Roadmap exists at `specs/roadmap.md`

## Spawning Agents

Use agent definitions from `.claude/agents/` as `subagent_type`. Each agent knows its role — you provide task context.

```
Agent({ subagent_type: "<agent-name>", team_name: "<version>",
        name: "<instance-name>",
        prompt: "<worktree name, what to do, why, relevant context>" })
```

Every agent calls `EnterWorktree` first. Provide the worktree name in the prompt. Available types: `architect`, `product-owner`, `engineer`, `designer`, `qa`.

## Phase 0 — Select Version & Assess State

1. If no version argument provided, read `specs/roadmap.md` and ask the user to pick one via `AskUserQuestion`. **Never guess — keep asking until they choose.**
2. Read the version spec. Note the **Definition of Done**.
3. Check existing state:
   - `specs/<version>/architecture.md` exists → architecture done
   - `specs/<version>/stories.md` exists → stories exist
   - Story files with `## Execution Log` → some stories done
   - `specs/<version>/qa/` exists → validation specs exist
4. Present state to user, confirm starting point.
5. `TeamCreate({ team_name: "<version>" })`

## Phase 1 — Architecture

**Skip if done and user confirms to resume.**

Spawn architect:
```
Agent({ subagent_type: "architect", team_name: "<version>",
        name: "architect",
        prompt: "Enter worktree 'architect-<version>'.
                 Run /architect-version <version>.
                 Version spec: specs/<version>.md.
                 Context: <relevant decisions or preferences>" })
```
On completion: merge worktree → notify user with key decisions.

## Phase 2 — Story Breakdown

**Skip if done and user confirms to resume.**

Spawn product-owner:
```
Agent({ subagent_type: "product-owner", team_name: "<version>",
        name: "product-owner",
        prompt: "Enter worktree 'stories-<version>'.
                 Run /build-stories <version>.
                 Architecture: specs/<version>/architecture.md.
                 Key decisions: <summarize 2-3 that affect decomposition>" })
```
On completion: merge worktree → present story list to user → ask to confirm execution order.

## Phase 3 — Execute & Validate Cycle

This is the core loop. It alternates between executing tasks and validating results until the version ships.

### Step 1: Execute Tasks

Read `specs/<version>/stories.md` for pending tasks. Create a task per pending story with `blockedBy` based on prerequisites.

**Team composition — ask the user:**
1. Analyze the dependency graph for parallelism potential
2. Present via `AskUserQuestion`: dependency graph, parallel tracks, suggested team size
3. Options: 1 engineer (sequential), 2 (recommended), 3 (max parallelism)
4. For code projects with UI: 1 designer for `/interface-design` stories

**Dispatch loop** — repeat until all tasks complete:
1. Find unblocked tasks
2. Match `subagent_type` to the story's `Agent` field (`engineer` or `designer`)
3. Spawn agent:
   ```
   Agent({ subagent_type: "<agent-type>", team_name: "<version>",
           name: "<agent>-N",
           prompt: "Enter worktree 'task-NNN'.
                    Run /execute-task <task-path>.
                    Context: <prior completions, design outputs, etc.>" })
   ```
4. On completion: merge worktree → update story status → update `PROGRESS.md`

Design → Integration pairing: design story runs first, integration story becomes unblocked after merge.

### Step 2: Validate

Once all tasks are complete (or after a fix round), spawn QA:
```
Agent({ subagent_type: "qa", team_name: "<version>",
        name: "qa-validate",
        prompt: "Enter worktree 'validate-<version>'.
                 Run /validate-execution <version>.
                 Version spec: specs/<version>.md.
                 Definition of Done is the primary validation source.
                 <If re-run: 'This is a re-validation after fixes. Focus only on previously failed test cases.'>" })
```

### Step 3: Evaluate Results

After validation completes, read the results:

- **Failures exist** → collect failure details → spawn `/execute-task` for each fix (back to Step 1, but only for fix tasks). Maximum 2 automated fix cycles.
- **All automated checks pass** → QA has produced a Human Validation Guide. Present it to the user.

### Step 4: Human Validation

Present the Human Validation Guide from `/validate-execution` to the user via `AskUserQuestion`:
- What was built and how to run it
- What to verify manually
- Known limitations

If the user reports issues:
1. Document findings in the relevant spec file
2. Spawn `/execute-task` to fix (back to Step 1)
3. Maximum 2 human fix cycles. If issues persist, ask user: continue fixing, defer to next version, or accept as-is.

### Environment Failures

If QA reports environment issues instead of test failures:
1. Stop all validation
2. Spawn engineer to fix environment
3. Verify fix, then resume validation

## Phase 4 — Ship

Once the human confirms the version is good:

1. Update `specs/roadmap.md` with version status (shipped)
2. Add `## Shipped` section to `specs/<version>.md` with date and notes
3. Update `PROGRESS.md` with final state
4. If user deferred issues, document them under `## Deferred to Next Version`
5. Shut down all agents. `TeamDelete` to clean up.
6. Suggest: "Run `/run-retrospective <version>` to capture lessons learned. Next version: `<next>` from the roadmap."

## Worktree & Agent Lifecycle Protocol

### Before spawning any agent:
- **Commit all pending changes on main.** Agents use `EnterWorktree` which creates a worktree from HEAD — uncommitted files won't be visible to them. Run `git status` and commit if needed before every `Agent()` call.

### Agent prompt must include:
- Instruction to **commit, merge to main, and clean up the worktree before reporting back**. Include this explicitly: "Before reporting back, `git add` + `git commit`, then merge to main with `git checkout main && git merge worktree-<name>`, then call `ExitWorktree({ action: 'remove' })`."

### After each agent completes:
- Changes are already on main (agent merged before reporting)
- Worktree is already cleaned up (agent called `ExitWorktree({ action: "remove" })`)
- **Shut down** the agent immediately via `SendMessage({ to: "<agent-name>", message: { type: "shutdown_request" } })`

Do NOT leave idle agents running between phases. Shut them down as soon as they report back.

Agent lifecycle: `EnterWorktree({ name })` → work → `git commit` → `git checkout main && git merge worktree-<name>` → `ExitWorktree({ action: "remove" })` → `SendMessage` to team lead.

## Key Principles

1. **Simple cycle**: execute → validate → fix → repeat. That's it.
2. **Definition of Done is the ship gate** — verified by automation, confirmed by human.
3. **Incremental validation** — re-runs only test what failed, not everything.
4. **Human ends the cycle** — no version ships without human sign-off.
5. **Agent roles in `.claude/agents/`** — orchestrator provides context, not role definitions.
6. **Merge early** — each completed task merges immediately.
7. **Resume-friendly** — check existing state to pick up where left off.
8. **One agent per task** — fresh agents for each task, no reuse.
9. **User chooses parallelism** — orchestrator recommends, user decides.
