# Packaging and Performance Validation

## Packaging Assumptions

- Runtime manager: `uv` for development and dependency resolution.
- App framework: PySide6 desktop application launched via `uv run shelf`.
- Local persistence roots: config, database, vectors, models, logs, and cache directories under the Shelf app-support root.
- External binary dependency: `antiword` remains the main packaging caveat for `.doc` parsing and should be bundled or documented explicitly before release packaging.

## Performance and Throttling Notes

- Background indexing worker concurrency is conservatively capped to `min(2, cpu_count)` and defaults to at least one worker to protect UI responsiveness.
- Search input is debounced in the UI before firing queries.
- Reconciliation enqueues deltas instead of forcing a full rebuild on every launch.
- Exact FTS search remains available even if vector model loading is slow or unavailable.

## Local Validation Snapshot

- Local benchmark on April 19, 2026 over three small DOCX files: `~2952 ms` to index the corpus with fallback hashing embeddings and `~3 ms` for a subsequent hybrid search query.
- Offscreen Qt smoke run verified the app could launch, background-index one DOCX file from a monitored folder, and surface one search result in the real main window UI.

## Validation Checklist

- Confirm the packaged build can write to the Shelf app-support directory.
- Confirm PySide6 plugins load correctly from the packaged environment.
- Confirm Chroma persistence resolves under the app-support vector directory.
- Confirm `antiword` packaging or installation guidance is present before a production release.
