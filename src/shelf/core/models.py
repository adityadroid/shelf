from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


SUPPORTED_EXTENSIONS = (".pdf", ".doc", ".docx")


@dataclass(slots=True, frozen=True)
class MonitoredFolder:
    path: str
    source: str = "user"
    accessible: bool = True

    @property
    def path_obj(self) -> Path:
        return Path(self.path)


@dataclass(slots=True)
class AppSettings:
    schema_version: int = 1
    onboarding_completed: bool = False
    monitored_folders: list[MonitoredFolder] = field(default_factory=list)
    last_error: str | None = None

