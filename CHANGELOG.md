# Changelog

All notable changes to this project will be documented in this file.

This project maintains independent sequential versions (`v1`, `v2`, `v3`...):
- **Marketplace** (`metadata.version` in `.claude-plugin/marketplace.json`)
- **Each plugin** (`version` in `plugins/<name>/.claude-plugin/plugin.json`)

Versions are bumped automatically by CI on merge to main.

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
