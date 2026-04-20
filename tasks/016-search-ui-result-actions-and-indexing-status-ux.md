# Task 016: Search UI, Result Actions, and Indexing Status UX

- Status: `Done`
- Priority: `P0`
- Depends On: `003`, `004`, `009`, `015`
- Last Updated: `2026-04-19`

## Objective

Deliver the core Shelf user experience: fast search input, ranked results with metadata/snippets, result actions, and clear indexing/status states.

## Why This Matters

This is the primary user-visible value of Shelf. The product plan emphasizes instant-feeling search, transparent indexing state, and actions that help users get to the right document immediately.

## Scope

- Build a search-first main screen and results list.
- Show file metadata, snippets, and indexing status without crowding the main search surface.
- Add result actions for open, reveal in Finder, and copy path.
- Move monitored folders and failure diagnostics into dedicated settings and monitor surfaces.
- Expose maintenance and repair commands in the GUI in addition to the CLI.
- Handle empty, loading, and error states clearly.

## Out of Scope

- Rich preview panes.
- Saved searches, filters, or advanced sorting.
- Optional semantic explanations or summaries.

## Implementation Checklist

- Implement responsive search input handling and result updates.
- Design result rows with filename, folder path, modified date, type, and snippet.
- Wire actions to open files, reveal them in Finder, and copy paths safely.
- Surface indexing-in-progress, fully indexed, empty library, and failure states.
- Ensure the UI never blocks on search or indexing work.

## Acceptance Criteria

- A user can search and act on results quickly from a native macOS UI.
- The app clearly distinguishes between indexing in progress, complete, empty, and error conditions.
- Result actions behave predictably and safely.

## Validation

- Manual UX checks for fast typing, no-results, partial indexing, and result-action flows.
- Add UI or integration tests for key states if practical within the chosen test setup.
- 2026-04-19 refresh: `uv run pytest tests/test_ui_shell.py tests/test_search.py tests/test_maintenance.py`

## Risks and Notes

- Search UX should prioritize clarity over visual complexity.
- Progressive updates are helpful, but avoid flicker or misleading state transitions while indexing is still underway.
