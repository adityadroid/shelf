from __future__ import annotations

from shelf.core.models import MonitoredFolder
from shelf.core.paths import AppPaths
from shelf.indexing.models import ParsedDocument, ParserStatus
from shelf.search.service import SearchService
from shelf.storage.database import Database
from shelf.storage.repositories import DocumentRepository, FolderRepository, new_document_id


class StubEmbeddingService:
    def query(self, query: str, limit: int = 20):
        if "semantic" not in query:
            return []
        return [
            {
                "document_id": self.document_id,
                "document": "semantic snippet",
                "distance": 0.2,
            }
        ]


def test_search_prefers_exact_filename_matches(tmp_path):
    database = Database(AppPaths.discover(root_override=tmp_path))
    database.initialize()
    connection = database.connect()
    folders = FolderRepository(connection)
    folders.sync([MonitoredFolder(path=str(tmp_path), source="default", accessible=True)])
    documents = DocumentRepository(connection)

    parsed = ParsedDocument(
        path=str(tmp_path / "alpha-report.pdf"),
        file_name="alpha-report.pdf",
        extension=".pdf",
        size_bytes=10,
        ctime=1.0,
        mtime=2.0,
        parser_type="test",
        parser_status=ParserStatus.SUCCESS,
        raw_text="project alpha details",
    )
    document_id = new_document_id()
    documents.upsert_document(
        document_id=document_id,
        folder_id=folders.get_id_for_path(parsed.path),
        parsed=parsed,
        fast_fingerprint="fp",
        content_hash="hash",
        chunk_schema_version="v1",
    )
    stub = StubEmbeddingService()
    stub.document_id = document_id

    service = SearchService(connection, stub)
    results = service.search("alpha")

    assert results
    assert results[0].file_name == "alpha-report.pdf"
