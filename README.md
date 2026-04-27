# Shelf

<p align="center">
  <img src="src/shelf/ui/assets/shelf_icon.svg" alt="Shelf app logo" width="104" />
</p>

<p align="center">
  <strong>Offline-first document search for macOS.</strong><br />
  Find local documents by filename, path, extracted text, and semantic matches without sending your files anywhere.
</p>

<p align="center">
  <a href="#demo">Demo</a> ·
  <a href="#features">Features</a> ·
  <a href="#getting-started">Getting Started</a> ·
  <a href="#how-it-works">How It Works</a> ·
  <a href="#justfile">Justfile</a>
</p>

## Demo

![Shelf demo](docs/assets/shelf-demo.gif)

For the original video with playback controls, open the MP4 directly:
[docs/assets/shelf-demo.mp4](docs/assets/shelf-demo.mp4).

## What Is Shelf?

Shelf is a native-feeling macOS desktop app for the moment when you know a document exists, but cannot remember what it was called or where you saved it.

It monitors folders you control, extracts document content locally, stores metadata and full-text search state in SQLite, persists vectors in ChromaDB, and uses a local embedding model when available for semantic retrieval. The app is intentionally offline-first: there are no hosted APIs, cloud sync requirements, or remote document processing paths in the MVP.

## Features

- **Floating Spotlight-style launcher** for fast document lookup.
- **Customizable global shortcut** to bring Shelf forward. The default is `Cmd+Option+S`.
- **Content-based indexing** for local documents, not just filenames.
- **Supported formats:** `.pdf`, `.doc`, `.docx`, `.txt`, `.md`, and `.markdown`.
- **Fast exact search** using SQLite FTS5.
- **Local semantic layer** using ChromaDB vector persistence and `sentence-transformers/all-MiniLM-L6-v2` when the model is cached locally.
- **Offline fallback embedder** so indexing and search remain usable even when the sentence-transformer model is not available.
- **Background reconciliation and folder watching** for selected local folders.
- **Search result actions** to open files in Preview or reveal them in Finder.
- **Keyboard navigation** for results, including reveal-selected with `Cmd+R`.
- **Settings surface** for monitored folders, indexed document types, launcher shortcut, appearance, and local storage paths.
- **Document Monitor** for indexing health, queued jobs, worker state, coverage, and recent failures.
- **Maintenance tools** for status, audit, FTS rebuilds, full rebuilds, and targeted file/folder reindexing.
- **Local app data directory** under `~/Library/Application Support/Shelf/` by default.

## Screens And Surfaces

Shelf is split into a few focused surfaces:

- **Main search window:** a compact, always-ready search bar with live result cards.
- **Results popup:** ranked matches with file type badges, compact paths, Preview opening, and Finder reveal.
- **Settings:** folder management, file type selection, global shortcut customization, appearance, and local storage visibility.
- **Document Monitor:** indexing counters, queued job status, failure diagnostics, worker snapshot, and monitored folder coverage.
- **Maintenance:** GUI access to the same status, audit, rebuild, and reindex commands exposed by the CLI.

## Tech Stack

- Python 3.11+
- PySide6 for the macOS desktop UI
- SQLite + FTS5 for metadata, queueing, failures, metrics, and exact search
- ChromaDB for local vector persistence
- `sentence-transformers` for local embeddings when a cached model is available
- `watchdog` for folder watching
- `pypdf` for PDFs
- `python-docx` for `.docx`
- `antiword` for legacy `.doc`
- `uv` for dependency management
- PyInstaller for app bundle builds

## Getting Started

Install dependencies:

```bash
uv sync
```

Or use the Justfile:

```bash
just sync
```

Run the desktop app:

```bash
uv run shelf
```

Or:

```bash
just gui
```

Build a macOS app bundle:

```bash
just build-app
open dist/Shelf.app
```

Run tests:

```bash
uv run pytest
```

Or:

```bash
just test
```

## How It Works

1. Shelf loads monitored folders and enabled document types from local settings.
2. Startup reconciliation scans monitored folders and enqueues supported files.
3. A durable SQLite-backed job queue feeds the indexing worker.
4. Parsers extract normalized text and metadata from supported files.
5. Document metadata and raw text are stored in SQLite.
6. SQLite FTS5 is updated for fast filename, path, and content search.
7. Text is split into deterministic chunks and stored in SQLite.
8. Chunk embeddings are persisted in ChromaDB using a local model when available.
9. The search service can run exact FTS and vector retrieval in parallel and merge results by document.
10. The live UI path favors quick exact matches while the semantic layer remains available in the application search service.

## Local Model Behavior

Shelf tries to load `sentence-transformers/all-MiniLM-L6-v2` from the local model cache:

```text
~/Library/Application Support/Shelf/models/
```

The model is loaded with `local_files_only=True`, so Shelf does not download a model at search time. If the model is not already cached, Shelf falls back to a deterministic hashing embedder. That keeps the app usable offline, while making it clear that best semantic results require the local sentence-transformer model to be present.

## Supported Formats

| Format | Parser |
| --- | --- |
| `.pdf` | `pypdf` |
| `.docx` | `python-docx` |
| `.doc` | `antiword` |
| `.txt` | built-in text parser |
| `.md` | built-in text parser |
| `.markdown` | built-in text parser |

`.doc` support depends on `antiword` being installed or bundled.

## CLI

Run the GUI:

```bash
uv run shelf
uv run shelf run
```

Inspect local status:

```bash
uv run shelf status
```

Audit SQLite and Chroma consistency:

```bash
uv run shelf audit
```

Queue rebuild and reindex operations:

```bash
uv run shelf rebuild-all
uv run shelf rebuild-fts
uv run shelf reindex-path /absolute/path/to/file.pdf
uv run shelf reindex-folder /absolute/path/to/folder
```

Use a custom app-support directory during development or tests:

```bash
uv run shelf --app-support-dir /tmp/shelf-dev
```

## Justfile

The repository includes a `Justfile` for common workflows.

| Command | What it does |
| --- | --- |
| `just sync` | Install project dependencies with `uv sync` |
| `just gui` | Run the desktop app |
| `just run <args>` | Run the `shelf` CLI with custom arguments |
| `just test` | Run the test suite |
| `just status` | Print local index/job/failure status |
| `just audit` | Check SQLite and vector-store consistency |
| `just rebuild-all` | Queue all monitored files for reconciliation/indexing |
| `just rebuild-fts` | Rebuild the SQLite FTS index from stored document text |
| `just reindex-path <path>` | Queue one file path for reindexing or deletion reconciliation |
| `just reindex-folder <path>` | Queue supported files under a folder for reindexing |
| `just build-icon` | Regenerate the `.icns` app icon from the SVG |
| `just build-app` | Build `dist/Shelf.app` with PyInstaller |
| `just open-app` | Build and open the app bundle |
| `just clean` | Remove build output and local test caches |

## Local Data

By default, Shelf stores local state under:

```text
~/Library/Application Support/Shelf/
```

This includes:

- `config/` for settings
- `db/` for SQLite
- `vectors/` for ChromaDB persistence
- `models/` for the local model cache
- `logs/` for JSON logs
- `cache/` for runtime scratch data

## Project Layout

```text
src/shelf/
  bootstrap.py          CLI and app entry point
  core/                 app services, settings, maintenance, lifecycle
  storage/              SQLite bootstrap and repositories
  indexing/             watcher, reconciliation, worker, chunking, embeddings
  parsers/              PDF, DOCX, DOC, text, and Markdown parsing
  search/               exact/vector search orchestration
  ui/                   PySide6 onboarding, launcher, settings, and search UI
tests/                  automated coverage for core flows
docs/                   product, engineering, operations, assets, and packaging notes
tasks/                  backlog and progress tracker
plans/                  implementation records for completed change sets
Justfile                common development commands
Shelf.spec              PyInstaller app bundle spec
```

## Validation

Current repository validation includes:

- automated tests with `uv run pytest`
- maintenance CLI smoke checks
- app-level Qt smoke verification of indexing and search
- packaging notes for the PyInstaller app bundle

See [docs/operations.md](docs/operations.md) and [docs/packaging_validation.md](docs/packaging_validation.md) for more detail.

## Current Notes

- Shelf is an MVP and still intentionally local-first.
- The live search UI uses fast exact matching for quick result updates.
- The application search service includes a hybrid path that combines SQLite FTS and Chroma vector retrieval.
- The sentence-transformer model is only used when available locally.
- The watcher uses a polling observer for reliability across local and headless validation environments.

## Planning References

- [docs/product_plan.md](docs/product_plan.md)
- [docs/engineering_plan.md](docs/engineering_plan.md)
- [tasks/progress.md](tasks/progress.md)
