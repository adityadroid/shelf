# Task 018: Performance Tuning, Throttling, and Packaging Validation

- Status: `Not Started`
- Priority: `P1`
- Depends On: `016`, `017`
- Last Updated: `2026-04-19`

## Objective

Harden Shelf for real-world macOS use by tuning responsiveness, controlling background resource usage, and validating packaging/distribution assumptions.

## Why This Matters

The MVP must feel fast, quiet, and trustworthy on a laptop. The engineering plan calls out battery-aware throttling, bounded background work, and packaging as the final steps before treating the app as production-ready.

## Scope

- Profile search latency, indexing throughput, and UI responsiveness.
- Add sensible worker concurrency and throttling policies for battery and active search use.
- Validate packaging strategy and runtime dependency assumptions for macOS.
- Close key performance and operability gaps discovered during end-to-end testing.

## Out of Scope

- New product features.
- Cloud telemetry or hosted deployment.
- Aggressive micro-optimization before baseline measurements exist.

## Implementation Checklist

- Measure search latency and indexing throughput on representative local datasets.
- Tune parser and embedding concurrency to preserve UI responsiveness.
- Reduce background throughput when on battery or while the user is actively typing.
- Validate app startup, resource paths, parser dependencies, and vector storage under the chosen packaging approach.
- Document remaining bottlenecks and any pre-release operational caveats.

## Acceptance Criteria

- Search feels immediate on representative personal-library workloads.
- Background indexing remains bounded and does not noticeably degrade normal laptop use.
- Packaging decisions are validated enough that the team understands remaining release blockers.

## Validation

- Run manual end-to-end checks on a realistic local corpus.
- Capture benchmark notes for search latency, indexing throughput, and system impact.
- Verify packaged or near-packaged builds can still find local dependencies and writable data directories.

## Risks and Notes

- Tune based on evidence, not intuition.
- If packaging reveals binary/runtime issues such as `antiword` distribution concerns, document them explicitly before release planning.
