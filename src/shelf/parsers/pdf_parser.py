from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from shelf.indexing.models import DocumentSection, ParsedDocument, ParserStatus
from shelf.parsers.base import DocumentParser


class PdfParser(DocumentParser):
    parser_type = "pypdf"

    def parse(self, path: Path) -> ParsedDocument:
        stats = path.stat()
        diagnostics: list[str] = []
        text_parts: list[str] = []
        sections: list[DocumentSection] = []
        page_count = 0

        try:
            reader = PdfReader(str(path))
            page_count = len(reader.pages)
            for index, page in enumerate(reader.pages, start=1):
                page_text = (page.extract_text() or "").strip()
                if page_text:
                    text_parts.append(page_text)
                    sections.append(DocumentSection(source_ref=f"page:{index}", text=page_text))
            if not text_parts:
                diagnostics.append("No extractable text found in PDF.")
                status = ParserStatus.NO_TEXT
            else:
                status = ParserStatus.SUCCESS
        except Exception as exc:
            diagnostics.append(str(exc))
            status = ParserStatus.FAILURE

        raw_text = "\n\n".join(text_parts)
        return ParsedDocument(
            path=str(path),
            file_name=path.name,
            extension=path.suffix.lower(),
            size_bytes=stats.st_size,
            ctime=stats.st_ctime,
            mtime=stats.st_mtime,
            parser_type=self.parser_type,
            parser_status=status,
            raw_text=raw_text,
            page_count=page_count or None,
            diagnostics=diagnostics,
            sections=sections,
        )
