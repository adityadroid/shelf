# Refine Settings Resizing and Tray Behavior (Plan 004, 2026-04-21 15:57)

## Summary

Improved Shelf's floating windows so the launcher can hide to the menu bar instead of quitting, the frameless windows can be resized from their edges, and the settings surface now adapts to smaller sizes with responsive layout and scrolling instead of clipping content.

## Context

Shelf's search-first macOS UI uses custom frameless PySide6 windows. That design needed native-feeling lifecycle behavior, especially for tray hiding and resizable settings, while preserving the fast, trustworthy desktop experience defined in the product and engineering plans.

## Changes Made

- Updated `src/shelf/ui/main_window.py` to add tray/menu-bar controls, close-to-tray behavior, frameless edge resizing, responsive settings layout, and a refined settings close button.
- Updated `src/shelf/bootstrap.py` so the app stays alive when windows are hidden to the tray.
- Expanded `tests/test_ui_shell.py` to cover launcher tray behavior plus launcher/settings resize behavior.
- Updated `tasks/016-search-ui-result-actions-and-indexing-status-ux.md` with the latest UI hardening note.

## Decisions and Tradeoffs

- Kept the frameless floating shell and implemented custom edge resizing rather than switching to native titled windows.
- Converted settings sections to scrollable pages so smaller window sizes remain usable instead of forcing a larger fixed minimum size.
- Used a compact rounded-square close button with destructive hover feedback to better fit the custom control-room styling without mimicking macOS traffic lights.

## Validation

- Ran `uv run pytest tests/test_ui_shell.py tests/test_settings.py`
- Verified 7 tests passed.
- LSP diagnostics were not available because the local `ty` server is not installed.

## Risks and Follow-ups

- Custom frameless resizing may still need tuning for grab-area feel on different displays.
- The settings dashboard now reflows responsively, but further layout simplification may be useful if even narrower sizes need support.
- Tray/menu-bar behavior should be smoke-tested in a packaged app bundle to confirm parity outside the dev runtime.
