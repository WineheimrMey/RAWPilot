from rawpilot.models import Diagnosis, LocalAdjustment
from rawpilot.planner import plan_edits, refine_edits
from rawpilot.settings import AppSettings
from rawpilot.api_client import QwenApiClient


def test_mock_plan_is_valid_and_bounded():
    client = QwenApiClient(AppSettings(mock_mode=True))
    plan = plan_edits(Diagnosis(), "暖色电影感", client, mock=True)
    assert -3 <= plan.exposure <= 3
    assert 2000 <= plan.temperature <= 50000
    assert plan.temperature > 5500
    assert plan.highlights < 0
    assert plan.cinematic.grain_amount > 0
    assert plan.white_balance == "Custom"
    assert plan.enable_profile_corrections
    assert plan.remove_chromatic_aberration
    assert 0.5 <= plan.sharpening_radius <= 3


def test_neutral_mock_plan_preserves_as_shot_white_balance():
    client = QwenApiClient(AppSettings(mock_mode=True))
    plan = plan_edits(Diagnosis(), "自然真实，保持现场色温", client, mock=True)
    assert plan.white_balance == "As Shot"


def test_plan_supports_color_mixer_and_local_ai_masks():
    class FakeClient:
        def language_json(self, system, user):
            return {
                "temperature": 4000,
                "shadows": 35,
                "color_mixer": {
                    "blue": {"hue": 0, "saturation": -120, "luminance": -140},
                    "orange": {"hue": -5, "saturation": 40, "luminance": 15},
                },
                "cinematic": {
                    "curve_shadows": 8, "curve_darks": -15, "curve_lights": 10,
                    "curve_highlights": -5, "shadow_hue": 220, "shadow_saturation": 12,
                    "highlight_hue": 38, "highlight_saturation": 22,
                    "split_balance": 5, "grain_amount": 18, "grain_size": 24,
                    "vignette": -12,
                },
                "local_adjustments": [
                    {"target": "sky", "label": "压暗天空", "exposure": -3, "saturation": -100},
                    {"target": "people", "label": "提亮人物", "exposure": 1.1, "shadows": 70},
                ],
                "rationale": "分区处理",
            }

    plan = plan_edits(Diagnosis(), "天空变黑，人物可见", FakeClient(), mock=False)
    assert plan.color_mixer.blue.saturation == -100
    assert plan.color_mixer.blue.luminance == -100
    assert plan.local_adjustments[0].exposure == -2
    assert plan.local_adjustments[1].target == "people"
    assert plan.shadows >= 70
    assert plan.blacks >= 8
    assert plan.cinematic.curve_shadows >= 10
    assert plan.local_adjustments[1].exposure >= 1.25


def test_dark_preview_cannot_receive_another_global_darkening_pass():
    class FakeClient:
        def language_json(self, system, user):
            return {
                "exposure": -0.3,
                "contrast": 30,
                "highlights": -65,
                "shadows": 40,
                "blacks": 10,
                "dehaze": 18,
                "color_mixer": {
                    "blue": {"luminance": -70},
                    "aqua": {"luminance": -70},
                },
                "cinematic": {"vignette": -30},
                "local_adjustments": [
                    {"target": "sky", "exposure": -1.0, "blacks": -40},
                ],
            }

    diagnosis = Diagnosis(
        preview_mean_luminance=52,
        preview_shadow_fraction=0.57,
    )
    plan = plan_edits(
        diagnosis,
        "解决前景死黑问题，压低天空高光，保留门洞结构",
        FakeClient(),
        mock=False,
    )
    assert plan.exposure >= 0.9
    assert plan.shadows >= 85
    assert plan.blacks >= 25
    assert plan.contrast <= 8
    assert plan.cinematic.vignette >= -5
    assert plan.color_mixer.blue.luminance >= -30
    assert plan.local_adjustments[0].exposure >= -0.4


def test_night_scene_guardrails_prevent_green_cast_and_ghost_enhancement():
    class FakeClient:
        def language_json(self, system, user):
            return {
                "white_balance": "Custom",
                "temperature": 4200,
                "tint": -22,
                "texture": 35,
                "clarity": 25,
                "dehaze": 18,
                "sharpening_detail": 75,
                "sharpening_masking": 20,
                "luminance_noise_reduction": 5,
                "color_mixer": {
                    "green": {"saturation": 30},
                    "aqua": {"saturation": 20},
                },
                "local_adjustments": [
                    {
                        "target": "subject",
                        "texture": 30,
                        "clarity": 25,
                    },
                    {
                        "target": "background",
                        "texture": 40,
                        "clarity": 20,
                    },
                ],
            }

    diagnosis = Diagnosis(
        scene="高 ISO 城市夜景",
        noise="暗部噪点明显",
        summary="人物存在运动拖影",
    )
    plan = plan_edits(
        diagnosis,
        "保持自然的冷夜氛围，不要改变灯光颜色",
        FakeClient(),
        mock=False,
    )
    assert plan.tint >= -4
    assert plan.color_mixer.green.saturation <= 0
    assert plan.color_mixer.aqua.saturation <= 0
    assert plan.texture <= 12
    assert plan.clarity <= 8
    assert plan.sharpening_detail <= 35
    assert plan.sharpening_masking >= 60
    assert plan.local_adjustments[0].clarity <= 6
    assert plan.local_adjustments[1].texture <= 15


def test_refinement_is_incremental_and_preserves_existing_masks():
    class FakeClient:
        def language_json(self, system, user):
            return {
                "exposure": 0.65,
                "temperature": 5700,
                "contrast": 5,
                "rationale": "按反馈提亮并转暖",
                "local_adjustments": [
                    {"target": "background", "exposure": -2},
                ],
            }

    current = plan_edits(
        Diagnosis(),
        "自然真实",
        QwenApiClient(AppSettings(mock_mode=True)),
        mock=True,
    )
    current.local_adjustments = [
        LocalAdjustment(
            target="sky",
            label="第一版天空",
            exposure=-0.3,
        )
    ]
    refined = refine_edits(
        Diagnosis(),
        current,
        "自然真实",
        "整体再亮一点，也更暖一些",
        FakeClient(),
        mock=False,
    )
    assert refined.exposure == 0.65
    assert refined.temperature == 5700
    assert refined.highlights == current.highlights
    assert refined.local_adjustments == current.local_adjustments


def test_refinement_keeps_masks_but_applies_night_safety_to_their_controls():
    class FakeClient:
        def language_json(self, system, user):
            return {
                "tint": -18,
                "texture": 30,
                "rationale": "去除绿色污染并减轻鬼影",
            }

    current = plan_edits(
        Diagnosis(),
        "自然真实",
        QwenApiClient(AppSettings(mock_mode=True)),
        mock=True,
    )
    current.local_adjustments = [
        LocalAdjustment(
            target="subject",
            texture=30,
            clarity=25,
        )
    ]
    refined = refine_edits(
        Diagnosis(scene="高 ISO 夜景", noise="暗部噪点明显"),
        current,
        "自然冷夜",
        "去掉绿色灯光和人物边缘鬼影",
        FakeClient(),
        mock=False,
    )
    assert len(refined.local_adjustments) == 1
    assert refined.local_adjustments[0].target == "subject"
    assert refined.local_adjustments[0].texture <= 8
    assert refined.local_adjustments[0].clarity <= 6
    assert refined.tint >= -4


def test_refinement_accepts_object_form_white_balance_from_model():
    class FakeClient:
        def language_json(self, system, user):
            return {
                "white_balance": {
                    "mode": "Custom",
                },
                "temperature": 4800,
                "tint": 6,
                "rationale": "修正偏绿",
            }

    current = plan_edits(
        Diagnosis(),
        "自然真实",
        QwenApiClient(AppSettings(mock_mode=True)),
        mock=True,
    )
    refined = refine_edits(
        Diagnosis(scene="城市夜景"),
        current,
        "保持自然灯光",
        "去掉绿色污染",
        FakeClient(),
        mock=False,
    )
    assert refined.white_balance == "Custom"
    assert refined.temperature == 4800
    assert refined.tint == 6
