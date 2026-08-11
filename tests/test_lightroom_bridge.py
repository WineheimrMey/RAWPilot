from pathlib import Path

from rawpilot.lightroom_bridge import LightroomBridge


def test_installs_bundled_plugin_to_appdata(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    installed = LightroomBridge().install_plugin()
    assert installed == tmp_path / "Adobe" / "Lightroom" / "Modules" / "RAWPilot.lrplugin"
    assert (installed / "Info.lua").exists()
    assert (installed / "InitPlugin.lua").exists()
    queue_path = installed / "queue_path.txt"
    assert queue_path.read_bytes().startswith(str(tmp_path).encode("utf-8"))
    assert not queue_path.read_bytes().startswith(b"\xef\xbb\xbf")


def test_bundled_plugin_forces_init_and_supports_yielding_calls():
    root = Path(__file__).parents[1] / "lightroom_plugin" / "RAWPilot.lrplugin"
    manifest = (root / "Info.lua").read_text(encoding="utf-8")
    implementation = (root / "InitPlugin.lua").read_text(encoding="utf-8")
    assert "LrForceInitPlugin = true" in manifest
    assert 'title = "启动原光 RAWPilot Bridge"' in manifest
    assert "LrTasks.pcall(processJob, path)" in implementation
    assert 'createNewMask("aiSelection", aiTarget)' in implementation
    assert 'aiTarget = "subject"' in implementation
    assert "numeric ~= nil and numeric or value" in implementation
    assert 'BRIDGE_VERSION = "0.5"' in implementation
    assert "previous RAWPilot mask delete" in implementation
    assert "LrDevelopController.setValue(parameter, value)" in implementation


def test_accepts_fresh_legacy_bridge_during_hot_upgrade(tmp_path: Path):
    ready = tmp_path / "bridge.ready"
    ready.write_text("ready|1784882778", encoding="utf-8")
    assert LightroomBridge._wait_for_ready(tmp_path, timeout=1) == "legacy"
