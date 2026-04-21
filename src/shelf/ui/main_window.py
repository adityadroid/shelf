from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
import json
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QEvent, QPoint, QTimer, Qt, Signal
from PySide6.QtGui import QAction, QGuiApplication, QIcon, QKeySequence, QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
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
    QMenu,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QStatusBar,
    QSystemTrayIcon,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from shelf.core.application import FailureRecord, ShelfApplication
from shelf.core.folders import remove_folder_by_path, validate_folder_candidate
from shelf.core.models import (
    AppSettings,
    DEFAULT_LAUNCH_SHORTCUT,
    DOCUMENT_TYPE_LABELS,
    MonitoredFolder,
    normalize_enabled_extensions,
)
from shelf.core.services import ServiceContainer
from shelf.indexing.models import SearchResult
from shelf.ui.launcher_shortcut import MacLauncherShortcut


APP_STYLESHEET = """
QMainWindow, QDialog {
    background: transparent;
}
QWidget {
    color: #dbeafe;
    font-size: 14px;
    background: transparent;
}
QWidget#FloatingRoot {
    background: transparent;
}
QFrame#GlassPanel, QFrame#EmptyCard {
    background: rgba(15, 23, 42, 0.84);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 24px;
}
QFrame#ComposerShell {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 rgba(15, 23, 42, 0.96),
        stop: 0.55 rgba(30, 41, 59, 0.96),
        stop: 1 rgba(37, 99, 235, 0.74)
    );
    border: 1px solid rgba(125, 211, 252, 0.28);
    border-radius: 24px;
}
QFrame#ResultsShell {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 rgba(15, 23, 42, 0.96),
        stop: 1 rgba(30, 41, 59, 0.96)
    );
    border: 1px solid rgba(96, 165, 250, 0.24);
    border-radius: 24px;
}
QFrame#ResultCard {
    background: rgba(51, 65, 85, 0.42);
    border: 1px solid rgba(148, 163, 184, 0.14);
    border-radius: 16px;
}
QFrame#ResultCard[active="true"] {
    background: rgba(37, 99, 235, 0.22);
    border: 1px solid rgba(96, 165, 250, 0.36);
}
QFrame#ResultCard:hover, QFrame#GlassPanel:hover, QFrame#EmptyCard:hover {
    background: rgba(51, 65, 85, 0.56);
    border: 1px solid rgba(125, 211, 252, 0.22);
}
QFrame#SettingsShell {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 rgba(8, 15, 33, 0.98),
        stop: 0.45 rgba(15, 23, 42, 0.98),
        stop: 1 rgba(30, 64, 175, 0.78)
    );
    border: 1px solid rgba(96, 165, 250, 0.24);
    border-radius: 30px;
}
QFrame#SettingsHero {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 rgba(37, 99, 235, 0.28),
        stop: 0.55 rgba(30, 41, 59, 0.52),
        stop: 1 rgba(14, 165, 233, 0.18)
    );
    border: 1px solid rgba(191, 219, 254, 0.18);
    border-radius: 24px;
}
QFrame#SettingsSidebar {
    background: rgba(15, 23, 42, 0.72);
    border: 1px solid rgba(148, 163, 184, 0.14);
    border-radius: 22px;
}
QFrame#SettingsPane {
    background: rgba(15, 23, 42, 0.4);
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 24px;
}
QFrame#SettingsOverviewPane {
    background: transparent;
    border: none;
}
QFrame#SettingsCard, QFrame#SettingsCommandCard {
    background: rgba(51, 65, 85, 0.28);
    border: 1px solid rgba(148, 163, 184, 0.16);
    border-radius: 20px;
}
QFrame#StatCard, QFrame#SidebarStatusCard, QFrame#ShortcutChip {
    background: rgba(15, 23, 42, 0.44);
    border: 1px solid rgba(148, 163, 184, 0.16);
    border-radius: 14px;
}
QFrame#ShortcutChip {
    background: rgba(30, 41, 59, 0.8);
    border-radius: 10px;
}
QLabel#Eyebrow {
    color: #60a5fa;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}
QLabel#HeroTitle {
    color: #eff6ff;
    font-size: 36px;
    font-weight: 600;
}
QLabel#HeroSubtitle {
    color: rgba(219, 234, 254, 0.84);
    font-size: 14px;
}
QLabel#SectionTitle {
    color: #e2e8f0;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
QLabel#SettingsTitle {
    color: #f8fbff;
    font-size: 32px;
    font-weight: 600;
}
QLabel#SettingsSubtitle {
    color: rgba(219, 234, 254, 0.8);
    font-size: 14px;
}
QLabel#CardTitle {
    color: #f8fbff;
    font-size: 14px;
    font-weight: 700;
}
QLabel#CardSubtitle, QLabel#NavMeta, QLabel#SidebarStatusMeta {
    color: rgba(191, 219, 254, 0.74);
    font-size: 12px;
}
QLabel#StatNumber {
    color: #38bdf8;
    font-size: 28px;
    font-weight: 700;
}
QLabel#StatLabel {
    color: rgba(219, 234, 254, 0.82);
    font-size: 11px;
}
QLabel#StatusOkay {
    color: #86efac;
    font-size: 12px;
    font-weight: 600;
}
QLabel#ShortcutPlus {
    color: rgba(219, 234, 254, 0.84);
    font-size: 16px;
    font-weight: 700;
}
QLabel#ShortcutChipLabel {
    color: #f8fbff;
    font-size: 12px;
    font-weight: 700;
}
QLabel#SectionCaption, QLabel#MetaText, QLabel#PathText, QLabel#ComposerHint {
    color: rgba(191, 219, 254, 0.82);
}
QLabel#ResultTitle {
    color: #f8fbff;
    font-size: 13px;
    font-weight: 700;
}
QLabel#PathText {
    font-size: 10px;
}
QPushButton#RevealButton {
    background: rgba(37, 99, 235, 0.18);
    border: 1px solid rgba(96, 165, 250, 0.22);
    border-radius: 12px;
    color: #dbeafe;
    font-size: 12px;
    min-height: 32px;
    max-height: 32px;
    padding: 0 12px;
}
QPushButton#RevealButton:hover {
    background: rgba(37, 99, 235, 0.28);
}
QLabel#Pill {
    background: rgba(37, 99, 235, 0.18);
    border: 1px solid rgba(96, 165, 250, 0.28);
    border-radius: 14px;
    color: #dbeafe;
    font-size: 12px;
    font-weight: 600;
    padding: 6px 12px;
}
QLabel#EmptyTitle {
    color: #eff6ff;
    font-size: 18px;
    font-weight: 700;
}
QLabel#EmptyBody {
    color: rgba(191, 219, 254, 0.78);
    font-size: 12px;
}
QLineEdit#SearchInput, QLineEdit#PathInput, QKeySequenceEdit#PathInput, QPlainTextEdit#MaintenanceOutput {
    background: rgba(15, 23, 42, 0.72);
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 14px;
    color: #eff6ff;
    padding: 14px 18px;
    selection-background-color: rgba(59, 130, 246, 0.5);
}
QLineEdit#PathInput[readOnly="true"] {
    color: rgba(219, 234, 254, 0.92);
}
QKeySequenceEdit#PathInput {
    min-height: 48px;
    padding: 0 16px;
}
QKeySequenceEdit#PathInput::part(lineedit) {
    background: transparent;
    border: none;
    color: #eff6ff;
}
QLineEdit#SearchInput {
    background: transparent;
    border: none;
    color: #eff6ff;
    font-size: 17px;
    font-weight: 600;
    padding: 10px 10px;
}
QLineEdit#SearchInput::placeholder, QLineEdit#PathInput::placeholder, QPlainTextEdit#MaintenanceOutput::placeholder {
    color: rgba(148, 163, 184, 0.74);
}
QLineEdit#PathInput:focus, QKeySequenceEdit#PathInput:focus, QPlainTextEdit#MaintenanceOutput:focus {
    border: 1px solid rgba(96, 165, 250, 0.68);
}
QCheckBox#DocumentTypeCheckbox {
    color: #dbeafe;
    spacing: 10px;
    padding: 4px 0;
}
QCheckBox#DocumentTypeCheckbox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid rgba(148, 163, 184, 0.3);
    background: rgba(15, 23, 42, 0.72);
}
QCheckBox#DocumentTypeCheckbox::indicator:checked {
    background: #2563eb;
    border: 1px solid rgba(191, 219, 254, 0.42);
}
QPushButton {
    background: rgba(51, 65, 85, 0.56);
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 14px;
    color: #dbeafe;
    font-weight: 600;
    min-height: 40px;
    padding: 0 18px;
}
QPushButton:hover {
    background: rgba(71, 85, 105, 0.72);
    border: 1px solid rgba(125, 211, 252, 0.22);
}
QPushButton#PrimaryButton {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #2563eb,
        stop: 1 #0ea5e9
    );
    border: 1px solid rgba(191, 219, 254, 0.26);
    color: #eff6ff;
    padding: 0 18px;
}
QPushButton#PrimaryButton:hover {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #3b82f6,
        stop: 1 #38bdf8
    );
}
QPushButton#GhostButton {
    background: rgba(15, 23, 42, 0.58);
    border: 1px solid rgba(148, 163, 184, 0.18);
    color: #dbeafe;
    padding: 0 16px;
}
QPushButton#DangerButton {
    background: rgba(127, 29, 29, 0.3);
    border: 1px solid rgba(248, 113, 113, 0.22);
    color: #fecaca;
}
QPushButton#DangerButton:hover {
    background: rgba(153, 27, 27, 0.42);
}
QPushButton#SettingsNavButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 16px;
    color: rgba(191, 219, 254, 0.7);
    font-size: 14px;
    font-weight: 600;
    min-height: 56px;
    padding: 0 16px;
    text-align: left;
}
QPushButton#SettingsNavButton:hover {
    background: rgba(37, 99, 235, 0.12);
    color: #eff6ff;
}
QPushButton#SettingsNavButton:checked {
    background: rgba(37, 99, 235, 0.18);
    border: 1px solid rgba(96, 165, 250, 0.28);
    color: #f8fbff;
}
QToolButton {
    background: rgba(241, 245, 249, 0.92);
    border: 1px solid rgba(191, 219, 254, 0.62);
    border-radius: 14px;
    color: #0f172a;
    padding: 8px 10px;
}
QToolButton#SettingsIconButton {
    background: rgba(37, 99, 235, 0.18);
    border: 1px solid rgba(125, 211, 252, 0.24);
    border-radius: 16px;
    color: #eff6ff;
    font-size: 20px;
    font-weight: 700;
    padding: 6px;
}
QToolButton#SettingsIconButton:hover {
    background: rgba(37, 99, 235, 0.3);
}
QToolButton#SettingsCloseButton {
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(148, 163, 184, 0.22);
    border-radius: 8px;
    color: #e2e8f0;
    font-size: 14px;
    font-weight: 500;
    padding: 0;
}
QToolButton#SettingsCloseButton:hover {
    background: rgba(239, 68, 68, 0.86);
    border: 1px solid rgba(248, 113, 113, 0.95);
    color: #ffffff;
}
QToolButton#SettingsCloseButton:pressed {
    background: rgba(220, 38, 38, 0.96);
    border: 1px solid rgba(248, 113, 113, 1);
    color: #ffffff;
}
QScrollArea {
    background: transparent;
    border: none;
}
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 10px 8px 10px 0;
}
QScrollBar::handle:vertical {
    background: rgba(96, 165, 250, 0.35);
    border-radius: 3px;
    min-height: 26px;
}
QScrollBar:horizontal {
    background: transparent;
    height: 6px;
    margin: 0 10px 8px 10px;
}
QScrollBar::handle:horizontal {
    background: rgba(96, 165, 250, 0.35);
    border-radius: 3px;
    min-width: 26px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
    height: 0;
    width: 0;
}
QProgressBar {
    background: rgba(51, 65, 85, 0.42);
    border: none;
    border-radius: 3px;
    max-height: 6px;
}
QProgressBar::chunk {
    background: rgba(96, 165, 250, 0.9);
    border-radius: 3px;
}
QListWidget, QPlainTextEdit {
    background: rgba(15, 23, 42, 0.52);
    border: 1px solid rgba(148, 163, 184, 0.14);
    border-radius: 16px;
    color: #eff6ff;
}
QListWidget {
    padding: 8px;
}
QListWidget#OverviewFolderList {
    padding: 0;
}
QListWidget#OverviewFolderList::item {
    border-bottom: 1px solid rgba(148, 163, 184, 0.08);
    padding: 14px 10px;
}
QListWidget#FolderAuditList::item {
    padding: 12px 10px;
}
QPlainTextEdit {
    padding: 10px;
}
QListWidget::item {
    border-radius: 10px;
    padding: 10px 12px;
}
QListWidget::item:selected {
    background: rgba(37, 99, 235, 0.22);
    color: #f8fbff;
}
QStatusBar {
    background: transparent;
    color: rgba(191, 219, 254, 0.78);
}
"""


ICON_PATH = Path(__file__).resolve().parent / "assets" / "shelf_icon.svg"
APP_VERSION = _version = "0.1.0"
try:
    APP_VERSION = version("shelf")
except PackageNotFoundError:
    APP_VERSION = _version


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
    RESIZE_MARGIN = 10

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
        self._resize_edges: set[str] = set()
        self._resize_start_geometry = None
        self._resize_start_global: QPoint | None = None
        self._nav_definitions = (
            ("⌂", "Overview", "Control room & actions", self._build_overview_tab),
            ("⌘", "Application", "Document types & storage", self._build_general_tab),
            ("♡", "Library Health", "Indexing & diagnostics", self._build_monitor_tab),
            ("⟳", "Maintenance", "Output & command history", self._build_maintenance_tab),
        )
        self._section_indexes = {
            "overview": 0,
            "application": 1,
            "health": 2,
            "maintenance": 3,
        }

        self.setWindowTitle("Shelf Settings")
        self.resize(1320, 880)
        self.setMinimumSize(820, 560)
        self.setObjectName("SettingsDialog")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setStyleSheet(APP_STYLESHEET)
        self.setMouseTracking(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(0)

        self.shell = QFrame(self)
        self.shell.setObjectName("SettingsShell")
        self._apply_shadow(self.shell, blur=44, offset_y=20, alpha=120)
        shell_layout = QVBoxLayout(self.shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        layout.addWidget(self.shell)

        header = QFrame(self.shell)
        header.setObjectName("SettingsHero")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 20, 20, 20)
        header_layout.setSpacing(18)
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
        close_button.setText("×")
        close_button.setToolTip("Close settings")
        close_button.setFixedSize(28, 28)
        close_button.clicked.connect(self.accept)
        header_layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignTop)

        content = QFrame(self.shell)
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        shell_layout.addWidget(content, 1)

        sidebar = QFrame(content)
        sidebar.setObjectName("SettingsSidebar")
        sidebar.setFixedWidth(252)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(18, 18, 18, 18)
        sidebar_layout.setSpacing(12)
        content_layout.addWidget(sidebar, 0)

        sidebar_title = QLabel("Sections", sidebar)
        sidebar_title.setObjectName("Eyebrow")
        sidebar_layout.addWidget(sidebar_title)
        self.sidebar_status_card = self._build_sidebar_status_card(sidebar)

        self.section_buttons = QButtonGroup(self)
        self.section_buttons.setExclusive(True)
        self.page_stack = QStackedWidget(content)
        content_layout.addWidget(self.page_stack, 1)

        for index, (icon, label, meta, factory) in enumerate(self._nav_definitions):
            button = QPushButton(f"{icon}  {label}\n{meta}", sidebar)
            button.setObjectName("SettingsNavButton")
            button.setCheckable(True)
            button.clicked.connect(lambda _checked=False, selected=index: self.page_stack.setCurrentIndex(selected))
            self.section_buttons.addButton(button, index)
            sidebar_layout.addWidget(button)
            self.page_stack.addWidget(factory())

        sidebar_layout.addStretch(1)
        sidebar_layout.addWidget(self.sidebar_status_card)
        first_button = self.section_buttons.button(0)
        if first_button is not None:
            first_button.setChecked(True)
        self.page_stack.setCurrentIndex(0)
        self.refresh_folder_list()
        self.refresh_monitor_data()
        self._render_shortcut_chips(self.settings.launcher_shortcut or DEFAULT_LAUNCH_SHORTCUT)

    def _apply_shadow(self, widget: QWidget, blur: int, offset_y: int, alpha: int) -> None:
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(blur)
        shadow.setOffset(0, offset_y)
        shadow.setColor(Qt.GlobalColor.black)
        color = shadow.color()
        color.setAlpha(alpha)
        shadow.setColor(color)
        widget.setGraphicsEffect(shadow)

    def _make_scrollable_settings_page(self) -> tuple[QWidget, QWidget, QVBoxLayout]:
        wrapper = QFrame(self)
        wrapper.setObjectName("SettingsPane")
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(0)

        scroll = QScrollArea(wrapper)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setViewportMargins(0, 0, 10, 0)
        wrapper_layout.addWidget(scroll)

        content = QWidget(scroll)
        content.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)
        scroll.setWidget(content)
        return wrapper, content, layout

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item is None:
                continue
            child_layout = item.layout()
            if child_layout is not None:
                self._clear_layout(child_layout)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

    def _resize_edges_for_global_pos(self, global_pos: QPoint) -> set[str]:
        frame = self.frameGeometry()
        margin = self.RESIZE_MARGIN
        edges: set[str] = set()
        if abs(global_pos.x() - frame.left()) <= margin:
            edges.add("left")
        elif abs(global_pos.x() - frame.right()) <= margin:
            edges.add("right")
        if abs(global_pos.y() - frame.top()) <= margin:
            edges.add("top")
        elif abs(global_pos.y() - frame.bottom()) <= margin:
            edges.add("bottom")
        return edges

    def _update_resize_cursor(self, global_pos: QPoint) -> None:
        edges = self._resize_edges_for_global_pos(global_pos)
        if edges == {"left"} or edges == {"right"}:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif edges == {"top"} or edges == {"bottom"}:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        elif edges in ({"left", "top"}, {"right", "bottom"}):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif edges in ({"right", "top"}, {"left", "bottom"}):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif self._drag_offset is None and not self._resize_edges:
            self.unsetCursor()

    def _resize_window(self, global_pos: QPoint) -> None:
        if not self._resize_edges or self._resize_start_geometry is None or self._resize_start_global is None:
            return

        delta = global_pos - self._resize_start_global
        geometry = self._resize_start_geometry.adjusted(0, 0, 0, 0)
        minimum_width = max(self.minimumWidth(), 820)
        minimum_height = max(self.minimumHeight(), 560)

        if "left" in self._resize_edges:
            new_left = min(geometry.right() - minimum_width, geometry.left() + delta.x())
            geometry.setLeft(new_left)
        if "right" in self._resize_edges:
            geometry.setRight(max(geometry.left() + minimum_width, geometry.right() + delta.x()))
        if "top" in self._resize_edges:
            new_top = min(geometry.bottom() - minimum_height, geometry.top() + delta.y())
            geometry.setTop(new_top)
        if "bottom" in self._resize_edges:
            geometry.setBottom(max(geometry.top() + minimum_height, geometry.bottom() + delta.y()))

        self.setGeometry(geometry)

    def _build_sidebar_status_card(self, parent: QWidget) -> QFrame:
        card = QFrame(parent)
        card.setObjectName("SidebarStatusCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        self.sidebar_status_title = QLabel("Shelf is running", card)
        self.sidebar_status_title.setObjectName("CardTitle")
        layout.addWidget(self.sidebar_status_title)

        self.sidebar_status_version = QLabel(f"Version {APP_VERSION}", card)
        self.sidebar_status_version.setObjectName("SidebarStatusMeta")
        layout.addWidget(self.sidebar_status_version)

        self.sidebar_status_detail = QLabel("All systems operational", card)
        self.sidebar_status_detail.setObjectName("SidebarStatusMeta")
        self.sidebar_status_detail.setWordWrap(True)
        layout.addWidget(self.sidebar_status_detail)
        return card

    def _build_overview_tab(self) -> QWidget:
        wrapper = QFrame(self)
        wrapper.setObjectName("SettingsOverviewPane")
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(18, 18, 18, 18)
        wrapper_layout.setSpacing(0)

        scroll = QScrollArea(wrapper)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setViewportMargins(0, 0, 10, 0)
        wrapper_layout.addWidget(scroll)

        content = QWidget(scroll)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(18)
        scroll.setWidget(content)

        title = QLabel("Overview", content)
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        subtitle = QLabel("Use this space for the controls and signals that matter most while Shelf is running.", content)
        subtitle.setObjectName("SectionCaption")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        self.overview_shortcut_card = self._build_overview_shortcut_card(content)
        self.overview_health_card = self._build_overview_health_card(content)
        self.overview_folders_card = self._build_overview_folders_card(content)
        self.overview_commands_card = self._build_overview_commands_card(content)
        self.overview_reindex_card = self._build_overview_reindex_card(content)
        self.overview_failures_card = self._build_overview_failures_card(content)

        self.overview_grid = QGridLayout()
        self.overview_grid.setHorizontalSpacing(18)
        self.overview_grid.setVerticalSpacing(18)
        layout.addLayout(self.overview_grid)
        self._refresh_overview_layout()
        layout.addStretch(1)
        return wrapper

    def _refresh_overview_layout(self) -> None:
        if not hasattr(self, "overview_grid"):
            return
        self._clear_layout(self.overview_grid)
        available_width = self.page_stack.width() if hasattr(self, "page_stack") else self.width()
        wide = available_width >= 1120

        if wide:
            self.overview_grid.addWidget(self.overview_shortcut_card, 0, 0)
            self.overview_grid.addWidget(self.overview_health_card, 0, 1)
            self.overview_grid.addWidget(self.overview_folders_card, 1, 0)

            right_column = QVBoxLayout()
            right_column.setSpacing(18)
            right_column.addWidget(self.overview_commands_card)
            right_column.addWidget(self.overview_reindex_card)
            right_column.addStretch(1)
            self.overview_grid.addLayout(right_column, 1, 1)
            self.overview_grid.addWidget(self.overview_failures_card, 2, 0, 1, 2)
            self.overview_grid.setColumnStretch(0, 5)
            self.overview_grid.setColumnStretch(1, 4)
        else:
            self.overview_grid.addWidget(self.overview_shortcut_card, 0, 0)
            self.overview_grid.addWidget(self.overview_health_card, 1, 0)
            self.overview_grid.addWidget(self.overview_folders_card, 2, 0)
            self.overview_grid.addWidget(self.overview_commands_card, 3, 0)
            self.overview_grid.addWidget(self.overview_reindex_card, 4, 0)
            self.overview_grid.addWidget(self.overview_failures_card, 5, 0)
            self.overview_grid.setColumnStretch(0, 1)

    def _build_overview_shortcut_card(self, parent: QWidget) -> QFrame:
        card = QFrame(parent)
        card.setObjectName("SettingsCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Launcher Shortcut", card)
        title.setObjectName("CardTitle")
        layout.addWidget(title)

        caption = QLabel("Use this shortcut to show or hide Shelf from anywhere while the app is running.", card)
        caption.setObjectName("CardSubtitle")
        caption.setWordWrap(True)
        layout.addWidget(caption)

        panel = QFrame(card)
        panel.setObjectName("StatCard")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(14, 14, 14, 14)
        panel_layout.setSpacing(12)

        current_label = QLabel("Current Shortcut", panel)
        current_label.setObjectName("Eyebrow")
        panel_layout.addWidget(current_label)

        chip_row = QHBoxLayout()
        chip_row.setSpacing(10)
        self.shortcut_chips_host = QHBoxLayout()
        self.shortcut_chips_host.setSpacing(10)
        chip_row.addLayout(self.shortcut_chips_host)
        chip_row.addStretch(1)
        panel_layout.addLayout(chip_row)

        self.overview_shortcut_summary = QLabel("Default: Cmd+Option+S", panel)
        self.overview_shortcut_summary.setObjectName("CardSubtitle")
        self.overview_shortcut_summary.setWordWrap(True)
        panel_layout.addWidget(self.overview_shortcut_summary)

        actions = QHBoxLayout()
        edit_app_button = QPushButton("Customize Shortcut", panel)
        edit_app_button.setObjectName("PrimaryButton")
        edit_app_button.clicked.connect(lambda: self._select_section(self._section_indexes["application"]))
        actions.addWidget(edit_app_button)
        manage_folders_button = QPushButton("Reset to Default", panel)
        manage_folders_button.setObjectName("GhostButton")
        manage_folders_button.clicked.connect(self.reset_launcher_shortcut)
        actions.addWidget(manage_folders_button)
        actions.addStretch(1)
        panel_layout.addLayout(actions)
        layout.addWidget(panel)
        return card

    def _build_overview_health_card(self, parent: QWidget) -> QFrame:
        card = QFrame(parent)
        card.setObjectName("SettingsCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Health Summary", card)
        title.setObjectName("CardTitle")
        layout.addWidget(title)
        subtitle = QLabel("Live status of indexing and system health.", card)
        subtitle.setObjectName("CardSubtitle")
        layout.addWidget(subtitle)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self.summary_indexed_value, indexed_card = self._make_stat_card(card, "Indexed\nfiles")
        self.summary_queued_value, queued_card = self._make_stat_card(card, "Queued\nfiles")
        self.summary_failures_value, failures_card = self._make_stat_card(card, "Failures\ndetected")
        stats_row.addWidget(indexed_card)
        stats_row.addWidget(queued_card)
        stats_row.addWidget(failures_card)
        layout.addLayout(stats_row)

        footer = QHBoxLayout()
        footer.setSpacing(12)
        self.health_status_label = QLabel("● Shelf is healthy and up to date", card)
        self.health_status_label.setObjectName("StatusOkay")
        footer.addWidget(self.health_status_label)
        footer.addStretch(1)
        details_button = QPushButton("View Library Health", card)
        details_button.setObjectName("GhostButton")
        details_button.clicked.connect(lambda: self._select_section(self._section_indexes["health"]))
        footer.addWidget(details_button)
        layout.addLayout(footer)
        return card

    def _build_overview_folders_card(self, parent: QWidget) -> QFrame:
        card = QFrame(parent)
        card.setObjectName("SettingsCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Monitored Folders", card)
        title.setObjectName("CardTitle")
        layout.addWidget(title)

        subtitle = QLabel("Folders being indexed and watched for changes.", card)
        subtitle.setObjectName("CardSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        self.folder_list = QListWidget(card)
        self.folder_list.setObjectName("OverviewFolderList")
        self.folder_list.itemSelectionChanged.connect(self._sync_folder_actions)
        layout.addWidget(self.folder_list, 1)

        self.overview_folder_summary = QLabel("", card)
        self.overview_folder_summary.setObjectName("CardSubtitle")
        self.overview_folder_summary.setWordWrap(True)
        layout.addWidget(self.overview_folder_summary)

        row = QHBoxLayout()
        row.setSpacing(10)

        add_button = QPushButton("Add Folder", card)
        add_button.setObjectName("PrimaryButton")
        add_button.clicked.connect(self.add_folder)
        add_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        row.addWidget(add_button)

        self.remove_folder_button = QPushButton("Remove Folder", card)
        self.remove_folder_button.setObjectName("DangerButton")
        self.remove_folder_button.clicked.connect(self.remove_selected_folder)
        self.remove_folder_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        row.addWidget(self.remove_folder_button)
        layout.addLayout(row)
        self._sync_folder_actions()
        return card

    def _build_overview_commands_card(self, parent: QWidget) -> QFrame:
        card = QFrame(parent)
        card.setObjectName("SettingsCommandCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Maintenance Commands", card)
        title.setObjectName("CardTitle")
        layout.addWidget(title)

        subtitle = QLabel("Run common maintenance operations and send output to the Maintenance section.", card)
        subtitle.setObjectName("CardSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        button_grid = QGridLayout()
        button_grid.setHorizontalSpacing(10)
        button_grid.setVerticalSpacing(10)
        for index, (label, command, object_name) in enumerate(
            (
                ("Status", "status", "PrimaryButton"),
                ("Audit", "audit", "PrimaryButton"),
                ("Rebuild All", "rebuild-all", "GhostButton"),
                ("Rebuild FTS", "rebuild-fts", "GhostButton"),
            )
        ):
            button = QPushButton(label, card)
            button.setObjectName(object_name)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            button.clicked.connect(lambda _checked=False, selected=command: self._run_and_focus_maintenance(selected))
            button_grid.addWidget(button, index // 2, index % 2)
        layout.addLayout(button_grid)
        return card

    def _build_overview_reindex_card(self, parent: QWidget) -> QFrame:
        card = QFrame(parent)
        card.setObjectName("SettingsCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Reindex", card)
        title.setObjectName("CardTitle")
        layout.addWidget(title)

        file_label = QLabel("Reindex a specific file path", card)
        file_label.setObjectName("Eyebrow")
        layout.addWidget(file_label)

        self.reindex_path_input = QLineEdit(card)
        self.reindex_path_input.setObjectName("PathInput")
        self.reindex_path_input.setPlaceholderText("Choose a file to enqueue for reindexing")
        layout.addWidget(self.reindex_path_input)

        file_row = QHBoxLayout()
        file_row.setSpacing(10)
        file_browse = QPushButton("Browse File", card)
        file_browse.setObjectName("GhostButton")
        file_browse.clicked.connect(self.choose_file_path)
        file_browse.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        file_row.addWidget(file_browse)

        file_run = QPushButton("Run Reindex Path", card)
        file_run.setObjectName("PrimaryButton")
        file_run.clicked.connect(lambda: self._run_and_focus_maintenance("reindex-path", self.reindex_path_input.text().strip()))
        file_run.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        file_row.addWidget(file_run)
        layout.addLayout(file_row)

        folder_label = QLabel("Reindex monitored folders", card)
        folder_label.setObjectName("Eyebrow")
        layout.addWidget(folder_label)

        self.reindex_folder_input = QLineEdit(card)
        self.reindex_folder_input.setObjectName("PathInput")
        self.reindex_folder_input.setPlaceholderText("Choose a monitored folder or any supported document directory")
        layout.addWidget(self.reindex_folder_input)

        folder_row = QHBoxLayout()
        folder_row.setSpacing(10)
        folder_browse = QPushButton("Browse Folder", card)
        folder_browse.setObjectName("GhostButton")
        folder_browse.clicked.connect(self.choose_folder_path)
        folder_browse.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        folder_row.addWidget(folder_browse)

        folder_run = QPushButton("Run Reindex Folder", card)
        folder_run.setObjectName("PrimaryButton")
        folder_run.clicked.connect(lambda: self._run_and_focus_maintenance("reindex-folder", self.reindex_folder_input.text().strip()))
        folder_run.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        folder_row.addWidget(folder_run)
        layout.addLayout(folder_row)
        return card

    def _build_overview_failures_card(self, parent: QWidget) -> QFrame:
        card = QFrame(parent)
        card.setObjectName("SettingsCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("Recent Failures", card)
        title.setObjectName("CardTitle")
        header.addWidget(title)
        header.addStretch(1)

        details_button = QPushButton("View Full Log", card)
        details_button.setObjectName("GhostButton")
        details_button.clicked.connect(lambda: self._select_section(self._section_indexes["health"]))
        header.addWidget(details_button)
        layout.addLayout(header)

        subtitle = QLabel("Latest parser or indexing issues surfaced by Shelf.", card)
        subtitle.setObjectName("CardSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        self.overview_failures_preview = QPlainTextEdit(card)
        self.overview_failures_preview.setReadOnly(True)
        self.overview_failures_preview.setMaximumBlockCount(50)
        self.overview_failures_preview.setMinimumHeight(160)
        layout.addWidget(self.overview_failures_preview)
        return card

    def _make_stat_card(self, parent: QWidget, label_text: str) -> tuple[QLabel, QFrame]:
        card = QFrame(parent)
        card.setObjectName("StatCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)
        value = QLabel("0", card)
        value.setObjectName("StatNumber")
        value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value)
        label = QLabel(label_text, card)
        label.setObjectName("StatLabel")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        layout.addWidget(label)
        return value, card

    def _render_shortcut_chips(self, shortcut: str) -> None:
        while self.shortcut_chips_host.count():
            item = self.shortcut_chips_host.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for index, token in enumerate(part.strip() for part in shortcut.split("+") if part.strip()):
            chip = QFrame(self)
            chip.setObjectName("ShortcutChip")
            chip_layout = QHBoxLayout(chip)
            chip_layout.setContentsMargins(12, 8, 12, 8)
            label = QLabel(token.replace("Meta", "Cmd").replace("Alt", "Option"), chip)
            label.setObjectName("ShortcutChipLabel")
            chip_layout.addWidget(label)
            self.shortcut_chips_host.addWidget(chip)
            if index < len([part for part in shortcut.split("+") if part.strip()]) - 1:
                plus = QLabel("+", self)
                plus.setObjectName("ShortcutPlus")
                self.shortcut_chips_host.addWidget(plus)
        self.shortcut_chips_host.addStretch(1)

    def _select_section(self, index: int) -> None:
        button = self.section_buttons.button(index)
        if button is not None:
            button.setChecked(True)
        self.page_stack.setCurrentIndex(index)

    def _run_and_focus_maintenance(self, command: str, path: str | None = None) -> None:
        self.run_command(command, path)
        if self.maintenance_output.toPlainText().strip():
            self._select_section(self._section_indexes["maintenance"])

    def _build_general_tab(self) -> QWidget:
        tab, content, layout = self._make_scrollable_settings_page()

        title = QLabel("Application", content)
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Choose which document types Shelf indexes and inspect where all local app data is stored on disk.",
            content,
        )
        subtitle.setObjectName("SectionCaption")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        shortcut_card = QFrame(content)
        shortcut_card.setObjectName("SettingsCard")
        shortcut_layout = QVBoxLayout(shortcut_card)
        shortcut_layout.setContentsMargins(20, 20, 20, 20)
        shortcut_layout.setSpacing(14)
        layout.addWidget(shortcut_card)

        shortcut_label = QLabel("Launcher shortcut", shortcut_card)
        shortcut_label.setObjectName("Eyebrow")
        shortcut_layout.addWidget(shortcut_label)

        shortcut_caption = QLabel(
            "Overview shows the current shortcut. Use this editor to customize the actual key combination.",
            shortcut_card,
        )
        shortcut_caption.setObjectName("SectionCaption")
        shortcut_caption.setWordWrap(True)
        shortcut_layout.addWidget(shortcut_caption)

        shortcut_row = QHBoxLayout()
        self.launcher_shortcut_input = QKeySequenceEdit(
            QKeySequence(self.settings.launcher_shortcut or DEFAULT_LAUNCH_SHORTCUT),
            content,
        )
        self.launcher_shortcut_input.setObjectName("PathInput")
        self.launcher_shortcut_input.editingFinished.connect(self.save_launcher_shortcut)
        shortcut_row.addWidget(self.launcher_shortcut_input, 1)

        reset_shortcut = QPushButton("Reset Default", content)
        reset_shortcut.setObjectName("GhostButton")
        reset_shortcut.clicked.connect(self.reset_launcher_shortcut)
        shortcut_row.addWidget(reset_shortcut)
        shortcut_layout.addLayout(shortcut_row)

        types_card = QFrame(content)
        types_card.setObjectName("SettingsCard")
        types_layout = QVBoxLayout(types_card)
        types_layout.setContentsMargins(20, 20, 20, 20)
        types_layout.setSpacing(12)
        layout.addWidget(types_card)

        types_label = QLabel("Indexed document types", tab)
        types_label.setObjectName("Eyebrow")
        types_layout.addWidget(types_label)

        types_caption = QLabel(
            "Choose which document formats Shelf indexes. If you change these selections, Shelf can reindex to add or remove matching files.",
            tab,
        )
        types_caption.setObjectName("SectionCaption")
        types_caption.setWordWrap(True)
        types_layout.addWidget(types_caption)

        self.document_type_checkboxes: dict[str, QCheckBox] = {}
        for extension, label in DOCUMENT_TYPE_LABELS.items():
            checkbox = QCheckBox(f"{label} ({extension})", content)
            checkbox.setObjectName("DocumentTypeCheckbox")
            checkbox.setChecked(extension in set(self.settings.enabled_extensions))
            self.document_type_checkboxes[extension] = checkbox
            types_layout.addWidget(checkbox)

        apply_types_button = QPushButton("Apply document type changes", content)
        apply_types_button.setObjectName("PrimaryButton")
        apply_types_button.clicked.connect(self.save_enabled_extensions)
        types_layout.addWidget(apply_types_button, alignment=Qt.AlignmentFlag.AlignLeft)

        storage_card = QFrame(content)
        storage_card.setObjectName("SettingsCard")
        storage_layout = QVBoxLayout(storage_card)
        storage_layout.setContentsMargins(20, 20, 20, 20)
        storage_layout.setSpacing(12)
        layout.addWidget(storage_card)

        for label, value in (
            ("Application Support", str(self.services.paths.root)),
            ("Settings File", str(self.services.paths.settings_file)),
            ("SQLite Database", str(self.services.paths.database_file)),
        ):
            label_widget = QLabel(label, content)
            label_widget.setObjectName("Eyebrow")
            storage_layout.addWidget(label_widget)

            value_widget = QLineEdit(value, content)
            value_widget.setReadOnly(True)
            value_widget.setObjectName("PathInput")
            storage_layout.addWidget(value_widget)

        layout.addStretch(1)
        return tab

    def _build_monitor_tab(self) -> QWidget:
        tab, content, layout = self._make_scrollable_settings_page()

        title = QLabel("Library health", content)
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        caption = QLabel(
            "Keep an eye on indexing progress and recent parser or worker failures without leaving the settings surface.",
            content,
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

        folders_card = QFrame(content)
        folders_card.setObjectName("SettingsCard")
        folders_layout = QVBoxLayout(folders_card)
        folders_layout.setContentsMargins(20, 20, 20, 20)
        folders_layout.setSpacing(12)
        layout.addWidget(folders_card)

        folders_title = QLabel("Coverage and access", folders_card)
        folders_title.setObjectName("Eyebrow")
        folders_layout.addWidget(folders_title)

        self.folder_audit_summary = QLabel("", folders_card)
        self.folder_audit_summary.setObjectName("SectionCaption")
        self.folder_audit_summary.setWordWrap(True)
        folders_layout.addWidget(self.folder_audit_summary)

        self.folder_audit_list = QListWidget(folders_card)
        self.folder_audit_list.setObjectName("FolderAuditList")
        folders_layout.addWidget(self.folder_audit_list)

        overview_card = QFrame(content)
        overview_card.setObjectName("SettingsCard")
        overview_layout = QVBoxLayout(overview_card)
        overview_layout.setContentsMargins(20, 20, 20, 20)
        overview_layout.setSpacing(12)
        layout.addWidget(overview_card, 1)

        self.overview_text = QPlainTextEdit(content)
        self.overview_text.setReadOnly(True)
        overview_layout.addWidget(self.overview_text, 1)

        failures_title = QLabel("Recent failures", content)
        failures_title.setObjectName("Eyebrow")
        layout.addWidget(failures_title)

        failures_card = QFrame(content)
        failures_card.setObjectName("SettingsCard")
        failures_layout = QVBoxLayout(failures_card)
        failures_layout.setContentsMargins(20, 20, 20, 20)
        failures_layout.setSpacing(12)
        layout.addWidget(failures_card, 1)

        self.failures_list = QListWidget(content)
        failures_layout.addWidget(self.failures_list, 1)

        refresh_button = QPushButton("Refresh health", content)
        refresh_button.setObjectName("PrimaryButton")
        refresh_button.clicked.connect(self.refresh_monitor_data)
        layout.addWidget(refresh_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.refresh_monitor_data()
        return tab

    def _build_maintenance_tab(self) -> QWidget:
        tab, content, layout = self._make_scrollable_settings_page()

        title = QLabel("Maintenance commands", content)
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        caption = QLabel(
            "Overview runs the command actions. This section keeps the latest output visible so maintenance work stays inspectable.",
            content,
        )
        caption.setObjectName("SectionCaption")
        caption.setWordWrap(True)
        layout.addWidget(caption)

        summary_card = QFrame(content)
        summary_card.setObjectName("SettingsCard")
        summary_layout = QVBoxLayout(summary_card)
        summary_layout.setContentsMargins(20, 20, 20, 20)
        summary_layout.setSpacing(12)
        layout.addWidget(summary_card)

        summary_title = QLabel("Last command activity", summary_card)
        summary_title.setObjectName("Eyebrow")
        summary_layout.addWidget(summary_title)

        summary_body = QLabel(
            "Use the Overview section for status, audits, rebuilds, and reindex actions. The latest JSON output is preserved here.",
            summary_card,
        )
        summary_body.setObjectName("SectionCaption")
        summary_body.setWordWrap(True)
        summary_layout.addWidget(summary_body)

        output_card = QFrame(content)
        output_card.setObjectName("SettingsCard")
        output_layout = QVBoxLayout(output_card)
        output_layout.setContentsMargins(20, 20, 20, 20)
        output_layout.setSpacing(12)
        layout.addWidget(output_card, 1)

        self.maintenance_output = QPlainTextEdit(content)
        self.maintenance_output.setObjectName("MaintenanceOutput")
        self.maintenance_output.setReadOnly(True)
        self.maintenance_output.setPlaceholderText("Command output will appear here.")
        output_layout.addWidget(self.maintenance_output, 1)

        layout.addStretch(1)
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
        count = len(self.settings.monitored_folders)
        accessible_count = sum(1 for folder in self.settings.monitored_folders if folder.accessible)
        if hasattr(self, "overview_folder_summary"):
            self.overview_folder_summary.setText(
                f"{count} monitored folder{'s' if count != 1 else ''} configured. {accessible_count} currently accessible."
            )
        self._sync_folder_actions()

    def save_launcher_shortcut(self) -> None:
        sequence = self.launcher_shortcut_input.keySequence().toString(QKeySequence.SequenceFormat.PortableText)
        self.settings.launcher_shortcut = sequence or DEFAULT_LAUNCH_SHORTCUT
        self.services.settings.save(self.settings)
        self._render_shortcut_chips(self.settings.launcher_shortcut)
        if hasattr(self, "overview_shortcut_summary"):
            self.overview_shortcut_summary.setText(
                f"Current shortcut: {self.settings.launcher_shortcut.replace('Meta', 'Cmd').replace('Alt', 'Option')}"
            )
        self.on_settings_changed()

    def save_enabled_extensions(self) -> None:
        selected = normalize_enabled_extensions(
            [extension for extension, checkbox in self.document_type_checkboxes.items() if checkbox.isChecked()]
        )
        current = normalize_enabled_extensions(self.settings.enabled_extensions)
        if selected == current:
            self.status_message("Document types are unchanged.")
            return
        if not selected:
            QMessageBox.warning(self, "Choose at least one type", "Shelf needs at least one document type enabled.")
            return

        answer = QMessageBox.question(
            self,
            "Reindex for document type changes?",
            "Changing indexed document types can add new files and remove no-longer-selected ones from search results. Reindex now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Yes,
        )
        if answer == QMessageBox.StandardButton.Cancel:
            for extension, checkbox in self.document_type_checkboxes.items():
                checkbox.setChecked(extension in current)
            return

        self.settings.enabled_extensions = selected
        self.services.settings.save(self.settings)
        self._update_enabled_extensions_summary()

        if answer == QMessageBox.StandardButton.Yes:
            self.app_controller.refresh_folders(self.settings)
            self.refresh_folder_list()
            self.refresh_monitor_data()
            self.status_message("Queued reindex for updated document types.")
        else:
            self.status_message("Saved document types. Reindex later from Maintenance to apply changes.")
        self.on_settings_changed()

    def _update_enabled_extensions_summary(self) -> None:
        labels = [DOCUMENT_TYPE_LABELS[extension] for extension in normalize_enabled_extensions(self.settings.enabled_extensions)]
        if hasattr(self, "folder_audit_summary"):
            summary = ", ".join(labels)
            self.folder_audit_summary.setText(f"Indexed formats currently enabled: {summary}")

    def status_message(self, message: str) -> None:
        if self.parent() is not None and hasattr(self.parent(), "statusBar"):
            try:
                self.parent().statusBar().showMessage(message, 4000)
                return
            except Exception:
                pass

    def reset_launcher_shortcut(self) -> None:
        self.launcher_shortcut_input.setKeySequence(QKeySequence(DEFAULT_LAUNCH_SHORTCUT))
        self.save_launcher_shortcut()

    def _sync_folder_actions(self) -> None:
        if hasattr(self, "remove_folder_button"):
            self.remove_folder_button.setEnabled(self.folder_list.currentItem() is not None)

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
        supported_patterns = " ".join(f"*{extension}" for extension in DOCUMENT_TYPE_LABELS)
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Choose File to Reindex",
            str(Path.home()),
            f"Documents ({supported_patterns});;All Files (*)",
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
        self.summary_indexed_value.setText(str(status.indexed_documents))
        self.summary_queued_value.setText(str(status.queued_jobs))
        self.summary_failures_value.setText(str(status.recent_failures))
        self.sidebar_status_detail.setText(
            "All systems operational" if status.recent_failures == 0 else f"{status.recent_failures} recent failures need attention"
        )
        self.health_status_label.setText(
            "● Shelf is healthy and up to date"
            if status.recent_failures == 0 and status.queued_jobs == 0
            else "● Shelf is indexing or needs attention"
        )
        if hasattr(self, "overview_shortcut_summary"):
            self.overview_shortcut_summary.setText(
                f"Current shortcut: {(self.settings.launcher_shortcut or DEFAULT_LAUNCH_SHORTCUT).replace('Meta', 'Cmd').replace('Alt', 'Option')}"
            )
        self._update_enabled_extensions_summary()

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

        if hasattr(self, "folder_audit_list"):
            self.folder_audit_list.clear()
            for folder in self.settings.monitored_folders:
                source = "Default" if folder.source == "default" else "User"
                access = "Accessible" if folder.accessible else "Access needs attention"
                self.folder_audit_list.addItem(f"{folder.path}\n{source} folder · {access}")

        self.failures_list.clear()
        failures = self.app_controller.recent_failures()
        failure_preview_lines: list[str] = []
        if not failures:
            self.failures_list.addItem("No recent failures recorded.")
            if hasattr(self, "overview_failures_preview"):
                self.overview_failures_preview.setPlainText("No recent failures recorded.")
            return
        for failure in failures:
            formatted = self._format_failure(failure)
            self.failures_list.addItem(formatted)
            if len(failure_preview_lines) < 3:
                failure_preview_lines.append(formatted)
        if hasattr(self, "overview_failures_preview"):
            self.overview_failures_preview.setPlainText("\n\n".join(failure_preview_lines))

    def _format_failure(self, failure: FailureRecord) -> str:
        detail = f"\n{failure.detail}" if failure.detail else ""
        ref = f" ({failure.ref_id})" if failure.ref_id else ""
        return f"[{failure.created_at}] {failure.scope}{ref}\n{failure.message}{detail}"

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            resize_edges = self._resize_edges_for_global_pos(event.globalPosition().toPoint())
            if resize_edges:
                self._resize_edges = resize_edges
                self._resize_start_global = event.globalPosition().toPoint()
                self._resize_start_geometry = self.geometry()
                event.accept()
                return
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        global_pos = event.globalPosition().toPoint()
        if self._resize_edges:
            self._resize_window(global_pos)
            event.accept()
            return
        self._update_resize_cursor(global_pos)
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(global_pos - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._drag_offset = None
        self._resize_edges.clear()
        self._resize_start_global = None
        self._resize_start_geometry = None
        self.unsetCursor()
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._refresh_overview_layout()


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
    RESIZE_MARGIN = 10

    def __init__(self, services: ServiceContainer, settings: AppSettings, app_controller: ShelfApplication) -> None:
        super().__init__()
        self.services = services
        self.settings = settings
        self.app_controller = app_controller
        self._drag_offset: QPoint | None = None
        self._resize_edges: set[str] = set()
        self._resize_start_geometry = None
        self._resize_start_global: QPoint | None = None
        self._is_quitting = False
        self._tray_message_shown = False
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
        self._install_tray_icon()
        self._configure_launcher_shortcut()
        self.search_input.setFocus()

        if settings.last_error:
            self.statusBar().showMessage(settings.last_error, 8000)

    def _build_actions(self) -> None:
        settings_action = QAction("Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.open_settings)
        self.addAction(settings_action)

        show_action = QAction("Show Shelf", self)
        show_action.triggered.connect(self.show_search_window)
        self.addAction(show_action)

        hide_action = QAction("Hide Shelf", self)
        hide_action.triggered.connect(self.hide_search_window)
        self.addAction(hide_action)

        quit_action = QAction("Quit Shelf", self)
        quit_action.triggered.connect(self.quit_application)
        self.addAction(quit_action)

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
        central.setMouseTracking(True)
        self.setMouseTracking(True)
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

    def _install_tray_icon(self) -> None:
        self.tray_icon: QSystemTrayIcon | None = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        tray_icon = QSystemTrayIcon(self)
        icon = QIcon(str(ICON_PATH)) if ICON_PATH.exists() else self.windowIcon()
        tray_icon.setIcon(icon)
        tray_icon.setToolTip("Shelf")

        menu = QMenu(self)
        show_action = menu.addAction("Show Shelf")
        show_action.triggered.connect(self.show_search_window)
        settings_action = menu.addAction("Open Settings")
        settings_action.triggered.connect(self.open_settings)
        hide_action = menu.addAction("Hide Shelf")
        hide_action.triggered.connect(self.hide_search_window)
        menu.addSeparator()
        quit_action = menu.addAction("Quit Shelf")
        quit_action.triggered.connect(self.quit_application)

        tray_icon.setContextMenu(menu)
        tray_icon.activated.connect(self._handle_tray_activation)
        tray_icon.show()
        self.tray_icon = tray_icon

    def _handle_tray_activation(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in {
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        }:
            self.toggle_launcher_window()

    def _show_tray_message_once(self) -> None:
        if self.tray_icon is None or self._tray_message_shown:
            return
        self.tray_icon.showMessage(
            "Shelf is still running",
            "Shelf was hidden to the menu bar. Use the tray icon or launcher shortcut to bring it back.",
            QSystemTrayIcon.MessageIcon.Information,
            2500,
        )
        self._tray_message_shown = True

    def _apply_shadow(self, widget: QWidget, blur: int, offset_y: int, alpha: int) -> None:
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(blur)
        shadow.setOffset(0, offset_y)
        shadow.setColor(Qt.GlobalColor.black)
        color = shadow.color()
        color.setAlpha(alpha)
        shadow.setColor(color)
        widget.setGraphicsEffect(shadow)

    def _focus_search_input(self) -> None:
        self.activateWindow()
        self.search_input.setFocus(Qt.FocusReason.OtherFocusReason)

    def eventFilter(self, watched: object, event: object) -> bool:
        if hasattr(self, "search_input") and watched is self.search_input and event.type() == QEvent.Type.KeyPress:
            if self._handle_results_navigation_key(event):
                return True
        if watched is self.centralWidget() and isinstance(event, QMouseEvent):
            if event.type() == QEvent.Type.MouseMove and self._resize_edges:
                self._resize_window(event.globalPosition().toPoint())
                return True
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                resize_edges = self._resize_edges_for_global_pos(event.globalPosition().toPoint())
                if resize_edges:
                    self._resize_edges = resize_edges
                    self._resize_start_global = event.globalPosition().toPoint()
                    self._resize_start_geometry = self.geometry()
                    return True
                widget = self.childAt(event.position().toPoint())
                if isinstance(widget, (QLineEdit, QPushButton, QToolButton)):
                    return False
                self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                return True
            if event.type() == QEvent.Type.MouseMove:
                self._update_resize_cursor(event.globalPosition().toPoint())
            if event.type() == QEvent.Type.MouseMove and self._drag_offset is not None:
                self.move(event.globalPosition().toPoint() - self._drag_offset)
                return True
            if event.type() == QEvent.Type.MouseButtonRelease:
                self._drag_offset = None
                self._resize_edges.clear()
                self._resize_start_global = None
                self._resize_start_geometry = None
                return True
        return super().eventFilter(watched, event)

    def _resize_edges_for_global_pos(self, global_pos: QPoint) -> set[str]:
        frame = self.frameGeometry()
        margin = self.RESIZE_MARGIN
        edges: set[str] = set()
        if abs(global_pos.x() - frame.left()) <= margin:
            edges.add("left")
        elif abs(global_pos.x() - frame.right()) <= margin:
            edges.add("right")
        if abs(global_pos.y() - frame.top()) <= margin:
            edges.add("top")
        elif abs(global_pos.y() - frame.bottom()) <= margin:
            edges.add("bottom")
        return edges

    def _update_resize_cursor(self, global_pos: QPoint) -> None:
        edges = self._resize_edges_for_global_pos(global_pos)
        if edges == {"left"} or edges == {"right"}:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif edges == {"top"} or edges == {"bottom"}:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        elif edges in ({"left", "top"}, {"right", "bottom"}):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif edges in ({"right", "top"}, {"left", "bottom"}):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif self._drag_offset is None and not self._resize_edges:
            self.unsetCursor()

    def _resize_window(self, global_pos: QPoint) -> None:
        if not self._resize_edges or self._resize_start_geometry is None or self._resize_start_global is None:
            return

        delta = global_pos - self._resize_start_global
        geometry = self._resize_start_geometry.adjusted(0, 0, 0, 0)
        minimum_width = max(self.minimumWidth(), 620)
        minimum_height = max(self.minimumHeight(), 180)

        if "left" in self._resize_edges:
            new_left = min(geometry.right() - minimum_width, geometry.left() + delta.x())
            geometry.setLeft(new_left)
        if "right" in self._resize_edges:
            geometry.setRight(max(geometry.left() + minimum_width, geometry.right() + delta.x()))
        if "top" in self._resize_edges:
            new_top = min(geometry.bottom() - minimum_height, geometry.top() + delta.y())
            geometry.setTop(new_top)
        if "bottom" in self._resize_edges:
            geometry.setBottom(max(geometry.top() + minimum_height, geometry.bottom() + delta.y()))

        self.setGeometry(geometry)

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
        if self.isVisible():
            QTimer.singleShot(10, self._focus_search_input)
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
        QTimer.singleShot(10, self._focus_search_input)

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
        QTimer.singleShot(10, self._focus_search_input)

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
        if not self.isVisible():
            self.move_to_top_of_screen()
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)
        self.raise_()
        self.activateWindow()
        QTimer.singleShot(10, self._focus_search_input)

    def hide_to_tray(self) -> None:
        self._navigating_results = False
        self.results_popup.hide()
        self.hide()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)
        self._show_tray_message_once()

    def hide_search_window(self) -> None:
        self.hide_to_tray()

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
        if event.type() == QEvent.Type.WindowStateChange and self.isMinimized():
            QTimer.singleShot(0, self.hide_to_tray)
            return
        if event.type() == QEvent.Type.ActivationChange and self.isVisible() and not self.isActiveWindow():
            self._handle_window_deactivated()

    def quit_application(self) -> None:
        self._is_quitting = True
        QApplication.instance().quit()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.move_to_top_of_screen()
        QTimer.singleShot(10, self._focus_search_input)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self.results_popup.isVisible():
            self.results_popup.resize(self.composer_shell.width(), self.results_popup.height())
            self.results_popup.anchor_below(self.composer_shell)

    def closeEvent(self, event) -> None:  # noqa: N802
        if not self._is_quitting:
            event.ignore()
            self.hide_to_tray()
            return
        self.results_popup.close()
        if self.tray_icon is not None:
            self.tray_icon.hide()
        self._launcher_shortcut.close()
        self._search_executor.shutdown(wait=False, cancel_futures=True)
        super().closeEvent(event)
