# Shelf Operations

## Local Commands

Run the app:

```bash
uv run shelf
```

Print current local metrics:

```bash
uv run shelf status
```

Audit SQLite and Chroma consistency:

```bash
uv run shelf audit
```

Queue a rebuild across monitored folders:

```bash
uv run shelf rebuild-all
```

Requeue one file or one folder:

```bash
uv run shelf reindex-path /absolute/path/to/file.pdf
uv run shelf reindex-folder /absolute/path/to/folder
```

Rebuild only the exact-search FTS index:

```bash
uv run shelf rebuild-fts
```

## Operational Notes

- Shelf stores all data locally under `~/Library/Application Support/Shelf` unless `--app-support-dir` is supplied.
- `antiword` is still required on the host for reliable `.doc` extraction; when it is missing, Shelf records a recoverable parser failure instead of crashing.
- Sentence-transformer embeddings are attempted first. If the model cannot be loaded locally, Shelf falls back to a deterministic hashing embedder so exact search and local indexing continue to work.
