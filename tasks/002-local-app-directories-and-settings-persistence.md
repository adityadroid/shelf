# Task 002: Local App Directories and Settings Persistence

- Status: `Not Started`
- Priority: `P0`
- Depends On: `001`
- Last Updated: `2026-04-19`

## Objective

Implement the local application support layout and settings persistence used to store monitored folders, preferences, and future durable subsystem data paths.

## Why This Matters

Both plans require Shelf to be fully local and trustworthy across restarts. The app needs stable directories and a settings layer before it can persist monitored folders, database paths, logs, or first-run state.

## Scope

- Define the application support directory structure under macOS user-owned storage.
- Implement settings persistence for first-run state, monitored folders, and lightweight preferences.
- Create path helpers so SQLite, vector storage, logs, and caches all resolve consistently.
- Add validation for missing or corrupt settings files with safe fallback behavior.

## Out of Scope

- Full database schema.
- Search or indexing behavior.
- Folder picker UI logic.

## Implementation Checklist

- Choose the canonical local storage root and document each subdirectory purpose.
- Implement a settings service with load, save, defaulting, and schema/version handling.
- Store default monitored folders in a way that supports first-run initialization versus user-modified state.
- Add path normalization rules for folder entries, including expansion of `~` and canonical absolute paths.
- Add tests for settings load/save, corrupted settings fallback, and default initialization.

## Acceptance Criteria

- Shelf can create and reuse deterministic local directories for config, DB, vectors, models, and logs.
- Settings persist across app restarts without losing monitored folder configuration.
- Corrupt or missing settings do not crash the app and are surfaced clearly for recovery.

## Validation

- Verify first-run settings creation in a temporary test directory.
- Verify reloading existing settings preserves user-managed folder data.
- Verify fallback behavior when the settings file is absent or malformed.

## Risks and Notes

- Keep settings narrowly scoped; high-volume operational state belongs in SQLite, not in ad hoc config files.
- Be careful not to lock the team into a brittle JSON structure without versioning.
