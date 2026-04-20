from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class AppPaths:
    root: Path
    config_dir: Path
    db_dir: Path
    vectors_dir: Path
    models_dir: Path
    logs_dir: Path
    cache_dir: Path
    settings_file: Path
    database_file: Path

    @classmethod
    def discover(cls, app_name: str = "Shelf", root_override: Path | None = None) -> "AppPaths":
        if root_override is not None:
            root = root_override.expanduser().resolve()
        else:
            root = (
                Path(
                    os.environ.get(
                        "SHELF_APP_SUPPORT_DIR",
                        Path.home() / "Library" / "Application Support" / app_name,
                    )
                )
                .expanduser()
                .resolve()
            )

        config_dir = root / "config"
        db_dir = root / "db"
        vectors_dir = root / "vectors"
        models_dir = root / "models"
        logs_dir = root / "logs"
        cache_dir = root / "cache"
        return cls(
            root=root,
            config_dir=config_dir,
            db_dir=db_dir,
            vectors_dir=vectors_dir,
            models_dir=models_dir,
            logs_dir=logs_dir,
            cache_dir=cache_dir,
            settings_file=config_dir / "settings.json",
            database_file=db_dir / "shelf.sqlite3",
        )

    def ensure(self) -> None:
        for directory in (
            self.root,
            self.config_dir,
            self.db_dir,
            self.vectors_dir,
            self.models_dir,
            self.logs_dir,
            self.cache_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)
