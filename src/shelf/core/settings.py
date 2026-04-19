from __future__ import annotations

import json
import logging
from dataclasses import asdict

from shelf.core.folders import build_default_folders
from shelf.core.models import AppSettings, MonitoredFolder
from shelf.core.paths import AppPaths


LOGGER = logging.getLogger(__name__)
SETTINGS_SCHEMA_VERSION = 1


class SettingsService:
    def __init__(self, paths: AppPaths) -> None:
        self.paths = paths

    def load(self) -> AppSettings:
        self.paths.ensure()
        if not self.paths.settings_file.exists():
            settings = AppSettings(
                schema_version=SETTINGS_SCHEMA_VERSION,
                onboarding_completed=False,
                monitored_folders=build_default_folders(),
            )
            self.save(settings)
            return settings

        try:
            payload = json.loads(self.paths.settings_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            LOGGER.exception("Failed to load settings, falling back to defaults: %s", exc)
            settings = AppSettings(
                schema_version=SETTINGS_SCHEMA_VERSION,
                onboarding_completed=False,
                monitored_folders=build_default_folders(),
                last_error="Settings file was invalid and has been reset.",
            )
            self.save(settings)
            return settings

        folders = [
            MonitoredFolder(
                path=item["path"],
                source=item.get("source", "user"),
                accessible=item.get("accessible", True),
            )
            for item in payload.get("monitored_folders", [])
        ]
        if not folders:
            folders = build_default_folders()

        return AppSettings(
            schema_version=payload.get("schema_version", SETTINGS_SCHEMA_VERSION),
            onboarding_completed=payload.get("onboarding_completed", False),
            monitored_folders=folders,
            last_error=payload.get("last_error"),
        )

    def save(self, settings: AppSettings) -> None:
        self.paths.ensure()
        payload = asdict(settings)
        self.paths.settings_file.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
