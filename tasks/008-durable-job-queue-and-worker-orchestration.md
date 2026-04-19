# Task 008: Durable Job Queue and Worker Orchestration

- Status: `Done`
- Priority: `P0`
- Depends On: `005`, `007`
- Last Updated: `2026-04-19`

## Objective

Build the persistent job queue, worker claiming logic, retry policies, and bounded background execution model for indexing work.

## Why This Matters

Queue durability is the reliability backbone of the ingestion system. Without it, crashes, duplicate events, and slow parsing would cause stale search results and lost indexing work.

## Scope

- Implement durable job insertion, claiming, status updates, retries, and backoff.
- Add bounded worker orchestration that keeps background work off the UI thread.
- Support idempotent upsert/delete processing semantics.
- Expose queue depth and worker state for later status surfaces.

## Out of Scope

- Parsing specifics.
- Reconciliation scanning.
- Performance tuning beyond safe initial limits.

## Implementation Checklist

- Define job statuses and legal transitions.
- Implement safe claim-and-lock behavior so workers do not double-process the same job.
- Add exponential backoff and max-attempt handling for transient failures.
- Collapse redundant pending jobs for the same path where safe.
- Expose queue inspection helpers for status reporting and debugging.

## Acceptance Criteria

- Jobs survive app restart and resume safely.
- Worker execution is bounded and does not run on the UI thread.
- Failed jobs retry with controlled backoff instead of looping aggressively.

## Validation

- Add tests for job claiming, retries, duplicate suppression, and restart recovery.
- Verify a simulated crash does not lose pending work.
- Verify queue metrics reflect reality during processing.

## Risks and Notes

- Idempotency matters more than raw throughput.
- Keep claim logic transactionally safe; race conditions here will poison trust quickly.
