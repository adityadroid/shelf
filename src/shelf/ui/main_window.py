from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStatusBar,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from shelf.core.application import AppStatus, FailureRecord, ShelfApplication
from shelf.core.folders import remove_folder_by_path, validate_folder_candidate
from shelf.core.models import AppSettings, MonitoredFolder, SUPPORTED_EXTENSIONS
from shelf.core.services import ServiceContainer
from shelf.indexing.models import SearchResult


APP_STYLESHEET = """
QMainWindow {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 rgba(231, 240, 255, 255),
        stop: 0.36 rgba(242, 248, 255, 255),
        stop: 0.72 rgba(251, 253, 255, 255),
        stop: 1 rgba(237, 244, 235, 255)
    );
}
QWidget {
    color: #17324d;
    font-size: 14px;
}
QFrame#GlassPanel, QFrame#ResultCard {
    background: rgba(255, 255, 255, 0.72);
    border: 1px solid rgba(255, 255, 255, 0.72);
    border-radius: 28px;
}
QFrame#HeroCard {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 rgba(255, 255, 255, 0.88),
        stop: 1 rgba(239, 247, 255, 0.76)
    );
    border: 1px solid rgba(255, 255, 255, 0.82);
    border-radius: 34px;
}
QFrame#ResultCard:hover {
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(147, 184, 219, 0.9);
}
QLabel#Eyebrow {
    color: #56718c;
    font-size: 12px;
    font-weight: 700;
}
QLabel#HeroTitle {
    color: #10253e;
    font-size: 34px;
    font-weight: 700;
}
QLabel#HeroSubtitle {
    color: #4d647c;
    font-size: 15px;
}
QLabel#SectionTitle {
    color: #17324d;
    font-size: 18px;
    font-weight: 700;
}
QLabel#SectionCaption, QLabel#MetaText, QLabel#PathText {
    color: #5b738a;
}
QLabel#ResultTitle {
    color: #15314e;
    font-size: 16px;
    font-weight: 700;
}
QLabel#ResultSnippet {
    color: #35516b;
}
QLabel#Pill {
    background: rgba(255, 255, 255, 0.7);
    border: 1px solid rgba(160, 190, 218, 0.72);
    border-radius: 15px;
    color: #31506c;
    font-size: 12px;
    font-weight: 600;
    padding: 6px 12px;
}
QLabel#EmptyTitle {
    color: #18324d;
    font-size: 22px;
    font-weight: 700;
}
QLabel#EmptyBody {
    color: #5c738a;
    font-size: 14px;
}
QLineEdit#SearchInput, QLineEdit#PathInput {
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid rgba(188, 209, 229, 0.88);
    border-radius: 24px;
    color: #15314e;
    padding: 16px 20px;
}
QLineEdit#SearchInput {
    font-size: 22px;
    font-weight: 600;
}
QLineEdit#SearchInput:focus, QLineEdit#PathInput:focus {
    border: 1px solid rgba(96, 145, 191, 0.95);
}
QPushButton {
    background: rgba(255, 255, 255, 0.78);
    border: 1px solid rgba(184, 205, 224, 0.9);
    border-radius: 18px;
    color: #15314e;
    font-weight: 600;
    padding: 10px 16px;
}
QPushButton:hover {
    background: rgba(255, 255, 255, 0.96);
}
QPushButton#PrimaryButton {
    background: rgba(23, 73, 124, 0.92);
    border: 1px solid rgba(23, 73, 124, 0.92);
    color: white;
}
QPushButton#DangerButton {
    color: #8c2f2f;
}
QToolButton {
    background: rgba(255, 255, 255, 0.82);
    border: 1px solid rgba(184, 205, 224, 0.9);
    border-radius: 16px;
    color: #15314e;
    font-size: 18px;
    padding: 6px;
}
QListWidget, QPlainTextEdit, QTabWidget::pane {
    background: rgba(255, 255, 255, 0.66);
    border: 1px solid rgba(188, 209, 229, 0.88);
    border-radius: 22px;
}
QListWidget {
    padding: 8px;
}
QPlainTextEdit {
    padding: 10px;
}
QTabBar::tab {
    background: rgba(255, 255, 255, 0.62);
    border: 1px solid rgba(188, 209, 229, 0.88);
    border-bottom: none;
    border-top-left-radius: 14px;
    border-top-right-radius: 14px;
    color: #48627b;
    padding: 10px 16px;
}
QTabBar::tab:selected {
    background: rgba(255, 255, 255, 0.94);
    color: #18324d;
}
QStatusBar {
    background: transparent;
    color: #48627b;
}
"""


def friendly_timestamp(timestamp: float | None) -> str:
    if not timestamp:
        return "Unknown"
    return datetime.fromtimestamp(float(timestamp)).strftime("%b %d, %Y at %H:%M")


class SearchResultCard(QFrame):
    clicked = Signal()

    def __init__(
        self,
        result: SearchResult,
        app_controller: ShelfApplication,
        status_bar: QStatusBar,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.result = result
        self.app_controller = app_controller
        self.status_bar = status_bar

        self.setObjectName("ResultCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 18, 18, 18)
        layout.setSpacing(16)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(6)

        title = QLabel(result.file_name, self)
        title.setObjectName("ResultTitle")
        text_layout.addWidget(title)

        meta = QLabel(
            f"{result.extension.upper().lstrip('.')}  |  {friendly_timestamp(result.modified_at)}  |  {result.source}",
            self,
        )
        meta.setObjectName("MetaText")
        text_layout.addWidget(meta)

        path_label = QLabel(result.path, self)
        path_label.setObjectName("PathText")
        path_label.setWordWrap(True)
        text_layout.addWidget(path_label)

        snippet = QLabel(result.snippet or "Indexed with no preview text available.", self)
        snippet.setObjectName("ResultSnippet")
        snippet.setWordWrap(True)
        text_layout.addWidget(snippet)

        layout.addLayout(text_layout, 1)

        self.actions_button = QToolButton(self)
        self.actions_button.setText("...")
        self.actions_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.actions_button.setMenu(self._build_menu())
        layout.addWidget(self.actions_button, alignment=Qt.AlignmentFlag.AlignTop)

    def _build_menu(self) -> QMenu:
        menu = QMenu(self)
        open_action = menu.addAction("Open")
        reveal_action = menu.addAction("Reveal in Finder")
        copy_action = menu.addAction("Copy Path")
        open_action.triggered.connect(lambda: self.app_controller.open_file(self.result.path))
        reveal_action.triggered.connect(lambda: self.app_controller.reveal_file(self.result.path))
        copy_action.triggered.connect(self.copy_path)
        return menu

    def copy_path(self) -> None:
        QApplication.clipboard().setText(self.result.path)
        self.status_bar.showMessage("Copied path to clipboard.", 3000)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class SettingsDialog(QDialog):
    def __init__(
        self,
        services: ServiceContainer,
        settings: AppSettings,
        app_controller: ShelfApplication,
        on_settings_changed: Callable[[], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.services = services
        self.settings = settings
        self.app_controller = app_controller
        self.on_settings_changed = on_settings_changed

        self.setWindowTitle("Shelf Settings")
        self.resize(860, 640)
        self.setStyleSheet(APP_STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        tabs = QTabWidget(self)
        layout.addWidget(tabs, 1)

        tabs.addTab(self._build_general_tab(), "Application")
        tabs.addTab(self._build_folders_tab(), "Folders")
        tabs.addTab(self._build_maintenance_tab(), "Maintenance")

    def _build_general_tab(self) -> QWidget:
        tab = QFrame(self)
        tab.setObjectName("GlassPanel")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        title = QLabel("Local app configuration", tab)
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Everything in Shelf stays on-device. These paths show where the app keeps settings, the index, logs, and vector data.",
            tab,
        )
        subtitle.setObjectName("SectionCaption")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        for label, value in (
            ("Application Support", str(self.services.paths.root)),
            ("Settings File", str(self.services.paths.settings_file)),
            ("SQLite Database", str(self.services.paths.database_file)),
            ("Supported Types", ", ".join(extension.upper() for extension in SUPPORTED_EXTENSIONS)),
        ):
            label_widget = QLabel(label, tab)
            label_widget.setObjectName("Eyebrow")
            layout.addWidget(label_widget)

            value_widget = QLineEdit(value, tab)
            value_widget.setReadOnly(True)
            value_widget.setObjectName("PathInput")
            layout.addWidget(value_widget)

        layout.addStretch(1)
        return tab

    def _build_folders_tab(self) -> QWidget:
        tab = QFrame(self)
        tab.setObjectName("GlassPanel")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        title = QLabel("Monitored folders", tab)
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        caption = QLabel(
            "Choose which locations are indexed. Removed folders will disappear from results after reconciliation finishes.",
            tab,
        )
        caption.setObjectName("SectionCaption")
        caption.setWordWrap(True)
        layout.addWidget(caption)

        self.folder_list = QListWidget(tab)
        layout.addWidget(self.folder_list, 1)

        controls = QHBoxLayout()
        add_button = QPushButton("Add Folder", tab)
        add_button.setObjectName("PrimaryButton")
        add_button.clicked.connect(self.add_folder)
        controls.addWidget(add_button)

        remove_button = QPushButton("Remove Folder", tab)
        remove_button.setObjectName("DangerButton")
        remove_button.clicked.connect(self.remove_selected_folder)
        controls.addWidget(remove_button)
        controls.addStretch(1)
        layout.addLayout(controls)

        self.refresh_folder_list()
        return tab

    def _build_maintenance_tab(self) -> QWidget:
        tab = QFrame(self)
        tab.setObjectName("GlassPanel")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        title = QLabel("Maintenance commands", tab)
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        caption = QLabel(
            "These controls expose the same operational commands available in the CLI so users can repair or inspect the library without leaving the app.",
            tab,
        )
        caption.setObjectName("SectionCaption")
        caption.setWordWrap(True)
        layout.addWidget(caption)

        button_grid = QGridLayout()
        button_grid.setHorizontalSpacing(10)
        button_grid.setVerticalSpacing(10)
        for index, (label, command) in enumerate(
            (
                ("Status", "status"),
                ("Audit", "audit"),
                ("Rebuild All", "rebuild-all"),
                ("Rebuild FTS", "rebuild-fts"),
            )
        ):
            button = QPushButton(label, tab)
            if command in {"status", "audit"}:
                button.setObjectName("PrimaryButton")
            button.clicked.connect(lambda _checked=False, selected=command: self.run_command(selected))
            button_grid.addWidget(button, 0, index)
        layout.addLayout(button_grid)

        path_label = QLabel("Reindex a specific file path", tab)
        path_label.setObjectName("Eyebrow")
        layout.addWidget(path_label)

        self.reindex_path_input = QLineEdit(tab)
        self.reindex_path_input.setObjectName("PathInput")
        self.reindex_path_input.setPlaceholderText("Choose a file to enqueue for reindexing")
        layout.addWidget(self.reindex_path_input)

        file_row = QHBoxLayout()
        file_browse = QPushButton("Browse File", tab)
        file_browse.clicked.connect(self.choose_file_path)
        file_row.addWidget(file_browse)
        file_run = QPushButton("Run Reindex Path", tab)
        file_run.clicked.connect(lambda: self.run_command("reindex-path", self.reindex_path_input.text().strip()))
        file_row.addWidget(file_run)
        file_row.addStretch(1)
        layout.addLayout(file_row)

        folder_label = QLabel("Reindex every supported document in a folder", tab)
        folder_label.setObjectName("Eyebrow")
        layout.addWidget(folder_label)

        self.reindex_folder_input = QLineEdit(tab)
        self.reindex_folder_input.setObjectName("PathInput")
        self.reindex_folder_input.setPlaceholderText("Choose a monitored folder or any supported document directory")
        layout.addWidget(self.reindex_folder_input)

        folder_row = QHBoxLayout()
        folder_browse = QPushButton("Browse Folder", tab)
        folder_browse.clicked.connect(self.choose_folder_path)
        folder_row.addWidget(folder_browse)
        folder_run = QPushButton("Run Reindex Folder", tab)
        folder_run.clicked.connect(
            lambda: self.run_command("reindex-folder", self.reindex_folder_input.text().strip())
        )
        folder_row.addWidget(folder_run)
        folder_row.addStretch(1)
        layout.addLayout(folder_row)

        self.maintenance_output = QPlainTextEdit(tab)
        self.maintenance_output.setReadOnly(True)
        self.maintenance_output.setPlaceholderText("Command output will appear here.")
        layout.addWidget(self.maintenance_output, 1)

        return tab

    def refresh_folder_list(self) -> None:
        self.folder_list.clear()
        for folder in self.settings.monitored_folders:
            suffix = "" if folder.accessible else " | access needs attention"
            item = QListWidgetItem(folder.path + suffix)
            item.setData(Qt.ItemDataRole.UserRole, folder.path)
            self.folder_list.addItem(item)

    def add_folder(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Choose Folder to Monitor", str(Path.home()))
        if not selected:
            return

        validation = validate_folder_candidate(selected, self.settings.monitored_folders)
        if not validation.accepted or validation.normalized_path is None:
            QMessageBox.warning(self, "Cannot Add Folder", validation.message or "Folder cannot be added.")
            return

        self.settings.monitored_folders.append(
            MonitoredFolder(path=validation.normalized_path, source="user", accessible=True)
        )
        self.services.settings.save(self.settings)
        self.app_controller.refresh_folders(self.settings)
        self.refresh_folder_list()
        self.on_settings_changed()

    def remove_selected_folder(self) -> None:
        item = self.folder_list.currentItem()
        if item is None:
            return

        folder_path = item.data(Qt.ItemDataRole.UserRole)
        answer = QMessageBox.question(
            self,
            "Remove Folder",
            "Removing this folder will remove its documents from search results after reindexing. Continue?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self.settings.monitored_folders = remove_folder_by_path(self.settings.monitored_folders, folder_path)
        self.services.settings.save(self.settings)
        self.app_controller.refresh_folders(self.settings)
        self.refresh_folder_list()
        self.on_settings_changed()

    def choose_file_path(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Choose File to Reindex",
            str(Path.home()),
            "Documents (*.pdf *.doc *.docx);;All Files (*)",
        )
        if selected:
            self.reindex_path_input.setText(selected)

    def choose_folder_path(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Choose Folder to Reindex", str(Path.home()))
        if selected:
            self.reindex_folder_input.setText(selected)

    def run_command(self, command: str, path: str | None = None) -> None:
        try:
            report = self.app_controller.run_maintenance(command, path)
        except ValueError as exc:
            QMessageBox.warning(self, "Missing path", str(exc))
            return
        except Exception as exc:  # pragma: no cover - defensive dialog path
            QMessageBox.critical(self, "Command failed", str(exc))
            return

        self.maintenance_output.setPlainText(json.dumps(report, indent=2, sort_keys=True))
        self.on_settings_changed()


class DocumentMonitorDialog(QDialog):
    def __init__(self, app_controller: ShelfApplication, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.app_controller = app_controller
        self.settings = settings

        self.setWindowTitle("Shelf Monitor")
        self.resize(840, 620)
        self.setStyleSheet(APP_STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        tabs = QTabWidget(self)
        layout.addWidget(tabs, 1)

        overview = QFrame(self)
        overview.setObjectName("GlassPanel")
        overview_layout = QVBoxLayout(overview)
        overview_layout.setContentsMargins(22, 22, 22, 22)
        overview_layout.setSpacing(16)

        title = QLabel("Library health", overview)
        title.setObjectName("SectionTitle")
        overview_layout.addWidget(title)

        pills_row = QHBoxLayout()
        self.documents_pill = self._make_pill()
        self.jobs_pill = self._make_pill()
        self.failures_pill = self._make_pill()
        pills_row.addWidget(self.documents_pill)
        pills_row.addWidget(self.jobs_pill)
        pills_row.addWidget(self.failures_pill)
        pills_row.addStretch(1)
        overview_layout.addLayout(pills_row)

        self.overview_text = QPlainTextEdit(overview)
        self.overview_text.setReadOnly(True)
        overview_layout.addWidget(self.overview_text, 1)
        tabs.addTab(overview, "Overview")

        failures_tab = QFrame(self)
        failures_tab.setObjectName("GlassPanel")
        failures_layout = QVBoxLayout(failures_tab)
        failures_layout.setContentsMargins(22, 22, 22, 22)
        failures_layout.setSpacing(14)

        failures_title = QLabel("Recent failures", failures_tab)
        failures_title.setObjectName("SectionTitle")
        failures_layout.addWidget(failures_title)

        self.failures_list = QListWidget(failures_tab)
        failures_layout.addWidget(self.failures_list, 1)
        tabs.addTab(failures_tab, "Failures")

        refresh_button = QPushButton("Refresh", self)
        refresh_button.setObjectName("PrimaryButton")
        refresh_button.clicked.connect(self.refresh_data)
        layout.addWidget(refresh_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.refresh_data()

    def _make_pill(self) -> QLabel:
        label = QLabel(self)
        label.setObjectName("Pill")
        return label

    def refresh_data(self) -> None:
        status = self.app_controller.status()
        self.documents_pill.setText(f"{status.indexed_documents} indexed")
        self.jobs_pill.setText(f"{status.queued_jobs} queued")
        self.failures_pill.setText(f"{status.recent_failures} failures")

        overview_lines = [
            f"Monitored folders: {status.monitored_folders}",
            f"Accessible folders: {status.accessible_folders}",
            f"Embedding model: {status.embedding_model}",
            f"Last reconciliation: {status.last_reconciliation or 'Not available yet'}",
            "",
            "Current monitored folders:",
        ]
        overview_lines.extend(f"- {folder.path}" for folder in self.settings.monitored_folders)
        self.overview_text.setPlainText("\n".join(overview_lines))

        self.failures_list.clear()
        failures = self.app_controller.recent_failures()
        if not failures:
            self.failures_list.addItem("No recent failures recorded.")
            return
        for failure in failures:
            self.failures_list.addItem(self._format_failure(failure))

    def _format_failure(self, failure: FailureRecord) -> str:
        detail = f"\n{failure.detail}" if failure.detail else ""
        ref = f" ({failure.ref_id})" if failure.ref_id else ""
        return f"[{failure.created_at}] {failure.scope}{ref}\n{failure.message}{detail}"


class MainWindow(QMainWindow):
    def __init__(self, services: ServiceContainer, settings: AppSettings, app_controller: ShelfApplication) -> None:
        super().__init__()
        self.services = services
        self.settings = settings
        self.app_controller = app_controller
        self.result_cards: list[SearchResultCard] = []

        self.setWindowTitle("Shelf")
        self.resize(1200, 820)
        self.setStyleSheet(APP_STYLESHEET)

        self._build_actions()
        self._build_ui()

        self.search_timer = QTimer(self)
        self.search_timer.setInterval(160)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.run_search)

        self.status_timer = QTimer(self)
        self.status_timer.setInterval(1500)
        self.status_timer.timeout.connect(self.refresh_status)
        self.status_timer.start()

        self.refresh_status()
        self.show_idle_state()

        if settings.last_error:
            self.statusBar().showMessage(settings.last_error, 8000)

    def _build_actions(self) -> None:
        settings_action = QAction("Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.open_settings)
        self.addAction(settings_action)

        monitor_action = QAction("Document Monitor", self)
        monitor_action.setShortcut("Ctrl+Shift+M")
        monitor_action.triggered.connect(self.open_monitor)
        self.addAction(monitor_action)

    def _build_ui(self) -> None:
        status_bar = QStatusBar(self)
        status_bar.showMessage("Ready")
        self.setStatusBar(status_bar)

        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(18)

        top_shell = QFrame(central)
        top_shell.setObjectName("GlassPanel")
        top_layout = QVBoxLayout(top_shell)
        top_layout.setContentsMargins(22, 22, 22, 22)
        top_layout.setSpacing(18)
        root_layout.addWidget(top_shell, 1)

        header_row = QHBoxLayout()
        brand_column = QVBoxLayout()
        eyebrow = QLabel("Shelf", top_shell)
        eyebrow.setObjectName("Eyebrow")
        brand_column.addWidget(eyebrow)
        title = QLabel("Find documents like Spotlight, but built for your library.", top_shell)
        title.setObjectName("HeroTitle")
        title.setWordWrap(True)
        brand_column.addWidget(title)
        subtitle = QLabel(
            "Search across local file names and extracted text, then open a match instantly or reveal it in Finder.",
            top_shell,
        )
        subtitle.setObjectName("HeroSubtitle")
        subtitle.setWordWrap(True)
        brand_column.addWidget(subtitle)
        header_row.addLayout(brand_column, 1)

        button_row = QHBoxLayout()
        monitor_button = QPushButton("Document Monitor", top_shell)
        monitor_button.clicked.connect(self.open_monitor)
        button_row.addWidget(monitor_button)
        settings_button = QPushButton("Settings", top_shell)
        settings_button.setObjectName("PrimaryButton")
        settings_button.clicked.connect(self.open_settings)
        button_row.addWidget(settings_button)
        header_row.addLayout(button_row)
        top_layout.addLayout(header_row)

        pills_row = QHBoxLayout()
        self.documents_pill = self._make_pill()
        self.jobs_pill = self._make_pill()
        self.failures_pill = self._make_pill()
        self.folders_pill = self._make_pill()
        pills_row.addWidget(self.documents_pill)
        pills_row.addWidget(self.jobs_pill)
        pills_row.addWidget(self.failures_pill)
        pills_row.addWidget(self.folders_pill)
        pills_row.addStretch(1)
        top_layout.addLayout(pills_row)

        hero = QFrame(top_shell)
        hero.setObjectName("HeroCard")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(24, 24, 24, 24)
        hero_layout.setSpacing(12)
        top_layout.addWidget(hero)

        hero_label = QLabel("Search your local document shelf", hero)
        hero_label.setObjectName("SectionTitle")
        hero_layout.addWidget(hero_label)

        self.search_input = QLineEdit(hero)
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Search filenames and document text")
        self.search_input.textChanged.connect(self.schedule_search)
        self.search_input.returnPressed.connect(self.open_primary_result)
        hero_layout.addWidget(self.search_input)

        self.search_caption = QLabel(
            "Type to search. Click a result to open it, or use the overflow menu to reveal it in Finder.",
            hero,
        )
        self.search_caption.setObjectName("SectionCaption")
        self.search_caption.setWordWrap(True)
        hero_layout.addWidget(self.search_caption)

        results_header = QHBoxLayout()
        results_title = QLabel("Results", top_shell)
        results_title.setObjectName("SectionTitle")
        results_header.addWidget(results_title)
        self.results_count_label = QLabel("Waiting for a search", top_shell)
        self.results_count_label.setObjectName("SectionCaption")
        results_header.addWidget(self.results_count_label)
        results_header.addStretch(1)
        top_layout.addLayout(results_header)

        self.results_scroll = QScrollArea(top_shell)
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.results_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        top_layout.addWidget(self.results_scroll, 1)

        self.results_container = QWidget(self.results_scroll)
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(12)
        self.results_scroll.setWidget(self.results_container)

    def _make_pill(self) -> QLabel:
        label = QLabel(self)
        label.setObjectName("Pill")
        return label

    def schedule_search(self, *_args) -> None:
        self.search_timer.start()

    def clear_results(self) -> None:
        self.result_cards.clear()
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def show_idle_state(self) -> None:
        self.clear_results()
        empty = QFrame(self.results_container)
        empty.setObjectName("GlassPanel")
        layout = QVBoxLayout(empty)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(10)

        title = QLabel("Search your document library", empty)
        title.setObjectName("EmptyTitle")
        layout.addWidget(title)

        body = QLabel(
            "Shelf keeps the interface focused on retrieval. Folder management, health checks, and failed document diagnostics live in Settings and Document Monitor.",
            empty,
        )
        body.setObjectName("EmptyBody")
        body.setWordWrap(True)
        layout.addWidget(body)

        self.results_layout.addWidget(empty)
        self.results_layout.addStretch(1)
        self.results_count_label.setText("Waiting for a search")

    def show_empty_results(self, query: str) -> None:
        self.clear_results()
        empty = QFrame(self.results_container)
        empty.setObjectName("GlassPanel")
        layout = QVBoxLayout(empty)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(10)

        title = QLabel("No matches found", empty)
        title.setObjectName("EmptyTitle")
        layout.addWidget(title)

        body = QLabel(
            f'No results for "{query}" yet. Try a broader keyword, wait for indexing to finish, or use Document Monitor to inspect recent failures.',
            empty,
        )
        body.setObjectName("EmptyBody")
        body.setWordWrap(True)
        layout.addWidget(body)

        self.results_layout.addWidget(empty)
        self.results_layout.addStretch(1)
        self.results_count_label.setText("0 results")

    def run_search(self) -> None:
        query = self.search_input.text().strip()
        if not query:
            self.show_idle_state()
            return

        results = self.app_controller.search(query)
        self.clear_results()

        if not results:
            self.show_empty_results(query)
            return

        self.results_count_label.setText(f'{len(results)} results for "{query}"')
        for result in results:
            card = SearchResultCard(result, self.app_controller, self.statusBar(), self.results_container)
            card.clicked.connect(lambda selected=result: self.open_result(selected.path))
            self.results_layout.addWidget(card)
            self.result_cards.append(card)
        self.results_layout.addStretch(1)

    def open_primary_result(self) -> None:
        if not self.result_cards and self.search_input.text().strip():
            self.run_search()
        if self.result_cards:
            self.open_result(self.result_cards[0].result.path)

    def open_result(self, path: str) -> None:
        self.app_controller.open_file(path)
        self.statusBar().showMessage(f"Opening {Path(path).name}", 2500)

    def refresh_status(self) -> None:
        status = self.app_controller.status()
        self.documents_pill.setText(f"{status.indexed_documents} indexed")
        self.jobs_pill.setText(f"{status.queued_jobs} queued")
        self.failures_pill.setText(f"{status.recent_failures} failures")
        self.folders_pill.setText(f"{status.accessible_folders}/{status.monitored_folders} folders ready")
        self.search_caption.setText(self._status_message(status))

    def _status_message(self, status: AppStatus) -> str:
        if status.queued_jobs:
            return (
                f"Indexing is active with {status.queued_jobs} queued jobs. "
                "You can search now while Shelf continues refreshing the library."
            )
        if status.indexed_documents == 0:
            return "Shelf is ready, but the library is still empty. Add folders in Settings or wait for indexing."
        return (
            f"Library is up to date across {status.accessible_folders} accessible folders. "
            f"Last reconciliation: {status.last_reconciliation or 'not recorded yet'}."
        )

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.services, self.settings, self.app_controller, self.refresh_status, self)
        dialog.exec()
        self.refresh_status()
        if not self.search_input.text().strip():
            self.show_idle_state()

    def open_monitor(self) -> None:
        dialog = DocumentMonitorDialog(self.app_controller, self.settings, self)
        dialog.exec()
        self.refresh_status()

    def closeEvent(self, event) -> None:  # noqa: N802
        self.status_timer.stop()
        self.search_timer.stop()
        super().closeEvent(event)
