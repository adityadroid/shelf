# Task 016: Search UI, Result Actions, and Indexing Status UX

- Status: `Done`
- Priority: `P0`
- Depends On: `003`, `004`, `009`, `015`
- Last Updated: `2026-04-22`

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
- 2026-04-20 redesign refresh: shifted the landing view to a chat-style search composer, moved library health into Settings, and re-ran `uv run pytest tests/test_ui_shell.py tests/test_search.py tests/test_maintenance.py`
- 2026-04-20 simplification refresh: removed live search from the landing view, reduced the main window to a floating composer plus Settings entry point, and re-ran `uv run pytest tests/test_ui_shell.py tests/test_search.py tests/test_maintenance.py`
- 2026-04-20 debounce/focus fix: delayed live search until the user pauses typing, kept the floating results pane from stealing focus, and re-ran `uv run pytest tests/test_ui_shell.py tests/test_search.py tests/test_maintenance.py`
- 2026-04-20 visual polish refresh: matched the results popup width to the search pill, tightened scrollbar spacing, added a source-tree app icon, and re-ran `uv run pytest tests/test_ui_shell.py tests/test_search.py tests/test_maintenance.py`
- 2026-04-20 launcher settings refresh: added a persisted launcher shortcut preference with `Cmd+Option+S` as the default, fixed the visible app display name to `Shelf`, and re-ran `uv run pytest tests/test_ui_shell.py tests/test_settings.py tests/test_search.py tests/test_maintenance.py`
- 2026-04-20 launcher behavior refresh: registered the macOS launcher shortcut to toggle the floating search surface at the top of the screen, rebuilt Settings to use the same floating glass design language as the main view, and re-ran `uv run pytest tests/test_ui_shell.py tests/test_settings.py tests/test_search.py tests/test_maintenance.py`
- 2026-04-20 settings polish refresh: replaced the abstract settings header copy with product-facing language, reduced settings transparency for readability, aligned the shortcut field styling with the rest of the floating UI, and re-ran `uv run pytest tests/test_ui_shell.py tests/test_settings.py tests/test_search.py tests/test_maintenance.py`
- 2026-04-20 search interaction refresh: reduced transparency on the floating search/results surfaces, hid the launcher when it loses focus, added keyboard-only result navigation and activation, and re-ran `uv run pytest tests/test_ui_shell.py tests/test_settings.py tests/test_search.py tests/test_maintenance.py`
- 2026-04-21 settings redesign refresh: shifted the app chrome to a cooler blue gradient palette, rebuilt the settings shell hierarchy with stronger cards/sidebar contrast, hardened launcher focus retention, and re-ran `uv run pytest tests/test_ui_shell.py tests/test_settings.py tests/test_search.py` plus `uv run pytest`
- 2026-04-21 overview dashboard refresh: adapted the AI mock into a real PySide6 overview dashboard with shortcut chips, live health stats, monitored-folder and maintenance cards, sidebar status, and re-ran `uv run pytest tests/test_ui_shell.py tests/test_settings.py tests/test_search.py` plus `uv run pytest`
- 2026-04-21 settings cleanup refresh: removed duplicated overview controls in favor of a true dashboard, aligned horizontal and vertical scrollbar styling, added configurable document-type settings with real TXT/Markdown parser support, prompted for reindex on document-type changes, and re-ran `uv run pytest`
- 2026-04-21 resize and tray refresh: added tray-based hide/minimize behavior for the launcher, enabled edge resizing for the floating search window and settings dialog, made settings pages responsive and scrollable instead of clipping, refined the settings close control, and re-ran `uv run pytest tests/test_ui_shell.py tests/test_settings.py`
- 2026-04-22 results popup polish refresh: softened the results shell/card boundaries, tuned popup shadow and spacing, made popup height grow with result count and cap at usable screen height, and re-ran `uv run pytest tests/test_search.py tests/test_ui_shell.py`

## Risks and Notes

- Search UX should prioritize clarity over visual complexity.
- Progressive updates are helpful, but avoid flicker or misleading state transitions while indexing is still underway.
- The current shell now favors a single settings entry point over a separate monitor dialog; future expansions should keep that simplified navigation model coherent.
