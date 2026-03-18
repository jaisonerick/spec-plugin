---
name: architect-version
description: "Deep-dive architecture for a single version. Reads the version spec, overall architecture, roadmap, and related versions, then produces a comprehensive architecture document with specific implementation choices. Adapts to project type. Use before /build-stories."
argument-hint: "[version, e.g. v0.1-core-push]"
---

Your task: produce a comprehensive architecture document for the given version that makes every important decision explicit, with rationale.

## Phase 1 — Load Context

1. Read the target version spec at `specs/<version>.md`
2. Read the overall architecture: `specs/architecture.md`
3. Read the roadmap: `specs/roadmap.md`
4. Read the project spec (find the main spec in `specs/`) — check **Project Context** for project type
5. Skim other version specs (`specs/v*.md`) to understand prior and future versions
6. Check if the version folder already has files: `specs/<version>/`

## Phase 2 — Analyze

Identify all key decisions needed for this version. Adapt categories to the project type.

### For Code Projects

- Technology choices (libraries, frameworks, tools)
- Data flow and data models
- API contracts (endpoints, request/response shapes)
- Component boundaries and responsibilities
- Integration points with prior and future versions
- Error handling, state management, performance
- Test strategy (see below)

### For Non-Code Projects

- Deliverable structure and format
- Research methodology or delivery approach for this version specifically
- Input sources and dependencies
- Quality criteria and review process
- Stakeholder touchpoints in this version
- Integration with prior deliverables

Pay special attention to **"Simplified in this version"** from the version spec — architecture should match the simplified scope, not the full future version.

## Phase 3 — Consult User

Use AskUserQuestion for every significant decision point. Present:
- The decision to make
- 2-4 concrete options with trade-offs
- Your recommendation and why

Limit to 2-3 decisions per round. Iterate until resolved.

## Phase 4 — Write Architecture Doc

Write `specs/<version>/architecture.md`.

### For Code Projects

1. **Overview** — What this version delivers, scope boundaries
2. **Key Decisions** — Each decision with chosen option and rationale
3. **Data Model** — Schemas, types, database tables
4. **API Contracts** — Endpoints, request/response shapes, error codes
5. **Component Breakdown** — Each component: responsibility, inputs, outputs
6. **Integration Points** — Connections to existing and future work
7. **Test Strategy** — Testing approach by complexity tier:
   - Core/complex logic: thorough unit tests
   - Key components: at least one test pass
   - Simple glue: tested implicitly
   - Integration and E2E tests
   - Test infrastructure (fixtures, mocking)
8. **Flow Diagrams** — Mermaid diagrams for data flows, sequences
9. **State Machines** — Mermaid state diagrams for stateful processes
10. **Constraints & Assumptions**

### For Non-Code Projects

1. **Overview** — What this version delivers, scope boundaries
2. **Key Decisions** — Each decision with rationale
3. **Deliverable Specification** — Exact structure, format, and content outline for each deliverable
4. **Input Requirements** — What data, access, or prior work is needed
5. **Quality Criteria** — How each deliverable will be evaluated
6. **Stakeholder Review Plan** — Who reviews what, when
7. **Dependencies & Risks** — What could block or delay this version
8. **Constraints & Assumptions**

### Diagram Requirements (all projects)

Use mermaid for ALL diagrams:
- `flowchart` for processes and relationships
- `sequenceDiagram` for interactions
- `erDiagram` for data models
- `stateDiagram-v2` for state machines

## Phase 5 — Final Review

Present a summary:
- Scope of decisions made
- Deferred decisions (and why)
- Key risks or open questions
- Ask for final sign-off
