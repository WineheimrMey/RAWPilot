from __future__ import annotations

import os
import traceback
from pathlib import Path


def report_startup_error() -> None:
    directory = Path(os.environ.get("APPDATA") or Path.home()) / "RAWPilot"
    directory.mkdir(parents=True, exist_ok=True)
    log_path = directory / "startup_error.log"
    log_path.write_text(traceback.format_exc(), encoding="utf-8")
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0,
            f"原光 RAWPilot 启动失败。\n错误详情已保存到：\n{log_path}",
            "原光 RAWPilot",
            0x10,
        )
    except Exception:
        pass


def launch() -> int:
    try:
        from rawpilot.main import main
        return main()
    except Exception:
        report_startup_error()
        return 1


if __name__ == "__main__":
    raise SystemExit(launch())
