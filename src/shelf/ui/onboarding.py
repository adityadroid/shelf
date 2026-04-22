from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from shelf.core.models import DOCUMENT_TYPE_LABELS, MonitoredFolder


class OnboardingDialog(QDialog):
    def __init__(self, folders: Iterable[MonitoredFolder], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Welcome to Shelf")
        self.setModal(True)
        self.resize(480, 320)
        self.setStyleSheet(
            """
            QDialog {
                background: #f8f7f3;
                color: #2f2f2b;
                font-family: "Geist Mono", "SF Mono", "Menlo", "Monaco";
            }
            QLabel {
                color: #3f3f3a;
                font-size: 13px;
                line-height: 1.45;
            }
            QLabel#OnboardingTitle {
                color: #2f2f2b;
                font-size: 28px;
                font-weight: 400;
                letter-spacing: 0.08em;
            }
            QPushButton {
                background: #2f2f2b;
                border: 1px solid #2f2f2b;
                border-radius: 0px;
                color: #fbfaf7;
                min-height: 36px;
                padding: 0 18px;
            }
            QPushButton:hover {
                background: #11110f;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 24)
        layout.setSpacing(16)

        title = QLabel("SHELF", self)
        title.setObjectName("OnboardingTitle")
        layout.addWidget(title)

        intro = QLabel(
            "Shelf keeps a local search library for documents on this Mac. "
            "It stays offline-first and only indexes supported files from folders you approve."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        types_label = QLabel(
            "Supported file types: " + ", ".join(label for label in DOCUMENT_TYPE_LABELS.values())
        )
        types_label.setWordWrap(True)
        layout.addWidget(types_label)

        folder_text = "\n".join(f"- {folder.path}" for folder in folders)
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
