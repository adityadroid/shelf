from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from shelf.core.models import MonitoredFolder


DEFAULT_FOLDERS = ("~/Documents", "~/Downloads", "~/Desktop")


@dataclass(slots=True, frozen=True)
class FolderValidationResult:
    accepted: bool
    normalized_path: str | None = None
    message: str | None = None


def normalize_folder_path(raw_path: str | Path) -> str:
    path = Path(raw_path).expanduser()
    return str(path.resolve(strict=False))


def build_default_folders() -> list[MonitoredFolder]:
    folders: list[MonitoredFolder] = []
    for raw_path in DEFAULT_FOLDERS:
        normalized = normalize_folder_path(raw_path)
        folders.append(
            MonitoredFolder(
                path=normalized,
                source="default",
                accessible=Path(normalized).exists(),
            )
        )
    return folders


def validate_folder_candidate(
    raw_path: str | Path,
    existing: list[MonitoredFolder],
) -> FolderValidationResult:
    normalized = normalize_folder_path(raw_path)
    candidate = Path(normalized)

    if not candidate.exists():
        return FolderValidationResult(False, normalized, "Folder does not exist.")
    if not candidate.is_dir():
        return FolderValidationResult(False, normalized, "Path is not a folder.")

    for folder in existing:
        current = Path(folder.path)
        if candidate == current:
            return FolderValidationResult(False, normalized, "Folder is already monitored.")
        if candidate in current.parents:
            return FolderValidationResult(
                False,
                normalized,
                "A child folder is already monitored. Remove it before adding the parent.",
            )
        if current in candidate.parents:
            return FolderValidationResult(
                False,
                normalized,
                "This folder is already covered by an existing parent folder.",
            )

    return FolderValidationResult(True, normalized, None)


def remove_folder_by_path(folders: list[MonitoredFolder], raw_path: str | Path) -> list[MonitoredFolder]:
    normalized = normalize_folder_path(raw_path)
    return [folder for folder in folders if folder.path != normalized]
