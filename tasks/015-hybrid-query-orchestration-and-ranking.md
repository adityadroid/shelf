# Task 015: Hybrid Query Orchestration and Ranking

- Status: `Not Started`
- Priority: `P1`
- Depends On: `006`, `014`
- Last Updated: `2026-04-19`

## Objective

Build the query layer that runs exact search and vector retrieval in parallel, merges results by document, and returns ranked results with useful snippets.

## Why This Matters

The engineering plan’s final recommendation is a hybrid system, not vector-only search. This task is where exact-match trust and semantic recall become one coherent search experience.

## Scope

- Normalize search queries.
- Execute SQLite FTS and Chroma searches in parallel.
- Merge and rank by document using a simple, inspectable weighted strategy.
- Attach the best chunk matches and metadata for the UI.

## Out of Scope

- Full UI rendering details.
- Advanced filters or sorting.
- Optional local RAG generation.

## Implementation Checklist

- Define the query service input/output contract used by the UI.
- Implement parallel FTS and vector lookups with sensible fallbacks if one subsystem is unavailable.
- Apply weighted ranking with strong filename boosts and transparent tie-breakers.
- Aggregate chunk-level hits into document-level results with snippets and metadata.
- Add tests for exact-match dominance, mixed result fusion, and no-result scenarios.

## Acceptance Criteria

- Search results reflect both exact keyword strength and semantic similarity without hiding filename matches.
- Result aggregation is document-centric and suitable for the MVP UI.
- The ranking strategy is simple enough to tune and debug from logs/tests.

## Validation

- Run integration tests on a seeded corpus with exact and semantic match cases.
- Verify results remain usable if vector retrieval is temporarily unavailable.

## Risks and Notes

- Do not overfit scoring too early; start with a documented baseline and iterate from evidence.
- Users should never lose trust because semantic similarity outranks an obvious filename hit.
