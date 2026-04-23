from __future__ import annotations

import time
from types import SimpleNamespace

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QCheckBox, QFrame, QLabel, QKeySequenceEdit, QScrollArea, QSlider, QToolButton

from shelf.core.application import AppStatus, FailureRecord
from shelf.core.models import AppSettings, MonitoredFolder
from shelf.indexing.models import SearchResult
from shelf.ui.main_window import ICON_PATH, MainWindow, SearchResultsDialog, SettingsDialog


class StubSettingsService:
    def __init__(self) -> None:
        self.saved_settings: list[AppSettings] = []

    def save(self, settings: AppSettings) -> None:
        self.saved_settings.append(settings)


class StubController:
    def __init__(self) -> None:
        self.search_queries: list[str] = []
        self.live_search_queries: list[str] = []
        self.opened_paths: list[str] = []
        self.previewed_paths: list[str] = []
        self.revealed_paths: list[str] = []
        self.maintenance_calls: list[tuple[str, str | None]] = []
        self.refreshed_settings: list[AppSettings] = []

    def search(self, query: str) -> list[SearchResult]:
        self.search_queries.append(query)
        return self.live_search(query)

    def live_search(self, query: str) -> list[SearchResult]:
        self.live_search_queries.append(query)
        return [
            SearchResult(
                document_id="doc-1",
                path="/tmp/alpha-report.pdf",
                file_name="apps_0b709200db41a31_ad4bb6b9-04dd-4b67-85ea-0d0f7ea51c7b-full.txt",
                extension=".pdf",
                snippet="project alpha roadmap",
                modified_at=1713517200.0,
                score=1.0,
                source="fts",
            )
        ]

    def open_file(self, path: str) -> None:
        self.opened_paths.append(path)

    def open_in_preview(self, path: str) -> None:
        self.previewed_paths.append(path)

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


class ConsecutiveSearchController(StubController):
    def live_search(self, query: str) -> list[SearchResult]:
        self.live_search_queries.append(query)
        if query == "alpha":
            time.sleep(1.0)
            raise RuntimeError("stale query failed")
        return [
            SearchResult(
                document_id=f"doc-{query}",
                path=f"/tmp/{query}-report.pdf",
                file_name=f"{query}-report.pdf",
                extension=".pdf",
                snippet=f"project {query} roadmap",
                modified_at=1713517200.0,
                score=1.0,
                source="fts",
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


def test_main_window_shows_live_results_popup(qtbot):
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
    window.show()

    assert window.search_input.placeholderText() == "Search documents by title, path, or text"
    assert window.windowTitle() == "Shelf"
    assert window.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert window.statusBar().isHidden()
    settings_button = window.findChild(QToolButton, "SettingsIconButton")
    assert settings_button is not None

    window.search_input.setFocus()
    qtbot.keyClick(window.search_input, "a")
    qtbot.wait(150)
    assert controller.live_search_queries == []
    assert window.search_input.text().startswith("a")
    qtbot.waitUntil(window.search_input.hasFocus)

    window.search_input.setText("alpha")
    qtbot.waitUntil(lambda: controller.live_search_queries == ["alpha"])
    qtbot.waitUntil(lambda: window.results_popup.isVisible())
    qtbot.waitUntil(lambda: len(window.results_popup.result_cards) == 1)
    assert len(window.results_popup.result_cards) == 1
    assert window.search_input.hasFocus()
    assert window.results_popup.width() == window.composer_shell.width()
    assert window.results_popup.result_cards[0].reveal_button.text() == "Reveal"
    assert not window.results_popup.result_cards[0].reveal_button.icon().isNull()
    card = window.results_popup.result_cards[0]
    reveal_right = card.reveal_button.mapTo(window.results_popup.scroll.viewport(), card.reveal_button.rect().topRight()).x()
    assert reveal_right <= window.results_popup.scroll.viewport().width() - window.results_popup.RIGHT_SAFE_INSET
    title_labels = [label for label in card.findChildren(QLabel) if label.objectName() == "ResultTitle"]
    assert title_labels and "\n" in title_labels[0].text()
    path_labels = window.results_popup.result_cards[0].findChildren(QLabel)
    assert any(label.text() == "/tmp" for label in path_labels)

    qtbot.keyClick(window.search_input, Qt.Key.Key_Down)
    assert window.results_popup.selected_index == 0
    assert window.results_popup.result_cards[0].property("active") is True
    qtbot.keyClick(window.search_input, Qt.Key.Key_Return)
    assert controller.previewed_paths == ["/tmp/alpha-report.pdf"]

    window.show_search_window()
    window._handle_window_deactivated()
    assert window.isHidden()

    window.show_search_window()
    window.open_primary_result()
    assert controller.previewed_paths == ["/tmp/alpha-report.pdf", "/tmp/alpha-report.pdf"]
    assert ICON_PATH.exists()

    window.toggle_launcher_window()
    assert window.isHidden()
    window.toggle_launcher_window()
    assert window.isVisible()
    assert window.y() >= 0


def test_live_search_recovers_when_consecutive_query_replaces_failing_search(qtbot):
    services = build_services_stub()
    settings = AppSettings(onboarding_completed=True)
    controller = ConsecutiveSearchController()

    window = MainWindow(services, settings, controller)
    window._live_search_timer.setInterval(40)
    qtbot.addWidget(window)
    window.show()

    window.search_input.setText("alpha")
    qtbot.waitUntil(lambda: controller.live_search_queries == ["alpha"], timeout=1000)
    window.search_input.setText("beta")

    qtbot.waitUntil(lambda: controller.live_search_queries == ["alpha", "beta"], timeout=2000)
    qtbot.waitUntil(lambda: len(window.results_popup.result_cards) == 1, timeout=2000)
    assert window.results_popup.result_cards[0].result.file_name == "beta-report.pdf"
    assert window.results_popup.progress_bar.isHidden()


def test_results_popup_height_tracks_result_count_and_caps_to_available_screen(qtbot):
    controller = StubController()
    parent = QFrame()
    parent.resize(760, 120)
    parent.move(120, 120)
    qtbot.addWidget(parent)
    parent.show()

    dialog = SearchResultsDialog(controller, parent)
    qtbot.addWidget(dialog)

    few_results = [
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
    many_results = [
        SearchResult(
            document_id=f"doc-{index}",
            path=f"/tmp/result-{index}.pdf",
            file_name=f"result-{index}.pdf",
            extension=".pdf",
            snippet="project alpha roadmap",
            modified_at=1713517200.0,
            score=1.0,
            source="fts",
        )
        for index in range(14)
    ]

    dialog.show_for_query(parent, "alpha", few_results)
    qtbot.waitUntil(dialog.isVisible)
    few_height = dialog.height()
    expected_few_height = dialog._desired_height(parent)

    dialog.show_for_query(parent, "alpha", many_results)
    many_height = dialog.height()
    expected_many_height = dialog._desired_height(parent)

    origin = parent.mapToGlobal(QPoint(0, parent.height() + 6))
    screen = parent.screen()
    assert screen is not None
    available_bottom = screen.availableGeometry().bottom() - origin.y() + 1
    max_expected_height = max(dialog.MIN_HEIGHT, available_bottom - dialog.SCREEN_BOTTOM_MARGIN)

    assert few_height == expected_few_height
    assert many_height == expected_many_height
    assert few_height >= dialog.MIN_HEIGHT
    assert many_height > few_height
    assert many_height == max_expected_height


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
    labels = dialog.findChildren(QLabel)
    assert any(label.text() == "SHELF" for label in labels)
    assert dialog.folder_list.count() == 1
    assert dialog.documents_pill.text() == "12 indexed"
    assert dialog.failures_list.count() == 1
    shortcut_input = dialog.findChild(QKeySequenceEdit)
    assert shortcut_input is not None
    assert shortcut_input.keySequence().toString(QKeySequence.SequenceFormat.PortableText) == "Meta+Alt+S"
    transparency_slider = dialog.findChild(QSlider, "TransparencySlider")
    assert transparency_slider is not None
    assert transparency_slider.value() == 96
    dark_toggle = dialog.findChild(QCheckBox, "AppearanceToggle")
    assert dark_toggle is not None
    assert dark_toggle.isChecked() is False

    shortcut_input.setKeySequence(QKeySequence("Meta+Shift+Space"))
    dialog.save_launcher_shortcut()
    assert settings.launcher_shortcut == "Meta+Shift+Space"

    dialog.dark_mode_toggle.setChecked(True)
    dialog.transparency_slider.setValue(84)
    dialog.save_appearance_settings()
    assert settings.dark_mode is True
    assert settings.ui_transparency == 84
    assert dialog.theme_state_label.text() == "Dark surfaces are on"

    dialog.run_command("status")

    assert controller.maintenance_calls == [("status", None)]
    assert '"command": "status"' in dialog.maintenance_output.toPlainText()
    assert refresh_calls == ["refresh", "refresh", "refresh", "refresh"]


def test_settings_dialog_can_resize_and_uses_refined_close_button(qtbot):
    services = build_services_stub()
    settings = AppSettings(
        onboarding_completed=True,
        monitored_folders=[MonitoredFolder(path="/tmp/Documents", source="default", accessible=True)],
    )
    controller = StubController()

    dialog = SettingsDialog(services, settings, controller, lambda: None)
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitUntil(dialog.isVisible)

    close_button = dialog.findChild(QToolButton, "SettingsCloseButton")
    assert close_button is not None
    assert close_button.text() == "×"
    assert close_button.size().width() == 28
    assert close_button.size().height() == 28

    start_width = dialog.width()
    frame = dialog.frameGeometry()
    right_edge = QPoint(frame.right(), frame.center().y())
    assert dialog._resize_edges_for_global_pos(right_edge) == {"right"}

    dialog._resize_edges = {"right"}
    dialog._resize_start_geometry = dialog.geometry()
    dialog._resize_start_global = right_edge
    dialog._resize_window(right_edge + QPoint(120, 0))
    assert dialog.width() > start_width

    start_height = dialog.height()
    bottom_edge = QPoint(dialog.frameGeometry().center().x(), dialog.frameGeometry().bottom())
    assert dialog._resize_edges_for_global_pos(bottom_edge) == {"bottom"}

    dialog._resize_edges = {"bottom"}
    dialog._resize_start_geometry = dialog.geometry()
    dialog._resize_start_global = bottom_edge
    dialog._resize_window(bottom_edge - QPoint(0, 120))
    assert dialog.height() < start_height

    scroll_areas = dialog.page_stack.currentWidget().findChildren(QScrollArea)
    assert scroll_areas


def test_main_window_closes_to_tray_and_can_resize(qtbot):
    services = build_services_stub()
    settings = AppSettings(
        onboarding_completed=True,
        monitored_folders=[MonitoredFolder(path="/tmp/Documents", source="default", accessible=True)],
    )
    controller = StubController()

    window = MainWindow(services, settings, controller)
    qtbot.addWidget(window)
    window.show()
    qtbot.waitUntil(window.isVisible)

    start_width = window.width()
    frame = window.frameGeometry()
    right_edge = QPoint(frame.right(), frame.center().y())
    resize_edges = window._resize_edges_for_global_pos(right_edge)
    assert resize_edges == {"right"}

    window._resize_edges = {"right"}
    window._resize_start_geometry = window.geometry()
    window._resize_start_global = right_edge
    window._resize_window(right_edge + QPoint(120, 0))
    assert window.width() > start_width

    window.close()
    assert window.isHidden()
    assert not window._is_quitting
