from __future__ import annotations

from pathlib import Path

from docx import Document

from shelf.core.models import AppSettings, MonitoredFolder
from shelf.core.services import build_services
from shelf.core.maintenance import MaintenanceService


def create_docx(path: Path, text: str) -> None:
    document = Document()
    document.add_paragraph(text)
    document.save(path)


def test_maintenance_reindex_and_audit(tmp_path):
    monitored = tmp_path / "monitored"
    monitored.mkdir()
    create_docx(monitored / "example.docx", "maintenance content")

    services = build_services(root_override=str(tmp_path / "support"))
    settings = AppSettings(
        onboarding_completed=True,
        monitored_folders=[MonitoredFolder(path=str(monitored.resolve()), source="default", accessible=True)],
    )
    maintenance = MaintenanceService(services, settings)
    maintenance.sync_settings()

    queued = maintenance.reindex_folder(str(monitored))
    audit = maintenance.audit()

    assert queued["queued_documents"] == 1
    assert "missing_vectors" in audit
    maintenance.close()
