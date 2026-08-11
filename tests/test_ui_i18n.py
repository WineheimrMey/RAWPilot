import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from rawpilot.ui import MainWindow


def test_main_window_switches_language_without_losing_state(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.output.setText(str(tmp_path / "renders"))

    assert window.studio_nav.text() == "工作台"
    window.toggle_language()

    assert window.studio_nav.text() == "Studio"
    assert window.history_nav.text() == "Archive"
    assert window.output.text() == str(tmp_path / "renders")
    assert window.settings.interface_language == "en_US"
    window.close()
    app.processEvents()
