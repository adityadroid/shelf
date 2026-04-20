from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from shelf.indexing.models import ParsedDocument


class DocumentParser(ABC):
    parser_type = "base"

    @abstractmethod
    def parse(self, path: Path) -> ParsedDocument:
        raise NotImplementedError

