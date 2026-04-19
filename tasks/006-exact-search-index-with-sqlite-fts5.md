# Task 006: Exact Search Index With SQLite FTS5

- Status: `Done`
- Priority: `P0`
- Depends On: `005`
- Last Updated: `2026-04-19`

## Objective

Implement the exact-text retrieval layer using SQLite FTS5 for filename, path, and extracted content search.

## Why This Matters

The plans explicitly recommend hybrid retrieval, with FTS handling filename and precise keyword recall. Shelf should not depend on embeddings for the core MVP search experience.

## Scope

- Add FTS5 schema objects and synchronization strategy.
- Index file names, paths, and searchable content.
- Implement ranked exact search queries for partial and multi-word input.
- Return enough data to support snippets and later result aggregation.

## Out of Scope

- Vector retrieval.
- Final hybrid score fusion.
- Full search UI rendering.

## Implementation Checklist

- Design the `documents_fts` table and its relationship to canonical metadata rows.
- Choose trigger-based sync or explicit write-through updates and document the decision.
- Implement search query normalization, token handling, and result ranking rules.
- Prioritize filename and exact keyword matches according to the product plan.
- Add tests for filename matches, content matches, partial terms, and empty/no-result behavior.

## Acceptance Criteria

- Shelf can return relevant exact matches for file names and extracted content.
- FTS data stays in sync with canonical document metadata updates and deletions.
- Search queries execute quickly against a local SQLite database.

## Validation

- Run integration tests on seeded document metadata and content.
- Verify delete or tombstone flows remove stale FTS results.
- Measure baseline query latency on representative local fixtures if practical.

## Risks and Notes

- Snippet generation should not force a UI dependency into the repository layer.
- Keep exact-search logic deterministic and debuggable; avoid opaque ranking heuristics too early.
