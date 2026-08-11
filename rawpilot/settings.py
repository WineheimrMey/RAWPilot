from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field


def config_dir() -> Path:
    base = Path(os.environ.get("APPDATA") or Path.home())
    return base / "RAWPilot"


class AppSettings(BaseModel):
    api_base_url: str = "https://api-inference.modelscope.cn/v1"
    api_key: str = Field(default="", repr=False)
    vision_model: str = "Qwen/Qwen3.5-35B-A3B"
    language_model: str = "Qwen/Qwen3.5-35B-A3B"
    mock_mode: bool = True
    lightroom_enabled: bool = False
    lightroom_path: str = ""
    interface_language: str = "zh_CN"
    retries: int = 2
    timeout_seconds: int = 90

    @classmethod
    def load(cls) -> "AppSettings":
        values: dict[str, object] = {}
        path = config_dir() / ".env"
        if path.exists():
            for line in path.read_text("utf-8").splitlines():
                if not line or line.lstrip().startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
        api_base_url = str(values.get("RAWPILOT_API_BASE_URL", cls.model_fields["api_base_url"].default))
        vision_model = str(values.get("RAWPILOT_VISION_MODEL", cls.model_fields["vision_model"].default))
        language_model = str(values.get("RAWPILOT_LANGUAGE_MODEL", cls.model_fields["language_model"].default))
        if (
            api_base_url.rstrip("/") == "https://dashscope.aliyuncs.com/compatible-mode/v1"
            and vision_model == "qwen-vl-max"
            and language_model == "qwen-plus"
        ):
            api_base_url = str(cls.model_fields["api_base_url"].default)
            vision_model = str(cls.model_fields["vision_model"].default)
            language_model = str(cls.model_fields["language_model"].default)
        return cls(
            api_base_url=api_base_url,
            api_key=str(values.get("RAWPILOT_API_KEY", "")).strip().strip('"').strip("'"),
            vision_model=vision_model,
            language_model=language_model,
            mock_mode=str(values.get("RAWPILOT_MOCK_MODE", "true")).lower() in {"1", "true", "yes", "on"},
            lightroom_enabled=str(values.get("RAWPILOT_LIGHTROOM_ENABLED", "false")).lower() in {"1", "true", "yes", "on"},
            lightroom_path=str(values.get("RAWPILOT_LIGHTROOM_PATH", "")),
            interface_language=(
                str(values.get("RAWPILOT_INTERFACE_LANGUAGE", "zh_CN"))
                if str(values.get("RAWPILOT_INTERFACE_LANGUAGE", "zh_CN")) in {"zh_CN", "en_US"}
                else "zh_CN"
            ),
        )

    def save(self) -> Path:
        directory = config_dir()
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / ".env"
        safe = self.api_key.replace("\r", "").replace("\n", "")
        content = (
            f"RAWPILOT_API_BASE_URL={self.api_base_url.strip()}\n"
            f"RAWPILOT_API_KEY={safe}\n"
            f"RAWPILOT_VISION_MODEL={self.vision_model.strip()}\n"
            f"RAWPILOT_LANGUAGE_MODEL={self.language_model.strip()}\n"
            f"RAWPILOT_MOCK_MODE={'true' if self.mock_mode else 'false'}\n"
            f"RAWPILOT_LIGHTROOM_ENABLED={'true' if self.lightroom_enabled else 'false'}\n"
            f"RAWPILOT_LIGHTROOM_PATH={self.lightroom_path.strip()}\n"
            f"RAWPILOT_INTERFACE_LANGUAGE={self.interface_language}\n"
        )
        path.write_text(content, encoding="utf-8")
        return path
