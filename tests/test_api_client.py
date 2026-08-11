import pytest
from PIL import Image

from rawpilot.api_client import ApiError, QwenApiClient, parse_json
from rawpilot.settings import AppSettings


def test_truncated_model_json_has_clear_error():
    with pytest.raises(ApiError, match="JSON 不完整"):
        parse_json('{"exposure": 0.5, "rationale": "未结束')


def test_vision_input_is_resized_below_service_limit(tmp_path, monkeypatch):
    source = tmp_path / "large.jpg"
    Image.new("RGB", (3000, 4500), (40, 50, 60)).save(source)
    client = QwenApiClient(AppSettings(api_key="test", mock_mode=False))
    captured = {}

    def fake_post(payload):
        captured.update(payload)
        return '{"ok": true}'

    monkeypatch.setattr(client, "_post", fake_post)
    assert client.vision_json(source, {}, "test") == {"ok": True}
    image_url = captured["messages"][1]["content"][1]["image_url"]["url"]
    import base64
    from io import BytesIO

    encoded = image_url.split(",", 1)[1]
    with Image.open(BytesIO(base64.b64decode(encoded))) as resized:
        assert max(resized.size) <= 1280


def test_visual_review_sends_before_and_after_images(tmp_path, monkeypatch):
    before = tmp_path / "before.jpg"
    after = tmp_path / "after.jpg"
    Image.new("RGB", (120, 80), (20, 30, 40)).save(before)
    Image.new("RGB", (120, 80), (40, 50, 60)).save(after)
    client = QwenApiClient(AppSettings(api_key="test", mock_mode=False))
    captured = {}

    def fake_post(payload):
        captured.update(payload)
        return '{"intent_match": 90}'

    monkeypatch.setattr(client, "_post", fake_post)
    result = client.vision_compare_json(
        before, after, {"intent": "自然"}, "review"
    )
    assert result["intent_match"] == 90
    image_parts = [
        part for part in captured["messages"][1]["content"]
        if part["type"] == "image_url"
    ]
    assert len(image_parts) == 2
