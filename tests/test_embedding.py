from __future__ import annotations

from shelf.indexing.embedding import EmbeddingService, HashingEmbedder
from shelf.indexing.models import ChunkRecord


class StubClient:
    def __init__(self, max_batch_size: int) -> None:
        self._max_batch_size = max_batch_size

    def get_max_batch_size(self) -> int:
        return self._max_batch_size


class StubCollection:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.deleted_where = None

    def upsert(self, *, ids, documents, embeddings, metadatas) -> None:
        self.calls.append(
            {
                "ids": ids,
                "documents": documents,
                "embeddings": embeddings,
                "metadatas": metadatas,
            }
        )

    def delete(self, *, where) -> None:
        self.deleted_where = where


def make_chunk(document_id: str, chunk_index: int) -> ChunkRecord:
    text = f"chunk-{chunk_index}"
    return ChunkRecord(
        chunk_id=f"chunk-id-{chunk_index}",
        document_id=document_id,
        chunk_index=chunk_index,
        text=text,
        start_char=chunk_index * 10,
        end_char=chunk_index * 10 + len(text),
        source_ref=f"section-{chunk_index}",
        checksum=f"checksum-{chunk_index}",
    )


def build_service(max_batch_size: int = 2) -> tuple[EmbeddingService, StubCollection]:
    service = EmbeddingService.__new__(EmbeddingService)
    service.client = StubClient(max_batch_size)
    service.collection = StubCollection()
    service._embedder = HashingEmbedder()
    service._max_batch_size = None
    return service, service.collection


def test_upsert_chunks_batches_to_chroma_limit():
    service, collection = build_service(max_batch_size=2)
    chunks = [make_chunk("doc-1", index) for index in range(5)]

    model_name, model_version = service.upsert_chunks("doc-1", chunks)

    assert (model_name, model_version) == ("hashing-fallback-v1", "v1")
    assert [call["ids"] for call in collection.calls] == [
        ["chunk-id-0", "chunk-id-1"],
        ["chunk-id-2", "chunk-id-3"],
        ["chunk-id-4"],
    ]
    assert [call["documents"] for call in collection.calls] == [
        ["chunk-0", "chunk-1"],
        ["chunk-2", "chunk-3"],
        ["chunk-4"],
    ]
    assert [len(call["embeddings"]) for call in collection.calls] == [2, 2, 1]
    assert [metadata["chunk_index"] for call in collection.calls for metadata in call["metadatas"]] == [0, 1, 2, 3, 4]


def test_upsert_chunks_deletes_document_when_empty():
    service, collection = build_service()

    service.upsert_chunks("doc-empty", [])

    assert collection.deleted_where == {"document_id": "doc-empty"}
    assert collection.calls == []


def test_upsert_chunks_guards_zero_batch_size():
    service, collection = build_service(max_batch_size=0)
    chunks = [make_chunk("doc-1", index) for index in range(2)]

    service.upsert_chunks("doc-1", chunks)

    assert [call["ids"] for call in collection.calls] == [
        ["chunk-id-0"],
        ["chunk-id-1"],
    ]
