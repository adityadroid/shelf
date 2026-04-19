from __future__ import annotations

from shelf.core.models import MonitoredFolder
from shelf.core.paths import AppPaths
from shelf.indexing.models import JobStatus, JobType, ParsedDocument, ParserStatus
from shelf.storage.database import Database
from shelf.storage.repositories import (
    DocumentRepository,
    FolderRepository,
    JobRepository,
    new_document_id,
)


def test_database_initializes_schema(tmp_path):
    database = Database(AppPaths.discover(root_override=tmp_path))
    database.initialize()

    connection = database.connect()
    tables = {
        row["name"]
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view')")
    }

    assert "folders" in tables
    assert "documents" in tables
    assert "jobs" in tables
    assert "documents_fts" in tables


def test_job_repository_claim_and_retry(tmp_path):
    database = Database(AppPaths.discover(root_override=tmp_path))
    database.initialize()
    connection = database.connect()
    jobs = JobRepository(connection)

    jobs.enqueue(JobType.UPSERT, "/tmp/example.pdf")
    claimed = jobs.claim_next()

    assert claimed is not None
    assert claimed["status"] == JobStatus.PROCESSING.value

    jobs.mark_failed(int(claimed["id"]), "boom", 1)
    row = connection.execute("SELECT * FROM jobs WHERE id = ?", (claimed["id"],)).fetchone()
    assert row["status"] == JobStatus.PENDING.value
    assert row["attempt_count"] == 1


def test_document_upsert_updates_fts(tmp_path):
    database = Database(AppPaths.discover(root_override=tmp_path))
    database.initialize()
    connection = database.connect()
    folders = FolderRepository(connection)
    folders.sync([MonitoredFolder(path=str(tmp_path), source="default", accessible=True)])

    documents = DocumentRepository(connection)
    document_id = new_document_id()
    parsed = ParsedDocument(
        path=str(tmp_path / "sample.pdf"),
        file_name="sample.pdf",
        extension=".pdf",
        size_bytes=10,
        ctime=1.0,
        mtime=2.0,
        parser_type="test",
        parser_status=ParserStatus.SUCCESS,
        raw_text="alpha beta gamma",
    )

    documents.upsert_document(
        document_id=document_id,
        folder_id=folders.get_id_for_path(parsed.path),
        parsed=parsed,
        fast_fingerprint="fp",
        content_hash="hash",
        chunk_schema_version="v1",
    )

    fts_row = connection.execute("SELECT content FROM documents_fts WHERE document_id = ?", (document_id,)).fetchone()
    assert fts_row["content"] == "alpha beta gamma"
