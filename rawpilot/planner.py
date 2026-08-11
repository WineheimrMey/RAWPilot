from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from .api_client import ApiError, QwenApiClient
from .color_knowledge import PLANNING_KNOWLEDGE, REVIEW_KNOWLEDGE
from .i18n import output_language_instruction
from .models import Diagnosis, EditPlan

PLAN_SYSTEM = """你是资深 Lightroom Classic 调色师与严格 JSON 规划器。结合画面诊断和用户要求制定可执行方案。
不要输出 markdown，只允许下列结构；未使用的控制设为 0，不得添加字段：
{
  "white_balance": "As Shot|Custom",
  "temperature": 2000..50000, "tint": -150..150, "exposure": -3..3,
  "contrast": -100..100, "highlights": -100..100, "shadows": -100..100,
  "whites": -100..100, "blacks": -100..100, "texture": -100..100,
  "clarity": -100..100, "dehaze": -100..100, "vibrance": -100..100,
  "saturation": -100..100, "sharpening": 0..150,
  "sharpening_radius": 0.5..3, "sharpening_detail": 0..100,
  "sharpening_masking": 0..100,
  "luminance_noise_reduction": 0..100, "color_noise_reduction": 0..100,
  "remove_chromatic_aberration": true|false,
  "enable_profile_corrections": true|false,
  "color_mixer": {
    "red|orange|yellow|green|aqua|blue|purple|magenta":
      {"hue": -100..100, "saturation": -100..100, "luminance": -100..100}
  },
  "cinematic": {
    "curve_shadows": -100..100, "curve_darks": -100..100,
    "curve_lights": -100..100, "curve_highlights": -100..100,
    "shadow_hue": 0..360, "shadow_saturation": 0..100,
    "highlight_hue": 0..360, "highlight_saturation": 0..100,
    "split_balance": -100..100, "grain_amount": 0..100,
    "grain_size": 0..100, "vignette": -100..100
  },
  "local_adjustments": [{
    "target": "sky|subject|people|background", "label": "中文用途",
    "exposure": -2..2, "contrast|highlights|shadows|whites|blacks|texture|clarity|dehaze|saturation|temperature|tint": -100..100,
    "luminance_noise_reduction": 0..100
  }],
  "rationale": "中文"
}
必须像专业摄影后期一样按以下顺序推理，但只输出最终 JSON：
1. 技术校正：先依据直方图统计、EXIF 与诊断识别高光裁切、黑位堵塞、色偏和噪声。没有明确色偏或风格要求时使用 As Shot，不得习惯性写死 5500K；需要改变白平衡时才用 Custom。
2. 全局基准：Exposure 只决定中间调整体亮度；Highlights/Whites 保护亮端，Shadows/Blacks 建立暗端。先获得可用动态范围，禁止用强对比制造“质感”。
3. 区域塑形：天空、主体、人物、背景存在不同要求时必须用 AI 蒙版分区。全局参数只解决全画面共同问题。
4. 色彩关系：先用 Vibrance 做温和统一，再用 HSL 修正画面中真实存在的色域。肤色主要落在红/橙，不得为处理天空连带破坏肤色。
5. 风格塑造：Tone Curve、Color Grading、Clarity、Dehaze、颗粒和暗角最后使用，幅度克制；风格不能破坏前面建立的曝光、肤色和主体可读性。
6. 细节输出：先按 ISO 估算降噪，再设置锐化；高 ISO 或大面积平滑区域提高 sharpening_masking，避免把噪声锐化。默认启用镜头配置文件与色差移除。

参数分工必须清晰：同一个视觉目的不要同时在五六个控制上重复叠加。普通修正优先保持单项在 ±35 内；超过 ±60 必须是诊断或用户要求明确支持的局部问题。
最多四个 local_adjustments。只对诊断中实际存在的区域创建蒙版。
不要在 rationale 中声称使用了 JSON local_adjustments 里不存在的蒙版。Lightroom Bridge 不支持 foreground 目标；大面积前景欠曝必须先用全局曝光、阴影、黑色色阶与曲线恢复，不能把任务错误地交给 subject 蒙版。
当要求之间互相冲突时必须分区处理：例如天空变暗但人物可见，应压暗 sky 蒙版并提亮 people 蒙版，不能用全局高对比抵消阴影提升。
蓝色天空变黑应组合 sky 局部曝光/黑色色阶、蓝/青 HSL 明度与饱和度；鲜明火花优先增强橙黄红色，不要把所有高光变白。
电影感应来自克制的曲线、冷阴影/暖高光、颗粒和适量暗角，不等于单纯增加对比。
避免过量降噪抹除火花与纹理；所有数值必须可逆且保护高光。
如果输入包含风格词，先拆成影调基调、色彩关系、饱和分布、质感、空间层级与强度，再映射参数。
不要机械复刻“电影感/高级/胶片感”的常见配方。技术校正不能随风格强度一起缩放。
""" + PLANNING_KNOWLEDGE

REFINE_SYSTEM = PLAN_SYSTEM + """

当前任务是成片后的二次调色。用户已经看过第一版成片，并给出了新的修改意见。
必须以 current_plan 为起点，只修改与 feedback 有关的参数；不要无故推翻用户已经认可的部分。
为了减少 token，只返回发生变化的字段组成的局部 JSON，不要重复未改变的字段。可以返回嵌套的
color_mixer 或 cinematic 子字段；必须包含 rationale，先简述用户不满意的地方，再说明本次改变。
不要返回 local_adjustments。后处理会保留第一版已有的 AI 蒙版，不会重新创建局部蒙版；
本次重点通过基础面板、HSL、曲线、色彩分级、颗粒与暗角完成修订。
""" + REVIEW_KNOWLEDGE


def _client_language(client: object) -> str:
    settings = getattr(client, "settings", None)
    return getattr(settings, "interface_language", "zh_CN")


def _clamp(data: dict[str, Any]) -> dict[str, Any]:
    limits = {
        "temperature": (2000, 50000), "tint": (-150, 150), "exposure": (-3.0, 3.0),
        "contrast": (-100, 100), "highlights": (-100, 100), "shadows": (-100, 100),
        "whites": (-100, 100), "blacks": (-100, 100), "texture": (-100, 100),
        "clarity": (-100, 100), "dehaze": (-100, 100), "vibrance": (-100, 100),
        "saturation": (-100, 100), "sharpening": (0, 150),
        "sharpening_radius": (0.5, 3.0), "sharpening_detail": (0, 100),
        "sharpening_masking": (0, 100),
        "luminance_noise_reduction": (0, 100), "color_noise_reduction": (0, 100),
    }
    white_balance_source = data.get("white_balance")
    if isinstance(white_balance_source, dict):
        white_balance_source = (
            white_balance_source.get("mode")
            or white_balance_source.get("value")
            or white_balance_source.get("name")
        )
    result: dict[str, Any] = {
        "white_balance": (
            white_balance_source
            if white_balance_source in {"As Shot", "Custom"}
            else "As Shot"
        ),
        "remove_chromatic_aberration": bool(data.get("remove_chromatic_aberration", True)),
        "enable_profile_corrections": bool(data.get("enable_profile_corrections", True)),
    }
    for key, (low, high) in limits.items():
        if key in data:
            value = float(data[key])
            result[key] = max(low, min(high, value))
    colors = ("red", "orange", "yellow", "green", "aqua", "blue", "purple", "magenta")
    mixer_source = data.get("color_mixer", {})
    mixer: dict[str, dict[str, float]] = {}
    if not isinstance(mixer_source, dict):
        mixer_source = {}
    for color in colors:
        channel_source = mixer_source.get(color, {})
        if not isinstance(channel_source, dict):
            channel_source = {}
        mixer[color] = {
            name: max(-100, min(100, float(channel_source.get(name, 0))))
            for name in ("hue", "saturation", "luminance")
        }
    result["color_mixer"] = mixer

    cinematic_source = data.get("cinematic", {})
    if not isinstance(cinematic_source, dict):
        cinematic_source = {}
    cinematic_limits = {
        "curve_shadows": (-100, 100), "curve_darks": (-100, 100),
        "curve_lights": (-100, 100), "curve_highlights": (-100, 100),
        "shadow_hue": (0, 360), "shadow_saturation": (0, 100),
        "highlight_hue": (0, 360), "highlight_saturation": (0, 100),
        "split_balance": (-100, 100), "grain_amount": (0, 100),
        "grain_size": (0, 100), "vignette": (-100, 100),
    }
    result["cinematic"] = {
        key: max(low, min(high, float(cinematic_source.get(key, 0 if key != "grain_size" else 25))))
        for key, (low, high) in cinematic_limits.items()
    }

    local_limits = {
        "exposure": (-2.0, 2.0), "contrast": (-100, 100), "highlights": (-100, 100),
        "shadows": (-100, 100), "whites": (-100, 100), "blacks": (-100, 100),
        "texture": (-100, 100), "clarity": (-100, 100), "dehaze": (-100, 100),
        "saturation": (-100, 100), "temperature": (-100, 100), "tint": (-100, 100),
        "luminance_noise_reduction": (0, 100),
    }
    local_result: list[dict[str, Any]] = []
    local_source = data.get("local_adjustments", [])
    if isinstance(local_source, list):
        for item in local_source[:4]:
            if not isinstance(item, dict) or item.get("target") not in {"sky", "subject", "people", "background"}:
                continue
            adjustment: dict[str, Any] = {
                "target": item["target"],
                "label": str(item.get("label", "")),
            }
            for key, (low, high) in local_limits.items():
                adjustment[key] = max(low, min(high, float(item.get(key, 0))))
            local_result.append(adjustment)
    result["local_adjustments"] = local_result
    result["rationale"] = str(data.get("rationale", ""))
    return result


def _apply_intent_guardrails(
    data: dict[str, Any],
    style: str,
    diagnosis: Diagnosis | None = None,
) -> dict[str, Any]:
    """Resolve common contradictory edits after model planning."""

    normalized = style.lower()
    english_intent = not any("\u4e00" <= char <= "\u9fff" for char in style)
    dark_sky = any(
        phrase in (normalized if english_intent else normalized.replace(" ", ""))
        for phrase in (
            "天空变黑",
            "天空压黑",
            "天空改成黑",
            "黑色天空",
            "天空不再蓝",
            "天空去蓝",
            "black sky",
            "darken the sky",
            "remove blue from the sky",
            "sky no longer blue",
        )
    )
    visible_people = any(
        token in normalized
        for token in (
            "看清", "暗部不能太低", "人物可见", "提亮人物",
            "people visible", "readable people", "lift the people", "see the people",
        )
    )
    cinematic = any(token in normalized for token in ("电影", "cinematic"))
    dark_frame = bool(diagnosis and diagnosis.preview_shadow_fraction >= 0.48)
    recover_dark_regions = any(
        token in normalized
        for token in (
            "死黑", "提亮前景", "抬起暗部", "暗部细节", "看清", "欠曝", "不能太黑",
            "blocked shadows", "lift the foreground", "open the shadows", "shadow detail",
            "underexposed", "too dark",
        )
    )
    warm_intent = any(token in normalized for token in ("偏暖", "温暖", "暖色", "warm", "金色"))
    green_intent = any(
        token in normalized
        for token in ("偏绿", "绿色调", "青绿色", "teal", "green cast")
    )
    diagnosis_text = ""
    if diagnosis:
        diagnosis_text = " ".join(
            (
                diagnosis.scene,
                diagnosis.exposure,
                diagnosis.noise,
                diagnosis.summary,
            )
        ).lower()
    night_scene = any(
        token in diagnosis_text
        for token in (
            "夜景", "夜间", "低光", "高iso", "高 iso", "噪点", "噪声",
            "night", "low light", "high iso", "noise",
        )
    )
    masks = data["local_adjustments"]

    def ensure_mask(target: str, label: str) -> dict[str, Any]:
        for adjustment in masks:
            if adjustment["target"] == target:
                return adjustment
        adjustment = {
            "target": target, "label": label, "exposure": 0.0, "contrast": 0,
            "highlights": 0, "shadows": 0, "whites": 0, "blacks": 0,
            "texture": 0, "clarity": 0, "dehaze": 0, "saturation": 0,
            "temperature": 0, "tint": 0, "luminance_noise_reduction": 0,
        }
        if len(masks) < 4:
            masks.append(adjustment)
        return adjustment

    if dark_sky:
        for color in ("aqua", "blue"):
            channel = data["color_mixer"][color]
            channel["saturation"] = min(channel["saturation"], -75)
            channel["luminance"] = min(channel["luminance"], -65)
        sky = ensure_mask(
            "sky",
            "Targeted darkening and blue removal for the sky"
            if english_intent else "定向压暗并去除蓝色天空",
        )
        sky["exposure"] = min(sky["exposure"], -0.9)
        sky["blacks"] = min(sky["blacks"], -35)
        sky["saturation"] = min(sky["saturation"], -70)

    if visible_people:
        data["exposure"] = max(data.get("exposure", 0), 0.55)
        data["shadows"] = max(data.get("shadows", 0), 80)
        data["contrast"] = min(data.get("contrast", 0), 15)
        data["blacks"] = max(data.get("blacks", 0), 15)
        look = data["cinematic"]
        look["curve_shadows"] = max(look["curve_shadows"], 15)
        look["curve_darks"] = max(look["curve_darks"], 0)
        look["vignette"] = max(look["vignette"], -10)
        people = ensure_mask(
            "people",
            "Recover silhouettes, clothing, and facial shadow detail"
            if english_intent else "恢复人物轮廓、衣着和面部暗部",
        )
        people["exposure"] = max(people["exposure"], 1.25)
        people["shadows"] = max(people["shadows"], 80)
        people["blacks"] = max(people["blacks"], 15)
        people["luminance_noise_reduction"] = max(people["luminance_noise_reduction"], 25)

    if cinematic:
        look = data["cinematic"]
        look["shadow_saturation"] = min(look["shadow_saturation"], 25)
        look["highlight_saturation"] = min(look["highlight_saturation"], 45)
        look["grain_amount"] = min(max(look["grain_amount"], 10), 30)
        look["vignette"] = max(look["vignette"], -20)

    if warm_intent:
        data["white_balance"] = "Custom"
        data["temperature"] = max(data.get("temperature", 5500), 5200)
        data["cinematic"]["shadow_saturation"] = min(
        data["cinematic"]["shadow_saturation"], 18
        )

    # A negative Tint is a magenta-to-green shift, not a generic way to make
    # a night scene cooler. Keep neutral lamps and concrete from turning
    # fluorescent green unless the photographer explicitly asks for it.
    if not green_intent:
        data["tint"] = max(data.get("tint", 0), -4)
        data["color_mixer"]["green"]["saturation"] = min(
            data["color_mixer"]["green"]["saturation"], 0
        )
        data["color_mixer"]["aqua"]["saturation"] = min(
            data["color_mixer"]["aqua"]["saturation"], 0
        )

    # Long-exposure and high-ISO night frames cannot tolerate aggressive
    # micro-contrast. It turns ordinary motion blur into halos/ghosting and
    # sharpens chroma noise around lamps and railings.
    if night_scene:
        data["texture"] = min(data.get("texture", 0), 12)
        data["clarity"] = min(data.get("clarity", 0), 8)
        data["dehaze"] = min(data.get("dehaze", 0), 8)
        data["sharpening_detail"] = min(
            data.get("sharpening_detail", 25), 35
        )
        data["sharpening_masking"] = max(
            data.get("sharpening_masking", 20), 60
        )
        data["luminance_noise_reduction"] = max(
            data.get("luminance_noise_reduction", 0), 25
        )
        data["color_noise_reduction"] = max(
            data.get("color_noise_reduction", 25), 30
        )
        for adjustment in masks:
            if adjustment["target"] == "subject":
                adjustment["texture"] = min(adjustment["texture"], 8)
                adjustment["clarity"] = min(adjustment["clarity"], 6)
                adjustment["luminance_noise_reduction"] = max(
                    adjustment["luminance_noise_reduction"], 20
                )
            elif adjustment["target"] == "background":
                adjustment["texture"] = min(adjustment["texture"], 15)
                adjustment["clarity"] = min(adjustment["clarity"], 8)

    # Embedded camera previews often contain a lifted vendor tone curve while
    # Lightroom's initial RAW rendering is considerably darker. Keep a dark
    # preview from receiving another global darkening pass.
    if dark_frame:
        data["exposure"] = max(data.get("exposure", 0), 0.4)
        data["shadows"] = max(data.get("shadows", 0), 68)
        data["blacks"] = max(data.get("blacks", 0), 18)
        data["contrast"] = min(data.get("contrast", 0), 15)
        data["dehaze"] = min(data.get("dehaze", 0), 10)
        look = data["cinematic"]
        look["curve_shadows"] = max(look["curve_shadows"], 15)
        look["curve_darks"] = max(look["curve_darks"], 8)
        look["vignette"] = max(look["vignette"], -10)
        if recover_dark_regions:
            data["exposure"] = max(data["exposure"], 0.9)
            data["shadows"] = max(data["shadows"], 85)
            data["blacks"] = max(data["blacks"], 25)
            data["contrast"] = min(data["contrast"], 8)
            data["dehaze"] = min(data["dehaze"], 6)
            look["curve_shadows"] = max(look["curve_shadows"], 20)
            look["curve_darks"] = max(look["curve_darks"], 14)
            look["vignette"] = max(look["vignette"], -5)
        if not dark_sky:
            for color in ("aqua", "blue"):
                channel = data["color_mixer"][color]
                channel["luminance"] = max(channel["luminance"], -30)
            for adjustment in masks:
                if adjustment["target"] == "sky":
                    adjustment["exposure"] = max(adjustment["exposure"], -0.4)
                    adjustment["blacks"] = max(adjustment["blacks"], -15)
    return data


def plan_edits(diagnosis: Diagnosis, style: str, client: QwenApiClient, mock: bool = False) -> EditPlan:
    if mock:
        warm = any(word in style.lower() for word in ("暖", "warm", "夕阳", "胶片"))
        dramatic = any(word in style.lower() for word in ("电影", "dramatic", "质感", "cinematic"))
        return EditPlan(
            white_balance="Custom" if warm else "As Shot",
            temperature=5900 if warm else 5500, exposure=0.2, contrast=12 if dramatic else 5,
            highlights=-28, shadows=22, whites=5, blacks=-8, texture=6,
            clarity=8 if dramatic else 3, dehaze=4, vibrance=12, saturation=-2,
            sharpening=45, sharpening_radius=1.0, sharpening_detail=25,
            sharpening_masking=35, luminance_noise_reduction=15,
            color_noise_reduction=25,
            cinematic={
                "curve_shadows": 6, "curve_darks": -8, "curve_lights": 8,
                "curve_highlights": -4, "shadow_hue": 220, "shadow_saturation": 8,
                "highlight_hue": 38, "highlight_saturation": 10, "split_balance": 5,
                "grain_amount": 12, "grain_size": 24, "vignette": -10,
            } if dramatic else {},
            rationale=(
                f"Mock plan: apply a restrained global baseline for the '{style or 'natural'}' direction."
                if _client_language(client) == "en_US"
                else f"Mock 方案：依据诊断并采用“{style or '自然真实'}”风格，进行克制的全局调整。"
            ),
        )
    data = client.language_json(
        PLAN_SYSTEM + output_language_instruction(_client_language(client)),
        {"diagnosis": diagnosis.model_dump(), "style": style or "自然真实"},
    )
    try:
        bounded = _apply_intent_guardrails(_clamp(data), style, diagnosis)
        return EditPlan.model_validate(bounded)
    except (ValidationError, TypeError, ValueError) as exc:
        raise ApiError(f"模型 edit_plan 校验失败：{exc}") from exc


def _merge_plan(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_plan(merged[key], value)
        else:
            merged[key] = value
    return merged


def refine_edits(
    diagnosis: Diagnosis,
    current_plan: EditPlan,
    original_intent: str,
    feedback: str,
    client: QwenApiClient,
    mock: bool = False,
) -> EditPlan:
    """Revise an existing recipe after the user has inspected the render."""

    if not feedback.strip():
        raise ApiError("请先填写对当前成片的修改意见。")
    if mock:
        refined = current_plan.model_copy(deep=True)
        normalized = feedback.lower()
        if any(token in normalized for token in ("亮", "提曝光", "暗部", "brighter", "exposure", "shadows")):
            refined.exposure = min(3.0, refined.exposure + 0.35)
            refined.shadows = min(100, max(refined.shadows, 65) + 10)
        if any(token in normalized for token in ("暗一点", "压暗", "太亮", "darker", "too bright")):
            refined.exposure = max(-3.0, refined.exposure - 0.3)
        if any(token in normalized for token in ("暖", "偏黄", "warmer", "warm")):
            refined.temperature = min(50000, refined.temperature + 300)
        if any(token in normalized for token in ("冷", "偏蓝", "cooler", "cool")):
            refined.temperature = max(2000, refined.temperature - 300)
        if any(token in normalized for token in ("太艳", "降低饱和", "淡一点", "saturation", "too vivid")):
            refined.vibrance = max(-100, refined.vibrance - 12)
            refined.saturation = max(-100, refined.saturation - 8)
        if any(token in normalized for token in ("对比低", "柔和", "对比太强", "lower contrast", "too contrasty")):
            refined.contrast = max(-100, refined.contrast - 12)
            refined.clarity = max(-100, refined.clarity - 8)
        refined.rationale = (
            f"Mock revision: incrementally update the first recipe using '{feedback}'."
            if _client_language(client) == "en_US"
            else f"Mock 后处理：根据“{feedback}”在第一版基础上进行增量修订。"
        )
        return refined

    base = current_plan.model_dump()
    data = client.language_json(
        REFINE_SYSTEM + output_language_instruction(_client_language(client)),
        {
            "diagnosis": diagnosis.model_dump(),
            "original_intent": original_intent,
            "feedback": feedback,
            "current_plan": base,
        },
    )
    # The first-pass Lightroom masks are intentionally retained. Replacing
    # them here would create duplicate masks on every review iteration.
    merged = _merge_plan(base, data)
    merged["local_adjustments"] = base["local_adjustments"]
    try:
        bounded = _apply_intent_guardrails(
            _clamp(merged),
            original_intent + "\n后处理意见：" + feedback,
            diagnosis,
        )
        return EditPlan.model_validate(bounded)
    except (ValidationError, TypeError, ValueError) as exc:
        raise ApiError(f"模型后处理 edit_plan 校验失败：{exc}") from exc
