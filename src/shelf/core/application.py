from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass

from shelf.core.models import AppSettings
from shelf.core.maintenance import MaintenanceService
from shelf.core.services import ServiceContainer
from shelf.indexing.embedding import EmbeddingService
from shelf.indexing.reconcile import ReconciliationService
from shelf.indexing.watcher import WatcherService
from shelf.indexing.worker import IndexingWorker, WorkerLoop
from shelf.search.service import SearchService
from shelf.storage.database import Database
from shelf.storage.repositories import (
    DocumentRepository,
    FailureRepository,
    FolderRepository,
    JobRepository,
    MetricsRepository,
    ScannerStateRepository,
)


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class AppStatus:
    indexed_documents: int
    queued_jobs: int
    recent_failures: int
    embedding_model: str
    monitored_folders: int
    accessible_folders: int
    last_reconciliation: str | None


@dataclass(slots=True)
class FailureRecord:
    scope: str
    message: str
    detail: str | None
    ref_id: str | None
    created_at: str


class ShelfApplication:
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
        self.scanner_state = ScannerStateRepository(self.connection)
        self.metrics_repository = MetricsRepository(self.connection)
        self.embedding_service = EmbeddingService(services.paths)
        self.search_service = SearchService(self.database, self.embedding_service)
        self.worker = IndexingWorker(self.database, self.embedding_service)
        self.worker_loop = WorkerLoop(self.worker, max_parallelism=1)
        self.watcher = WatcherService(self.database)
        self.reconciliation = ReconciliationService(
            self.folder_repository,
            self.document_repository,
            self.job_repository,
            self.scanner_state,
            set(self.settings.enabled_extensions),
        )

    def start(self) -> None:
        self.sync_settings()
        self.reconciliation.supported_extensions = set(self.settings.enabled_extensions)
        self.reconciliation.run()
        self.connection.commit()
        self.worker_loop.start()
        self.watcher.refresh_with_extensions(
            [folder.path for folder in self.settings.monitored_folders if folder.accessible],
            set(self.settings.enabled_extensions),
        )
        LOGGER.info("Shelf services started")

    def stop(self) -> None:
        self.watcher.stop()
        self.worker_loop.stop()
        self.connection.close()
        LOGGER.info("Shelf services stopped")

    def sync_settings(self) -> None:
        self.folder_repository.sync(self.settings.monitored_folders)
        self.connection.commit()

    def refresh_folders(self, settings: AppSettings) -> None:
        self.settings = settings
        self.sync_settings()
        self.reconciliation.supported_extensions = set(self.settings.enabled_extensions)
        self.reconciliation.run()
        self.connection.commit()
        self.watcher.refresh_with_extensions(
            [folder.path for folder in self.settings.monitored_folders if folder.accessible],
            set(self.settings.enabled_extensions),
        )

    def search(self, query: str):
        return self.search_service.search(query)

    def live_search(self, query: str, limit: int = 8):
        return self.search_service.exact_search(query, limit=limit)

    def status(self) -> AppStatus:
        with self.database.connect() as connection:
            document_count = connection.execute("SELECT COUNT(*) AS total FROM documents").fetchone()["total"]
            job_stats = JobRepository(connection).stats()
            failure_count = connection.execute("SELECT COUNT(*) AS total FROM failures").fetchone()["total"]
            last_reconciliation = ScannerStateRepository(connection).get("last_reconciliation")
        embedder = self.embedding_service._embedder
        return AppStatus(
            indexed_documents=document_count,
            queued_jobs=job_stats.get("PENDING", 0) + job_stats.get("PROCESSING", 0),
            recent_failures=failure_count,
            embedding_model=embedder.model_name if embedder is not None else "warming-up",
            monitored_folders=len(self.settings.monitored_folders),
            accessible_folders=sum(1 for folder in self.settings.monitored_folders if folder.accessible),
            last_reconciliation=last_reconciliation,
        )

    def recent_failures(self, limit: int = 20) -> list[FailureRecord]:
        with self.database.connect() as connection:
            rows = FailureRepository(connection).list_recent(limit)
        return [
            FailureRecord(
                scope=str(row["scope"]),
                message=str(row["message"]),
                detail=str(row["detail"]) if row["detail"] is not None else None,
                ref_id=str(row["ref_id"]) if row["ref_id"] is not None else None,
                created_at=str(row["created_at"]),
            )
            for row in rows
        ]

    def run_maintenance(self, command: str, path: str | None = None) -> dict:
        maintenance = MaintenanceService(self.services, self.settings)
        maintenance.sync_settings()
        try:
            if command == "status":
                return maintenance.metrics_snapshot()
            if command == "audit":
                return maintenance.audit()
            if command == "rebuild-all":
                return maintenance.rebuild_all()
            if command == "rebuild-fts":
                return maintenance.rebuild_fts()
            if command == "reindex-path":
                if not path:
                    raise ValueError("A file path is required for reindex-path.")
                return maintenance.reindex_path(path)
            if command == "reindex-folder":
                if not path:
                    raise ValueError("A folder path is required for reindex-folder.")
                return maintenance.reindex_folder(path)
        finally:
            maintenance.close()
        raise ValueError(f"Unsupported maintenance command: {command}")

    def open_file(self, path: str) -> None:
        subprocess.run(["open", path], check=False)

    def open_in_preview(self, path: str) -> None:
        subprocess.run(["open", "-a", "Preview", path], check=False)

    def reveal_file(self, path: str) -> None:
        subprocess.run(["open", "-R", path], check=False)
