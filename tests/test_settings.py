from __future__ import annotations

import json

from shelf.core.models import DEFAULT_ENABLED_EXTENSIONS, DEFAULT_LAUNCH_SHORTCUT
from shelf.core.settings import SettingsService
from shelf.core.paths import AppPaths


def test_settings_create_defaults(tmp_path):
    paths = AppPaths.discover(root_override=tmp_path)
    service = SettingsService(paths)

    settings = service.load()

    assert settings.onboarding_completed is False
    assert len(settings.monitored_folders) == 3
    assert settings.launcher_shortcut == DEFAULT_LAUNCH_SHORTCUT
    assert settings.enabled_extensions == list(DEFAULT_ENABLED_EXTENSIONS)
    assert paths.settings_file.exists()


def test_settings_round_trip(tmp_path):
    paths = AppPaths.discover(root_override=tmp_path)
    service = SettingsService(paths)
    settings = service.load()
    settings.onboarding_completed = True
    settings.launcher_shortcut = "Meta+Shift+Space"
    settings.enabled_extensions = [".pdf", ".txt", ".md"]

    service.save(settings)
    reloaded = service.load()

    assert reloaded.onboarding_completed is True
    assert reloaded.launcher_shortcut == "Meta+Shift+Space"
    assert reloaded.enabled_extensions == [".pdf", ".txt", ".md"]
    assert [folder.path for folder in reloaded.monitored_folders] == [
        folder.path for folder in settings.monitored_folders
    ]


def test_settings_invalid_json_recovers(tmp_path):
    paths = AppPaths.discover(root_override=tmp_path)
    paths.ensure()
    paths.settings_file.write_text("{oops", encoding="utf-8")

    settings = SettingsService(paths).load()
    payload = json.loads(paths.settings_file.read_text(encoding="utf-8"))

    assert settings.last_error is not None
    assert payload["last_error"] == settings.last_error
