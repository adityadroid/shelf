from __future__ import annotations

from pathlib import Path

from shelf.indexing.models import DocumentSection, ParsedDocument, ParserStatus
from shelf.parsers.base import DocumentParser


class TextParser(DocumentParser):
    parser_type = "text"

    def parse(self, path: Path) -> ParsedDocument:
        stats = path.stat()
        diagnostics: list[str] = []
        raw_bytes = path.read_bytes()
        text = ""
        for encoding in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                text = raw_bytes.decode(encoding)
                if encoding != "utf-8":
                    diagnostics.append(f"Decoded using {encoding}.")
                break
            except UnicodeDecodeError:
                continue

        normalized = text.strip()
        status = ParserStatus.SUCCESS if normalized else ParserStatus.NO_TEXT
        sections = [DocumentSection(source_ref=None, text=normalized)] if normalized else []
        return ParsedDocument(
            path=str(path),
            file_name=path.name,
            extension=path.suffix.lower(),
            size_bytes=stats.st_size,
            ctime=stats.st_ctime,
            mtime=stats.st_mtime,
            parser_type=self.parser_type,
            parser_status=status,
            raw_text=normalized,
            diagnostics=diagnostics,
            sections=sections,
        )
