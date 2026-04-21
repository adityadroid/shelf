# Package macOS App Bundle (Plan 003, 2026-04-21 13:44)

## Summary

Added a repeatable macOS app-bundle build path for Shelf using PyInstaller, documented common project commands in a Justfile, and fixed packaging issues so the generated `Shelf.app` launches without the recent Chroma import errors.

## Context

Shelf needed to be launchable like a normal macOS application instead of only from Terminal. The solution had to preserve the local-first desktop architecture, keep packaging steps repeatable for development, and document known release caveats such as the external `antiword` dependency.

## Changes Made

- `Shelf.spec`: added PyInstaller app-bundle configuration, hidden imports for Chroma dynamic modules, package exclusions to avoid bundling large optional ML stacks, and the macOS app icon.
- `Justfile`: added common development, maintenance, icon-generation, and `build-app`/`open-app` recipes.
- `tools/build_icon.py`: added a small SVG-to-iconset helper used to generate the `.icns` file from the existing Shelf SVG.
- `src/shelf/ui/assets/shelf_icon.icns`: added the macOS application icon used by the bundled app.
- `pyproject.toml` and `uv.lock`: added PyInstaller as a development dependency.
- `README.md` and `docs/packaging_validation.md`: documented the new build flow and packaging validation notes.
- `tasks/018-performance-tuning-throttling-and-packaging-validation.md`: recorded the packaging completion notes and updated task metadata.

## Decisions and Tradeoffs

- Chose PyInstaller because it matched the existing PySide6 app entry point and provided the fastest route to a Finder-launchable `.app`.
- Excluded `sentence_transformers`, `transformers`, `torch`, `onnxruntime`, and related optional packages from the bundle to keep the app size manageable, accepting fallback hashing embeddings in the packaged build unless a full local model bundle is intentionally added later.
- Included `chromadb.telemetry.*` and `chromadb.api.*` hidden imports because Chroma uses dynamic imports that PyInstaller did not discover automatically.

## Validation

- Ran `just build-app`
- Verified `open dist/Shelf.app`
- Smoke-tested `dist/Shelf.app/Contents/MacOS/Shelf` to ensure startup no longer failed immediately on missing Chroma imports
- Ran `uv run pytest` (`17 passed`)
- Did not package or bundle `antiword`; that remains a release caveat

## Risks and Follow-ups

- `.doc` parsing in packaged builds still depends on `antiword` being installed or bundled explicitly.
- The packaged app currently relies on the hashing embedder instead of bundling the full local sentence-transformer stack.
- Distribution outside local development will still need proper signing and notarization.
