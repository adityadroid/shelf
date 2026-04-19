# Shelf MVP Task Progress Tracker

This tracker is the execution map for the Shelf MVP backlog derived from [docs/product_plan.md](/Users/adityadroid/VSCodeProjects/ai/shelf/docs/product_plan.md) and [docs/engineering_plan.md](/Users/adityadroid/VSCodeProjects/ai/shelf/docs/engineering_plan.md).

## Progress Summary

- Total tasks: 18
- Not Started: 2
- In Progress: 0
- Done: 16
- Blocked: 0

## Milestones

1. Foundation: app shell, settings, permissions, monitored folder management.
2. Local retrieval core: SQLite schema, FTS search, watcher, queue, reconciliation, parsing.
3. Semantic layer: chunking, embeddings, Chroma integration, hybrid ranking.
4. Product hardening: UX polish, observability, rebuild paths, performance tuning, packaging validation.

## Status Legend

- `NS` = Not Started
- `IP` = In Progress
- `BL` = Blocked
- `DN` = Done

## Task Board

| ID | Task | Phase | Depends On | Status | Primary Deliverable |
| --- | --- | --- | --- | --- | --- |
| 001 | App skeleton and lifecycle bootstrapping | Foundation | None | DN | Launchable PySide6 app shell with clear app/core boundaries |
| 002 | Local app directories and settings persistence | Foundation | 001 | DN | Stable local storage paths and settings service |
| 003 | Default folders, permissions, and onboarding flow | Foundation | 001, 002 | DN | First-run flow for default monitored folders and permission guidance |
| 004 | Monitored folder management UI and domain rules | Foundation | 002, 003 | DN | Add/remove folder UX with duplicate and access validation |
| 005 | SQLite schema, migrations, and repository layer | Retrieval Core | 002 | DN | Durable metadata schema for folders, documents, jobs, state, and failures |
| 006 | Exact search index with SQLite FTS5 | Retrieval Core | 005 | DN | Filename and content search with ranked FTS queries |
| 007 | File watcher and event normalization | Retrieval Core | 004, 005 | DN | `watchdog` ingestion path that emits normalized jobs |
| 008 | Durable job queue and worker orchestration | Retrieval Core | 005, 007 | DN | Persistent job claiming, retries, backoff, and worker execution model |
| 009 | Baseline scan and startup reconciliation | Retrieval Core | 004, 005, 008 | DN | Delta-based scan bootstrap and restart recovery |
| 010 | Parser framework and normalized document model | Retrieval Core | 005, 008 | DN | Stable parser interface and internal document representation |
| 011 | PDF and DOCX parsing pipeline | Retrieval Core | 010 | DN | Working `.pdf` and `.docx` extraction with parser diagnostics |
| 012 | Legacy DOC parsing and failure handling | Retrieval Core | 010, 011 | DN | Safe `antiword` integration with timeout and error capture |
| 013 | Fingerprinting and deterministic chunking | Semantic Layer | 010, 011, 012 | DN | Change detection and chunk records ready for embedding |
| 014 | Embedding worker and Chroma persistence | Semantic Layer | 008, 013 | DN | Local embedding pipeline with schema/version awareness |
| 015 | Hybrid query orchestration and ranking | Semantic Layer | 006, 014 | DN | Parallel FTS and vector retrieval merged into document results |
| 016 | Search UI, result actions, and indexing status UX | Product UX | 003, 004, 009, 015 | DN | User-facing search flow, snippets, actions, and status surfaces |
| 017 | Observability, rebuild tools, and consistency audits | Hardening | 005, 008, 014, 015 | NS | Logs, metrics, repair utilities, and store-consistency checks |
| 018 | Performance tuning, throttling, and packaging validation | Hardening | 016, 017 | NS | Production-readiness checks for responsiveness, battery, and distribution |

## Recommended Execution Order

1. Finish tasks `001` through `006` before introducing watcher-driven indexing.
2. Finish tasks `007` through `012` before attempting hybrid retrieval end-to-end.
3. Finish tasks `013` through `015` before optimizing search UX beyond exact-match behavior.
4. Finish tasks `016` through `018` to harden the MVP for trustworthy daily use.

## Parallel Work Opportunities

- `003` and `005` can overlap once the app shell and settings boundaries from `001` and `002` are stable.
- `011` and UX mock work for `016` can proceed in parallel if the parser interface from `010` is frozen.
- `017` can begin once the first end-to-end indexing path is functional, even before final packaging work in `018`.

## Update Checklist

When a task changes state, update:

- the `Status` column in this tracker,
- the `Last Updated` field inside the task file,
- any newly discovered blockers, risks, or dependency changes.

When a task is finished, updating this progress tracker is mandatory before the work is considered complete.
