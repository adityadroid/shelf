# Shelf

Shelf is an offline-first macOS document search app for local documents. It indexes supported files from user-controlled folders, stores all metadata and search state locally, and provides a native desktop UI for fast filename and content search.

The current UI is intentionally search-first: a Spotlight-inspired main window keeps the focus on retrieval, while monitored folders, maintenance controls, and failure diagnostics live in dedicated Settings and Document Monitor surfaces.

## MVP Scope

- Native macOS desktop app built with PySide6
- Fully local storage and search
- Supported formats: `.pdf`, `.doc`, `.docx`
- Default monitored folders: `~/Documents`, `~/Downloads`, `~/Desktop`
- Search-first macOS-style glass UI
- Spotlight-inspired search field with fast result updates
- Result actions for open, reveal in Finder, and copy path
- Dedicated Settings dialog for folder management and app configuration
- Dedicated Document Monitor for indexing health and recent failures
- GUI access to maintenance and reindex operations
- Exact search with SQLite FTS5
- Local semantic layer with Chroma persistence
- Background reconciliation, queueing, and file watching

## Tech Stack

- Python 3.11+
- `uv` for dependency management
- PySide6 for the desktop UI
- SQLite + FTS5 for metadata, jobs, failures, metrics, and exact search
- ChromaDB for vector persistence
- `sentence-transformers` for local embeddings when a cached model is available
- `watchdog` for folder watching
- `pypdf`, `python-docx`, and `antiword` for document parsing

## Project Layout

```text
src/shelf/
  bootstrap.py          CLI and app entry point
  core/                 app services, settings, maintenance, lifecycle
  storage/              SQLite bootstrap and repositories
  indexing/             watcher, queue worker, reconciliation, chunking, embeddings
  parsers/              PDF, DOCX, and DOC parser implementations
  search/               hybrid search orchestration
  ui/                   PySide6 onboarding and main window
tests/                  automated coverage for core flows
docs/                   product, engineering, operations, and packaging notes
tasks/                  backlog and progress tracker
plans/                  required implementation records for completed change sets
```

## Getting Started

Install dependencies:

```bash
uv sync
```

Run the desktop app:

```bash
uv run shelf
```

## UI Overview

Shelf is split into three user-facing areas:

- Main window: search-first surface for entering queries, reviewing ranked matches, and opening documents.
- Settings: monitored folder management, local path/config visibility, and GUI wrappers for maintenance commands.
- Document Monitor: indexing health, queue/failure visibility, and recent failure diagnostics.

The main window no longer mixes folder management and failed-document details into the search view. Those operational details live in Settings and Document Monitor so the default experience stays focused on finding files quickly.

Run the test suite:

```bash
uv run pytest
```

## CLI Commands

The same maintenance operations exposed below are also available in the GUI under Settings.

Run the GUI:

```bash
uv run shelf
uv run shelf run
```

Inspect local status:

```bash
uv run shelf status
```

Audit SQLite and vector consistency:

```bash
uv run shelf audit
```

Queue rebuild operations:

```bash
uv run shelf rebuild-all
uv run shelf rebuild-fts
uv run shelf reindex-path /absolute/path/to/file.docx
uv run shelf reindex-folder /absolute/path/to/folder
```

Use a custom app-support directory during development or tests:

```bash
uv run shelf --app-support-dir /tmp/shelf-dev
```

## How It Works

1. Shelf loads monitored folders from local settings.
2. A startup reconciliation scan discovers supported files and enqueues indexing jobs.
3. A durable SQLite-backed queue feeds background workers.
4. Parsers extract normalized text and metadata from supported documents.
5. Extracted text is written to SQLite metadata tables and the FTS index.
6. Deterministic chunks are generated and stored in SQLite.
7. Embeddings are persisted to Chroma when available locally.
8. Search runs exact FTS and vector retrieval in parallel and merges results by document.

## Search Experience

- Results update as the user types.
- Clicking a result opens the file in its default macOS application.
- Each result includes an overflow menu for Reveal in Finder and Copy Path.
- Indexing state stays visible without overwhelming the main search screen.

## Local Data

By default, Shelf stores local state under:

```text
~/Library/Application Support/Shelf/
```

This includes:

- `config/` for settings
- `db/` for SQLite
- `vectors/` for Chroma data
- `models/` for local model cache
- `logs/` for JSON logs
- `cache/` for runtime scratch data

## Current Operational Notes

- `.doc` parsing requires `antiword` to be installed on the machine or bundled later during packaging.
- If the sentence-transformer model is not already cached locally, Shelf falls back to a deterministic hashing embedder so indexing and search remain usable offline.
- The watcher uses a polling observer for reliability in local and headless validation environments.

## Validation

Current repository validation includes:

- automated tests with `uv run pytest`
- maintenance CLI smoke checks
- app-level Qt smoke verification of indexing and search

See [docs/operations.md](/Users/adityadroid/VSCodeProjects/ai/shelf/docs/operations.md) and [docs/packaging_validation.md](/Users/adityadroid/VSCodeProjects/ai/shelf/docs/packaging_validation.md) for more detail.

## Planning References

- [docs/product_plan.md](/Users/adityadroid/VSCodeProjects/ai/shelf/docs/product_plan.md)
- [docs/engineering_plan.md](/Users/adityadroid/VSCodeProjects/ai/shelf/docs/engineering_plan.md)
- [tasks/progress.md](/Users/adityadroid/VSCodeProjects/ai/shelf/tasks/progress.md)
