# Task 004: Monitored Folder Management UI and Domain Rules

- Status: `Not Started`
- Priority: `P0`
- Depends On: `002`, `003`
- Last Updated: `2026-04-19`

## Objective

Implement the monitored folder management experience and business rules for adding, removing, validating, and listing indexed roots.

## Why This Matters

Transparent folder control is a core trust feature in the product plan. Users must always be able to see and manage the scope of indexing without guessing what the app is watching.

## Scope

- Display current monitored folders.
- Add new folders through a native macOS folder picker.
- Remove folders with an explicit confirmation that explains search impact.
- Prevent duplicate, nested, or inaccessible folder entries where appropriate.

## Out of Scope

- Actual index cleanup when a folder is removed.
- Continuous watcher integration.
- Deep permission repair tooling beyond clear messaging.

## Implementation Checklist

- Define a monitored folder domain model with normalized paths and identifiers.
- Add UI for listing folders, adding a folder, and removing a folder.
- Decide and document how to handle nested folder additions to avoid redundant scanning.
- Validate folder accessibility before saving.
- Surface blocked or revoked folder states clearly in the UI.

## Acceptance Criteria

- Users can view all monitored folders and manage them without editing config files manually.
- Duplicate or invalid folder additions are prevented with understandable feedback.
- Folder removal requires explicit confirmation and clearly explains search consequences.

## Validation

- Manual tests for add, remove, duplicate add, and inaccessible path scenarios.
- Unit tests for folder normalization and duplicate/nesting rules.

## Risks and Notes

- Be explicit about whether parent/child folder overlap is disallowed or normalized automatically.
- Removal semantics must stay aligned with later index cleanup work in the queue and storage layers.
