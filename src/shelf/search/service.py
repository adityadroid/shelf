from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor

from shelf.indexing.models import SearchResult


def _fts_query(query: str) -> str:
    tokens = [token.strip() for token in query.replace("/", " ").split() if token.strip()]
    if not tokens:
        return ""
    return " ".join(f"{token}*" for token in tokens)


class SearchService:
    def __init__(self, connection: sqlite3.Connection, embedding_service) -> None:
        self.connection = connection
        self.embedding_service = embedding_service
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="search")

    def exact_search(self, query: str, limit: int = 20) -> list[SearchResult]:
        fts_query = _fts_query(query)
        if not fts_query:
            return []
        rows = self.connection.execute(
            """
            SELECT
                d.id AS document_id,
                d.path,
                d.file_name,
                d.extension,
                d.mtime,
                snippet(documents_fts, 3, '[', ']', '...', 16) AS snippet,
                bm25(documents_fts, 5.0, 2.0, 1.0) AS rank
            FROM documents_fts
            JOIN documents d ON d.id = documents_fts.document_id
            WHERE documents_fts MATCH ?
            ORDER BY
                CASE WHEN lower(d.file_name) LIKE lower(?) THEN 0 ELSE 1 END,
                rank
            LIMIT ?
            """,
            (fts_query, f"%{query.lower()}%", limit),
        ).fetchall()
        return [
            SearchResult(
                document_id=row["document_id"],
                path=row["path"],
                file_name=row["file_name"],
                extension=row["extension"],
                snippet=row["snippet"] or "",
                modified_at=row["mtime"],
                score=1 / (1 + abs(float(row["rank"]))),
                source="fts",
            )
            for row in rows
        ]

    def vector_search(self, query: str, limit: int = 20) -> list[SearchResult]:
        try:
            vector_hits = self.embedding_service.query(query, limit=limit)
        except Exception:
            return []

        results: list[SearchResult] = []
        for hit in vector_hits:
            row = self.connection.execute(
                """
                SELECT id, path, file_name, extension, mtime
                FROM documents
                WHERE id = ?
                """,
                (hit["document_id"],),
            ).fetchone()
            if row is None:
                continue
            score = max(0.0, 1.0 - float(hit["distance"]))
            results.append(
                SearchResult(
                    document_id=row["id"],
                    path=row["path"],
                    file_name=row["file_name"],
                    extension=row["extension"],
                    snippet=str(hit["document"] or ""),
                    modified_at=row["mtime"],
                    score=score,
                    source="vector",
                )
            )
        return results

    def search(self, query: str, limit: int = 20) -> list[SearchResult]:
        future_exact = self.executor.submit(self.exact_search, query, limit)
        future_vector = self.executor.submit(self.vector_search, query, limit)
        exact_results = future_exact.result()
        vector_results = future_vector.result()

        by_document: dict[str, SearchResult] = {}
        for result in exact_results:
            by_document[result.document_id] = result

        for result in vector_results:
            existing = by_document.get(result.document_id)
            if existing is None:
                by_document[result.document_id] = result
                continue
            combined_score = existing.score * 1.4 + result.score
            snippet = existing.snippet if existing.snippet else result.snippet
            by_document[result.document_id] = SearchResult(
                document_id=existing.document_id,
                path=existing.path,
                file_name=existing.file_name,
                extension=existing.extension,
                snippet=snippet,
                modified_at=max(existing.modified_at, result.modified_at),
                score=combined_score,
                source="hybrid",
            )

        return sorted(by_document.values(), key=lambda item: item.score, reverse=True)[:limit]
