from __future__ import annotations

import hashlib
from dataclasses import dataclass

from shelf.indexing.models import ChunkRecord, DocumentSection, ParsedDocument


CHUNK_SCHEMA_VERSION = "v1"


@dataclass(slots=True)
class ChunkingPolicy:
    target_size: int = 700
    overlap: int = 100


class DeterministicChunker:
    def __init__(self, policy: ChunkingPolicy | None = None) -> None:
        self.policy = policy or ChunkingPolicy()

    def chunk(self, document_id: str, parsed: ParsedDocument) -> list[ChunkRecord]:
        source_text = parsed.sections or [DocumentSection(source_ref=None, text=parsed.raw_text)]
        chunks: list[ChunkRecord] = []
        chunk_index = 0
        absolute_offset = 0

        for section in source_text:
            paragraphs = [part.strip() for part in section.text.split("\n") if part.strip()]
            if not paragraphs:
                absolute_offset += len(section.text)
                continue

            current = ""
            current_start = absolute_offset
            for paragraph in paragraphs:
                addition = paragraph if not current else f"{current}\n\n{paragraph}"
                if current and len(addition) > self.policy.target_size:
                    chunks.append(
                        self._make_chunk(
                            document_id=document_id,
                            chunk_index=chunk_index,
                            text=current,
                            start_char=current_start,
                            source_ref=section.source_ref,
                        )
                    )
                    chunk_index += 1
                    overlap_text = current[-self.policy.overlap :] if self.policy.overlap else ""
                    current = overlap_text + ("\n\n" if overlap_text else "") + paragraph
                    current_start = max(0, absolute_offset - len(overlap_text))
                else:
                    current = addition
                absolute_offset += len(paragraph) + 2

            if current:
                chunks.append(
                    self._make_chunk(
                        document_id=document_id,
                        chunk_index=chunk_index,
                        text=current,
                        start_char=current_start,
                        source_ref=section.source_ref,
                    )
                )
                chunk_index += 1

        return chunks

    def _make_chunk(
        self,
        *,
        document_id: str,
        chunk_index: int,
        text: str,
        start_char: int,
        source_ref: str | None,
    ) -> ChunkRecord:
        checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()
        chunk_id = hashlib.sha256(f"{document_id}:{chunk_index}:{checksum}".encode("utf-8")).hexdigest()
        return ChunkRecord(
            chunk_id=chunk_id,
            document_id=document_id,
            chunk_index=chunk_index,
            text=text,
            start_char=start_char,
            end_char=start_char + len(text),
            source_ref=source_ref,
            checksum=checksum,
        )
