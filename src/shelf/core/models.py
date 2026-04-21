from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


DOCUMENT_TYPE_LABELS: dict[str, str] = {
    ".pdf": "PDF documents",
    ".doc": "Word .doc",
    ".docx": "Word .docx",
    ".txt": "Plain text",
    ".md": "Markdown (.md)",
    ".markdown": "Markdown (.markdown)",
}
SUPPORTED_EXTENSIONS = tuple(DOCUMENT_TYPE_LABELS)
DEFAULT_ENABLED_EXTENSIONS = SUPPORTED_EXTENSIONS
DEFAULT_LAUNCH_SHORTCUT = "Meta+Alt+S"


def normalize_enabled_extensions(values: list[str] | tuple[str, ...] | None) -> list[str]:
    if not values:
        return list(DEFAULT_ENABLED_EXTENSIONS)
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        extension = value.lower().strip()
        if not extension.startswith("."):
            extension = f".{extension}"
        if extension in DOCUMENT_TYPE_LABELS and extension not in seen:
            normalized.append(extension)
            seen.add(extension)
    return normalized or list(DEFAULT_ENABLED_EXTENSIONS)


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
    enabled_extensions: list[str] = field(default_factory=lambda: list(DEFAULT_ENABLED_EXTENSIONS))
    launcher_shortcut: str = DEFAULT_LAUNCH_SHORTCUT
    last_error: str | None = None
