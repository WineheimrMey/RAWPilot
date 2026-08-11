"""Render the main window offscreen for visual regression review."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap

from rawpilot.ui import MainWindow, apply_application_style


def main() -> int:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "ui_redesign_preview.png")
    app = QApplication([])
    apply_application_style(app)
    window = MainWindow()
    window.resize(1680, 1020)
    window.show()
    app.processEvents()
    if len(sys.argv) > 2:
        sample = Path(sys.argv[2])
        if sample.exists():
            pixmap = QPixmap(str(sample))
            for image_target in (window.preview, window.output_preview):
                image_target.setPixmap(
                    pixmap.scaled(
                        image_target.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
            window.preview_title.setText(sample.stem + ".NEF")
            window.frame_meta.setText("NEF · LOCAL PREVIEW")
            window.analysis_state.setText("建议已就绪")
            window.analysis_lead.setText(
                "夜景主体层次偏弱，实用灯光存在黄绿色污染风险；先保护灯具高光并恢复人物可读性，再以克制冷暖关系建立电影感。"
            )
            window.style.setPlainText(
                "保留夜景深度但让主体可读。压住灯具高光，减少黄绿色溢色，暗部只恢复关键结构；"
                "使用低饱和冷阴影与温暖高光建立电影感，避免清晰度和去朦胧放大鬼影与光晕。"
            )
    if not window.grab().save(str(target)):
        raise RuntimeError(f"Unable to save UI preview to {target}")
    window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
