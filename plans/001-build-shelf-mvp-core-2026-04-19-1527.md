# Build Shelf MVP Core (Plan 001, 2026-04-19 15:27)

## Summary

Built the first end-to-end Shelf MVP slice: a launchable PySide6 desktop app with onboarding, monitored-folder management, durable local settings and SQLite storage, background indexing, supported document parsing, chunking, local vector persistence, and hybrid search surfaced in the main window.

## Context

The repository started as a planning-only backlog, so the first implementation milestone had to establish the actual application structure while staying aligned with the product and engineering plans: offline-first behavior, macOS-native UI, local persistence, supported PDF/DOC/DOCX formats, and modular indexing/search boundaries.

## Changes Made

- Added `uv` project configuration, packaging metadata, and a runnable `shelf` entry point in `pyproject.toml`.
- Created the application package under `src/shelf` with bootstrap, service wiring, path management, logging, settings persistence, onboarding, and the main window shell.
- Implemented SQLite schema/bootstrap plus repositories for folders, documents, jobs, scanner state, failures, metrics, and FTS-backed exact search.
- Added watcher normalization, durable queue handling, reconciliation scanning, parser registry and parsers, deterministic chunking, embedding persistence, worker orchestration, and hybrid search composition.
- Added automated tests covering settings, folder rules, database behavior, parsers, chunking, search, and worker indexing flow.
- Updated `/tasks/progress.md` and tasks `001` through `016` to `Done`.

## Decisions and Tradeoffs

- Used a simple service container and direct module boundaries instead of a heavier dependency-injection framework to keep MVP startup understandable.
- Implemented semantic retrieval with Chroma plus a deterministic hashing fallback embedder so the app remains usable when the sentence-transformer model is unavailable locally.
- Kept queue workers conservatively bounded and reconciliation delta-based to preserve responsiveness over maximum throughput.
- Used write-through FTS synchronization during document upsert/delete to keep search state explicit and debuggable.

## Validation

- Ran `uv sync`.
- Ran `uv run pytest` with 14 passing tests.
- Ran dependency-free sanity checks during development with `python3 -m compileall src tests`.
- Full manual GUI verification is deferred to the next hardening slice after adding operational tooling and a scripted app-level smoke run.

## Risks and Follow-ups

- `.doc` extraction still depends on `antiword` being present on the host system; packaging and distribution caveats need to be documented.
- Semantic quality depends on whether the sentence-transformer model is cached locally; the fallback keeps the app functional but is lower quality.
- Observability, repair tooling, and packaging/performance validation remain to be completed in tasks `017` and `018`.
