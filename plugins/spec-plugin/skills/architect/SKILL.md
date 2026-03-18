---
name: architect
description: "Create the implementation approach for a project. For code projects: technology stack, schemas, API contracts, system design. For non-code projects: delivery approach, document structure, resource plan. Adapts based on the project spec. Use after /ideate."
argument-hint: "[project name or spec path]"
---

Your task: produce a comprehensive implementation approach document that makes every foundational decision explicit, with rationale. This is the PROJECT-LEVEL architecture — it covers decisions shared across ALL versions. Individual versions get their own architecture docs via `/architect-version`.

## Phase 1 — Load Context

1. **Find the project spec.** Check:
   - Argument provided → use as path or search for matching spec
   - `specs/<project-name>.md` in the current directory
   - `specs/spec.md` if only one spec exists
   - If nothing found, tell the user to run `/ideate` first
2. **Read the spec** — pay attention to the **Project Context** section (type, language, workspace)
3. If `specs/roadmap.md` exists, read it
4. If any `specs/v*.md` version files exist, skim them
5. Check if `specs/architecture.md` already exists — if so, ask user whether to redo or revise

The spec's **Project Context → Type** tells you what kind of architecture this needs.

## Phase 2 — Identify Decision Points

Catalog every foundational decision needed. The categories depend on the project type.

### For Code / Product Projects

- **Language & Runtime** — Programming language(s), version requirements, package management
- **Web Framework** — Backend API framework, frontend framework
- **Data Storage** — Primary database(s), caches, state storage
- **Task Processing** — Queue system, worker architecture, job patterns
- **LLM & AI** — LLM abstraction, embedding strategy, provider config (if applicable)
- **External Services** — Third-party APIs, integrations
- **Pipeline Orchestration** — How processing steps are defined and coordinated
- **State Management** — What's tracked where, incremental processing
- **Real-time Communication** — Live updates, webhooks, SSE
- **Observability** — Tracing, metrics, logging, cost tracking
- **Frontend** — UI framework, component library, data visualization
- **Configuration** — Settings management (files, env vars, runtime)
- **Project Structure** — Directory layout, module organization
- **Setup & Deployment** — How to install dependencies, configure, start, and deploy

Not every project needs all categories. Skip what's irrelevant.

### For Business / Consulting Projects

- **Delivery Structure** — What gets delivered, in what order, in what format
- **Document Organization** — How deliverables are structured and where they live
- **Tools & Resources** — What tools, data sources, or reference materials are needed
- **Stakeholder Communication** — How updates, reviews, and approvals flow
- **Quality Gates** — What review/approval steps exist before delivery
- **Dependencies** — External inputs, access, or decisions needed
- **Risk Mitigation** — How identified risks are managed

### For Research / Exploration Projects

- **Research Methodology** — How investigation will be conducted
- **Source Strategy** — What sources to use, how to evaluate them
- **Output Format** — Structure of the research output
- **Analysis Framework** — How findings will be organized and evaluated
- **Tool Selection** — Research tools, data collection methods
- **Scope Management** — How to handle scope expansion during research

### For Hybrid Projects

Mix categories from the above as appropriate.

## Phase 3 — Consult User

For each major decision, use AskUserQuestion to present:

- The decision to make
- 2-4 concrete options with trade-offs (include a comparison table when useful)
- Your recommendation and why

Group related decisions (2-3 per round) to keep the conversation efficient. Iterate until all major decisions are resolved.

## Phase 4 — Write Architecture Doc

Write `specs/architecture.md` (relative to where the project spec lives).

### For Code Projects

Include these sections:

1. **Technology Stack** — Table: Layer, Technology, Rationale
2. **System Architecture** — Diagram (ASCII/mermaid) showing components and data flow
3. **Project Structure** — Full directory tree with annotations
4. **Configuration** — Config file format, environment variables
5. **API Routes** — Endpoints grouped by domain (method, path, description)
6. **Database Schemas** — Full schema definitions with comments
7. **Pipeline Architecture** — Job flow, queue patterns, step transitions
8. **State Management** — Data store responsibilities, incremental processing
9. **Observability** — Instrumentation strategy, metrics, cost tracking
10. **Key Design Decisions** — Table: Decision, Choice, Why
11. **Setup & Deployment** — How to install, configure, start, and deploy the project. Include exact commands, environment setup, and any prerequisites.
12. **Dependencies** — Explicit dependency lists with version constraints

### For Non-Code Projects

Include these sections:

1. **Delivery Approach** — How the project will be executed, what phases
2. **Deliverable Structure** — What gets produced, document templates, folder organization
3. **Tools & Resources** — What's needed, where to find it, access requirements
4. **Communication Plan** — How stakeholders stay informed, review cadence
5. **Quality Framework** — How deliverables are reviewed and validated
6. **Key Decisions** — Table: Decision, Choice, Why
7. **Risk Register** — Risk, Impact, Mitigation, Owner
8. **Dependencies & Prerequisites** — What's needed from outside the project

### Writing Principles

- **Show, don't tell.** Include actual schemas, config examples, code patterns, directory trees, document templates — not descriptions of them.
- **Rationale everywhere.** Every choice should have a "Why" connected to project constraints.
- **Concrete over abstract.** Show actual queries, actual configs, actual document outlines.
- **Diagrams for complex relationships.** Use mermaid for architecture, data flow, sequences.

## Phase 5 — Consistency Check

Before finalizing, verify:
- Every success criterion from the spec has a corresponding component in the architecture
- Every deliverable has a clear production path
- No component references something not described in the architecture
- The architecture matches the project type (don't describe API routes for a research project)

## Phase 6 — Final Review

Present a summary:
- Key decisions made and their rationale
- Any deferred decisions (and when they'll be resolved)
- Risks or concerns
- Suggested next step: "Run `/plan` to design the delivery milestones, then `/orchestrate` to execute each version."

Ask for final sign-off.
