from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass

from shelf.core.models import AppSettings
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
        )

    def start(self) -> None:
        self.sync_settings()
        self.reconciliation.run()
        self.connection.commit()
        self.worker_loop.start()
        self.watcher.refresh([folder.path for folder in self.settings.monitored_folders if folder.accessible])
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
        self.reconciliation.run()
        self.connection.commit()
        self.watcher.refresh([folder.path for folder in self.settings.monitored_folders if folder.accessible])

    def search(self, query: str):
        return self.search_service.search(query)

    def status(self) -> AppStatus:
        with self.database.connect() as connection:
            document_count = connection.execute("SELECT COUNT(*) AS total FROM documents").fetchone()["total"]
            job_stats = JobRepository(connection).stats()
            failure_count = connection.execute("SELECT COUNT(*) AS total FROM failures").fetchone()["total"]
        embedder = self.embedding_service._embedder
        return AppStatus(
            indexed_documents=document_count,
            queued_jobs=job_stats.get("PENDING", 0) + job_stats.get("PROCESSING", 0),
            recent_failures=failure_count,
            embedding_model=embedder.model_name if embedder is not None else "warming-up",
        )

    def recent_failures(self) -> list[str]:
        with self.database.connect() as connection:
            return [row["message"] for row in FailureRepository(connection).list_recent()]

    def open_file(self, path: str) -> None:
        subprocess.run(["open", path], check=False)

    def reveal_file(self, path: str) -> None:
        subprocess.run(["open", "-R", path], check=False)
