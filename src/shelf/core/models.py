from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


SUPPORTED_EXTENSIONS = (".pdf", ".doc", ".docx")
DEFAULT_LAUNCH_SHORTCUT = "Meta+Alt+S"


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
    launcher_shortcut: str = DEFAULT_LAUNCH_SHORTCUT
    last_error: str | None = None
