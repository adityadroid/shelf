from __future__ import annotations

import json
from pathlib import Path

from shelf.core.models import AppSettings, SUPPORTED_EXTENSIONS
from shelf.core.services import ServiceContainer
from shelf.indexing.embedding import EmbeddingService
from shelf.indexing.models import JobType
from shelf.indexing.reconcile import ReconciliationService
from shelf.storage.database import Database
from shelf.storage.repositories import (
    DocumentRepository,
    FailureRepository,
    FolderRepository,
    JobRepository,
    MetricsRepository,
    ScannerStateRepository,
)


class MaintenanceService:
    def __init__(self, services: ServiceContainer, settings: AppSettings) -> None:
        self.services = services
        self.settings = settings
        self.database = Database(services.paths)
        self.database.initialize()
        self.connection = self.database.connect()
        self.folder_repository = FolderRepository(self.connection)
        self.document_repository = DocumentRepository(self.connection)
        self.job_repository = JobRepository(self.connection)
        self.failure_repository = FailureRepository(self.connection)
        self.metrics_repository = MetricsRepository(self.connection)
        self.scanner_state = ScannerStateRepository(self.connection)
        self.embedding_service = EmbeddingService(services.paths)

    def sync_settings(self) -> None:
        self.folder_repository.sync(self.settings.monitored_folders)
        self.connection.commit()

    def metrics_snapshot(self) -> dict:
        document_total = self.connection.execute("SELECT COUNT(*) AS total FROM documents").fetchone()["total"]
        failure_total = self.connection.execute("SELECT COUNT(*) AS total FROM failures").fetchone()["total"]
        return {
            "documents": document_total,
            "jobs": self.job_repository.stats(),
            "failures": failure_total,
            "last_processed_job": self.metrics_repository.get("last_processed_job"),
            "last_reconciliation": self.scanner_state.get("last_reconciliation"),
        }

    def rebuild_all(self) -> dict:
        self.sync_settings()
        reconciliation = ReconciliationService(
            self.folder_repository,
            self.document_repository,
            self.job_repository,
            self.scanner_state,
        )
        reconciliation.run()
        self.connection.commit()
        return {"queued_jobs": self.job_repository.stats()}

    def reindex_path(self, path: str) -> dict:
        normalized = str(Path(path).expanduser().resolve(strict=False))
        event = JobType.UPSERT if Path(normalized).exists() else JobType.DELETE
        self.job_repository.enqueue(event, normalized, folder_id=self.folder_repository.get_id_for_path(normalized))
        self.connection.commit()
        return {"queued": normalized, "event_type": event.value}

    def reindex_folder(self, path: str) -> dict:
        root = Path(path).expanduser().resolve(strict=False)
        count = 0
        for candidate in root.rglob("*"):
            if candidate.is_file() and candidate.suffix.lower() in SUPPORTED_EXTENSIONS:
                self.job_repository.enqueue(
                    JobType.UPSERT,
                    str(candidate.resolve()),
                    folder_id=self.folder_repository.get_id_for_path(str(candidate.resolve())),
                )
                count += 1
        self.connection.commit()
        return {"queued_documents": count, "folder": str(root)}

    def rebuild_fts(self) -> dict:
        self.connection.execute("DELETE FROM documents_fts")
        rows = self.connection.execute("SELECT id, file_name, path, raw_text FROM documents").fetchall()
        for row in rows:
            self.connection.execute(
                "INSERT INTO documents_fts(document_id, file_name, path, content) VALUES (?, ?, ?, ?)",
                (row["id"], row["file_name"], row["path"], row["raw_text"]),
            )
        self.connection.commit()
        return {"rebuilt_documents": len(rows)}

    def audit(self) -> dict:
        sqlite_chunk_ids = {
            row["id"] for row in self.connection.execute("SELECT id FROM document_chunks").fetchall()
        }
        vector_payload = self.embedding_service.collection.get(include=[])
        vector_chunk_ids = set(vector_payload.get("ids", []))
        missing_vectors = sorted(sqlite_chunk_ids - vector_chunk_ids)
        stale_vectors = sorted(vector_chunk_ids - sqlite_chunk_ids)

        doc_rows = self.connection.execute("SELECT id FROM documents").fetchall()
        documents_without_chunks = []
        for row in doc_rows:
            has_chunk = self.connection.execute(
                "SELECT 1 FROM document_chunks WHERE document_id = ? LIMIT 1",
                (row["id"],),
            ).fetchone()
            if has_chunk is None:
                documents_without_chunks.append(row["id"])

        report = {
            "missing_vectors": missing_vectors,
            "stale_vectors": stale_vectors,
            "documents_without_chunks": documents_without_chunks,
        }
        self.metrics_repository.set("last_audit", report)
        self.connection.commit()
        return report

    def close(self) -> None:
        self.connection.close()

    def format_report(self, report: dict) -> str:
        return json.dumps(report, indent=2, sort_keys=True)
