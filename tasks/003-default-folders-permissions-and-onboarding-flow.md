# Task 003: Default Folders, Permissions, and Onboarding Flow

- Status: `Not Started`
- Priority: `P0`
- Depends On: `001`, `002`
- Last Updated: `2026-04-19`

## Objective

Build the first-run experience that explains Shelf, preconfigures the default folders, and guides users through macOS permission requirements with minimal friction.

## Why This Matters

The product plan makes out-of-the-box value a core promise. Users need to understand what Shelf indexes, which folders are included, and why permissions matter before indexing can be trusted.

## Scope

- Add a first-run onboarding flow for Shelf’s purpose and supported file types.
- Preconfigure `~/Documents`, `~/Downloads`, and `~/Desktop`.
- Surface permission requirements and recovery guidance clearly.
- Transition from onboarding into the main app with indexing-ready state.

## Out of Scope

- Full folder management after onboarding.
- Actual indexing implementation.
- Advanced preferences.

## Implementation Checklist

- Define first-run screens or steps with clear, concise copy.
- Show the default monitored folders and supported file types during onboarding.
- Detect whether onboarding has already completed and skip it on subsequent launches.
- Integrate permission checks and user guidance for denied or missing access.
- Ensure onboarding completion persists only after the required state is saved successfully.

## Acceptance Criteria

- A first-time user sees a clear introduction to Shelf and its monitored default folders.
- Default folder configuration is created automatically on first run.
- The app provides understandable guidance when permissions are missing or revoked.

## Validation

- Manually verify first-run versus returning-user behavior.
- Test denied-permission and permission-retry flows.
- Confirm onboarding copy and states stay consistent with the MVP scope in the product plan.

## Risks and Notes

- Avoid overly technical permission language; the user needs confidence, not system internals.
- Make sure onboarding does not imply OCR, cloud sync, or other out-of-scope capabilities.
