from pathlib import Path

from rawpilot.importer import collect_raw_files


def test_collect_supported_recursively(tmp_path: Path):
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "A.NEF").write_bytes(b"x")
    (nested / "ignore.jpg").write_bytes(b"x")
    assert collect_raw_files([tmp_path]) == [(nested / "A.NEF").resolve()]


def test_deduplicates(tmp_path: Path):
    raw = tmp_path / "one.dng"
    raw.write_bytes(b"x")
    assert collect_raw_files([raw, tmp_path]) == [raw.resolve()]
