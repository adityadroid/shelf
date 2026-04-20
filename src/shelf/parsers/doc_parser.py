from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from shelf.indexing.models import DocumentSection, ParsedDocument, ParserStatus
from shelf.parsers.base import DocumentParser


class DocParser(DocumentParser):
    parser_type = "antiword"

    def __init__(self, timeout_seconds: int = 10) -> None:
        self.timeout_seconds = timeout_seconds

    def parse(self, path: Path) -> ParsedDocument:
        stats = path.stat()
        diagnostics: list[str] = []
        sections: list[DocumentSection] = []

        antiword = shutil.which("antiword")
        if antiword is None:
            diagnostics.append("antiword is not installed.")
            return ParsedDocument(
                path=str(path),
                file_name=path.name,
                extension=path.suffix.lower(),
                size_bytes=stats.st_size,
                ctime=stats.st_ctime,
                mtime=stats.st_mtime,
                parser_type=self.parser_type,
                parser_status=ParserStatus.FAILURE,
                raw_text="",
                diagnostics=diagnostics,
                sections=sections,
            )

        try:
            completed = subprocess.run(
                [antiword, str(path)],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            diagnostics.append("antiword timed out while parsing the document.")
            status = ParserStatus.FAILURE
            raw_text = ""
        else:
            raw_text = completed.stdout.strip()
            if completed.returncode != 0:
                diagnostics.append(completed.stderr.strip() or "antiword failed.")
                status = ParserStatus.FAILURE
            elif not raw_text:
                diagnostics.append("No readable text found in DOC.")
                status = ParserStatus.NO_TEXT
            else:
                status = ParserStatus.SUCCESS
                sections.append(DocumentSection(source_ref="body", text=raw_text))

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
            diagnostics=diagnostics,
            sections=sections,
        )
