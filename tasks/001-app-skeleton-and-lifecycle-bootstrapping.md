# Task 001: App Skeleton and Lifecycle Bootstrapping

- Status: `Not Started`
- Priority: `P0`
- Depends On: `None`
- Last Updated: `2026-04-19`

## Objective

Create the minimal native application skeleton for Shelf so the team has a clean PySide6 entry point, application lifecycle wiring, and a clear separation between UI code and the Python core.

## Why This Matters

The plans call for a native macOS app with a modular architecture. A clean shell is the foundation for every later task: onboarding, indexing, search, status updates, and background work all need a predictable application boundary.

## Scope

- Define the initial project layout for the app, UI layer, and core services.
- Add a launchable PySide6 application entry point.
- Establish the main window, app startup flow, and shutdown hooks.
- Create a dependency injection or service registration pattern simple enough for MVP growth.
- Ensure no indexing, parsing, or heavy work runs on the UI thread during startup.

## Out of Scope

- Full search experience.
- Real folder watching or indexing logic.
- Packaging or notarization work.

## Implementation Checklist

- Choose and document the source layout for UI, domain/core, infrastructure, and tests.
- Add a top-level app bootstrap module that initializes configuration, logging, and service wiring.
- Create the initial main window shell with placeholders for search, status, and settings/navigation areas.
- Add lifecycle hooks for app start, graceful shutdown, and background worker cleanup.
- Ensure startup failures surface clearly and safely instead of crashing silently.

## Acceptance Criteria

- The application launches locally into a native window without doing heavy background work.
- The codebase has a stable place for UI code, infrastructure code, and future indexing/search services.
- Application startup and shutdown paths are explicit and testable.

## Validation

- Run the app locally and verify the main window opens successfully.
- Confirm no blocking operations are executed on the UI thread at launch.
- Add at least one smoke test or bootstrap test if practical.

## Risks and Notes

- Avoid overengineering dependency injection; use the smallest pattern that keeps boundaries clear.
- Keep file paths, data directories, and service registration centralized so later tasks do not duplicate startup logic.
