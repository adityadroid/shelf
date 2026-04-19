# Task 013: Fingerprinting and Deterministic Chunking

- Status: `Done`
- Priority: `P1`
- Depends On: `010`, `011`, `012`
- Last Updated: `2026-04-19`

## Objective

Implement file fingerprinting and a deterministic chunking pipeline that prepares extracted text for semantic retrieval and efficient reindexing.

## Why This Matters

The engineering plan calls out deterministic chunking and change fingerprinting as the key to bounded incremental work. Without them, every edit risks forcing expensive and noisy reprocessing.

## Scope

- Add fast and optional deep fingerprints for supported files.
- Create a deterministic chunker with overlap and paragraph-aware boundaries.
- Persist chunk metadata needed for snippets, aggregation, and future re-embedding.
- Tie chunk lifecycle to document reindex behavior.

## Out of Scope

- Embedding inference.
- Final vector-store writes.
- Search-result UI presentation.

## Implementation Checklist

- Implement fast fingerprints using path, size, and high-resolution mtime.
- Decide when deep hashes are needed to confirm real content change.
- Build the chunker around deterministic boundaries with stable ordering.
- Persist chunk records with indexes, character ranges, and source page/section metadata.
- Add tests for chunk boundary determinism, overlap, and minimal unnecessary churn after small edits.

## Acceptance Criteria

- Unchanged documents are skipped reliably when fingerprints match.
- Changed documents produce predictable chunk sets suitable for re-embedding.
- Chunk metadata is rich enough for document-level result aggregation later.

## Validation

- Unit tests for fingerprint comparisons and chunk output determinism.
- Regression tests showing small edits do not create chaotic chunk reshaping when avoidable.

## Risks and Notes

- Keep chunking rules simple and explicit; hidden heuristics will make reindex behavior hard to reason about.
- Record chunking schema/version metadata so later policy changes can trigger controlled reprocessing.
