from __future__ import annotations

import logging
import threading
import time
from pathlib import Path

from shelf.indexing.chunking import CHUNK_SCHEMA_VERSION, DeterministicChunker
from shelf.indexing.embedding import EmbeddingService
from shelf.indexing.fingerprint import fast_fingerprint, sha256_for_file
from shelf.indexing.models import JobType
from shelf.parsers.registry import ParserRegistry
from shelf.storage.repositories import (
    DocumentRepository,
    FailureRepository,
    FolderRepository,
    JobRepository,
    MetricsRepository,
    new_document_id,
)


LOGGER = logging.getLogger(__name__)


class IndexingWorker:
    def __init__(
        self,
        folder_repository: FolderRepository,
        document_repository: DocumentRepository,
        job_repository: JobRepository,
        failure_repository: FailureRepository,
        metrics_repository: MetricsRepository,
        embedding_service: EmbeddingService,
    ) -> None:
        self.folder_repository = folder_repository
        self.document_repository = document_repository
        self.job_repository = job_repository
        self.failure_repository = failure_repository
        self.metrics_repository = metrics_repository
        self.embedding_service = embedding_service
        self.parsers = ParserRegistry()
        self.chunker = DeterministicChunker()

    def process_one(self) -> bool:
        job = self.job_repository.claim_next()
        if job is None:
            return False

        try:
            event_type = JobType(job["event_type"])
            if event_type is JobType.DELETE:
                self._handle_delete(job["path"])
            elif event_type is JobType.MOVE:
                if job["old_path"]:
                    self._handle_delete(job["old_path"])
                self._handle_upsert(job["path"])
            else:
                self._handle_upsert(job["path"])
        except Exception as exc:
            LOGGER.exception("Job failed: %s", exc)
            self.failure_repository.record("job", str(exc), ref_id=str(job["id"]))
            self.job_repository.mark_failed(job["id"], str(exc), int(job["attempt_count"]) + 1)
            return True

        self.job_repository.mark_done(job["id"])
        self.metrics_repository.set("last_processed_job", job["path"])
        return True

    def _handle_delete(self, path: str) -> None:
        document_id = self.document_repository.delete_by_path(path)
        if document_id:
            self.embedding_service.delete_document(document_id)

    def _handle_upsert(self, path: str) -> None:
        file_path = Path(path)
        if not file_path.exists():
            self._handle_delete(path)
            return

        parser_result = self.parsers.parse(file_path)
        existing = self.document_repository.get_by_path(path)
        current_fast_fingerprint = fast_fingerprint(file_path)
        if existing and existing["fast_fingerprint"] == current_fast_fingerprint:
            return

        content_hash = sha256_for_file(file_path)
        document_id = str(existing["id"]) if existing else new_document_id()
        folder_id = self.folder_repository.get_id_for_path(path)
        chunks = self.chunker.chunk(document_id, parser_result)
        embedding_model, embedding_version = self.embedding_service.upsert_chunks(document_id, chunks)
        self.document_repository.upsert_document(
            document_id=document_id,
            folder_id=folder_id,
            parsed=parser_result,
            fast_fingerprint=current_fast_fingerprint,
            content_hash=content_hash,
            chunk_schema_version=CHUNK_SCHEMA_VERSION,
            embedding_model=embedding_model,
            embedding_version=embedding_version,
        )
        self.document_repository.replace_chunks(document_id, chunks, embedding_model, embedding_version)
        if parser_result.diagnostics:
            self.failure_repository.record(
                "parser",
                "\n".join(parser_result.diagnostics),
                ref_id=document_id,
                detail=parser_result.path,
            )


class WorkerLoop:
    def __init__(self, worker: IndexingWorker, max_parallelism: int = 1) -> None:
        self.worker = worker
        self.max_parallelism = max_parallelism
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []

    def start(self) -> None:
        if self._threads:
            return
        for index in range(self.max_parallelism):
            thread = threading.Thread(target=self._run, name=f"shelf-worker-{index}", daemon=True)
            thread.start()
            self._threads.append(thread)

    def _run(self) -> None:
        while not self._stop.is_set():
            handled = self.worker.process_one()
            if not handled:
                time.sleep(0.5)

    def stop(self) -> None:
        self._stop.set()
        for thread in self._threads:
            thread.join(timeout=5)
        self._threads.clear()
