from __future__ import annotations

import argparse
import logging
import sys

from shelf.core.application import ShelfApplication
from shelf.core.logging_utils import configure_logging
from shelf.core.maintenance import MaintenanceService
from shelf.core.services import build_services


LOGGER = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Shelf document search")
    parser.add_argument("--app-support-dir", help="Override the default app support directory.")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("run")
    subparsers.add_parser("status")
    subparsers.add_parser("audit")
    subparsers.add_parser("rebuild-all")
    subparsers.add_parser("rebuild-fts")
    reindex_path_parser = subparsers.add_parser("reindex-path")
    reindex_path_parser.add_argument("path")
    reindex_folder_parser = subparsers.add_parser("reindex-folder")
    reindex_folder_parser.add_argument("path")
    args = parser.parse_args(argv)

    services = build_services(root_override=args.app_support_dir)
    configure_logging(services.paths)
    settings = services.settings.load()
    command = args.command or "run"

    if command != "run":
        maintenance = MaintenanceService(services, settings)
        maintenance.sync_settings()
        try:
            if command == "status":
                print(maintenance.format_report(maintenance.metrics_snapshot()))
            elif command == "audit":
                print(maintenance.format_report(maintenance.audit()))
            elif command == "rebuild-all":
                print(maintenance.format_report(maintenance.rebuild_all()))
            elif command == "rebuild-fts":
                print(maintenance.format_report(maintenance.rebuild_fts()))
            elif command == "reindex-path":
                print(maintenance.format_report(maintenance.reindex_path(args.path)))
            elif command == "reindex-folder":
                print(maintenance.format_report(maintenance.reindex_folder(args.path)))
        finally:
            maintenance.close()
        return 0

    try:
        from PySide6.QtGui import QIcon
        from PySide6.QtWidgets import QApplication, QMessageBox

        from shelf.ui.main_window import ICON_PATH, MainWindow
        from shelf.ui.onboarding import OnboardingDialog
    except ModuleNotFoundError as exc:
        print(
            "Missing GUI dependencies. Install them with `uv sync` before running the app.\n"
            f"Original error: {exc}",
            file=sys.stderr,
        )
        return 1

    application = QApplication(argv or sys.argv)
    application.setApplicationName("Shelf")
    application.setApplicationDisplayName("Shelf")
    application.setOrganizationName("Shelf")
    application.setQuitOnLastWindowClosed(False)
    if ICON_PATH.exists():
        application.setWindowIcon(QIcon(str(ICON_PATH)))

    if not settings.onboarding_completed:
        dialog = OnboardingDialog(settings.monitored_folders)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return 0
        settings.onboarding_completed = True
        services.settings.save(settings)

    try:
        app_controller = ShelfApplication(services, settings)
        app_controller.start()
        application.aboutToQuit.connect(app_controller.stop)
        window = MainWindow(services, settings, app_controller)
        window.show()
        LOGGER.info("Application started")
        return application.exec()
    except Exception as exc:  # pragma: no cover - defensive UI path
        LOGGER.exception("Startup failed: %s", exc)
        QMessageBox.critical(None, "Shelf failed to start", str(exc))
        return 1
