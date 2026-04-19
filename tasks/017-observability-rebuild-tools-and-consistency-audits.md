# Task 017: Observability, Rebuild Tools, and Consistency Audits

- Status: `Done`
- Priority: `P1`
- Depends On: `005`, `008`, `014`, `015`
- Last Updated: `2026-04-19`

## Objective

Add the diagnostics and recovery tooling needed to keep Shelf’s local index trustworthy over time.

## Why This Matters

Indexing failures, stale vectors, and missed events are high-risk trust problems in a desktop search app. The plans explicitly call for logs, local metrics, failures tracking, and rebuild paths.

## Scope

- Add structured local logging and useful operational metrics.
- Persist failures for parser, embedding, and queue diagnostics.
- Implement rebuild and repair utilities for documents, folders, FTS, and vectors.
- Add consistency checks between SQLite metadata and Chroma chunk state.

## Out of Scope

- Remote telemetry.
- Complex admin dashboards.
- Automated self-healing beyond explicit local repair paths.

## Implementation Checklist

- Define structured log events for queue lifecycle, parsing outcomes, indexing failures, and search execution.
- Expose failure records and scan/job health in local storage.
- Add commands or internal actions for reindexing one document, one folder, FTS only, vectors only, or the whole index.
- Implement a consistency audit comparing SQLite chunk/document expectations against Chroma state.
- Document when audits or rebuilds should be used.

## Acceptance Criteria

- Engineers and future support/debug flows can inspect local failures and important state transitions.
- Shelf can recover from common local corruption or schema drift scenarios without manual database surgery.
- SQLite and Chroma alignment can be audited explicitly.

## Validation

- Run targeted checks for rebuild flows and audit mismatches.
- Verify logs and metrics are written locally only.
- Confirm failure records are created for controlled parser or embedding errors.

## Risks and Notes

- Keep observability practical; noisy logs can be as harmful as missing logs.
- Recovery tooling must respect the app’s source-of-truth model so repairs do not introduce new drift.
