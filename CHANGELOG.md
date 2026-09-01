# Changelog

All notable changes to this project will be documented in this file.

This project maintains independent sequential versions (`v1`, `v2`, `v3`...):
- **Marketplace** (`metadata.version` in `.claude-plugin/marketplace.json`)
- **Each plugin** (`version` in `plugins/<name>/.claude-plugin/plugin.json`)

Versions are bumped automatically by CI on merge to main.

## [Plugin: plaud v29] - 2026-09-01

### Changed
- Tell the user what the page can hear, and how to keep a voice out

## [Marketplace v51] - 2026-09-01

### Changed
- Tell the user what the page can hear, and how to keep a voice out

## [Marketplace v50] - 2026-08-30

### Changed
- Correct what the marketplace version is evidence of

## [Marketplace v49] - 2026-08-30

### Changed
- Say that a plugin release moves the marketplace version

## [Plugin: plaud v28] - 2026-08-22

### Changed
- Follow the CLI down to one path per thing

## [Plugin: plaud v27] - 2026-08-22

### Changed
- Tell the user when voices have no name, and open the page when they ask

## [Plugin: plaud v26] - 2026-08-22

### Changed
- The route for an account that tags nothing

## [Plugin: plaud v25] - 2026-08-22

### Changed
- A profile is written by two people

## [Plugin: plaud v24] - 2026-08-22

### Changed
- Leave the Python one job: putting the CLI on the machine

## [Plugin: plaud v23] - 2026-08-22

### Changed
- plaud: install where the shell will find it

## [Plugin: plaud v22] - 2026-08-22

### Changed
- plaud: keep the binary that runs up to date, instead of installing beside it

## [Plugin: plaud v21] - 2026-08-22

### Changed
- plaud: ask for a transcript again, or in the language it was spoken

## [Plugin: plaud v20] - 2026-08-21

### Changed
- plaud: pin the CLI whose transcripts keep resolving after a re-run

## [Plugin: plaud v19] - 2026-08-21

### Changed
- plaud: a recording is transcribed once

## [Plugin: plaud v18] - 2026-08-21

### Changed
- plaud: pin the CLI that says whether a recording was transcribed here

## [Plugin: plaud v17] - 2026-08-21

### Changed
- plaud: write in UTF-8 whatever console it lands on

## [Plugin: plaud v16] - 2026-08-21

### Changed
- plaud: the context flags are the CLI's, here too

## [Plugin: plaud v15] - 2026-08-21

### Changed
- plaud: keep the CLI current, and say what describes a recording

## [Plugin: plaud v14] - 2026-08-21

### Changed
- plaud: find this machine's Python instead of demanding python3

## [Plugin: plaud v13] - 2026-08-21

### Changed
- plaud: fetch a transcript again to bring its names up to date

## [Plugin: miro-board v2] - 2026-08-20

### Changed
- miro-board: say what to run when the extract is gone

## [Plugin: plaud v12] - 2026-08-20

### Changed
- plaud: say who was in the room, from what already knows

## [Plugin: plaud v11] - 2026-08-20

### Changed
- plaud: require the context document, and stop pricing the tool

## [Plugin: plaud v10] - 2026-08-20

### Changed
- plaud: follow the CLI down to one transcript command

## [Plugin: plaud v9] - 2026-08-19

### Changed
- plaud: Smart App Control is not SmartScreen, and the advice differed

## [Plugin: plaud v8] - 2026-08-19

### Changed
- plaud: say what Windows does to an unsigned binary

## [Plugin: plaud v7] - 2026-08-19

### Changed
- plaud: pin the release that has the service in it

## [Plugin: artifact-publish v4] - 2026-08-12

### Changed
- fix: a published artifact can load external resources, and the docs said it could not

## [Plugin: nexaedge v7] - 2026-08-12

### Changed
- fix: read a file's mtime the same way on GNU and BSD

## [Plugin: nexaedge v6] - 2026-08-12

### Changed
- fix: install on a machine where the agent's own CLI is not on the PATH

## [Marketplace v48] - 2026-08-12

### Changed
- fix: install on a machine where the agent's own CLI is not on the PATH

## [Plugin: nexaedge v5] - 2026-08-08

### Changed
- fix: create the launcher on update too, for installs that predate it

## [Plugin: nexaedge v4] - 2026-08-08

### Changed
- fix: one stable command string, so approving the plugin once is enough

## [Marketplace v47] - 2026-08-08

### Changed
- fix: one stable command string, so approving the plugin once is enough

## [Marketplace v46] - 2026-08-07

### Changed
- fix: make INSTALL.md imperative, after Antigravity read it and did nothing

## [Plugin: nexaedge v3] - 2026-08-07

### Changed
- Merge pull request #6 from nexaedge/unambiguous-bootstrap

## [Marketplace v45] - 2026-08-07

### Changed
- Merge pull request #6 from nexaedge/unambiguous-bootstrap

## [Plugin: artifact-publish v3] - 2026-08-07

### Changed
- Merge pull request #5 from nexaedge/multi-agent-standards

## [Plugin: cloudflare-dns v3] - 2026-08-07

### Changed
- Merge pull request #5 from nexaedge/multi-agent-standards

## [Plugin: html-report v3] - 2026-08-07

### Changed
- Merge pull request #5 from nexaedge/multi-agent-standards

## [Plugin: linear-spec-plugin v2] - 2026-08-07

### Changed
- Merge pull request #5 from nexaedge/multi-agent-standards

## [Plugin: marketplace v2] - 2026-08-07

### Changed
- Merge pull request #5 from nexaedge/multi-agent-standards

## [Plugin: plaud v6] - 2026-08-07

### Changed
- Merge pull request #5 from nexaedge/multi-agent-standards

## [Plugin: spec-plugin v15] - 2026-08-07

### Changed
- Merge pull request #5 from nexaedge/multi-agent-standards

## [Plugin: vendored-skills v5] - 2026-08-07

### Changed
- Merge pull request #5 from nexaedge/multi-agent-standards

## [Marketplace v44] - 2026-08-07

### Changed
- Merge pull request #5 from nexaedge/multi-agent-standards

## [Plugin: plaud v5] - 2026-08-07

### Changed
- plaud: the assistant signs the user in, and never asks for a password

## [Plugin: plaud v4] - 2026-08-07

### Changed
- plaud: a new machine authenticates with an email and a password

## [Plugin: plaud v3] - 2026-08-07

### Changed
- plaud: report when the session expires, since nothing refreshes it

## [Plugin: plaud v2] - 2026-08-07

### Changed
- plaud: run anywhere — install the CLI, drop the sqlite3 dependency

## [Plugin: html-report v2] - 2026-08-03

### Changed
- feat: add html-report plugin (#4)

## [Marketplace v43] - 2026-08-03

### Changed
- feat: add html-report plugin (#4)

## [Plugin: artifact-publish v2] - 2026-07-27

### Changed
- feat: add artifact-publish plugin

## [Marketplace v42] - 2026-07-27

### Changed
- feat: add artifact-publish plugin

## [Plugin: spec-plugin v14] - 2026-06-19

### Changed
- feat(spec-plugin): honor external spec workspace mapping from CLAUDE.md

## [Plugin: spec-plugin v13] - 2026-06-08

### Changed
- Merge pull request #3 from nexaedge/spec-plugin-tuning-r2

## [Plugin: spec-plugin v12] - 2026-06-07

### Changed
- Merge pull request #2 from nexaedge/spec-plugin-perf-tuning

## [Plugin: spec-plugin v11] - 2026-06-06

### Changed
- Merge spec-plugin tuning F1–F12 + F14 alignment (v10); retire work-modes

## [Plugin: spec-plugin v9] - 2026-06-04

### Changed
- feat: lean spec-plugin orchestration redesign + work-modes primitives plugin

## [Plugin: work-modes v2] - 2026-06-04

### Changed
- feat: lean spec-plugin orchestration redesign + work-modes primitives plugin

## [Marketplace v41] - 2026-06-04

### Changed
- feat: lean spec-plugin orchestration redesign + work-modes primitives plugin

## [Plugin: spec-plugin v8] - 2026-06-04

### Changed
- fix(spec-plugin): add worktree .env setup to execute-task and validate-execution skills

## [Plugin: spec-plugin v7] - 2026-04-13

### Changed
- fix(orchestrate): require version architecture for PO, verify HEAD before spawning, worktree env setup

## [Plugin: vendored-skills v4] - 2026-04-02

### Changed
- feat: add from vercel-labs/agent-skills

## [Plugin: spec-plugin v6] - 2026-03-24

### Changed
- feat: base branch support, code-first mode, clean commits, strict agent reuse

## [Plugin: spec-plugin v5] - 2026-03-23

### Changed
- feat: add multi-repo worktree support for cross-repo orchestration

## [Marketplace v39] - 2026-03-19

### Changed
- feat: remove chrome-devtools-mcp

## [Plugin: cloudflare-dns v2] - 2026-03-19

### Changed
- Merge pull request #1 from nexaedge/feat/cloudflare-dns-plugin

## [Marketplace v38] - 2026-03-19

### Changed
- Merge pull request #1 from nexaedge/feat/cloudflare-dns-plugin

## [Plugin: vendored-skills v3] - 2026-03-19

### Changed
- feat: add from steipete/agent-scripts

## [Plugin: vendored-skills v2] - 2026-03-19

### Changed
- feat: add from anthropics/skills

## [Marketplace v37] - 2026-03-19

### Changed
- feat: add from anthropics/skills

## [Marketplace v36] - 2026-03-19

### Changed
- fix: use full HTTPS URLs for git-subdir to avoid SSH clone failures

## [Marketplace v35] - 2026-03-19

### Changed
- feat: remove marketing-skills

## [Marketplace v34] - 2026-03-19

### Changed
- feat: remove vendored-skills/mcp-builder

## [Plugin: vendored-skills v3] - 2026-03-19

### Changed
- feat: single vendored-skills plugin for all vendored skills, remove --plugin flag

## [Marketplace v33] - 2026-03-19

### Changed
- feat: single vendored-skills plugin for all vendored skills, remove --plugin flag

## [Plugin: skills v2] - 2026-03-19

### Changed
- feat: add from anthropics/skills

## [Marketplace v32] - 2026-03-19

### Changed
- feat: add from anthropics/skills

## [Marketplace v31] - 2026-03-19

### Changed
- feat: remove marketingskills/ai-seo,marketingskills/cold-email

## [Plugin: marketingskills v2] - 2026-03-19

### Changed
- feat: add from coreyhaines31/marketingskills

## [Marketplace v30] - 2026-03-19

### Changed
- feat: add from coreyhaines31/marketingskills

## [Marketplace v29] - 2026-03-19

### Changed
- feat: remove marketingskills/ai-seo,marketingskills/cold-email

## [Plugin: marketingskills v2] - 2026-03-19

### Changed
- feat: add from coreyhaines31/marketingskills

## [Marketplace v28] - 2026-03-19

### Changed
- feat: add from coreyhaines31/marketingskills

## [Marketplace v27] - 2026-03-19

### Changed
- fix: use url source for repo-root plugins, fix broken marketing-skills entry

## [Marketplace v26] - 2026-03-19

### Changed
- feat: remove marketingskills/ai-seo,marketingskills/content-strategy,marketingskills/copywriting, ...

## [Plugin: marketingskills v2] - 2026-03-19

### Changed
- feat: add skills from marketingskills, rewrite add command with fzf pickers

## [Marketplace v25] - 2026-03-19

### Changed
- feat: add skills from marketingskills, rewrite add command with fzf pickers

## [Plugin: seo v2] - 2026-03-19

### Changed
- feat: add plugin(s) from coreyhaines31/marketingskills

## [Marketplace v24] - 2026-03-19

### Changed
- feat: add plugin(s) from coreyhaines31/marketingskills

## [Marketplace v23] - 2026-03-19

### Changed
- feat: remove seo-audit

## [Plugin: seo v2] - 2026-03-19

### Changed
- feat: add plugin(s) from coreyhaines31/marketingskills

## [Marketplace v22] - 2026-03-19

### Changed
- feat: add plugin(s) from coreyhaines31/marketingskills

## [Marketplace v21] - 2026-03-19

### Changed
- feat: remove seo-audit

## [Marketplace v20] - 2026-03-19

### Changed
- feat: remove seo-audit

## [Plugin: seo v2] - 2026-03-19

### Changed
- feat: add plugin(s) from coreyhaines31/marketingskills

## [Marketplace v19] - 2026-03-19

### Changed
- feat: add plugin(s) from coreyhaines31/marketingskills

## [Marketplace v18] - 2026-03-19

### Changed
- feat: remove seo-audit

## [Plugin: seo v2] - 2026-03-19

### Changed
- feat: add plugin(s) from coreyhaines31/marketingskills

## [Marketplace v17] - 2026-03-19

### Changed
- feat: add plugin(s) from coreyhaines31/marketingskills

## [Marketplace v16] - 2026-03-19

### Changed
- feat: remove seo-audit

## [Marketplace v15] - 2026-03-19

### Changed
- fix: remove pluginRoot, use full paths for local plugins

## [Plugin: seo v2] - 2026-03-19

### Changed
- feat: add plugin(s) from coreyhaines31/marketingskills

## [Marketplace v14] - 2026-03-19

### Changed
- feat: add plugin(s) from coreyhaines31/marketingskills

## [Plugin: seo v2] - 2026-03-19

### Changed
- feat: add plugin(s) from coreyhaines31/marketingskills

## [Marketplace v13] - 2026-03-19

### Changed
- feat: add plugin(s) from coreyhaines31/marketingskills

## [Plugin: seo v2] - 2026-03-19

### Changed
- feat: add plugin(s) from coreyhaines31/marketingskills

## [Marketplace v12] - 2026-03-19

### Changed
- feat: add plugin(s) from coreyhaines31/marketingskills

## [Marketplace v11] - 2026-03-19

### Changed
- feat: remove seo-audit

## [Plugin: seo v2] - 2026-03-19

### Changed
- feat: add plugin(s) from coreyhaines31/marketingskills

## [Marketplace v10] - 2026-03-19

### Changed
- feat: add plugin(s) from coreyhaines31/marketingskills

## [Marketplace v9] - 2026-03-19

### Changed
- feat: remove seo

## [Marketplace v8] - 2026-03-19

### Changed
- feat: add plugin(s) from coreyhaines31/marketingskills

## [Marketplace v7] - 2026-03-19

### Changed
- feat: remove seo-audit

## [Plugin: seo-audit v2] - 2026-03-19

### Changed
- feat: add plugin(s) from coreyhaines31/marketingskills

## [Marketplace v6] - 2026-03-19

### Changed
- feat: add plugin(s) from coreyhaines31/marketingskills

## [Marketplace v5] - 2026-03-18

### Changed
- feat: add chrome-devtools-mcp plugin from ChromeDevTools/chrome-devtools-mcp

## [Marketplace v4] - 2026-03-18

### Changed
- fix: use url source for interface-design to force HTTPS cloning

## [Marketplace v3] - 2026-03-18

### Changed
- fix: use owner/repo shorthand for git-subdir URLs, remove vercel plugin

## [Marketplace v2] - 2026-03-18

### Changed
- fix: use HTTPS URLs for git-subdir plugin sources

## [Marketplace v1] - 2025-03-18

### Added
- Initial marketplace structure with spec-plugin as the first local plugin
- Added interface-design as an external plugin (from Dammyjay93/interface-design)
- Sequential versioning (`v1`, `v2`, ...) for marketplace and all plugins
- CI workflow for automatic version bumping and changelog updates
- Dynamic plugin detection in CI (bumps only changed plugins)
- CLAUDE.md with marketplace and plugin format conventions

### Changed
- Renamed from spec-plugin repo to nexaedge-marketplace

## [Plugin: spec-plugin v4] - 2025-03-18

### Changed
- Migrated to sequential versioning (from semver v3.1.0 to v4)

## [Plugin: spec-plugin v3] - 2025-03-16

### Changed
- Agent worktree lifecycle: agents now commit, merge to main, and clean up worktrees before reporting back to the team lead
- All 5 agents enforce commit-merge-cleanup flow before SendMessage

## [Plugin: spec-plugin v2] - 2025-03-10

### Added
- Context-aware project type detection (code repo, document workspace, empty directory, nested project)
- Skills adapt behavior based on workspace context
- Evolutionary delivery: projects broken into versions, each with its own architecture, stories, and validation
- Pipeline flow: /ideate -> /architect -> /plan -> /orchestrate

### Changed
- Refactored to version-based execution pipeline
- All skills now read workspace context before executing

## [Plugin: spec-plugin v1] - 2025-03-05

### Added
- Initial plugin with spec-driven development pipeline
- 5 agents: architect, product-owner, engineer, designer, qa
- 9 skills: ideate, architect, plan, architect-version, build-stories, execute-task, validate-execution, run-retrospective, orchestrate
- QA commit guard hook
- Worktree isolation for all agents
