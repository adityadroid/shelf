from __future__ import annotations

from shelf.indexing.chunking import DeterministicChunker
from shelf.indexing.models import ParsedDocument, ParserStatus


def test_chunking_is_deterministic():
    parsed = ParsedDocument(
        path="/tmp/demo.pdf",
        file_name="demo.pdf",
        extension=".pdf",
        size_bytes=20,
        ctime=1.0,
        mtime=2.0,
        parser_type="test",
        parser_status=ParserStatus.SUCCESS,
        raw_text="Paragraph one.\n\nParagraph two.\n\nParagraph three.",
    )
    chunker = DeterministicChunker()

    first = chunker.chunk("doc-1", parsed)
    second = chunker.chunk("doc-1", parsed)

    assert [chunk.chunk_id for chunk in first] == [chunk.chunk_id for chunk in second]
    assert first[0].text == second[0].text
