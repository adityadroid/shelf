# Task 014: Embedding Worker and Chroma Persistence

- Status: `Not Started`
- Priority: `P1`
- Depends On: `008`, `013`
- Last Updated: `2026-04-19`

## Objective

Implement the local embedding pipeline and durable Chroma persistence for chunk-level semantic retrieval.

## Why This Matters

Semantic retrieval is not the first MVP deliverable, but the engineering plan clearly includes it as part of the hybrid architecture. This task adds the local vector layer without weakening offline guarantees.

## Scope

- Load the chosen sentence-transformer model locally.
- Generate embeddings in bounded micro-batches off the UI thread.
- Persist chunk embeddings and metadata to Chroma.
- Record embedding model and schema versions for future re-embedding.

## Out of Scope

- Hybrid ranking logic.
- Optional local LLM generation.
- Broad performance tuning beyond safe defaults.

## Implementation Checklist

- Implement an embedding worker interface decoupled from parser and UI code.
- Configure the initial model as `all-MiniLM-L6-v2` unless the team intentionally changes direction.
- Persist chunk metadata in SQLite before or alongside embedding state so crashes are recoverable.
- Add Chroma collection initialization and document-chunk upsert/delete behavior.
- Add tests or controlled checks for model loading, batching behavior, and vector-store writes.

## Acceptance Criteria

- Shelf can embed chunk text locally and store vectors durably in Chroma.
- Embedding work is bounded, observable, and recoverable after failure.
- Each chunk records the embedding model/schema used to generate its vector.

## Validation

- Run a local integration path on a small fixture corpus from chunk generation through Chroma persistence.
- Verify document reindex deletes or replaces stale vectors for changed chunks only.

## Risks and Notes

- Keep model loading and execution isolated; semantic retrieval should not destabilize exact search or UI startup.
- Be careful about memory pressure from model residency and batch sizing.
