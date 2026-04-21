from __future__ import annotations

from pathlib import Path

from docx import Document

from shelf.core.models import MonitoredFolder
from shelf.core.paths import AppPaths
from shelf.indexing.models import JobType
from shelf.indexing.worker import IndexingWorker
from shelf.storage.database import Database
from shelf.storage.repositories import (
    DocumentRepository,
    FailureRepository,
    FolderRepository,
    JobRepository,
    MetricsRepository,
)


class StubEmbeddingService:
    def upsert_chunks(self, document_id: str, chunks):
        self.last_chunks = list(chunks)
        return ("stub-model", "v1")

    def delete_document(self, document_id: str) -> None:
        self.deleted = document_id


def create_docx(path: Path, text: str) -> None:
    document = Document()
    document.add_paragraph(text)
    document.save(path)


def test_worker_indexes_docx_end_to_end(tmp_path):
    doc_path = tmp_path / "indexed.docx"
    create_docx(doc_path, "worker pipeline content")

    database = Database(AppPaths.discover(root_override=tmp_path / "support"))
    database.initialize()
    connection = database.connect()
    folders = FolderRepository(connection)
    folders.sync([MonitoredFolder(path=str(tmp_path.resolve()), source="default", accessible=True)])
    documents = DocumentRepository(connection)
    jobs = JobRepository(connection)
    failures = FailureRepository(connection)
    metrics = MetricsRepository(connection)
    embedding = StubEmbeddingService()

    jobs.enqueue(JobType.UPSERT, str(doc_path.resolve()), folder_id=folders.get_id_for_path(str(doc_path.resolve())))
    connection.commit()
    worker = IndexingWorker(database, embedding)

    assert worker.process_one() is True
    row = documents.get_by_path(str(doc_path.resolve()))
    assert row is not None
    assert "worker pipeline content" in row["raw_text"]


def test_worker_indexes_text_file_end_to_end(tmp_path):
    doc_path = tmp_path / "indexed.txt"
    doc_path.write_text("worker text pipeline content", encoding="utf-8")

    database = Database(AppPaths.discover(root_override=tmp_path / "support"))
    database.initialize()
    connection = database.connect()
    folders = FolderRepository(connection)
    folders.sync([MonitoredFolder(path=str(tmp_path.resolve()), source="default", accessible=True)])
    documents = DocumentRepository(connection)
    jobs = JobRepository(connection)
    embedding = StubEmbeddingService()

    jobs.enqueue(JobType.UPSERT, str(doc_path.resolve()), folder_id=folders.get_id_for_path(str(doc_path.resolve())))
    connection.commit()
    worker = IndexingWorker(database, embedding)

    assert worker.process_one() is True
    row = documents.get_by_path(str(doc_path.resolve()))
    assert row is not None
    assert "worker text pipeline content" in row["raw_text"]
