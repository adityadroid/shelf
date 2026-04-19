from __future__ import annotations

import hashlib
import logging
from typing import Iterable

import chromadb
from chromadb.api.models.Collection import Collection

from shelf.core.paths import AppPaths
from shelf.indexing.models import ChunkRecord


LOGGER = logging.getLogger(__name__)


class HashingEmbedder:
    model_name = "hashing-fallback-v1"
    model_version = "v1"

    def encode(self, texts: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for text in texts:
            values: list[float] = []
            seed = hashlib.sha256(text.encode("utf-8")).digest()
            for index in range(0, 128):
                byte = seed[index % len(seed)]
                values.append((byte / 255.0) * 2 - 1)
            embeddings.append(values)
        return embeddings


class SentenceTransformerEmbedder:
    def __init__(self, paths: AppPaths, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.paths = paths
        self.model_name = model_name
        self.model_version = "sentence-transformers"
        self._model = None

    def _load(self):
        if self._model is not None:
            return self._model
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(self.model_name, cache_folder=str(self.paths.models_dir))
        return self._model

    def encode(self, texts: list[str]) -> list[list[float]]:
        model = self._load()
        return [list(vector) for vector in model.encode(texts, normalize_embeddings=True)]


class EmbeddingService:
    def __init__(self, paths: AppPaths) -> None:
        self.paths = paths
        self.client = chromadb.PersistentClient(path=str(paths.vectors_dir))
        self.collection: Collection = self.client.get_or_create_collection(
            "document_chunks",
            metadata={"space": "cosine"},
        )
        self._embedder = None

    @property
    def embedder(self):
        if self._embedder is None:
            try:
                self._embedder = SentenceTransformerEmbedder(self.paths)
                self._embedder.encode(["shelf warmup"])
            except Exception as exc:  # pragma: no cover - depends on model availability
                LOGGER.warning("Falling back to hashing embedder: %s", exc)
                self._embedder = HashingEmbedder()
        return self._embedder

    def upsert_chunks(self, document_id: str, chunks: Iterable[ChunkRecord]) -> tuple[str, str]:
        chunk_list = list(chunks)
        if not chunk_list:
            self.delete_document(document_id)
            return self.embedder.model_name, self.embedder.model_version

        texts = [chunk.text for chunk in chunk_list]
        embeddings = self.embedder.encode(texts)
        metadatas = [
            {
                "document_id": document_id,
                "chunk_index": chunk.chunk_index,
                "source_ref": chunk.source_ref or "",
            }
            for chunk in chunk_list
        ]
        self.collection.upsert(
            ids=[chunk.chunk_id for chunk in chunk_list],
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return self.embedder.model_name, self.embedder.model_version

    def delete_document(self, document_id: str) -> None:
        self.collection.delete(where={"document_id": document_id})

    def query(self, query_text: str, limit: int = 10) -> list[dict]:
        query_vector = self.embedder.encode([query_text])[0]
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=limit,
            include=["documents", "metadatas", "distances"],
        )
        items: list[dict] = []
        ids = results.get("ids", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        documents = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]
        for chunk_id, metadata, document, distance in zip(ids, metadatas, documents, distances, strict=False):
            items.append(
                {
                    "chunk_id": chunk_id,
                    "document_id": metadata.get("document_id"),
                    "chunk_index": metadata.get("chunk_index"),
                    "source_ref": metadata.get("source_ref"),
                    "document": document,
                    "distance": distance,
                }
            )
        return items
