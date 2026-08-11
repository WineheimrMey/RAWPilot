from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from .settings import config_dir
from .ui import MainWindow, apply_application_style


def configure_logging() -> None:
    directory = config_dir()
    directory.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(directory / "rawpilot.log", encoding="utf-8")],
    )


def main() -> int:
    configure_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("原光 RAWPilot")
    app.setOrganizationName("原光")
    apply_application_style(app)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
