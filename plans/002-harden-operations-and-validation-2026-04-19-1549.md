# Harden Operations and Validation (Plan 002, 2026-04-19 15:49)

## Summary

Completed the MVP hardening slice by adding operational repair/audit commands, repository hygiene cleanup, packaging and performance notes, and final validation that the app can index and search through the real Qt window flow.

## Context

After the core app workflow was in place, the remaining backlog focused on trust and operability: local observability, rebuild paths, consistency audits, performance guardrails, and explicit packaging caveats for the desktop runtime.

## Changes Made

- Added `.gitignore` and removed accidentally committed `__pycache__` artifacts.
- Added `MaintenanceService` plus CLI subcommands for `status`, `audit`, `rebuild-all`, `rebuild-fts`, `reindex-path`, and `reindex-folder`.
- Added operations and packaging/performance documentation in `docs/operations.md` and `docs/packaging_validation.md`.
- Fixed threaded SQLite usage by moving worker, watcher, search, and status paths to fresh per-operation connections.
- Switched the watcher backend to a polling observer for more reliable local/offscreen operation and made embedding model loading local-cache-only with immediate fallback.
- Fixed the startup queue commit boundary so background workers can see reconciliation jobs.
- Updated `/tasks/progress.md` and tasks `017` and `018` to `Done`.

## Decisions and Tradeoffs

- Favored polling-based file watching over the macOS FSEvents backend in this environment because it proved more reliable and still satisfies the plan’s reliability-first guidance.
- Kept semantic retrieval operational offline by failing fast to a hashing embedder instead of stalling on remote model fetches.
- Prioritized correctness and observability over maximum throughput by using one worker thread with independent SQLite connections.

## Validation

- Ran `uv run pytest` with 15 passing tests.
- Ran `uv run shelf --app-support-dir /tmp/shelf-status-check status` and verified the maintenance CLI output.
- Ran an offscreen Qt smoke scenario that launched the real main window, background-indexed a DOCX file, and returned one result for a search query.
- Collected a small local benchmark: about `2952 ms` to index three DOCX files and about `3 ms` for a subsequent search.

## Risks and Follow-ups

- `.doc` support still depends on `antiword` being available or bundled.
- The semantic layer currently falls back to hashing when the MiniLM model is not cached locally, which preserves function but reduces retrieval quality.
- PySide6 packaging, plugin paths, and binary bundling still need real packaged-build validation before release, even though the development/runtime assumptions are now documented.
