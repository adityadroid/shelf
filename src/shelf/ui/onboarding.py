from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from shelf.core.models import MonitoredFolder, SUPPORTED_EXTENSIONS


class OnboardingDialog(QDialog):
    def __init__(self, folders: Iterable[MonitoredFolder], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Welcome to Shelf")
        self.setModal(True)
        self.resize(480, 320)

        layout = QVBoxLayout(self)

        intro = QLabel(
            "Shelf keeps a local search library for documents on this Mac. "
            "It stays offline-first and only indexes supported files from folders you approve."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        types_label = QLabel(
            "Supported file types: " + ", ".join(extension.upper() for extension in SUPPORTED_EXTENSIONS)
        )
        types_label.setWordWrap(True)
        layout.addWidget(types_label)

        folder_text = "\n".join(f"• {folder.path}" for folder in folders)
        folders_label = QLabel(f"Default monitored folders:\n{folder_text}")
        folders_label.setWordWrap(True)
        folders_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(folders_label)

        permissions = QLabel(
            "macOS may ask you to grant access to Documents, Downloads, and Desktop. "
            "If access is denied, Shelf will show that state in the folder list so you can retry."
        )
        permissions.setWordWrap(True)
        layout.addWidget(permissions)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
