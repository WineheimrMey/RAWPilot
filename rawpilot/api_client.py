from __future__ import annotations

import base64
import json
import re
from io import BytesIO
from pathlib import Path
from typing import Any

import httpx
from PIL import Image, ImageOps

from .settings import AppSettings


class ApiError(RuntimeError):
    pass


class QwenApiClient:
    """OpenAI-compatible Qwen client. Only JPEG preview bytes enter vision calls."""

    def __init__(self, settings: AppSettings):
        self.settings = settings

    @property
    def endpoint(self) -> str:
        base = self.settings.api_base_url.rstrip("/")
        return base if base.endswith("/chat/completions") else f"{base}/chat/completions"

    def _post(self, payload: dict[str, Any]) -> str:
        if not self.settings.api_key:
            raise ApiError("未配置 API Key，请在设置中填写或启用 Mock API")
        headers = {"Authorization": f"Bearer {self.settings.api_key}", "Content-Type": "application/json"}
        last: Exception | None = None
        structured = "response_format" in payload
        for attempt in range(self.settings.retries + 1):
            try:
                with httpx.Client(timeout=self.settings.timeout_seconds) as client:
                    response = client.post(self.endpoint, headers=headers, json=payload)
                if structured and response.status_code in {400, 422}:
                    payload = {key: value for key, value in payload.items() if key != "response_format"}
                    structured = False
                    continue
                if response.status_code == 401:
                    platform = "ModelScope" if "modelscope" in self.endpoint.lower() else "当前 API 平台"
                    raise ApiError(
                        f"{platform} 认证失败（401）。API Key 无效，或 Key 与 Base URL 不属于同一平台。"
                    )
                if response.status_code == 404:
                    raise ApiError(f"接口或模型不存在（404）：{payload.get('model', '')}")
                if response.status_code == 429:
                    raise ApiError("模型服务限流或当日额度已用完（429），请稍后重试。")
                if 400 <= response.status_code < 500:
                    detail = response.text[:500]
                    raise ApiError(f"模型请求被拒绝（{response.status_code}）：{detail}")
                response.raise_for_status()
                data = response.json()
                choices = data.get("choices") if isinstance(data, dict) else None
                if not choices:
                    error = data.get("error") if isinstance(data, dict) else None
                    raise ValueError(
                        "模型服务返回空 choices"
                        + (f"：{str(error)[:300]}" if error else "")
                    )
                content = choices[0]["message"]["content"]
                return content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
            except ApiError:
                raise
            except (httpx.HTTPError, KeyError, ValueError, IndexError) as exc:
                last = exc
                if attempt >= self.settings.retries:
                    break
        detail = re.sub(r"sk-[A-Za-z0-9_-]+", "sk-***", str(last))
        raise ApiError(f"API 请求失败（已重试 {self.settings.retries} 次）：{detail}") from last

    @staticmethod
    def _encoded_vision_jpeg(preview: Path) -> str:
        with Image.open(preview) as source:
            image = ImageOps.exif_transpose(source)
            image.thumbnail((1280, 1280), Image.Resampling.LANCZOS)
            if image.mode != "RGB":
                image = image.convert("RGB")
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=88, optimize=True)
        return base64.b64encode(buffer.getvalue()).decode("ascii")

    def vision_json(self, preview: Path, exif: dict[str, str], prompt: str) -> dict[str, Any]:
        encoded = self._encoded_vision_jpeg(preview)
        payload = {
            "model": self.settings.vision_model,
            "temperature": 0.1,
            "max_tokens": 950,
            "enable_thinking": False,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": "EXIF（可能不完整）：" + json.dumps(exif, ensure_ascii=False)},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}},
                ]},
            ],
        }
        return parse_json(self._post(payload))

    def vision_compare_json(
        self,
        before: Path,
        after: Path,
        context: dict[str, Any],
        prompt: str,
    ) -> dict[str, Any]:
        """Send compressed before/after frames in one visual review call."""

        before_encoded = self._encoded_vision_jpeg(before)
        after_encoded = self._encoded_vision_jpeg(after)
        payload = {
            "model": self.settings.vision_model,
            "temperature": 0.1,
            "max_tokens": 950,
            "enable_thinking": False,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": [
                    {
                        "type": "text",
                        "text": (
                            "第一张是相机内嵌预览（BEFORE），第二张是 Lightroom "
                            "导出成片（AFTER）。上下文："
                            + json.dumps(context, ensure_ascii=False)
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{before_encoded}"
                        },
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{after_encoded}"
                        },
                    },
                ]},
            ],
        }
        return parse_json(self._post(payload))

    def language_json(self, system: str, user: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "model": self.settings.language_model,
            "temperature": 0.15,
            "max_tokens": 1200,
            "enable_thinking": False,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
            ],
        }
        return parse_json(self._post(payload))

    def test_connection(self) -> str:
        payload = {
            "model": self.settings.language_model,
            "temperature": 0,
            "max_tokens": 8,
            "enable_thinking": False,
            "messages": [{"role": "user", "content": "Reply only: OK"}],
        }
        return self._post(payload).strip()


def parse_json(text: str) -> dict[str, Any]:
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.I)
    candidate = fenced.group(1) if fenced else text
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError as first_error:
        match = re.search(r"\{[\s\S]*\}", candidate)
        if not match:
            if candidate.lstrip().startswith("{"):
                raise ApiError(
                    "模型返回的 JSON 不完整，可能在输出上限处被截断"
                ) from first_error
            raise ApiError("模型返回内容不是 JSON") from first_error
        try:
            value = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise ApiError("模型返回的 JSON 不完整，可能在输出上限处被截断") from exc
    if not isinstance(value, dict):
        raise ApiError("模型返回 JSON 顶层必须是对象")
    return value
