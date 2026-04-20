from __future__ import annotations

from types import SimpleNamespace

from PySide6.QtCore import Qt

from shelf.core.application import AppStatus, FailureRecord
from shelf.core.models import AppSettings, MonitoredFolder
from shelf.indexing.models import SearchResult
from shelf.ui.main_window import MainWindow, SettingsDialog


class StubSettingsService:
    def __init__(self) -> None:
        self.saved_settings: list[AppSettings] = []

    def save(self, settings: AppSettings) -> None:
        self.saved_settings.append(settings)


class StubController:
    def __init__(self) -> None:
        self.search_queries: list[str] = []
        self.opened_paths: list[str] = []
        self.revealed_paths: list[str] = []
        self.maintenance_calls: list[tuple[str, str | None]] = []
        self.refreshed_settings: list[AppSettings] = []

    def search(self, query: str) -> list[SearchResult]:
        self.search_queries.append(query)
        return [
            SearchResult(
                document_id="doc-1",
                path="/tmp/alpha-report.pdf",
                file_name="alpha-report.pdf",
                extension=".pdf",
                snippet="project alpha roadmap",
                modified_at=1713517200.0,
                score=1.0,
                source="fts",
            )
        ]

    def open_file(self, path: str) -> None:
        self.opened_paths.append(path)

    def reveal_file(self, path: str) -> None:
        self.revealed_paths.append(path)

    def run_maintenance(self, command: str, path: str | None = None) -> dict:
        self.maintenance_calls.append((command, path))
        return {"command": command, "path": path}

    def refresh_folders(self, settings: AppSettings) -> None:
        self.refreshed_settings.append(settings)

    def status(self) -> AppStatus:
        return AppStatus(
            indexed_documents=12,
            queued_jobs=2,
            recent_failures=1,
            embedding_model="test-model",
            monitored_folders=2,
            accessible_folders=2,
            last_reconciliation="2026-04-19T18:20:00+05:30",
        )

    def recent_failures(self, limit: int = 20) -> list[FailureRecord]:
        return [
            FailureRecord(
                scope="parser",
                message="Could not extract text",
                detail=None,
                ref_id="/tmp/alpha-report.pdf",
                created_at="2026-04-19T18:10:00+05:30",
            )
        ]


def build_services_stub() -> SimpleNamespace:
    return SimpleNamespace(
        settings=StubSettingsService(),
        paths=SimpleNamespace(
            root="/tmp/shelf",
            settings_file="/tmp/shelf/settings.json",
            database_file="/tmp/shelf/db.sqlite3",
        ),
    )


def test_main_window_is_search_first_and_opens_results(qtbot):
    services = build_services_stub()
    settings = AppSettings(
        onboarding_completed=True,
        monitored_folders=[
            MonitoredFolder(path="/tmp/Documents", source="default", accessible=True),
            MonitoredFolder(path="/tmp/Downloads", source="default", accessible=True),
        ],
    )
    controller = StubController()

    window = MainWindow(services, settings, controller)
    qtbot.addWidget(window)

    assert window.search_input.placeholderText() == "Search filenames and document text"
    assert window.results_count_label.text() == "Waiting for a search"

    window.search_input.setText("alpha")
    qtbot.wait(250)

    assert controller.search_queries[-1] == "alpha"
    assert len(window.result_cards) == 1
    assert window.results_count_label.text() == '1 results for "alpha"'

    qtbot.mouseClick(window.result_cards[0], Qt.MouseButton.LeftButton)
    assert controller.opened_paths == ["/tmp/alpha-report.pdf"]


def test_settings_dialog_surfaces_maintenance_commands(qtbot):
    services = build_services_stub()
    settings = AppSettings(
        onboarding_completed=True,
        monitored_folders=[MonitoredFolder(path="/tmp/Documents", source="default", accessible=True)],
    )
    controller = StubController()
    refresh_calls: list[str] = []

    dialog = SettingsDialog(services, settings, controller, lambda: refresh_calls.append("refresh"))
    qtbot.addWidget(dialog)

    assert dialog.windowTitle() == "Shelf Settings"
    assert dialog.folder_list.count() == 1

    dialog.run_command("status")

    assert controller.maintenance_calls == [("status", None)]
    assert '"command": "status"' in dialog.maintenance_output.toPlainText()
    assert refresh_calls == ["refresh"]
