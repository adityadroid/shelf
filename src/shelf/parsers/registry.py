from __future__ import annotations

from pathlib import Path

from shelf.indexing.models import ParsedDocument, ParserStatus
from shelf.parsers.base import DocumentParser
from shelf.parsers.doc_parser import DocParser
from shelf.parsers.docx_parser import DocxParser
from shelf.parsers.pdf_parser import PdfParser
from shelf.parsers.text_parser import TextParser


class ParserRegistry:
    def __init__(self) -> None:
        self._parsers: dict[str, DocumentParser] = {
            ".pdf": PdfParser(),
            ".docx": DocxParser(),
            ".doc": DocParser(),
            ".txt": TextParser(),
            ".md": TextParser(),
            ".markdown": TextParser(),
        }

    def get(self, extension: str) -> DocumentParser | None:
        return self._parsers.get(extension.lower())

    def parse(self, path: Path) -> ParsedDocument:
        parser = self.get(path.suffix)
        if parser is None:
            stats = path.stat()
            return ParsedDocument(
                path=str(path),
                file_name=path.name,
                extension=path.suffix.lower(),
                size_bytes=stats.st_size,
                ctime=stats.st_ctime,
                mtime=stats.st_mtime,
                parser_type="unsupported",
                parser_status=ParserStatus.UNSUPPORTED,
                raw_text="",
                diagnostics=[f"Unsupported extension: {path.suffix}"],
            )
        return parser.parse(path)
