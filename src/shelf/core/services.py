from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from shelf.core.paths import AppPaths
from shelf.core.settings import SettingsService


@dataclass(slots=True)
class ServiceContainer:
    paths: AppPaths
    settings: SettingsService


def build_services(root_override: str | None = None) -> ServiceContainer:
    paths = AppPaths.discover(root_override=Path(root_override) if root_override else None)
    settings = SettingsService(paths)
    return ServiceContainer(paths=paths, settings=settings)
