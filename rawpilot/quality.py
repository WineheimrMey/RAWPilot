from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from .models import EditPlan


@dataclass(frozen=True)
class LuminanceStats:
    mean: float
    p05: float
    p50: float
    p95: float
    black_fraction: float
    shadow_fraction: float
    highlight_fraction: float


@dataclass(frozen=True)
class QualityReport:
    passed: bool
    reason: str
    source: LuminanceStats
    rendered: LuminanceStats

    @property
    def summary(self) -> str:
        state = "通过" if self.passed else "需要恢复"
        return (
            f"成片质检{state}：输入均值 {self.source.mean:.1f} / 输出均值 "
            f"{self.rendered.mean:.1f}；输出暗部 {self.rendered.shadow_fraction:.0%}。"
            + (f" {self.reason}" if self.reason else "")
        )


def luminance_stats(path: Path) -> LuminanceStats:
    with Image.open(path) as image:
        gray = image.convert("L")
        gray.thumbnail((640, 640))
        histogram = gray.histogram()
    total = max(sum(histogram), 1)
    mean = sum(value * count for value, count in enumerate(histogram)) / total

    def percentile(fraction: float) -> float:
        target = total * fraction
        cumulative = 0
        for value, count in enumerate(histogram):
            cumulative += count
            if cumulative >= target:
                return float(value)
        return 255.0

    return LuminanceStats(
        mean=mean,
        p05=percentile(0.05),
        p50=percentile(0.50),
        p95=percentile(0.95),
        black_fraction=sum(histogram[:8]) / total,
        shadow_fraction=sum(histogram[:32]) / total,
        highlight_fraction=sum(histogram[235:]) / total,
    )


def intentionally_dark(intent: str) -> bool:
    normalized = intent.lower().replace(" ", "")
    if "天空" in normalized and not any(
        token in normalized for token in ("全片", "整张", "整个画面", "全场")
    ):
        return False
    return any(
        phrase in normalized
        for phrase in ("刻意全黑", "压成黑色", "纯黑剪影", "低调黑场", "主体剪影")
    )


def assess_render(source_preview: Path, rendered: Path, intent: str = "") -> QualityReport:
    source = luminance_stats(source_preview)
    output = luminance_stats(rendered)
    if intentionally_dark(intent):
        return QualityReport(True, "用户明确要求黑场或剪影。", source, output)

    reasons: list[str] = []
    if output.mean < max(12.0, source.mean * 0.52):
        reasons.append("输出平均亮度相对输入异常下降")
    if output.shadow_fraction > 0.82 and (
        output.shadow_fraction - source.shadow_fraction > 0.20
    ):
        reasons.append("超过八成画面落入深暗部")
    if output.p95 < max(35.0, source.p95 * 0.45):
        reasons.append("高光端也发生整体塌缩")
    return QualityReport(not reasons, "；".join(reasons), source, output)


def recover_underexposed_plan(
    plan: EditPlan,
    report: QualityReport,
    intent: str = "",
) -> EditPlan:
    """Create a reversible global recovery while keeping the first-pass masks."""

    recovered = plan.model_copy(deep=True)
    target_mean = report.source.mean * 0.70
    ratio = (target_mean + 4.0) / (report.rendered.mean + 4.0)
    exposure_boost = max(0.35, min(1.25, math.log2(max(ratio, 1.0))))
    recovered.exposure = round(min(3.0, max(0.4, recovered.exposure + exposure_boost)), 2)
    recovered.shadows = max(recovered.shadows, 70)
    recovered.blacks = max(recovered.blacks, 10)
    recovered.contrast = min(recovered.contrast, 12)
    recovered.dehaze = min(recovered.dehaze, 8)
    recovered.cinematic.curve_shadows = max(recovered.cinematic.curve_shadows, 12)
    recovered.cinematic.curve_darks = max(recovered.cinematic.curve_darks, 8)
    recovered.cinematic.vignette = max(recovered.cinematic.vignette, -8)
    if any(token in intent.lower() for token in ("暖", "warm", "金色", "夕阳")):
        recovered.temperature = max(recovered.temperature, 5200)
        recovered.cinematic.shadow_saturation = min(
            recovered.cinematic.shadow_saturation, 15
        )
    dark_sky = "天空" in intent and any(
        token in intent for token in ("变黑", "压黑", "接近黑", "不再蓝", "去蓝")
    )
    if not dark_sky:
        for color in ("aqua", "blue"):
            recovered.color_mixer.__getattribute__(color).luminance = max(
                recovered.color_mixer.__getattribute__(color).luminance, -25
            )
        for adjustment in recovered.local_adjustments:
            if adjustment.target == "sky":
                adjustment.exposure = max(adjustment.exposure, -0.35)
                adjustment.blacks = max(adjustment.blacks, -12)
    recovered.rationale = (
        recovered.rationale
        + f" 自动成片质检发现输出显著欠曝，追加 {exposure_boost:.2f} EV 的全局恢复，"
        "同时抬升阴影、黑色色阶并减弱暗角；保留高光压缩以保护窗外区域。"
    ).strip()
    return recovered
