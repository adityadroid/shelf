# Task 009: Baseline Scan and Startup Reconciliation

- Status: `Not Started`
- Priority: `P0`
- Depends On: `004`, `005`, `008`
- Last Updated: `2026-04-19`

## Objective

Implement the initial folder scan and restart-time delta reconciliation so Shelf can populate and repair the index even when watcher events were missed.

## Why This Matters

The plans explicitly state that watchers alone are insufficient. Users need accurate results after first launch, after downtime, and after changes made while the app was not running.

## Scope

- Run the first baseline scan of monitored folders.
- Compare current disk state to stored metadata on startup.
- Enqueue deltas rather than forcing unnecessary full reprocessing.
- Track scan checkpoints, last scan time, and reconciliation outcomes.

## Out of Scope

- Full parser implementation.
- Search UI polish.
- Deep repair tooling beyond reconciliation.

## Implementation Checklist

- Implement recursive supported-file discovery for monitored folders.
- Compare discovered files against indexed metadata using fingerprints and lifecycle state.
- Enqueue `UPSERT`, `MOVE`, or `DELETE` work as appropriate.
- Persist scan progress and completion markers in `scanner_state`.
- Support partial availability so results can appear before a full scan completes.

## Acceptance Criteria

- First launch can populate the queue from monitored folders without manual user action.
- Restart reconciliation catches files added, changed, or removed while the app was closed.
- The system avoids unnecessary reparsing when fingerprints show no change.

## Validation

- Test first-run baseline behavior on a sample directory tree.
- Test restart reconciliation after offline adds, edits, moves, and deletes.
- Verify scan state persists across restarts and partial completion.

## Risks and Notes

- Large libraries should enqueue work incrementally to preserve responsiveness.
- Be careful with path canonicalization so moved files are not duplicated as brand-new documents unless necessary.
