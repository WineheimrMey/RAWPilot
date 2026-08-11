from pathlib import Path
from xml.etree import ElementTree

from rawpilot.models import EditPlan
from rawpilot.xmp_writer import write_xmp


def test_writes_xmp_and_json(tmp_path: Path):
    raw = tmp_path / "photo.NEF"
    plan = EditPlan(exposure=0.35, highlights=-20)
    xmp, edit_json = write_xmp(raw, plan, tmp_path / "out")
    payload = xmp.read_bytes().split(b"\n", 1)[1].rsplit(b"\n", 1)[0]
    ElementTree.fromstring(payload)
    text = xmp.read_text("utf-8")
    assert "Exposure2012" in text and "+0.35" in text
    assert "HueAdjustmentBlue" in text
    assert "SplitToningShadowHue" in text
    assert 'crs:WhiteBalance="As Shot"' in text
    assert "crs:Temperature" not in text
    assert 'crs:AutoLateralCA="1"' in text
    assert 'crs:LensProfileEnable="1"' in text
    assert "crs:SharpenEdgeMasking" in text
    assert edit_json.exists()


def test_custom_white_balance_is_written_explicitly(tmp_path: Path):
    raw = tmp_path / "warm.NEF"
    plan = EditPlan(white_balance="Custom", temperature=6100, tint=8)
    xmp, _ = write_xmp(raw, plan, tmp_path / "out")
    text = xmp.read_text("utf-8")
    assert 'crs:WhiteBalance="Custom"' in text
    assert 'crs:Temperature="6100"' in text
    assert 'crs:Tint="8"' in text
