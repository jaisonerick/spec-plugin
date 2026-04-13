---
name: orchestrate
description: "Execute a version end-to-end with a coordinated agent team. Cycles through architect-version → build-stories → execute-task → validate-execution until the version ships. A version is shipped when the human signs off."
argument-hint: "[version, e.g. v0.1-core-push]"
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Agent, Task, TaskCreate, TaskList, TaskGet, TaskUpdate, TeamCreate, TeamDelete, SendMessage, AskUserQuestion, Skill
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

## Phase 0 — Detect Workspace, Select Version & Assess State

### Step 0a: Record Base Branch

Record the **current git branch** as `base_branch` (`git branch --show-current`). This is the reference branch for ALL agent work — agents create worktrees from it, compare against it, and merge back to it. **Never hardcode "main"** — use whatever branch is current when `/orchestrate` is invoked.

### Step 0b: Detect Workspace & Locate Specs

Before doing anything else, understand the workspace — the same way `/ideate` does:

1. **Read CLAUDE.md** (project-level and user-level) — learn conventions, folder structure, references to second-brain or external repos.
2. **Scan the directory** — what's here? Code repo (package.json, Cargo.toml, go.mod)? Document workspace? Organized workspace with project subdirectories?
3. **Check for existing specs** — does a `specs/` directory exist here, or inside a subdirectory?
4. **Check parent context** — if this is a subdirectory, what's above?

From this, determine the workspace layout:

- **`specs/` exists in CWD** → you're in a project directory (or single-repo). Record CWD as the specs location. If the Project Context references a separate code repo, record it as `code_repo` (specs-first multi-repo).
- **CWD is a workspace root** (e.g., second-brain, organized by projects/areas) → look for the project inside subdirectories. Scan for project folders with `specs/` inside them. If the version argument or user context hints at a specific project, match by name. If ambiguous, ask via `AskUserQuestion`.
- **CWD is a code repository** (has code markers but no `specs/`) → search for an external specs location:
  a. Check CLAUDE.md for references to a second-brain or specs repository.
  b. Search there for a folder matching the current project — by directory name, git remote, or project name.
  c. If found, record `specs_repo` (absolute path), `code_repo` (CWD), and `specs_prefix` (path to specs within the specs repo).
  d. If not found, ask the user via `AskUserQuestion`.

This determines the **workspace mode**:
- **Single-repo**: specs and code in the same repo. Agents use `EnterWorktree`.
- **Specs-first multi-repo**: CWD is the specs/workspace repo, code lives elsewhere. Agents create manual worktrees in the code repo.
- **Code-first multi-repo**: CWD is the code repo, specs live elsewhere (e.g., second-brain). Agents use `EnterWorktree` for code isolation. Spec changes are committed directly in the specs repo.

### Step 0c: Select Version & Assess State

1. If no version argument provided, read the roadmap (in the specs location) and ask the user to pick one via `AskUserQuestion`. **Never guess — keep asking until they choose.**
2. Read the version spec. Note the **Definition of Done**.
3. Check existing state:
   - `<version>/architecture.md` exists → architecture done
   - `<version>/stories.md` exists → stories exist
   - Story files with `## Execution Log` → some stories done
   - `<version>/qa/` exists → validation specs exist
4. Present state to user, confirm starting point.
5. `TeamCreate({ team_name: "<version>" })`

## Phase 1 — Architecture

**Skip if done and user confirms to resume.**

Spawn architect:
```
Agent({ subagent_type: "architect", team_name: "<version>",
        name: "architect",
        prompt: "Base branch: <base_branch>.
                 Specs location: <specs path>.
                 Enter worktree 'architect-<version>'.
                 Run /architect-version <version>.
                 Version spec: <specs_prefix>/<version>.md.
                 Context: <relevant decisions or preferences>" })
```
On completion: merge worktree → **shut down the architect agent immediately** → notify user with key decisions.

## Phase 2 — Story Breakdown

**Skip if done and user confirms to resume.**

**CRITICAL: Version architecture is a hard prerequisite.** Before spawning the PO, verify `<specs_prefix>/<version>/architecture.md` exists on the base branch HEAD. If it doesn't exist, STOP and investigate — the architect phase may not have merged correctly. PO agents that work without the version architecture produce stories that diverge from architectural decisions.

Spawn product-owner:
```
Agent({ subagent_type: "product-owner", team_name: "<version>",
        name: "product-owner",
        prompt: "Base branch: <base_branch>.
                 Specs location: <specs path>.
                 Enter worktree 'stories-<version>'.
                 Run /build-stories <version>.

                 REQUIRED FIRST STEP: Read the VERSION-SPECIFIC architecture before doing anything else:
                   <specs_prefix>/<version>/architecture.md
                 This file is your PRIMARY source for story breakdown. It contains the file manifest,
                 component breakdown, code sketches, test strategy, and dependency graph.
                 Do NOT proceed with story writing until you have read this file.
                 If the file doesn't exist or is empty, STOP and report back immediately.

                 Architecture: <specs_prefix>/<version>/architecture.md.
                 Key decisions: <summarize 2-3 that affect decomposition>" })
```
On completion: merge worktree → **shut down the product-owner agent immediately** → present story list to user → **review stories against the version architecture** for divergences → ask to confirm execution order.

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
3. **CRITICAL: Never reuse an existing agent for a different task.** Every task MUST get a fresh agent. Before spawning, shut down any completed agents that are still running.
4. Spawn agent — adapt prompt based on workspace mode:
   **Single-repo:**
   ```
   Agent({ subagent_type: "<agent-type>", team_name: "<version>",
           name: "<agent>-N",
           prompt: "Base branch: <base_branch>.
                    Enter worktree 'task-NNN'.
                    Run /execute-task <task-path>.
                    Context: <prior completions, design outputs, etc.>" })
   ```
   **Specs-first multi-repo (CWD is specs repo, code_repo is external):**
   ```
   Agent({ subagent_type: "<agent-type>", team_name: "<version>",
           name: "<agent>-N",
           prompt: "Base branch: <base_branch>.
                    Code repository: <code_repo>
                    Create a code worktree: git -C <code_repo> worktree add .claude/worktrees/task-NNN -b worktree-task-NNN <base_branch>
                    Work from <code_repo>/.claude/worktrees/task-NNN for all code changes.
                    Run /execute-task <task-path>.
                    Context: <prior completions, design outputs, etc.>
                    Before reporting back: clean commit history, merge to <base_branch> in code repo (fast-forward only), remove code worktree, commit spec updates." })
   ```
   **Code-first multi-repo (CWD is code repo, specs in external repo):**
   ```
   Agent({ subagent_type: "<agent-type>", team_name: "<version>",
           name: "<agent>-N",
           prompt: "Base branch: <base_branch>.
                    Specs repo: <specs_repo>.
                    Enter worktree 'task-NNN'.
                    Run /execute-task <task-path>.
                    Context: <prior completions, design outputs, etc.>
                    Before reporting back: clean commit history, merge to <base_branch> (fast-forward only), commit spec updates in specs repo." })
   ```
5. On completion: merge worktree → **shut down the agent immediately** → update story status → update `PROGRESS.md`

Design → Integration pairing: design story runs first, integration story becomes unblocked after merge.

### Step 2: Validate

Once all tasks are complete (or after a fix round), spawn QA. **Always spawn a fresh QA agent** — never reuse from a previous validation round. Shut down the previous QA agent first if one exists. Adapt prompt based on workspace mode:

**Single-repo:**
```
Agent({ subagent_type: "qa", team_name: "<version>",
        name: "qa-validate-N",
        prompt: "Base branch: <base_branch>.
                 Enter worktree 'validate-<version>'.
                 Run /validate-execution <version>.
                 Version spec: <specs_prefix>/<version>.md.
                 Definition of Done is the primary validation source.
                 <If re-run: 'This is a re-validation after fixes. Focus only on previously failed test cases.'>" })
```

**Specs-first multi-repo (CWD is specs repo, code_repo is external):**
```
Agent({ subagent_type: "qa", team_name: "<version>",
        name: "qa-validate-N",
        prompt: "Base branch: <base_branch>.
                 Code repository: <code_repo>
                 Create a code worktree: git -C <code_repo> worktree add .claude/worktrees/validate-<version> -b worktree-validate-<version> <base_branch>
                 Work from <code_repo>/.claude/worktrees/validate-<version> for all testing.
                 Run /validate-execution <version>.
                 Version spec: <specs_prefix>/<version>.md.
                 Definition of Done is the primary validation source.
                 Before reporting back: commit QA results, merge to <base_branch> in code repo (fast-forward only), remove code worktree, commit spec updates.
                 <If re-run: 'This is a re-validation after fixes. Focus only on previously failed test cases.'>" })
```

**Code-first multi-repo (CWD is code repo, specs in external repo):**
```
Agent({ subagent_type: "qa", team_name: "<version>",
        name: "qa-validate-N",
        prompt: "Base branch: <base_branch>.
                 Specs repo: <specs_repo>.
                 Enter worktree 'validate-<version>'.
                 Run /validate-execution <version>.
                 Version spec: <specs_prefix>/<version>.md.
                 Definition of Done is the primary validation source.
                 Before reporting back: merge to <base_branch> (fast-forward only), commit QA results in specs repo.
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

### Base Branch

All agents work relative to the `base_branch` recorded in Phase 0. **Every agent prompt MUST include the base branch.** Agents create worktrees from it, merge back to it, and compare against it. Never hardcode "main".

### Before spawning any agent:
- **Commit all pending changes on the base branch** in ALL repositories agents will work on. Run `git status` (and `git -C <code_repo> status` if applicable) and commit if needed before every `Agent()` call. Worktrees are created from HEAD — uncommitted files won't be visible.
- **Verify HEAD includes all prior phase commits.** Run `git log --oneline -1` on each repo's base branch and confirm the most recent merge from the previous phase is present. Agents in specs-first multi-repo mode create worktrees via `git worktree add` from HEAD — if a prior phase's merge hasn't landed yet, the new agent won't see those files.
- **For specs-first multi-repo manual worktrees:** After `git worktree add`, check if `scripts/setup-worktree.sh` exists in the code repo and instruct the agent to run it. This script copies `.env` and other gitignored files that worktrees don't inherit. If the script doesn't exist, instruct the agent to copy `.env` files manually: `cp <code_repo>/.env* <worktree_path>/`.

### Single-repo mode (specs and code in the same repo):
Agent lifecycle: `EnterWorktree({ name })` → work → clean up commit history → `git checkout <base_branch> && git merge --ff-only worktree-<name>` → `ExitWorktree({ action: "remove" })` → `SendMessage` to team lead.

### Specs-first multi-repo mode (CWD is specs repo, code_repo is external):
Agents that modify code must create worktrees in the **code repository** using git commands — `EnterWorktree` only isolates the CWD repo (where specs live), not external repos.

Agent prompt must include:
```
Base branch: <base_branch>
Code repository: <absolute-path-to-code-repo>
Create a worktree in the code repo before starting:
  git -C <code_repo> worktree add .claude/worktrees/<name> -b worktree-<name> <base_branch>
Work from <code_repo>/.claude/worktrees/<name> for all code changes.
Before reporting back:
  1. Clean up commit history (squash/rebase to minimal commits)
  2. cd <code_repo> && git checkout <base_branch> && git pull --rebase && git merge --ff-only worktree-<name>
  3. git worktree remove .claude/worktrees/<name>
  4. Commit any spec changes directly (story status updates, execution logs)
```

Spec-only agents (architect, product-owner doing story breakdown) that don't modify code can use `EnterWorktree` as usual — they only write to the specs repo.

### Code-first multi-repo mode (CWD is code repo, specs in external repo):
Agents use `EnterWorktree` for code isolation (since CWD is the code repo). Spec changes are committed directly in the specs repo.

Agent prompt must include:
```
Base branch: <base_branch>
Specs repo: <absolute-path-to-specs-repo>
Enter worktree '<name>' for code isolation.
Before reporting back:
  1. Clean up commit history (squash/rebase to minimal commits)
  2. git checkout <base_branch> && git pull --rebase && git merge --ff-only worktree-<name>
  3. ExitWorktree({ action: "remove" })
  4. Commit spec changes in the specs repo (story status, execution logs)
```

### After each agent completes:
- Changes are already on the base branch in all repos (agent merged before reporting)
- Worktrees are already cleaned up
- **Shut down** the agent immediately via `SendMessage({ to: "<agent-name>", message: { type: "shutdown_request" } })`

Do NOT leave idle agents running between phases. Shut them down as soon as they report back.

### Agent Reuse Policy — NEVER Reuse Agents

**Every task MUST get a fresh agent.** Never send a new task to an existing agent, even if it's the same agent type. The orchestrator must:
1. Shut down the previous agent (`SendMessage` with `shutdown_request`)
2. Spawn a new agent with a unique name (e.g., `engineer-1`, `engineer-2`)
3. Provide full context in the new agent's prompt — don't assume it has prior context

This applies to ALL agents: engineers, designers, QA, architects, product-owners. No exceptions.

## Key Principles

1. **Simple cycle**: execute → validate → fix → repeat. That's it.
2. **Definition of Done is the ship gate** — verified by automation, confirmed by human.
3. **Incremental validation** — re-runs only test what failed, not everything.
4. **Human ends the cycle** — no version ships without human sign-off.
5. **Agent roles in `.claude/agents/`** — orchestrator provides context, not role definitions.
6. **Merge early** — each completed task merges immediately.
7. **Resume-friendly** — check existing state to pick up where left off.
8. **One agent per task, always fresh** — NEVER reuse an agent for a different task. Kill the previous agent, spawn a new one. Every task = new agent instance with a unique name.
9. **User chooses parallelism** — orchestrator recommends, user decides.
10. **Base branch, not main** — use the branch the user is on, not hardcoded "main".
11. **Clean commit history** — each agent merges exactly one commit into the base branch via fast-forward.
