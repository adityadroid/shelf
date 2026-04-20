from __future__ import annotations

import json
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QEvent, QPoint, QTimer, Qt, Signal
from PySide6.QtGui import QAction, QGuiApplication, QKeySequence, QMouseEvent
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QKeySequenceEdit,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QStatusBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from shelf.core.application import FailureRecord, ShelfApplication
from shelf.core.folders import remove_folder_by_path, validate_folder_candidate
from shelf.core.models import AppSettings, DEFAULT_LAUNCH_SHORTCUT, MonitoredFolder, SUPPORTED_EXTENSIONS
from shelf.core.services import ServiceContainer
from shelf.indexing.models import SearchResult
from shelf.ui.launcher_shortcut import MacLauncherShortcut


APP_STYLESHEET = """
QMainWindow {
    background: transparent;
}
QWidget {
    color: #221f1d;
    font-size: 14px;
    background: transparent;
}
QFrame#GlassPanel, QFrame#ComposerShell, QFrame#SettingsHero, QFrame#EmptyCard {
    background: rgba(255, 255, 255, 0.74);
    border: 1px solid rgba(255, 255, 255, 0.84);
    border-radius: 28px;
}
QFrame#SettingsShell, QFrame#SettingsSidebar, QFrame#SettingsPane, QFrame#SettingsCard, QFrame#SettingsCommandCard {
    background: rgba(102, 98, 96, 0.92);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 28px;
}
QFrame#SettingsSidebar, QFrame#SettingsPane, QFrame#SettingsCard, QFrame#SettingsCommandCard {
    background: rgba(255, 255, 255, 0.12);
}
QFrame#ComposerShell {
    background: rgba(102, 98, 96, 0.9);
    border: 1px solid rgba(255, 255, 255, 0.34);
    border-radius: 26px;
}
QFrame#ResultsShell {
    background: rgba(102, 98, 96, 0.86);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 26px;
}
QFrame#ResultCard {
    background: rgba(255, 255, 255, 0.16);
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 18px;
}
QFrame#ResultCard[active="true"] {
    background: rgba(255, 255, 255, 0.28);
    border: 1px solid rgba(255, 255, 255, 0.3);
}
QToolButton#SettingsIconButton {
    background: rgba(255, 255, 255, 0.18);
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 18px;
    color: #f5f2ee;
    font-size: 20px;
    font-weight: 700;
    padding: 6px;
}
QToolButton#SettingsIconButton:hover {
    background: rgba(255, 255, 255, 0.28);
}
QToolButton#SettingsCloseButton {
    background: rgba(255, 255, 255, 0.14);
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 16px;
    color: #f5f2ee;
    font-size: 16px;
    font-weight: 700;
}
QToolButton#SettingsCloseButton:hover {
    background: rgba(255, 255, 255, 0.22);
}
QFrame#ResultCard:hover, QFrame#GlassPanel:hover, QFrame#EmptyCard:hover {
    background: rgba(255, 255, 255, 0.24);
    border: 1px solid rgba(255, 255, 255, 0.22);
}
QLabel#Eyebrow {
    color: #7c6f67;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.08em;
}
QLabel#HeroTitle {
    color: #191615;
    font-size: 42px;
    font-weight: 700;
}
QLabel#HeroSubtitle {
    color: #665d58;
    font-size: 15px;
}
QLabel#SectionTitle {
    color: #f4efea;
    font-size: 15px;
    font-weight: 700;
}
QLabel#SettingsTitle {
    color: #f5f2ee;
    font-size: 28px;
    font-weight: 700;
}
QLabel#SettingsSubtitle {
    color: rgba(245, 242, 238, 0.72);
    font-size: 13px;
}
QLabel#SectionCaption, QLabel#MetaText, QLabel#PathText, QLabel#ComposerHint {
    color: rgba(245, 242, 238, 0.72);
}
QLabel#ResultTitle {
    color: #f5f2ee;
    font-size: 13px;
    font-weight: 700;
}
QLabel#PathText {
    font-size: 10px;
}
QPushButton#RevealButton {
    background: rgba(255, 255, 255, 0.18);
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 14px;
    color: #f5f2ee;
    font-size: 12px;
    padding: 7px 12px;
}
QPushButton#RevealButton:hover {
    background: rgba(255, 255, 255, 0.26);
}
QLabel#Pill {
    background: rgba(255, 255, 255, 0.14);
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 15px;
    color: #f5f2ee;
    font-size: 12px;
    font-weight: 600;
    padding: 6px 12px;
}
QLabel#EmptyTitle {
    color: #f4efea;
    font-size: 18px;
    font-weight: 700;
}
QLabel#EmptyBody {
    color: rgba(245, 242, 238, 0.72);
    font-size: 12px;
}
QLineEdit#SearchInput, QLineEdit#PathInput, QKeySequenceEdit#PathInput, QPlainTextEdit#MaintenanceOutput {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 22px;
    color: #f5f2ee;
    padding: 14px 18px;
}
QKeySequenceEdit#PathInput {
    min-height: 50px;
    padding: 0 18px;
}
QKeySequenceEdit#PathInput::part(lineedit) {
    background: transparent;
    border: none;
    color: #f5f2ee;
}
QLineEdit#SearchInput {
    background: transparent;
    border: none;
    color: #f5f2ee;
    font-size: 17px;
    font-weight: 600;
    padding: 10px 10px;
}
QLineEdit#PathInput:focus, QKeySequenceEdit#PathInput:focus, QPlainTextEdit#MaintenanceOutput:focus {
    border: 1px solid rgba(255, 255, 255, 0.3);
}
QPushButton {
    background: rgba(255, 255, 255, 0.14);
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 18px;
    color: #f5f2ee;
    font-weight: 600;
    padding: 10px 18px;
}
QPushButton:hover {
    background: rgba(255, 255, 255, 0.22);
}
QPushButton#PrimaryButton {
    background: rgba(255, 255, 255, 0.22);
    border: 1px solid rgba(255, 255, 255, 0.24);
    color: #f5f2ee;
    padding: 12px 18px;
}
QPushButton#GhostButton {
    background: rgba(108, 103, 101, 0.78);
    border: 1px solid rgba(255, 255, 255, 0.22);
    color: #f5f2ee;
    padding: 12px 16px;
}
QPushButton#DangerButton {
    color: #ffd3cb;
}
QPushButton#SettingsNavButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 18px;
    color: rgba(245, 242, 238, 0.72);
    font-size: 14px;
    font-weight: 600;
    padding: 12px 14px;
    text-align: left;
}
QPushButton#SettingsNavButton:hover {
    background: rgba(255, 255, 255, 0.08);
}
QPushButton#SettingsNavButton:checked {
    background: rgba(255, 255, 255, 0.18);
    border: 1px solid rgba(255, 255, 255, 0.18);
    color: #f5f2ee;
}
QToolButton {
    background: rgba(255, 255, 255, 0.82);
    border: 1px solid rgba(214, 205, 197, 0.92);
    border-radius: 16px;
    color: #201c1a;
    padding: 8px 10px;
}
QScrollArea {
    background: transparent;
}
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 10px 0 10px 0;
}
QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.26);
    border-radius: 3px;
    min-height: 26px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
    height: 0;
}
QProgressBar {
    background: rgba(255, 255, 255, 0.08);
    border: none;
    border-radius: 3px;
    max-height: 6px;
}
QProgressBar::chunk {
    background: rgba(255, 255, 255, 0.88);
    border-radius: 3px;
}
QListWidget, QPlainTextEdit {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 22px;
    color: #f5f2ee;
}
QListWidget {
    padding: 8px;
}
QPlainTextEdit {
    padding: 10px;
}
QStatusBar {
    background: transparent;
    color: rgba(245, 242, 238, 0.72);
}
"""


ICON_PATH = Path(__file__).resolve().parent / "assets" / "shelf_icon.svg"


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
        self.setProperty("active", False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 12, 12)
        layout.setSpacing(12)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        title = QLabel(result.file_name, self)
        title.setObjectName("ResultTitle")
        title.setWordWrap(True)
        text_layout.addWidget(title)

        path_label = QLabel(compact_result_path(result.path), self)
        path_label.setObjectName("PathText")
        path_label.setWordWrap(True)
        text_layout.addWidget(path_label)

        layout.addLayout(text_layout, 1)

        self.reveal_button = QPushButton("Reveal", self)
        self.reveal_button.setObjectName("RevealButton")
        self.reveal_button.setFixedHeight(32)
        self.reveal_button.clicked.connect(lambda: self.app_controller.reveal_file(self.result.path))
        layout.addWidget(self.reveal_button, alignment=Qt.AlignmentFlag.AlignCenter)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and not self.reveal_button.geometry().contains(event.position().toPoint()):
            self.clicked.emit()
        super().mousePressEvent(event)

    def set_active(self, active: bool) -> None:
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


def compact_result_path(path: str) -> str:
    path_obj = Path(path).expanduser()
    directory = path_obj.parent
    try:
        relative_to_home = directory.relative_to(Path.home())
        directory_text = "~" if str(relative_to_home) == "." else f"~/{relative_to_home.as_posix()}"
    except ValueError:
        directory_text = directory.as_posix()
    return directory_text


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
        self._drag_offset: QPoint | None = None

        self.setWindowTitle("Shelf Settings")
        self.resize(860, 640)
        self.setObjectName("SettingsDialog")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setStyleSheet(APP_STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(0)

        self.shell = QFrame(self)
        self.shell.setObjectName("SettingsShell")
        self._apply_shadow(self.shell, blur=44, offset_y=20, alpha=120)
        shell_layout = QVBoxLayout(self.shell)
        shell_layout.setContentsMargins(20, 20, 20, 20)
        shell_layout.setSpacing(18)
        layout.addWidget(self.shell)

        header = QFrame(self.shell)
        header.setObjectName("SettingsCard")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 18, 18, 18)
        header_layout.setSpacing(16)
        shell_layout.addWidget(header)

        title_column = QVBoxLayout()
        title_column.setSpacing(4)
        eyebrow = QLabel("Control room", header)
        eyebrow.setObjectName("Eyebrow")
        title_column.addWidget(eyebrow)

        title = QLabel("Configure Shelf", header)
        title.setObjectName("SettingsTitle")
        title.setWordWrap(True)
        title_column.addWidget(title)

        subtitle = QLabel(
            "Manage the launcher shortcut, monitored folders, indexing health, and maintenance tools from one place.",
            header,
        )
        subtitle.setObjectName("SettingsSubtitle")
        subtitle.setWordWrap(True)
        title_column.addWidget(subtitle)
        header_layout.addLayout(title_column, 1)

        close_button = QToolButton(header)
        close_button.setObjectName("SettingsCloseButton")
        close_button.setText("x")
        close_button.setFixedSize(34, 34)
        close_button.clicked.connect(self.accept)
        header_layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignTop)

        content_row = QHBoxLayout()
        content_row.setSpacing(18)
        shell_layout.addLayout(content_row, 1)

        sidebar = QFrame(self.shell)
        sidebar.setObjectName("SettingsSidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(14, 14, 14, 14)
        sidebar_layout.setSpacing(8)
        content_row.addWidget(sidebar, 0)

        sidebar_title = QLabel("Sections", sidebar)
        sidebar_title.setObjectName("Eyebrow")
        sidebar_layout.addWidget(sidebar_title)

        self.section_buttons = QButtonGroup(self)
        self.section_buttons.setExclusive(True)
        self.page_stack = QStackedWidget(self.shell)
        content_row.addWidget(self.page_stack, 1)

        for index, (label, factory) in enumerate(
            (
                ("Application", self._build_general_tab),
                ("Folders", self._build_folders_tab),
                ("Library Health", self._build_monitor_tab),
                ("Maintenance", self._build_maintenance_tab),
            )
        ):
            button = QPushButton(label, sidebar)
            button.setObjectName("SettingsNavButton")
            button.setCheckable(True)
            button.clicked.connect(lambda _checked=False, selected=index: self.page_stack.setCurrentIndex(selected))
            self.section_buttons.addButton(button, index)
            sidebar_layout.addWidget(button)
            self.page_stack.addWidget(factory())

        sidebar_layout.addStretch(1)
        first_button = self.section_buttons.button(0)
        if first_button is not None:
            first_button.setChecked(True)
        self.page_stack.setCurrentIndex(0)

    def _apply_shadow(self, widget: QWidget, blur: int, offset_y: int, alpha: int) -> None:
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(blur)
        shadow.setOffset(0, offset_y)
        shadow.setColor(Qt.GlobalColor.black)
        color = shadow.color()
        color.setAlpha(alpha)
        shadow.setColor(color)
        widget.setGraphicsEffect(shadow)

    def _build_general_tab(self) -> QWidget:
        tab = QFrame(self)
        tab.setObjectName("SettingsPane")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)

        title = QLabel("Application", tab)
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Everything in Shelf stays local. Choose how you launch the app and inspect where its on-device data lives.",
            tab,
        )
        subtitle.setObjectName("SectionCaption")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        launch_card = QFrame(tab)
        launch_card.setObjectName("SettingsCard")
        launch_layout = QVBoxLayout(launch_card)
        launch_layout.setContentsMargins(18, 18, 18, 18)
        launch_layout.setSpacing(12)
        layout.addWidget(launch_card)

        shortcut_label = QLabel("Launcher shortcut", tab)
        shortcut_label.setObjectName("Eyebrow")
        launch_layout.addWidget(shortcut_label)

        shortcut_caption = QLabel(
            "This shortcut should show or hide Shelf from anywhere while the app is running. Default: Cmd+Option+S.",
            tab,
        )
        shortcut_caption.setObjectName("SectionCaption")
        shortcut_caption.setWordWrap(True)
        launch_layout.addWidget(shortcut_caption)

        shortcut_row = QHBoxLayout()
        self.launcher_shortcut_input = QKeySequenceEdit(
            QKeySequence(self.settings.launcher_shortcut or DEFAULT_LAUNCH_SHORTCUT),
            tab,
        )
        self.launcher_shortcut_input.setObjectName("PathInput")
        self.launcher_shortcut_input.editingFinished.connect(self.save_launcher_shortcut)
        shortcut_row.addWidget(self.launcher_shortcut_input, 1)

        reset_shortcut = QPushButton("Reset Default", tab)
        reset_shortcut.clicked.connect(self.reset_launcher_shortcut)
        shortcut_row.addWidget(reset_shortcut)
        launch_layout.addLayout(shortcut_row)

        storage_card = QFrame(tab)
        storage_card.setObjectName("SettingsCard")
        storage_layout = QVBoxLayout(storage_card)
        storage_layout.setContentsMargins(18, 18, 18, 18)
        storage_layout.setSpacing(12)
        layout.addWidget(storage_card)

        for label, value in (
            ("Application Support", str(self.services.paths.root)),
            ("Settings File", str(self.services.paths.settings_file)),
            ("SQLite Database", str(self.services.paths.database_file)),
            ("Supported Types", ", ".join(extension.upper() for extension in SUPPORTED_EXTENSIONS)),
        ):
            label_widget = QLabel(label, tab)
            label_widget.setObjectName("Eyebrow")
            storage_layout.addWidget(label_widget)

            value_widget = QLineEdit(value, tab)
            value_widget.setReadOnly(True)
            value_widget.setObjectName("PathInput")
            storage_layout.addWidget(value_widget)

        layout.addStretch(1)
        return tab

    def _build_folders_tab(self) -> QWidget:
        tab = QFrame(self)
        tab.setObjectName("SettingsPane")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)

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

        list_card = QFrame(tab)
        list_card.setObjectName("SettingsCard")
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(16, 16, 16, 16)
        list_layout.setSpacing(12)
        layout.addWidget(list_card, 1)

        self.folder_list = QListWidget(tab)
        list_layout.addWidget(self.folder_list, 1)

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
        list_layout.addLayout(controls)

        self.refresh_folder_list()
        return tab

    def _build_monitor_tab(self) -> QWidget:
        tab = QFrame(self)
        tab.setObjectName("SettingsPane")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)

        title = QLabel("Library health", tab)
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        caption = QLabel(
            "Keep an eye on indexing progress and recent parser or worker failures without leaving the settings surface.",
            tab,
        )
        caption.setObjectName("SectionCaption")
        caption.setWordWrap(True)
        layout.addWidget(caption)

        pills_row = QHBoxLayout()
        self.documents_pill = self._make_pill()
        self.jobs_pill = self._make_pill()
        self.failures_pill = self._make_pill()
        pills_row.addWidget(self.documents_pill)
        pills_row.addWidget(self.jobs_pill)
        pills_row.addWidget(self.failures_pill)
        pills_row.addStretch(1)
        layout.addLayout(pills_row)

        overview_card = QFrame(tab)
        overview_card.setObjectName("SettingsCard")
        overview_layout = QVBoxLayout(overview_card)
        overview_layout.setContentsMargins(16, 16, 16, 16)
        overview_layout.setSpacing(12)
        layout.addWidget(overview_card, 1)

        self.overview_text = QPlainTextEdit(tab)
        self.overview_text.setReadOnly(True)
        overview_layout.addWidget(self.overview_text, 1)

        failures_title = QLabel("Recent failures", tab)
        failures_title.setObjectName("Eyebrow")
        layout.addWidget(failures_title)

        failures_card = QFrame(tab)
        failures_card.setObjectName("SettingsCard")
        failures_layout = QVBoxLayout(failures_card)
        failures_layout.setContentsMargins(16, 16, 16, 16)
        failures_layout.setSpacing(12)
        layout.addWidget(failures_card, 1)

        self.failures_list = QListWidget(tab)
        failures_layout.addWidget(self.failures_list, 1)

        refresh_button = QPushButton("Refresh health", tab)
        refresh_button.setObjectName("PrimaryButton")
        refresh_button.clicked.connect(self.refresh_monitor_data)
        layout.addWidget(refresh_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.refresh_monitor_data()
        return tab

    def _build_maintenance_tab(self) -> QWidget:
        tab = QFrame(self)
        tab.setObjectName("SettingsPane")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)

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

        commands_card = QFrame(tab)
        commands_card.setObjectName("SettingsCommandCard")
        commands_layout = QVBoxLayout(commands_card)
        commands_layout.setContentsMargins(16, 16, 16, 16)
        commands_layout.setSpacing(12)
        layout.addWidget(commands_card)

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
        commands_layout.addLayout(button_grid)

        reindex_card = QFrame(tab)
        reindex_card.setObjectName("SettingsCard")
        reindex_layout = QVBoxLayout(reindex_card)
        reindex_layout.setContentsMargins(16, 16, 16, 16)
        reindex_layout.setSpacing(12)
        layout.addWidget(reindex_card)

        path_label = QLabel("Reindex a specific file path", tab)
        path_label.setObjectName("Eyebrow")
        reindex_layout.addWidget(path_label)

        self.reindex_path_input = QLineEdit(tab)
        self.reindex_path_input.setObjectName("PathInput")
        self.reindex_path_input.setPlaceholderText("Choose a file to enqueue for reindexing")
        reindex_layout.addWidget(self.reindex_path_input)

        file_row = QHBoxLayout()
        file_browse = QPushButton("Browse File", tab)
        file_browse.clicked.connect(self.choose_file_path)
        file_row.addWidget(file_browse)
        file_run = QPushButton("Run Reindex Path", tab)
        file_run.clicked.connect(lambda: self.run_command("reindex-path", self.reindex_path_input.text().strip()))
        file_row.addWidget(file_run)
        file_row.addStretch(1)
        reindex_layout.addLayout(file_row)

        folder_label = QLabel("Reindex every supported document in a folder", tab)
        folder_label.setObjectName("Eyebrow")
        reindex_layout.addWidget(folder_label)

        self.reindex_folder_input = QLineEdit(tab)
        self.reindex_folder_input.setObjectName("PathInput")
        self.reindex_folder_input.setPlaceholderText("Choose a monitored folder or any supported document directory")
        reindex_layout.addWidget(self.reindex_folder_input)

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
        reindex_layout.addLayout(folder_row)

        output_card = QFrame(tab)
        output_card.setObjectName("SettingsCard")
        output_layout = QVBoxLayout(output_card)
        output_layout.setContentsMargins(16, 16, 16, 16)
        output_layout.setSpacing(12)
        layout.addWidget(output_card, 1)

        self.maintenance_output = QPlainTextEdit(tab)
        self.maintenance_output.setObjectName("MaintenanceOutput")
        self.maintenance_output.setReadOnly(True)
        self.maintenance_output.setPlaceholderText("Command output will appear here.")
        output_layout.addWidget(self.maintenance_output, 1)

        return tab

    def _make_pill(self) -> QLabel:
        label = QLabel(self)
        label.setObjectName("Pill")
        return label

    def refresh_folder_list(self) -> None:
        self.folder_list.clear()
        for folder in self.settings.monitored_folders:
            suffix = "" if folder.accessible else " | access needs attention"
            item = QListWidgetItem(folder.path + suffix)
            item.setData(Qt.ItemDataRole.UserRole, folder.path)
            self.folder_list.addItem(item)

    def save_launcher_shortcut(self) -> None:
        sequence = self.launcher_shortcut_input.keySequence().toString(QKeySequence.SequenceFormat.PortableText)
        self.settings.launcher_shortcut = sequence or DEFAULT_LAUNCH_SHORTCUT
        self.services.settings.save(self.settings)
        self.on_settings_changed()

    def reset_launcher_shortcut(self) -> None:
        self.launcher_shortcut_input.setKeySequence(QKeySequence(DEFAULT_LAUNCH_SHORTCUT))
        self.save_launcher_shortcut()

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
        self.refresh_monitor_data()
        self.on_settings_changed()

    def refresh_monitor_data(self) -> None:
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

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._drag_offset = None
        super().mouseReleaseEvent(event)


class SearchResultsDialog(QDialog):
    def __init__(
        self,
        app_controller: ShelfApplication,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.app_controller = app_controller
        self.result_cards: list[SearchResultCard] = []
        self.selected_index = -1

        self.setWindowTitle("Shelf Results")
        self.resize(760, 360)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setStyleSheet(APP_STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 18)
        layout.setSpacing(0)

        self.shell = QFrame(self)
        self.shell.setObjectName("ResultsShell")
        shell_layout = QVBoxLayout(self.shell)
        shell_layout.setContentsMargins(16, 16, 16, 16)
        shell_layout.setSpacing(12)
        layout.addWidget(self.shell)
        effect = QGraphicsDropShadowEffect(self.shell)
        effect.setBlurRadius(36)
        effect.setOffset(0, 16)
        color = effect.color()
        color.setAlpha(110)
        effect.setColor(color)
        self.shell.setGraphicsEffect(effect)

        self.title_label = QLabel("Results", self.shell)
        self.title_label.setObjectName("SectionTitle")
        shell_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("", self.shell)
        self.subtitle_label.setObjectName("SectionCaption")
        self.subtitle_label.setWordWrap(True)
        shell_layout.addWidget(self.subtitle_label)

        self.progress_bar = QProgressBar(self.shell)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        shell_layout.addWidget(self.progress_bar)

        self.status_bar = QStatusBar(self)
        self.status_bar.setSizeGripEnabled(False)

        self.scroll = QScrollArea(self.shell)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setViewportMargins(0, 0, 10, 0)
        shell_layout.addWidget(self.scroll, 1)

        self.results_container = QWidget(self.scroll)
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(0, 0, 6, 0)
        self.results_layout.setSpacing(10)
        self.scroll.setWidget(self.results_container)
        shell_layout.addWidget(self.status_bar)
        self.hide()

    def open_result(self, path: str) -> None:
        self.app_controller.open_in_preview(path)
        self.status_bar.showMessage(f"Opening {Path(path).name} in Preview", 2500)
        self.hide()

    def update_results(self, query: str, results: list[SearchResult]) -> None:
        self.title_label.setText(f'Results for "{query}"')
        self.selected_index = -1
        if results:
            self.subtitle_label.setText(f"{len(results)} quick matches")
        else:
            self.subtitle_label.setText("No matching files yet.")

        self.result_cards.clear()
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if results:
            for result in results:
                card = SearchResultCard(result, self.app_controller, self.status_bar, self.results_container)
                card.clicked.connect(lambda selected=result: self.open_result(selected.path))
                self.results_layout.addWidget(card)
                self.result_cards.append(card)
        else:
            empty = QFrame(self.results_container)
            empty.setObjectName("EmptyCard")
            empty_layout = QVBoxLayout(empty)
            empty_layout.setContentsMargins(24, 24, 24, 24)
            empty_layout.setSpacing(8)
            empty_title = QLabel("No matches found", empty)
            empty_title.setObjectName("EmptyTitle")
            empty_layout.addWidget(empty_title)
            empty_body = QLabel(
                "Keep typing to refine the search, or check indexing health in Settings.",
                empty,
            )
            empty_body.setObjectName("EmptyBody")
            empty_body.setWordWrap(True)
            empty_layout.addWidget(empty_body)
            self.results_layout.addWidget(empty)

        self.results_layout.addStretch(1)
        self.set_selected_index(0 if self.result_cards else -1)

    def set_loading(self, loading: bool) -> None:
        self.progress_bar.setVisible(loading)

    def set_selected_index(self, index: int) -> None:
        if not self.result_cards:
            self.selected_index = -1
            return
        bounded = max(0, min(index, len(self.result_cards) - 1))
        self.selected_index = bounded
        for card_index, card in enumerate(self.result_cards):
            card.set_active(card_index == bounded)
        active_card = self.result_cards[bounded]
        self.scroll.ensureWidgetVisible(active_card, 0, 24)

    def select_next(self) -> None:
        if not self.result_cards:
            return
        if self.selected_index < 0:
            self.set_selected_index(0)
            return
        self.set_selected_index(min(self.selected_index + 1, len(self.result_cards) - 1))

    def select_previous(self) -> None:
        if not self.result_cards:
            return
        if self.selected_index < 0:
            self.set_selected_index(0)
            return
        self.set_selected_index(max(self.selected_index - 1, 0))

    def activate_selected(self) -> None:
        if 0 <= self.selected_index < len(self.result_cards):
            self.open_result(self.result_cards[self.selected_index].result.path)

    def reveal_selected(self) -> None:
        if 0 <= self.selected_index < len(self.result_cards):
            self.app_controller.reveal_file(self.result_cards[self.selected_index].result.path)

    def anchor_below(self, parent: QWidget) -> None:
        origin = parent.mapToGlobal(QPoint(0, parent.height() + 6))
        self.move(origin.x(), origin.y())

    def show_for_query(self, parent: QWidget, query: str, results: list[SearchResult]) -> None:
        self.update_results(query, results)
        self.setFixedWidth(parent.width())
        self.resize(parent.width(), 360)
        self.anchor_below(parent)
        self.show()
        self.raise_()

    def hide_for_empty_query(self) -> None:
        self.hide()


class MainWindow(QMainWindow):
    def __init__(self, services: ServiceContainer, settings: AppSettings, app_controller: ShelfApplication) -> None:
        super().__init__()
        self.services = services
        self.settings = settings
        self.app_controller = app_controller
        self._drag_offset: QPoint | None = None
        self._search_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="shelf-ui-search")
        self._live_search_timer = QTimer(self)
        self._live_search_timer.setInterval(380)
        self._live_search_timer.setSingleShot(True)
        self._live_search_timer.timeout.connect(self._queue_live_search)
        self._active_search: Future | None = None
        self._queued_query: str | None = None
        self._active_query: str | None = None
        self._navigating_results = False
        self._settings_dialog: SettingsDialog | None = None
        self._launcher_shortcut = MacLauncherShortcut(self.toggle_launcher_window)
        self.results_popup = SearchResultsDialog(self.app_controller, self)

        self.setWindowTitle("Shelf")
        self.resize(760, 220)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setStyleSheet(APP_STYLESHEET)

        self._build_actions()
        self._build_ui()
        self._configure_launcher_shortcut()
        self.search_input.setFocus()

        if settings.last_error:
            self.statusBar().showMessage(settings.last_error, 8000)

    def _build_actions(self) -> None:
        settings_action = QAction("Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.open_settings)
        self.addAction(settings_action)

    def _build_ui(self) -> None:
        status_bar = QStatusBar(self)
        status_bar.showMessage("Ready")
        status_bar.setSizeGripEnabled(False)
        self.setStatusBar(status_bar)
        status_bar.hide()

        central = QWidget(self)
        central.setObjectName("FloatingRoot")
        self.setCentralWidget(central)
        central.installEventFilter(self)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(26, 26, 26, 26)
        root_layout.setSpacing(0)
        root_layout.addStretch(1)

        composer_row = QHBoxLayout()
        composer_row.addStretch(1)

        composer_shell = QFrame(central)
        composer_shell.setObjectName("ComposerShell")
        self.composer_shell = composer_shell
        self._apply_shadow(composer_shell, blur=40, offset_y=18, alpha=110)
        composer_shell_layout = QHBoxLayout(composer_shell)
        composer_shell_layout.setContentsMargins(18, 12, 18, 12)
        composer_shell_layout.setSpacing(8)
        composer_shell.setMinimumWidth(620)

        self.search_input = QLineEdit(composer_shell)
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Search files using natural language or keywords")
        self.search_input.installEventFilter(self)
        self.search_input.textChanged.connect(self.schedule_live_search)
        self.search_input.returnPressed.connect(self.open_primary_result)
        composer_shell_layout.addWidget(self.search_input, 1)

        settings_button = QToolButton(composer_shell)
        settings_button.setObjectName("SettingsIconButton")
        settings_button.setText("⚙")
        settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_button.setToolTip("Settings")
        settings_button.setFixedSize(38, 38)
        settings_button.clicked.connect(self.open_settings)
        composer_shell_layout.addWidget(settings_button)

        composer_row.addWidget(composer_shell)
        composer_row.addStretch(1)
        root_layout.addLayout(composer_row)
        root_layout.addStretch(1)

    def _apply_shadow(self, widget: QWidget, blur: int, offset_y: int, alpha: int) -> None:
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(blur)
        shadow.setOffset(0, offset_y)
        shadow.setColor(Qt.GlobalColor.black)
        color = shadow.color()
        color.setAlpha(alpha)
        shadow.setColor(color)
        widget.setGraphicsEffect(shadow)

    def eventFilter(self, watched: object, event: object) -> bool:
        if hasattr(self, "search_input") and watched is self.search_input and event.type() == QEvent.Type.KeyPress:
            if self._handle_results_navigation_key(event):
                return True
        if watched is self.centralWidget() and isinstance(event, QMouseEvent):
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                widget = self.childAt(event.position().toPoint())
                if isinstance(widget, (QLineEdit, QPushButton, QToolButton)):
                    return False
                self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                return True
            if event.type() == QEvent.Type.MouseMove and self._drag_offset is not None:
                self.move(event.globalPosition().toPoint() - self._drag_offset)
                return True
            if event.type() == QEvent.Type.MouseButtonRelease:
                self._drag_offset = None
                return True
        return super().eventFilter(watched, event)

    def run_search(self) -> None:
        query = self.search_input.text().strip()
        if not query:
            self.results_popup.hide_for_empty_query()
            return

        self.schedule_live_search(query)

    def schedule_live_search(self, text: str) -> None:
        query = text.strip()
        self._queued_query = query
        self._navigating_results = False
        if not query:
            self._live_search_timer.stop()
            self.results_popup.set_loading(False)
            self.results_popup.hide_for_empty_query()
            return
        self._live_search_timer.start()

    def _show_results_popup_loading(self) -> None:
        self.results_popup.set_loading(True)
        self.results_popup.resize(self.composer_shell.width(), self.results_popup.height())
        self.results_popup.anchor_below(self.composer_shell)
        self.results_popup.show()
        self.results_popup.raise_()
        self.search_input.setFocus(Qt.FocusReason.OtherFocusReason)

    def _queue_live_search(self) -> None:
        query = self._queued_query or ""
        if not query:
            self.results_popup.set_loading(False)
            self.results_popup.hide_for_empty_query()
            return
        self._show_results_popup_loading()
        if self._active_search is not None and not self._active_search.done():
            return
        self._active_query = query
        self._active_search = self._search_executor.submit(self.app_controller.live_search, query)
        QTimer.singleShot(25, self._poll_search_result)

    def _poll_search_result(self) -> None:
        future = self._active_search
        if future is None:
            return
        if not future.done():
            QTimer.singleShot(25, self._poll_search_result)
            return

        self._active_search = None

        try:
            results = future.result()
        except Exception as exc:  # pragma: no cover - defensive UI path
            self.results_popup.set_loading(False)
            self.statusBar().showMessage(str(exc), 3000)
            return

        if self._active_query != (self._queued_query or ""):
            self._queue_live_search()
            return
        self.results_popup.set_loading(False)
        self.results_popup.show_for_query(self.composer_shell, self._active_query or "", results)
        self.search_input.setFocus(Qt.FocusReason.OtherFocusReason)

    def open_primary_result(self) -> None:
        if self.results_popup.result_cards:
            if self._navigating_results:
                self.results_popup.activate_selected()
                return
            self.results_popup.open_result(self.results_popup.result_cards[0].result.path)

    def open_settings(self) -> None:
        self.results_popup.hide()
        dialog = SettingsDialog(self.services, self.settings, self.app_controller, self.refresh_after_settings, self)
        self._settings_dialog = dialog
        dialog.move(self.frameGeometry().center() - dialog.rect().center())
        dialog.exec()
        self._settings_dialog = None
        self.refresh_after_settings()

    def refresh_after_settings(self) -> None:
        self._configure_launcher_shortcut()
        self.search_input.setFocus()

    def _configure_launcher_shortcut(self) -> None:
        shortcut = self.settings.launcher_shortcut or DEFAULT_LAUNCH_SHORTCUT
        if not self._launcher_shortcut.register(shortcut):
            self.statusBar().showMessage(f"Could not register launcher shortcut: {shortcut}", 4000)

    def move_to_top_of_screen(self) -> None:
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is None:
            return
        geometry = screen.availableGeometry()
        x = geometry.x() + max(0, (geometry.width() - self.width()) // 2)
        y = geometry.y() + 44
        self.move(x, y)

    def show_search_window(self) -> None:
        if self._settings_dialog is not None and self._settings_dialog.isVisible():
            self._settings_dialog.hide()
        self.move_to_top_of_screen()
        self.show()
        self.raise_()
        self.activateWindow()
        self.search_input.setFocus(Qt.FocusReason.ShortcutFocusReason)

    def hide_search_window(self) -> None:
        self._navigating_results = False
        self.results_popup.hide()
        self.hide()

    def toggle_launcher_window(self) -> None:
        if self.isVisible():
            self.hide_search_window()
            return
        self.show_search_window()

    def moveEvent(self, event) -> None:  # noqa: N802
        super().moveEvent(event)
        if self.results_popup.isVisible():
            self.results_popup.anchor_below(self.composer_shell)

    def _handle_results_navigation_key(self, event) -> bool:
        if self.results_popup.isVisible() and self.results_popup.result_cards:
            if event.key() in {Qt.Key.Key_Down, Qt.Key.Key_Tab} and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                self._navigating_results = True
                self.results_popup.select_next()
                event.accept()
                return True
            if event.key() in {Qt.Key.Key_Up, Qt.Key.Key_Backtab} or (
                event.key() == Qt.Key.Key_Tab and event.modifiers() & Qt.KeyboardModifier.ShiftModifier
            ):
                self._navigating_results = True
                self.results_popup.select_previous()
                event.accept()
                return True
            if event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter} and self._navigating_results:
                self.results_popup.activate_selected()
                event.accept()
                return True
            if event.key() == Qt.Key.Key_R and event.modifiers() & Qt.KeyboardModifier.MetaModifier and self._navigating_results:
                self.results_popup.reveal_selected()
                event.accept()
                return True
            if event.key() == Qt.Key.Key_Escape:
                if self._navigating_results:
                    self._navigating_results = False
                    self.search_input.setFocus(Qt.FocusReason.ShortcutFocusReason)
                    event.accept()
                    return True
                self.hide_search_window()
                event.accept()
                return True
        return False

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if self._handle_results_navigation_key(event):
            return
        super().keyPressEvent(event)

    def _handle_window_deactivated(self) -> None:
        if self._settings_dialog is not None and self._settings_dialog.isVisible():
            return
        self.hide_search_window()

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.ActivationChange and self.isVisible() and not self.isActiveWindow():
            self._handle_window_deactivated()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.move_to_top_of_screen()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self.results_popup.isVisible():
            self.results_popup.resize(self.composer_shell.width(), self.results_popup.height())
            self.results_popup.anchor_below(self.composer_shell)

    def closeEvent(self, event) -> None:  # noqa: N802
        self.results_popup.close()
        self._launcher_shortcut.close()
        self._search_executor.shutdown(wait=False, cancel_futures=True)
        super().closeEvent(event)
