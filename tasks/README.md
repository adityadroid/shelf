# Shelf Task Backlog

This folder turns the product and engineering plans into an execution-ready backlog for the Shelf MVP.

## How To Use This Backlog

- Start from [progress.md](/Users/adityadroid/VSCodeProjects/ai/shelf/tasks/progress.md) to understand ordering, dependencies, and overall status.
- Use one task file at a time as the implementation brief for that slice of work.
- Update the tracker and the matching task file when a task starts, is blocked, or completes.
- Treat updating [progress.md](/Users/adityadroid/VSCodeProjects/ai/shelf/tasks/progress.md) after task completion as required workflow, not optional cleanup.
- Prefer finishing tasks in sequence unless dependencies explicitly allow parallel work.

## Status Conventions

- `Not Started`: no implementation work has begun.
- `In Progress`: active engineering work is underway.
- `Blocked`: cannot continue until a dependency or decision is resolved.
- `Done`: code, validation, and any follow-up notes for the task are complete.

## Task Document Structure

Each task file includes:

- objective and why it matters,
- scope and non-goals,
- dependencies,
- implementation checklist,
- acceptance criteria,
- validation guidance,
- notes on risks and handoff.

## Planning Principles Used

- Tasks are sequenced to match the recommended MVP implementation order in `docs/engineering_plan.md`.
- Product trust, offline-first guarantees, and deterministic local behavior take priority over feature breadth.
- High-risk lifecycle areas such as indexing, deletion handling, queue durability, and store consistency are isolated into explicit tasks.
