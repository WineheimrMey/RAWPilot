from __future__ import annotations

from pathlib import Path
from typing import Iterable

SUPPORTED_EXTENSIONS = {".arw", ".cr2", ".cr3", ".nef", ".raf", ".dng"}


def is_supported(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS


def collect_raw_files(paths: Iterable[str | Path]) -> list[Path]:
    found: set[Path] = set()
    for value in paths:
        path = Path(value).expanduser().resolve()
        if path.is_dir():
            found.update(p for p in path.rglob("*") if is_supported(p))
        elif is_supported(path):
            found.add(path)
    return sorted(found, key=lambda p: str(p).lower())
