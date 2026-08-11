from __future__ import annotations

from .api_client import QwenApiClient
from .color_knowledge import (
    DIAGNOSIS_KNOWLEDGE,
    REVIEW_KNOWLEDGE,
    SERIES_KNOWLEDGE,
    STYLE_KNOWLEDGE,
)
from .i18n import output_language_instruction
from .models import Diagnosis, EditPlan, RawAsset, RenderReview
from .quality import luminance_stats

VISION_SYSTEM = """你是一名严谨的 RAW 摄影诊断助手。只分析所给压缩预览和 EXIF，不能声称看过 RAW 原始数据。
请像专业调色师一样识别画面的空间与语义区域，特别留意天空、人物、主体、前景、火焰/灯光/烟花等高亮物。
返回严格 JSON，不要 markdown，且仅含字段：
scene, exposure, white_balance, highlights, shadows, skin_tone, noise,
subjects, sky, foreground, bright_regions, dark_regions, color_palette,
local_edit_opportunities, summary, suggested_style。
local_edit_opportunities 要指出哪些区域适合天空、人物、主体或背景 AI 蒙版，以及各区域应避免的问题。
suggested_style 必须是一段 60 到 140 字、摄影师可以直接修改并作为调色指令使用的自然中文；先说明画面最值得修正的问题，再提出光线、色彩、主体、局部蒙版和质感方向。建议必须针对当前画面，不要写成通用模板，也不要给出具体滑杆数字。
可自动执行的 AI 选区只有天空、主体和背景；不要承诺“前景蒙版”。大面积前景欠曝时应建议用全局曝光、阴影和黑色色阶恢复，再用主体选区做重点加强。
每个字段使用简洁中文；不确定时明确说明。
建议风格时要说明影调基调、色彩关系、主体层级与质感，避免只写“电影感”“高级感”等空泛标签。
""" + DIAGNOSIS_KNOWLEDGE + STYLE_KNOWLEDGE + SERIES_KNOWLEDGE

RENDER_REVIEW_SYSTEM = """你是摄影工作室的成片质检总监。你会同时看到相机内嵌预览 BEFORE 和 Lightroom 成片 AFTER。
请判断调色是否真正改善画面并符合用户意图，而不只是判断 AFTER 是否能看。重点核对：主体与关键人物是否可读、
亮暗层次是否堵塞或溢出、白平衡与肤色是否可信、用户点名的颜色和区域是否改变、风格是否由克制的曲线与色彩关系形成，
以及噪声/锐化是否自然。必须特别检查 AFTER 是否相对 BEFORE 新增或放大了绿色/青色灯光污染、人物重影、边缘光晕、
运动拖影、塑料感、过度锐化、局部蒙版边界和灯具溢色。原片已有且未被放大的运动模糊不能误判为调色新增问题。
只返回严格 JSON：
{
  "intent_match": 0..100,
  "tonal_balance": 0..100,
  "color_coherence": 0..100,
  "retry_required": true|false,
  "issues": ["最多五条具体问题"],
  "feedback": "一段可直接交给 Lightroom 调色师执行的修订意见"
}
只有存在明确、可修正且影响用户主要意图的问题时 retry_required 才为 true。不要要求 Photoshop、生成式填充、移动物体或 Lightroom 无法完成的像素级改造。
""" + REVIEW_KNOWLEDGE


def _client_language(client: object) -> str:
    settings = getattr(client, "settings", None)
    return getattr(settings, "interface_language", "zh_CN")


def analyze(asset: RawAsset, client: QwenApiClient, mock: bool = False) -> Diagnosis:
    if mock:
        iso = asset.exif.get("EXIF ISOSpeedRatings", "unknown")
        if _client_language(client) == "en_US":
            diagnosis = Diagnosis(
                scene="Mock: general photographic scene",
                exposure="Exposure is broadly usable; a slight midtone lift may help",
                white_balance="White balance appears neutral",
                highlights="Recover highlights conservatively to retain texture",
                shadows="Open useful shadows moderately",
                skin_tone="The preview is insufficient for a confident skin-tone judgment",
                noise=f"Based on EXIF ISO {iso}, apply moderate noise reduction",
                summary="Mock assessment: build a natural, restrained baseline with protected highlights.",
                suggested_style=(
                    "Correct the overall exposure and white balance first, protect vulnerable highlights, "
                    "and open only useful subject shadows. Preserve the scene's existing color relationships, "
                    "then add subtle warm/cool separation, fine grain, and a gentle vignette without over-styling."
                ),
            )
        else:
            diagnosis = Diagnosis(
                scene="Mock：通用摄影场景",
                exposure="整体曝光基本正常，建议轻微提亮",
                white_balance="白平衡偏中性",
                highlights="保守压低高光以保留层次",
                shadows="可适度提亮阴影",
                skin_tone="预览不足以确认肤色",
                noise=f"基于 EXIF ISO {iso}，建议适量降噪",
                summary="Mock 诊断：采用自然、克制、保留高光的基础调整。",
                suggested_style=(
                    "先校正整体曝光与白平衡，压住容易溢出的高光，同时适度抬起主体暗部。"
                    "保持画面原有色彩关系，以克制的冷暖分离增加层次，再加入轻微颗粒和柔和暗角，"
                    "让视觉重心更集中但不过度风格化。"
                ),
            )
    else:
        if not asset.preview_path:
            raise ValueError("缺少可上传的 JPEG 预览")
        diagnosis = Diagnosis.model_validate(
            client.vision_json(
                asset.preview_path,
                asset.exif,
                VISION_SYSTEM + output_language_instruction(_client_language(client)),
            )
        )
    if not diagnosis.suggested_style.strip():
        if _client_language(client) == "en_US":
            diagnosis.suggested_style = (
                f"Resolve exposure ({diagnosis.exposure}) and white balance ({diagnosis.white_balance}) first. "
                f"For highlights, {diagnosis.highlights}; for shadows, {diagnosis.shadows}. "
                "Keep the subject natural, use local masks only for clearly identified regions, and finish with "
                "a restrained curve, color grading, and grain treatment."
            )
        else:
            diagnosis.suggested_style = (
                f"先处理{diagnosis.exposure}与{diagnosis.white_balance}的问题，"
                f"高光方面{diagnosis.highlights}，暗部方面{diagnosis.shadows}。"
                "保持主体自然，针对明确的天空、主体或背景区域使用局部蒙版，"
                "最后以克制的曲线、色彩分级和颗粒统一画面质感。"
            )
    if asset.preview_path:
        stats = luminance_stats(asset.preview_path)
        diagnosis.preview_mean_luminance = round(stats.mean, 2)
        diagnosis.preview_shadow_fraction = round(stats.shadow_fraction, 4)
        diagnosis.preview_highlight_fraction = round(stats.highlight_fraction, 4)
    return diagnosis


def review_render(
    source_preview: Path,
    rendered: Path,
    intent: str,
    plan: EditPlan,
    client: QwenApiClient,
    mock: bool = False,
) -> RenderReview:
    """Judge the exported frame against intent before accepting the result."""

    if mock:
        return RenderReview(
            intent_match=90,
            tonal_balance=90,
            color_coherence=90,
            retry_required=False,
            feedback=(
                "Mock render review passed."
                if _client_language(client) == "en_US"
                else "Mock 成片复审通过。"
            ),
        )
    context = {
        "用户意图": intent,
        "已执行参数摘要": {
            "white_balance": plan.white_balance,
            "exposure": plan.exposure,
            "highlights": plan.highlights,
            "shadows": plan.shadows,
            "whites": plan.whites,
            "blacks": plan.blacks,
            "local_adjustments": [
                {"target": item.target, "label": item.label}
                for item in plan.local_adjustments
            ],
        },
    }
    review = RenderReview.model_validate(
        client.vision_compare_json(
            source_preview,
            rendered,
            context,
            RENDER_REVIEW_SYSTEM
            + output_language_instruction(_client_language(client)),
        )
    )
    critical_text = "；".join(review.issues) + review.feedback
    critical = any(
        token in critical_text
        for token in (
            "严重过曝", "严重欠曝", "死黑", "层次丢失", "主体不可见",
            "人物不可见", "肤色失真", "明显偏离", "偏绿", "绿色污染",
            "鬼影", "重影", "光晕", "过度锐化", "蒙版边界",
        )
    )
    # A model should not request another paid render for a merely aesthetic
    # nit, but explicit technical failures must not be waved through by an
    # over-generous numeric score.
    review.retry_required = (
        (review.retry_required and (
            review.intent_match < 85 or review.tonal_balance < 75
        ))
        or review.intent_match < 72
        or review.tonal_balance < 65
        or critical
    )
    return review
