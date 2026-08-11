from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RawAsset(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    path: Path
    preview_path: Path | None = None
    exif: dict[str, str] = Field(default_factory=dict)


class Diagnosis(BaseModel):
    scene: str = "未知场景"
    exposure: str = "曝光正常"
    white_balance: str = "白平衡自然"
    highlights: str = "高光正常"
    shadows: str = "阴影正常"
    skin_tone: str = "未检测到明确肤色"
    noise: str = "噪声水平未知"
    subjects: list[str] = Field(default_factory=list)
    sky: str = ""
    foreground: str = ""
    bright_regions: list[str] = Field(default_factory=list)
    dark_regions: list[str] = Field(default_factory=list)
    color_palette: list[str] = Field(default_factory=list)
    local_edit_opportunities: dict[str, str] = Field(default_factory=dict)
    summary: str = ""
    suggested_style: str = ""
    preview_mean_luminance: float = Field(0, ge=0, le=255)
    preview_shadow_fraction: float = Field(0, ge=0, le=1)
    preview_highlight_fraction: float = Field(0, ge=0, le=1)

    @field_validator("subjects", "bright_regions", "dark_regions", "color_palette", mode="before")
    @classmethod
    def normalize_string_lists(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return [str(item) for item in value]

    @field_validator("local_edit_opportunities", mode="before")
    @classmethod
    def normalize_local_opportunities(cls, value: Any) -> dict[str, str]:
        if value is None:
            return {}
        if isinstance(value, str):
            return {"general": value}
        if isinstance(value, dict):
            return {str(key): str(item) for key, item in value.items()}
        return {"general": str(value)}


class ColorChannel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    hue: int = Field(0, ge=-100, le=100)
    saturation: int = Field(0, ge=-100, le=100)
    luminance: int = Field(0, ge=-100, le=100)


class ColorMixer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    red: ColorChannel = Field(default_factory=ColorChannel)
    orange: ColorChannel = Field(default_factory=ColorChannel)
    yellow: ColorChannel = Field(default_factory=ColorChannel)
    green: ColorChannel = Field(default_factory=ColorChannel)
    aqua: ColorChannel = Field(default_factory=ColorChannel)
    blue: ColorChannel = Field(default_factory=ColorChannel)
    purple: ColorChannel = Field(default_factory=ColorChannel)
    magenta: ColorChannel = Field(default_factory=ColorChannel)


class CinematicLook(BaseModel):
    model_config = ConfigDict(extra="forbid")
    curve_shadows: int = Field(0, ge=-100, le=100)
    curve_darks: int = Field(0, ge=-100, le=100)
    curve_lights: int = Field(0, ge=-100, le=100)
    curve_highlights: int = Field(0, ge=-100, le=100)
    shadow_hue: int = Field(220, ge=0, le=360)
    shadow_saturation: int = Field(0, ge=0, le=100)
    highlight_hue: int = Field(40, ge=0, le=360)
    highlight_saturation: int = Field(0, ge=0, le=100)
    split_balance: int = Field(0, ge=-100, le=100)
    grain_amount: int = Field(0, ge=0, le=100)
    grain_size: int = Field(25, ge=0, le=100)
    vignette: int = Field(0, ge=-100, le=100)


class LocalAdjustment(BaseModel):
    """A bounded Lightroom AI selection and its local Develop controls."""

    model_config = ConfigDict(extra="forbid")
    target: Literal["sky", "subject", "people", "background"]
    label: str = ""
    exposure: float = Field(0, ge=-2.0, le=2.0)
    contrast: int = Field(0, ge=-100, le=100)
    highlights: int = Field(0, ge=-100, le=100)
    shadows: int = Field(0, ge=-100, le=100)
    whites: int = Field(0, ge=-100, le=100)
    blacks: int = Field(0, ge=-100, le=100)
    texture: int = Field(0, ge=-100, le=100)
    clarity: int = Field(0, ge=-100, le=100)
    dehaze: int = Field(0, ge=-100, le=100)
    saturation: int = Field(0, ge=-100, le=100)
    temperature: int = Field(0, ge=-100, le=100)
    tint: int = Field(0, ge=-100, le=100)
    luminance_noise_reduction: int = Field(0, ge=0, le=100)

    @field_validator("exposure", mode="before")
    @classmethod
    def round_local_exposure(cls, value: object) -> float:
        return round(float(value), 2)


class EditPlan(BaseModel):
    """A bounded Lightroom recipe with global, color and AI-local controls."""

    model_config = ConfigDict(extra="forbid")
    white_balance: Literal["As Shot", "Custom"] = "As Shot"
    temperature: int = Field(5500, ge=2000, le=50000, description="Absolute white-balance Kelvin")
    tint: int = Field(0, ge=-150, le=150)
    exposure: float = Field(0, ge=-3.0, le=3.0)
    contrast: int = Field(0, ge=-100, le=100)
    highlights: int = Field(0, ge=-100, le=100)
    shadows: int = Field(0, ge=-100, le=100)
    whites: int = Field(0, ge=-100, le=100)
    blacks: int = Field(0, ge=-100, le=100)
    texture: int = Field(0, ge=-100, le=100)
    clarity: int = Field(0, ge=-100, le=100)
    dehaze: int = Field(0, ge=-100, le=100)
    vibrance: int = Field(0, ge=-100, le=100)
    saturation: int = Field(0, ge=-100, le=100)
    sharpening: int = Field(40, ge=0, le=150)
    sharpening_radius: float = Field(1.0, ge=0.5, le=3.0)
    sharpening_detail: int = Field(25, ge=0, le=100)
    sharpening_masking: int = Field(20, ge=0, le=100)
    luminance_noise_reduction: int = Field(0, ge=0, le=100)
    color_noise_reduction: int = Field(25, ge=0, le=100)
    remove_chromatic_aberration: bool = True
    enable_profile_corrections: bool = True
    color_mixer: ColorMixer = Field(default_factory=ColorMixer)
    cinematic: CinematicLook = Field(default_factory=CinematicLook)
    local_adjustments: list[LocalAdjustment] = Field(default_factory=list, max_length=4)
    rationale: str = ""

    @field_validator("exposure", mode="before")
    @classmethod
    def round_exposure(cls, value: object) -> float:
        return round(float(value), 2)


class RenderReview(BaseModel):
    """A compact visual acceptance review of Lightroom's rendered result."""

    model_config = ConfigDict(extra="forbid")
    intent_match: int = Field(100, ge=0, le=100)
    tonal_balance: int = Field(100, ge=0, le=100)
    color_coherence: int = Field(100, ge=0, le=100)
    retry_required: bool = False
    issues: list[str] = Field(default_factory=list, max_length=5)
    feedback: str = ""

    @property
    def summary(self) -> str:
        issues = "；".join(self.issues) if self.issues else "未发现明显偏差"
        return (
            f"AI 成片复审：意图 {self.intent_match} / 明暗 {self.tonal_balance} / "
            f"色彩 {self.color_coherence}。{issues}"
        )


class ProcessResult(BaseModel):
    source: Path
    status: Literal["等待", "分析中", "待确认", "处理中", "成功", "失败"] = "等待"
    preview_path: Path | None = None
    diagnosis: Diagnosis | None = None
    suggested_style: str = ""
    final_prompt: str = ""
    plan: EditPlan | None = None
    xmp_path: Path | None = None
    rendered_path: Path | None = None
    quality_note: str = ""
    error: str = ""
