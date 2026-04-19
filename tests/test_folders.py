from __future__ import annotations

from pathlib import Path

from shelf.core.folders import normalize_folder_path, validate_folder_candidate
from shelf.core.models import MonitoredFolder


def test_normalize_folder_path(tmp_path):
    raw = tmp_path / ".." / tmp_path.name
    assert normalize_folder_path(raw) == str(tmp_path.resolve())


def test_validate_duplicate_folder(tmp_path):
    folder = tmp_path / "docs"
    folder.mkdir()
    existing = [MonitoredFolder(path=str(folder.resolve()))]

    result = validate_folder_candidate(folder, existing)

    assert result.accepted is False
    assert "already monitored" in (result.message or "")


def test_validate_parent_child_overlap(tmp_path):
    parent = tmp_path / "parent"
    child = parent / "child"
    child.mkdir(parents=True)

    result = validate_folder_candidate(parent, [MonitoredFolder(path=str(child.resolve()))])

    assert result.accepted is False
    assert "child folder" in (result.message or "")
