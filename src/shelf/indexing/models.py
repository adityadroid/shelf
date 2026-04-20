from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class JobType(StrEnum):
    UPSERT = "UPSERT"
    DELETE = "DELETE"
    MOVE = "MOVE"


class JobStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    FAILED = "FAILED"


class ParserStatus(StrEnum):
    SUCCESS = "SUCCESS"
    NO_TEXT = "NO_TEXT"
    PARTIAL = "PARTIAL"
    UNSUPPORTED = "UNSUPPORTED"
    FAILURE = "FAILURE"


@dataclass(slots=True)
class DocumentSection:
    source_ref: str | None
    text: str


@dataclass(slots=True)
class ParsedDocument:
    path: str
    file_name: str
    extension: str
    size_bytes: int
    ctime: float
    mtime: float
    parser_type: str
    parser_status: ParserStatus
    raw_text: str
    page_count: int | None = None
    diagnostics: list[str] = field(default_factory=list)
    sections: list[DocumentSection] = field(default_factory=list)


@dataclass(slots=True)
class ChunkRecord:
    chunk_id: str
    document_id: str
    chunk_index: int
    text: str
    start_char: int
    end_char: int
    source_ref: str | None
    checksum: str


@dataclass(slots=True)
class SearchResult:
    document_id: str
    path: str
    file_name: str
    extension: str
    snippet: str
    modified_at: float
    score: float
    source: str

