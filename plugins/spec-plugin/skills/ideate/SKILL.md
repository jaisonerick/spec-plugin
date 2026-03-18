---
name: ideate
description: "Build a comprehensive project specification through conversational refinement. Adapts to any project type — code, business, research, consulting. Reads workspace context to understand where it is and what kind of project this is. Use at the very start of a new project or major initiative."
argument-hint: "[what the project is about, e.g. 'a new inventory management system' or 'research on LLM evaluation strategies']"
---

Your task: produce a comprehensive project specification through iterative conversation with the user. You adapt your approach based on what kind of project this is — you figure that out by reading the workspace and asking smart questions.

## Phase 1 — Understand the Workspace

Before asking the user anything, read the environment:

1. **Read CLAUDE.md** (if it exists) — this tells you the conventions, folder structure, and how this workspace is organized
2. **Scan the directory** — what's here? Is this a code repo (package.json, Cargo.toml, go.mod)? A document workspace? An empty directory? A project within a larger structure?
3. **Check for existing specs** — does a `specs/` directory already exist? Are there prior specs?
4. **Check parent context** — if this is a subdirectory, what's above? (e.g., you might be in `clients/acme/` inside a larger workspace)

From this, form an initial understanding:
- **Where am I?** (standalone repo, subdirectory of a larger workspace, empty directory)
- **What kind of workspace is this?** (code project, document workspace, blank slate)
- **Where should specs go?** (local `specs/`, or somewhere informed by the workspace structure)

Do NOT assume the project type yet — let Phase 2 confirm it.

## Phase 2 — Seed the Vision

Start by asking the user what they want to build. Use `AskUserQuestion` and adapt based on the workspace context you discovered.

**Round 1 — What and Why:**
- What are you trying to accomplish? What's the problem or opportunity?
- Who is this for? (yourself, a client, end users, a team?)

If you recognized workspace structure (e.g., a workspace organized by client or project type), ask a smart follow-up:
- "Is this related to [entity you found]? Should I add this there, or create a new project?"
- "I see this workspace organizes by [pattern]. Where does this project fit?"

**Round 2 — Shape and Scope:**

Adapt these questions based on what you're learning about the project:

*If it's becoming a code/product project:*
- What does the end state look like? What exists when this is done?
- What's the core transformation? (inputs → outputs)
- Any technology preferences or constraints?
- What's explicitly out of scope?

*If it's becoming a business/consulting project:*
- What's the desired outcome? What does success look like?
- Who are the stakeholders? What are the constraints (timeline, budget, dependencies)?
- What deliverables are expected?
- What's out of scope?

*If it's becoming a research/exploration project:*
- What questions are you trying to answer?
- What would a useful output look like? (report, analysis, dataset, prototype?)
- How deep should this go? What's the boundary?
- What do you already know vs. what needs investigation?

*If you're not sure yet:*
- Ask directly: "This could go several directions — are you thinking of this as a coding project, a research effort, a business initiative, or something else?"

**Round 3 — Constraints and Context:**
- Scale, timeline, dependencies
- Any resources or references to incorporate
- Language preferences for the output (check workspace conventions)

Adapt questions based on answers — skip what's already clear, dig deeper where it's vague. Don't front-load questions that aren't relevant yet.

## Phase 3 — Determine Spec Location

Based on what you've learned, decide where the spec goes:

- **Code repo with no existing specs:** create `specs/<project-name>.md` at the repo root
- **Code repo with existing specs:** add to existing `specs/` directory
- **Organized workspace:** place specs where the project lives (e.g., `clients/acme/billing-project/specs/spec.md`)
- **Empty directory:** create `specs/<project-name>.md` — this directory IS the project

If uncertain, ask the user: "Where should I save the spec? Here's what I'm thinking: [path]. Does that work?"

## Phase 4 — Draft the Specification

Write a first draft. The structure adapts to the project type, but always includes these core elements:

### Universal Sections (all project types)

1. **Problem / Opportunity** — Why this exists. What's painful or missing.
2. **What This Is** — One-paragraph description.
3. **What This Is NOT** — Explicit boundaries (prevents scope creep).
4. **Success Criteria** — Numbered list of concrete, verifiable conditions that define "done."
5. **Open Questions** — Unresolved decisions.

### Project Context (always include)

Add a context block at the top of the spec so downstream skills understand the project:

```markdown
## Project Context

- **Type**: code | business | research | consulting | hybrid
- **Language**: en | pt-BR | (whatever the workspace convention is)
- **Location**: where this spec lives relative to the workspace root
- **Workspace**: brief description of the workspace (e.g., "monorepo with multiple projects", "Rust CLI project", "empty directory")
- **Stakeholders**: who's involved (if applicable)
```

### Additional Sections by Project Type

*Code / Product projects — add:*
- **Data Model** — Core entities, properties, relationships (use tables)
- **Pipeline / Process** — Processing phases with input → process → output
- **File Formats** — Example artifacts the system produces
- **Core Constraints** — Non-negotiable technical rules

*Business / Consulting projects — add:*
- **Stakeholders** — Who's involved, their roles and interests
- **Deliverables** — What gets produced, in what format
- **Timeline / Milestones** — Key dates and dependencies
- **Risks** — What could go wrong, mitigation strategies

*Research / Exploration projects — add:*
- **Research Questions** — What we're trying to answer
- **Methodology** — How we'll investigate (sources, tools, approach)
- **Expected Outputs** — What the research produces (report, dataset, recommendations)
- **Scope Boundaries** — How deep, how broad, what's excluded

*Hybrid projects — mix sections as needed.*

### Writing Principles

- **Concrete over abstract.** Show examples — example deliverables, example outputs, example scenarios. Don't just describe; demonstrate.
- **Explicit over implicit.** If something is out of scope, say so. If a term has a specific meaning, define it.
- **Why over what.** Every design choice should explain its rationale.
- **Tables for structured data.** Entities, comparisons, stakeholder maps — use tables, not prose.

## Phase 5 — Refine Through Conversation

Present the draft to the user. Use AskUserQuestion to refine:

- "Does this capture the right scope?"
- "Are these success criteria specific enough?"
- "What's missing?"
- "Are these the right boundaries?"

Iterate until the user is satisfied. Expect 2-4 refinement rounds.

## Phase 6 — Write the Spec File

Write the final document to the determined location.

Present a summary to the user:
- What kind of project this is
- Where the spec was saved
- Core scope and success criteria
- Open questions that need resolution during architecture/planning
- Suggested next step: "Run `/architect` to define the implementation approach, or `/plan` to design the delivery milestones."
