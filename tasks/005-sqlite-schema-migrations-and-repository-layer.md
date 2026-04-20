# Task 005: SQLite Schema, Migrations, and Repository Layer

- Status: `Done`
- Priority: `P0`
- Depends On: `002`
- Last Updated: `2026-04-19`

## Objective

Create the durable SQLite system of record for Shelf, including schema creation, migration handling, and repository abstractions for core persisted entities.

## Why This Matters

The engineering plan makes SQLite the durable source of truth for monitored folders, documents, jobs, failures, and scanner state. Everything trustworthy in indexing depends on safe local persistence.

## Scope

- Define initial schema and migration strategy.
- Implement data access for folders, documents, jobs, failures, and scanner state.
- Add schema version tracking and safe database initialization.
- Prepare the database for future FTS and chunk storage work.

## Out of Scope

- Full FTS search behavior.
- Chroma/vector persistence.
- UI integration beyond what is required for basic app startup.

## Implementation Checklist

- Create schema definitions for `folders`, `documents`, `document_chunks`, `jobs`, `scanner_state`, and `failures`.
- Define indexes and constraints that support path uniqueness, lifecycle state, and efficient job polling.
- Add database bootstrap and migration execution at startup.
- Implement repository methods with clear transaction boundaries.
- Add tests that cover database creation, migration from earlier versions, and basic CRUD flows.

## Acceptance Criteria

- Shelf can initialize a fresh SQLite database safely.
- Schema versioning is explicit and migration-ready.
- Core repository operations are isolated from UI code and usable by indexing workers later.

## Validation

- Run repository tests against a temporary SQLite database.
- Verify migration behavior from at least one prior schema version fixture if possible.
- Confirm failures in DB initialization are observable and non-silent.

## Risks and Notes

- Avoid leaking raw SQL everywhere; centralize schema ownership.
- Design for tombstones and lifecycle state instead of assuming hard deletes are always safe.
