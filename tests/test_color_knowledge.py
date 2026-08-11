from rawpilot.analyzer import RENDER_REVIEW_SYSTEM, VISION_SYSTEM
from rawpilot.color_knowledge import (
    DIAGNOSIS_KNOWLEDGE,
    PLANNING_KNOWLEDGE,
    REVIEW_KNOWLEDGE,
    SERIES_KNOWLEDGE,
    STYLE_KNOWLEDGE,
)
from rawpilot.planner import PLAN_SYSTEM, REFINE_SYSTEM


def test_runtime_agents_share_the_lightroom_skill() -> None:
    assert DIAGNOSIS_KNOWLEDGE in VISION_SYSTEM
    assert PLANNING_KNOWLEDGE in PLAN_SYSTEM
    assert REVIEW_KNOWLEDGE in RENDER_REVIEW_SYSTEM
    assert REVIEW_KNOWLEDGE in REFINE_SYSTEM
    assert STYLE_KNOWLEDGE in VISION_SYSTEM
    assert STYLE_KNOWLEDGE in PLAN_SYSTEM
    assert SERIES_KNOWLEDGE in VISION_SYSTEM
    assert SERIES_KNOWLEDGE in PLAN_SYSTEM


def test_skill_encodes_closed_loop_and_artifact_gates() -> None:
    assert "诊断 → 技术基准 → 区域塑形 → 色彩关系 → 风格 → 细节 → 成片复审" in PLAN_SYSTEM
    for issue in ("绿色", "鬼影", "光晕", "蒙版边界"):
        assert issue in RENDER_REVIEW_SYSTEM
    assert "最多自动返工两次" in RENDER_REVIEW_SYSTEM


def test_skill_routes_style_by_attributes_not_preset_names() -> None:
    for attribute in ("影调基调", "色彩关系", "饱和分布", "质感", "空间层级"):
        assert attribute in STYLE_KNOWLEDGE
    for style in ("自然纪实", "干净商业", "明亮通透", "情绪低调", "克制电影感", "黑白"):
        assert style in STYLE_KNOWLEDGE
    assert "电影感”不得默认青橙" in STYLE_KNOWLEDGE
    assert "技术校正不能随风格强度一起缩放" in PLAN_SYSTEM


def test_skill_separates_batch_style_from_per_frame_correction() -> None:
    for layer in ("技术层", "风格层", "局部层"):
        assert layer in SERIES_KNOWLEDGE
    assert "hero frame" in SERIES_KNOWLEDGE
    assert "禁止整套参数盲目同步" in SERIES_KNOWLEDGE
    assert "相邻帧" in REVIEW_KNOWLEDGE
