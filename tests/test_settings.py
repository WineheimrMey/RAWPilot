from pathlib import Path

from rawpilot.settings import AppSettings


def test_migrates_original_dashscope_defaults(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    directory = tmp_path / "RAWPilot"
    directory.mkdir()
    (directory / ".env").write_text(
        "RAWPILOT_API_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1\n"
        "RAWPILOT_API_KEY=test-token\n"
        "RAWPILOT_VISION_MODEL=qwen-vl-max\n"
        "RAWPILOT_LANGUAGE_MODEL=qwen-plus\n"
        "RAWPILOT_MOCK_MODE=false\n",
        encoding="utf-8",
    )
    settings = AppSettings.load()
    assert settings.api_base_url == "https://api-inference.modelscope.cn/v1"
    assert settings.vision_model == "Qwen/Qwen3.5-35B-A3B"
    assert settings.api_key == "test-token"


def test_strips_accidental_key_quotes(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    directory = tmp_path / "RAWPilot"
    directory.mkdir()
    (directory / ".env").write_text(
        "RAWPILOT_API_KEY=\"quoted-token\"\n",
        encoding="utf-8",
    )
    assert AppSettings.load().api_key == "quoted-token"


def test_persists_interface_language(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    settings = AppSettings(interface_language="en_US")
    settings.save()
    assert AppSettings.load().interface_language == "en_US"
