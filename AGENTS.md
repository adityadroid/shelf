# AGENTS.md

## Purpose

This file defines how autonomous coding agents should work in the Shelf repository.

Shelf is a native macOS document search app with a Python core. The current source of truth for project intent is:

- `docs/product_plan.md`
- `docs/engineering_plan.md`

Agents must read those documents before making meaningful changes. When the codebase grows, agents should continue to use them as the baseline for product scope, architecture, and quality decisions.

## Product Context

Shelf exists to help users quickly find local documents on macOS. The MVP is intentionally focused:

- 100% local and offline by default
- Native macOS experience
- Python-first implementation
- Support for `.pdf`, `.doc`, and `.docx`
- User-controlled monitored folders
- Fast, trustworthy search over filename and extracted text
- Reliable background indexing and reconciliation

Agents should optimize for trust, speed, privacy, and maintainability over feature sprawl.

## Engineering Direction

The engineering plan currently points toward:

- Python 3.11+
- PySide6 for the desktop UI
- `watchdog` for file monitoring
- SQLite + FTS5 for metadata, queueing, and exact search
- ChromaDB for local vector storage
- `sentence-transformers` for local embeddings
- `pypdf`, `python-docx`, and `antiword` for parsing

The architecture is intentionally modular. Agents should preserve clear separation between:

- UI
- folder configuration and permissions
- file watching and event ingestion
- parsing and normalization
- chunking and embedding
- metadata storage and FTS
- vector retrieval
- query orchestration and ranking

Do not introduce hosted APIs, cloud dependencies, mandatory subscriptions, or architecture that weakens offline-first guarantees unless the user explicitly requests a change in direction.

## Working Principles

Agents should:

- Read relevant code and planning docs before editing
- Prefer the smallest change that solves the real problem cleanly
- Preserve separation of concerns and extensibility
- Keep indexing and search behavior observable and testable
- Favor deterministic behavior, clear failure handling, and safe local persistence
- Protect UX responsiveness during background work
- Keep privacy guarantees intact

Agents should not:

- Add speculative MVP features that are currently out of scope
- Couple unrelated subsystems together for convenience
- Bypass durable state where reliability depends on persistence
- Replace local processing with remote services
- Commit code that lacks appropriate validation for the level of risk

## Quality Standards

Every meaningful change should be evaluated against these standards:

- Correctness: behavior matches product and engineering intent
- Reliability: crashes, duplicate events, stale index entries, and partial failures are handled gracefully
- Performance: search remains fast and background work stays bounded
- Maintainability: modules have single responsibilities and clear interfaces
- Testability: logic can be validated with automated tests where practical
- Observability: failures and important state transitions are inspectable
- Privacy: document content and metadata stay local unless explicitly designed otherwise

## Implementation Guidance

### Architecture

- Keep parser implementations behind stable interfaces
- Keep scanning, indexing, storage, and retrieval loosely coupled
- Prefer explicit schemas and durable local storage over implicit in-memory state
- Design for incremental reprocessing instead of full rebuilds where possible
- Make schema or pipeline versioning explicit when changing chunking, embeddings, or storage behavior

### UX and Product

- Default to simple, transparent flows
- Keep folder coverage and indexing state understandable
- Favor predictable search behavior over opaque ranking tricks
- Preserve support for partial indexing progress and clear empty/error states

### Safety

- Treat deletes, moves, reindexing, and queue reconciliation as high-risk areas
- Avoid one-off scripts or migrations without documenting assumptions and rollback considerations
- If a change impacts persistence, indexing semantics, or user trust, add or update tests

## Testing Expectations

Agents should run the most relevant validation they can before finishing. Examples:

- unit tests for pure logic
- parser tests for supported document types
- storage or integration tests for queue/index behavior
- UI checks for user-visible workflows when applicable
- linting or formatting if the repo adopts those tools

If a test cannot be run, the agent must say so plainly in its final summary and in the plan record.

## Task Backlog Maintenance

When work maps to the execution backlog in `/tasks`, agents must keep the backlog current.

Required behavior:

- When a task starts, update `/tasks/progress.md` and the corresponding task file to show `In Progress`.
- When a task is blocked, update `/tasks/progress.md` and the corresponding task file to show `Blocked`, with a short blocker note when useful.
- When a task is finished, agents must update the progress board in `/tasks/progress.md` and mark the corresponding task file as `Done`.
- If a completed change affects sequencing, dependencies, or newly discovered follow-up work, update the backlog documents before committing.

Do not treat the progress board as optional documentation. It is part of the repository workflow.

## Planning Record Requirement

Every agent must leave a task record in `/plans` for any finalized change set that is about to be committed.

This record is required.

### Timing

Create the plan record only after the task has been finalized and validated, and immediately before the commit is created.

Do not create the record at task start.
Do not create it for abandoned work-in-progress unless the user explicitly asks for a handoff note.

### Folder

- `/plans`

If the folder does not exist, create it.

### File Naming

Use this filename format:

`NNN-short-kebab-task-name-YYYY-MM-DD-HHMM.md`

Rules:

- `NNN` is a zero-padded sequential index, starting from `001`
- the task segment is short, descriptive, and kebab-case
- timestamp should use local repository working time when available
- prefer 24-hour time

Example:

`001-add-agents-guidance-2026-04-19-0915.md`

### Document Title

The first heading must include the task, the index, and the timestamp.

Use this format:

`# <Task Title> (Plan NNN, YYYY-MM-DD HH:MM)`

Example:

`# Add AGENTS.md Guidance (Plan 001, 2026-04-19 09:15)`

### Required Sections

Each plan file should be concise but complete. Use this structure:

1. `## Summary`
2. `## Context`
3. `## Changes Made`
4. `## Decisions and Tradeoffs`
5. `## Validation`
6. `## Risks and Follow-ups`

### Section Guidance

`## Summary`

- One short paragraph describing the final outcome

`## Context`

- Why the task was done
- Relevant product or engineering constraints

`## Changes Made`

- Key files created or updated
- Short description of what changed in each area

`## Decisions and Tradeoffs`

- Important implementation choices
- Alternatives intentionally avoided

`## Validation`

- Tests run
- Manual checks performed
- Anything not verified

`## Risks and Follow-ups`

- Remaining limitations
- Known risks
- Logical next steps, if any

### Best Practices for Plan Records

- Write for the next engineer or agent who needs context quickly
- Prefer facts over narrative
- Record why a decision was made, not just what changed
- Keep it short enough to scan in under two minutes
- Reference files and commands when useful
- Do not paste large diffs or logs
- Be honest about skipped validation or unresolved risk

## Commit Readiness Checklist

Before committing, agents should verify:

- the change matches `docs/product_plan.md`
- the change aligns with `docs/engineering_plan.md`
- relevant tests or checks were run, or the gap is documented
- user-visible behavior is coherent
- persistence and indexing changes are safe
- `/tasks/progress.md` and the relevant task file reflect the completed task state
- a `/plans` record has been created for the finalized task

## When Instructions Conflict

Use this precedence order:

1. Direct user request
2. This `AGENTS.md`
3. `docs/product_plan.md`
4. `docs/engineering_plan.md`
5. Local implementation patterns already present in the codebase

If plans and implementation disagree, prefer the user request, then update code in the direction that best preserves product trust, offline-first behavior, and maintainability.
