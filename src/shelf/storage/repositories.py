from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Iterable

from shelf.core.models import MonitoredFolder
from shelf.indexing.models import ChunkRecord, JobStatus, JobType, ParsedDocument


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class FolderRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def sync(self, folders: Iterable[MonitoredFolder]) -> None:
        existing_paths = {
            row["path"]: row["id"] for row in self.connection.execute("SELECT id, path FROM folders")
        }
        incoming_paths = set()

        for folder in folders:
            incoming_paths.add(folder.path)
            if folder.path in existing_paths:
                self.connection.execute(
                    """
                    UPDATE folders
                    SET source = ?, accessible = ?, updated_at = ?
                    WHERE path = ?
                    """,
                    (folder.source, int(folder.accessible), utc_now(), folder.path),
                )
            else:
                self.connection.execute(
                    """
                    INSERT INTO folders(path, source, accessible, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (folder.path, folder.source, int(folder.accessible), utc_now(), utc_now()),
                )

        for path in existing_paths.keys() - incoming_paths:
            self.connection.execute("DELETE FROM folders WHERE path = ?", (path,))

    def get_id_for_path(self, file_path: str) -> int | None:
        file_path_obj = Path(file_path)
        rows = self.connection.execute("SELECT id, path FROM folders ORDER BY LENGTH(path) DESC").fetchall()
        for row in rows:
            folder_path = Path(row["path"])
            if folder_path == file_path_obj or folder_path in file_path_obj.parents:
                return int(row["id"])
        return None

    def list_paths(self) -> list[str]:
        return [row["path"] for row in self.connection.execute("SELECT path FROM folders ORDER BY path")]


class DocumentRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def get_by_path(self, path: str) -> sqlite3.Row | None:
        return self.connection.execute("SELECT * FROM documents WHERE path = ?", (path,)).fetchone()

    def upsert_document(
        self,
        document_id: str,
        folder_id: int | None,
        parsed: ParsedDocument,
        fast_fingerprint: str,
        content_hash: str | None,
        chunk_schema_version: str,
        embedding_model: str | None = None,
        embedding_version: str | None = None,
    ) -> None:
        parser_message = "\n".join(parsed.diagnostics) if parsed.diagnostics else None
        self.connection.execute(
            """
            INSERT INTO documents(
                id, folder_id, path, file_name, extension, size_bytes, ctime, mtime,
                fast_fingerprint, content_hash, parser_type, parser_status, parser_message,
                raw_text, text_length, page_count, last_indexed_at, lifecycle_state,
                chunk_schema_version, embedding_model, embedding_version
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                folder_id = excluded.folder_id,
                path = excluded.path,
                file_name = excluded.file_name,
                extension = excluded.extension,
                size_bytes = excluded.size_bytes,
                ctime = excluded.ctime,
                mtime = excluded.mtime,
                fast_fingerprint = excluded.fast_fingerprint,
                content_hash = excluded.content_hash,
                parser_type = excluded.parser_type,
                parser_status = excluded.parser_status,
                parser_message = excluded.parser_message,
                raw_text = excluded.raw_text,
                text_length = excluded.text_length,
                page_count = excluded.page_count,
                last_indexed_at = excluded.last_indexed_at,
                lifecycle_state = 'active',
                chunk_schema_version = excluded.chunk_schema_version,
                embedding_model = excluded.embedding_model,
                embedding_version = excluded.embedding_version
            """,
            (
                document_id,
                folder_id,
                parsed.path,
                parsed.file_name,
                parsed.extension,
                parsed.size_bytes,
                parsed.ctime,
                parsed.mtime,
                fast_fingerprint,
                content_hash,
                parsed.parser_type,
                parsed.parser_status.value,
                parser_message,
                parsed.raw_text,
                len(parsed.raw_text),
                parsed.page_count,
                utc_now(),
                chunk_schema_version,
                embedding_model,
                embedding_version,
            ),
        )
        self.connection.execute("DELETE FROM documents_fts WHERE document_id = ?", (document_id,))
        self.connection.execute(
            """
            INSERT INTO documents_fts(document_id, file_name, path, content)
            VALUES (?, ?, ?, ?)
            """,
            (document_id, parsed.file_name, parsed.path, parsed.raw_text),
        )

    def delete_by_path(self, path: str) -> str | None:
        row = self.get_by_path(path)
        if row is None:
            return None
        document_id = str(row["id"])
        self.connection.execute("DELETE FROM document_chunks WHERE document_id = ?", (document_id,))
        self.connection.execute("DELETE FROM documents_fts WHERE document_id = ?", (document_id,))
        self.connection.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        return document_id

    def replace_chunks(
        self,
        document_id: str,
        chunks: Iterable[ChunkRecord],
        embedding_model: str | None,
        embedding_version: str | None,
    ) -> None:
        self.connection.execute("DELETE FROM document_chunks WHERE document_id = ?", (document_id,))
        now = utc_now()
        for chunk in chunks:
            self.connection.execute(
                """
                INSERT INTO document_chunks(
                    id, document_id, chunk_index, text, start_char, end_char,
                    source_ref, checksum, embedding_model, embedding_version, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk.chunk_id,
                    document_id,
                    chunk.chunk_index,
                    chunk.text,
                    chunk.start_char,
                    chunk.end_char,
                    chunk.source_ref,
                    chunk.checksum,
                    embedding_model,
                    embedding_version,
                    now,
                ),
            )

    def list_document_paths(self) -> dict[str, str]:
        return {row["path"]: row["id"] for row in self.connection.execute("SELECT path, id FROM documents")}

    def list_chunks_for_document(self, document_id: str) -> list[sqlite3.Row]:
        return self.connection.execute(
            "SELECT * FROM document_chunks WHERE document_id = ? ORDER BY chunk_index",
            (document_id,),
        ).fetchall()


class JobRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def enqueue(
        self,
        event_type: JobType,
        path: str,
        *,
        old_path: str | None = None,
        folder_id: int | None = None,
        priority: int = 100,
        fingerprint_hint: str | None = None,
    ) -> None:
        pending = self.connection.execute(
            """
            SELECT id FROM jobs
            WHERE path = ? AND status IN (?, ?)
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (path, JobStatus.PENDING.value, JobStatus.PROCESSING.value),
        ).fetchone()
        if pending:
            self.connection.execute(
                """
                UPDATE jobs
                SET event_type = ?, old_path = ?, priority = ?, fingerprint_hint = ?, updated_at = ?
                WHERE id = ?
                """,
                (event_type.value, old_path, priority, fingerprint_hint, utc_now(), pending["id"]),
            )
            return

        now = utc_now()
        self.connection.execute(
            """
            INSERT INTO jobs(
                event_type, path, old_path, folder_id, priority, status,
                attempt_count, next_attempt_at, fingerprint_hint, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
            """,
            (
                event_type.value,
                path,
                old_path,
                folder_id,
                priority,
                JobStatus.PENDING.value,
                now,
                fingerprint_hint,
                now,
                now,
            ),
        )

    def claim_next(self) -> sqlite3.Row | None:
        row = self.connection.execute(
            """
            SELECT * FROM jobs
            WHERE status = ? AND next_attempt_at <= ?
            ORDER BY priority ASC, id ASC
            LIMIT 1
            """,
            (JobStatus.PENDING.value, utc_now()),
        ).fetchone()
        if row is None:
            return None
        self.connection.execute(
            "UPDATE jobs SET status = ?, updated_at = ? WHERE id = ?",
            (JobStatus.PROCESSING.value, utc_now(), row["id"]),
        )
        return self.connection.execute("SELECT * FROM jobs WHERE id = ?", (row["id"],)).fetchone()

    def mark_done(self, job_id: int) -> None:
        self.connection.execute("DELETE FROM jobs WHERE id = ?", (job_id,))

    def mark_failed(self, job_id: int, message: str, attempt_count: int) -> None:
        delay_seconds = min(300, 2**attempt_count)
        next_attempt = datetime.now(UTC) + timedelta(seconds=delay_seconds)
        status = JobStatus.FAILED.value if attempt_count >= 5 else JobStatus.PENDING.value
        self.connection.execute(
            """
            UPDATE jobs
            SET status = ?, attempt_count = ?, next_attempt_at = ?, last_error = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, attempt_count, next_attempt.isoformat(), message, utc_now(), job_id),
        )

    def stats(self) -> dict[str, int]:
        rows = self.connection.execute(
            "SELECT status, COUNT(*) AS total FROM jobs GROUP BY status"
        ).fetchall()
        result = {status.value: 0 for status in JobStatus}
        for row in rows:
            result[row["status"]] = row["total"]
        return result


class FailureRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def record(self, scope: str, message: str, ref_id: str | None = None, detail: str | None = None) -> None:
        self.connection.execute(
            """
            INSERT INTO failures(scope, ref_id, message, detail, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (scope, ref_id, message, detail, utc_now()),
        )

    def list_recent(self, limit: int = 20) -> list[sqlite3.Row]:
        return self.connection.execute(
            "SELECT * FROM failures ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()


class ScannerStateRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def set(self, key: str, value: dict | str) -> None:
        encoded = value if isinstance(value, str) else json.dumps(value)
        self.connection.execute(
            """
            INSERT INTO scanner_state(key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            (key, encoded, utc_now()),
        )

    def get(self, key: str) -> str | None:
        row = self.connection.execute("SELECT value FROM scanner_state WHERE key = ?", (key,)).fetchone()
        return str(row["value"]) if row else None


class MetricsRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def set(self, key: str, value: dict | str | int | float) -> None:
        if isinstance(value, (dict, list)):
            encoded = json.dumps(value)
        else:
            encoded = str(value)
        self.connection.execute(
            """
            INSERT INTO metrics(key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            (key, encoded, utc_now()),
        )

    def get(self, key: str) -> str | None:
        row = self.connection.execute("SELECT value FROM metrics WHERE key = ?", (key,)).fetchone()
        return str(row["value"]) if row else None


def new_document_id() -> str:
    return str(uuid.uuid4())
