# Task 007: File Watcher and Event Normalization

- Status: `Done`
- Priority: `P0`
- Depends On: `004`, `005`
- Last Updated: `2026-04-19`

## Objective

Implement the `watchdog`-based file watcher subsystem and normalize raw file events into durable indexing intents.

## Why This Matters

Real-time freshness is a core trust requirement. The watcher is the live input to the indexing system, but the engineering plan is clear that raw file events must be normalized before any heavy processing occurs.

## Scope

- Start and stop recursive watchers for monitored folders.
- Normalize create, modify, move, rename, and delete events.
- Filter unsupported file types early.
- Debounce noisy bursts and coalesce duplicate events before queue insertion.

## Out of Scope

- Job execution and retry behavior.
- Baseline reconciliation scanning.
- Parsing or extraction logic.

## Implementation Checklist

- Wrap `watchdog.Observer` lifecycle in an isolated infrastructure service.
- Normalize paths, detect supported extensions, and map raw events to `UPSERT`, `DELETE`, or `MOVE`.
- Add a short debounce/coalescing strategy keyed by path plus metadata hints.
- Ensure folder add/remove operations update active watcher subscriptions safely.
- Write normalized jobs into SQLite instead of invoking parsing directly.

## Acceptance Criteria

- Supported file events under monitored roots become normalized durable jobs.
- Unsupported files and duplicate bursts do not create noisy work.
- Watchers can be started and stopped without leaking background threads.

## Validation

- Add tests or controlled integration checks for create, modify, move, and delete scenarios.
- Verify duplicate save storms collapse into a smaller number of durable jobs.
- Verify watcher updates when the monitored folder list changes.

## Risks and Notes

- File system events are noisy and platform-specific; keep normalization logic observable.
- Do not assume event order is reliable across applications or save patterns.
