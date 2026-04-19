from __future__ import annotations

import argparse
import logging
import sys

from shelf.core.application import ShelfApplication
from shelf.core.logging_utils import configure_logging
from shelf.core.services import build_services


LOGGER = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Shelf document search")
    parser.add_argument("--app-support-dir", help="Override the default app support directory.")
    args = parser.parse_args(argv)

    services = build_services(root_override=args.app_support_dir)
    configure_logging(services.paths)
    settings = services.settings.load()

    try:
        from PySide6.QtWidgets import QApplication, QMessageBox

        from shelf.ui.main_window import MainWindow
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
    application.setOrganizationName("Shelf")

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
