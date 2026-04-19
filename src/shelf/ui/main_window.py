from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from shelf.core.application import ShelfApplication
from shelf.core.folders import remove_folder_by_path, validate_folder_candidate
from shelf.core.models import AppSettings, MonitoredFolder
from shelf.core.services import ServiceContainer


class MainWindow(QMainWindow):
    def __init__(self, services: ServiceContainer, settings: AppSettings, app_controller: ShelfApplication) -> None:
        super().__init__()
        self.services = services
        self.settings = settings
        self.app_controller = app_controller

        self.setWindowTitle("Shelf")
        self.resize(980, 640)

        root = QSplitter(self)
        root.setOrientation(Qt.Orientation.Horizontal)
        self.setCentralWidget(root)

        sidebar = QWidget(root)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_label = QLabel("Monitored Folders")
        sidebar_layout.addWidget(sidebar_label)

        self.folder_list = QListWidget(sidebar)
        sidebar_layout.addWidget(self.folder_list)

        add_button = QPushButton("Add Folder", sidebar)
        add_button.clicked.connect(self.add_folder)
        sidebar_layout.addWidget(add_button)

        remove_button = QPushButton("Remove Folder", sidebar)
        remove_button.clicked.connect(self.remove_selected_folder)
        sidebar_layout.addWidget(remove_button)

        self.status_summary = QLabel(sidebar)
        self.status_summary.setWordWrap(True)
        sidebar_layout.addWidget(self.status_summary)
        sidebar_layout.addStretch(1)

        content = QWidget(root)
        content_layout = QVBoxLayout(content)
        content_layout.addWidget(QLabel("Search"))

        self.search_input = QLineEdit(content)
        self.search_input.setPlaceholderText("Search indexed filenames and document text")
        self.search_input.textChanged.connect(self.schedule_search)
        content_layout.addWidget(self.search_input)

        self.result_list = QListWidget(content)
        self.result_list.currentItemChanged.connect(self.show_selected_result)
        content_layout.addWidget(self.result_list, 2)

        self.result_details = QTextEdit(content)
        self.result_details.setReadOnly(True)
        content_layout.addWidget(self.result_details, 1)

        root.addWidget(sidebar)
        root.addWidget(content)
        root.setStretchFactor(0, 1)
        root.setStretchFactor(1, 2)

        status_bar = QStatusBar(self)
        status_bar.showMessage("Ready")
        self.setStatusBar(status_bar)

        if settings.last_error:
            self.statusBar().showMessage(settings.last_error, 8000)

        open_action = QAction("Open File", self)
        open_action.triggered.connect(self.open_selected_file)
        reveal_action = QAction("Reveal in Finder", self)
        reveal_action.triggered.connect(self.reveal_selected_file)
        copy_action = QAction("Copy Path", self)
        copy_action.triggered.connect(self.copy_selected_path)
        self.result_list.addActions([open_action, reveal_action, copy_action])
        self.result_list.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)

        self.search_timer = QTimer(self)
        self.search_timer.setInterval(200)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.run_search)

        self.status_timer = QTimer(self)
        self.status_timer.setInterval(1000)
        self.status_timer.timeout.connect(self.refresh_status)
        self.status_timer.start()

        self.refresh_folder_list()
        self.refresh_status()

    def refresh_folder_list(self) -> None:
        self.folder_list.clear()
        for folder in self.settings.monitored_folders:
            suffix = "" if folder.accessible else " (access needs attention)"
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
        self.statusBar().showMessage(f"Added folder: {validation.normalized_path}", 5000)

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
        self.statusBar().showMessage(f"Removed folder: {folder_path}", 5000)

    def schedule_search(self, *_args) -> None:
        self.search_timer.start()

    def run_search(self) -> None:
        query = self.search_input.text().strip()
        self.result_list.clear()
        self.result_details.clear()
        if not query:
            return

        results = self.app_controller.search(query)
        for result in results:
            item = QListWidgetItem(f"{result.file_name} [{result.source}]")
            item.setData(Qt.ItemDataRole.UserRole, result.path)
            item.setData(Qt.ItemDataRole.UserRole + 1, result.snippet)
            item.setData(Qt.ItemDataRole.UserRole + 2, result.modified_at)
            self.result_list.addItem(item)

        if not results:
            self.result_details.setPlainText("No matching documents found yet.")

    def show_selected_result(self, *_args) -> None:
        item = self.result_list.currentItem()
        if item is None:
            return
        path = item.data(Qt.ItemDataRole.UserRole)
        snippet = item.data(Qt.ItemDataRole.UserRole + 1)
        modified_at = item.data(Qt.ItemDataRole.UserRole + 2)
        modified_text = datetime.fromtimestamp(float(modified_at)).strftime("%Y-%m-%d %H:%M")
        self.result_details.setPlainText(f"{path}\nModified: {modified_text}\n\n{snippet}")

    def selected_path(self) -> str | None:
        item = self.result_list.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def open_selected_file(self) -> None:
        path = self.selected_path()
        if path:
            self.app_controller.open_file(path)

    def reveal_selected_file(self) -> None:
        path = self.selected_path()
        if path:
            self.app_controller.reveal_file(path)

    def copy_selected_path(self) -> None:
        path = self.selected_path()
        if path:
            QApplication.clipboard().setText(path)
            self.statusBar().showMessage("Copied path to clipboard.", 3000)

    def refresh_status(self) -> None:
        status = self.app_controller.status()
        self.status_summary.setText(
            "Index status\n"
            f"Documents: {status.indexed_documents}\n"
            f"Queued jobs: {status.queued_jobs}\n"
            f"Failures: {status.recent_failures}\n"
            f"Semantic model: {status.embedding_model}"
        )

    def closeEvent(self, event) -> None:  # noqa: N802
        self.status_timer.stop()
        self.search_timer.stop()
        super().closeEvent(event)
