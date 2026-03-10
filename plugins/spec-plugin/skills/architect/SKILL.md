---
name: architect
description: "Create the high-level technical architecture for an entire project. Produces specs/architecture.md covering technology stack, system design, schemas, API contracts, state management, and observability. Use after /ideate has produced the product spec."
argument-hint: "[project name, e.g. corpus-graph-builder]"
---

Your task: produce a comprehensive technical architecture document that makes every foundational technology choice explicit, with rationale. This is the PROJECT-LEVEL architecture — it covers decisions shared across ALL versions. Individual versions get their own architecture docs via `/architect-version`.

## Phase 1 — Load Context

1. Read the product spec: `specs/<project-name>.md`
2. If `specs/roadmap.md` exists, read it for additional context
3. If any `specs/v*.md` version files exist, skim them for additional context
4. Check if `specs/architecture.md` already exists — if so, ask user whether to redo or revise

## Phase 2 — Identify Decision Points

Catalog every foundational technical decision needed across the project:

### Categories to Cover

- **Language & Runtime** — Programming language(s), version requirements, package management
- **Web Framework** — Backend API framework, frontend framework
- **Data Storage** — Primary database(s), vector storage, operational state storage
- **Task Processing** — Queue system, worker architecture, job patterns
- **LLM & AI** — LLM abstraction layer, embedding strategy, provider configuration
- **External Services** — Any domain-specific external services
- **Pipeline Orchestration** — How pipeline steps are defined, dispatched, and coordinated
- **State Management** — What's tracked where, how incremental processing works
- **Real-time Communication** — How the frontend gets live updates
- **Observability** — Tracing, metrics, logging, cost tracking
- **Frontend** — UI framework, component library, data visualization, data tables
- **Configuration** — How settings are managed (files, env vars, runtime)
- **Project Structure** — Directory layout, module organization

Not every project needs all categories. Skip what's irrelevant.

## Phase 3 — Consult User

For each major decision, use AskUserQuestion to present:

- The decision to make
- 2-4 concrete options with trade-offs (include a comparison table when useful)
- Your recommendation and why

Group related decisions (2-3 per round) to keep the conversation efficient. Iterate until all major decisions are resolved.

### Decision Presentation Format

```
**Decision: [What needs to be decided]**

| Option | Pros | Cons |
|--------|------|------|
| Option A | ... | ... |
| Option B | ... | ... |

**Recommendation:** Option A because [rationale tied to project constraints].
```

## Phase 4 — Write Architecture Doc

Write `specs/architecture.md` with these sections:

### Document Structure

1. **Technology Stack** — Table with Layer, Technology, Rationale columns. Cover every technology the project depends on.

2. **System Architecture** — ASCII or mermaid diagram showing all major components and how they connect. Show data flow between frontend, backend, databases, queues, workers, external services.

3. **Project Structure** — Full directory tree showing where every type of file lives. Annotate with comments explaining each directory's purpose.

4. **Configuration** — Show the actual config file format with all settings, commented. Show environment variables needed.

5. **API Routes** — Full list of API endpoints grouped by domain. Include HTTP method, path, and brief description. Detailed request/response shapes go in per-version architecture docs.

6. **Database Schemas** — Full schema definitions for every database. For SQL: CREATE TABLE statements with comments. For graph DBs: node labels, relationship types, constraints, indexes.

7. **Pipeline Architecture** — How jobs flow from definition to execution. Show the queue pattern, job types per pipeline step, and event-driven step transitions.

8. **State Management** — What each data store is responsible for. How incremental processing works. What's recoverable vs. what requires reprocessing.

9. **Observability & Cost Tracking** — Instrumentation strategy, what gets measured, how costs are calculated and stored.

10. **Provider Abstraction** — How external services are abstracted. Show the interface pattern with code examples.

11. **Key Design Decisions Summary** — Table with Decision, Choice, Why columns. One row per major decision made in Phase 3.

12. **Open Questions Resolved** — Table mapping questions from the product spec to their resolutions.

13. **Dependencies** — Explicit dependency lists for backend and frontend, with version constraints.

### Writing Principles

- **Show, don't tell.** Include actual schema definitions, config file examples, code patterns, and directory trees — not just descriptions of them.
- **Rationale everywhere.** Every technology choice should have a "Why" that connects back to project constraints or requirements.
- **Cross-reference versions.** Note which version introduces each component.
- **Concrete over abstract.** Show actual queries, actual schemas, actual config — not pseudocode descriptions.
- **Diagrams for system topology.** Use ASCII art for complex system architecture diagrams.

## Phase 5 — Consistency Check

Before finalizing, verify:

- Every pipeline phase from the product spec has a corresponding component in the architecture
- Database schemas cover all entity types from the product spec's data model
- API routes cover all the functionality described in the spec
- Configuration covers all tunable parameters mentioned in the spec
- No component references a technology or pattern not described in the architecture

## Phase 6 — Final Review

Present a summary to the user:
- Technology stack overview (one line per layer)
- Key decisions made and their rationale
- Any deferred decisions (and which version's architecture phase will resolve them)
- Risks or concerns
- Suggested next step: "Run `/plan <project-name>` to design the version roadmap, then `/orchestrate <version>` to execute each version."

Ask for final sign-off before considering the architecture complete.
