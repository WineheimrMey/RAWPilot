from pathlib import Path

from PIL import Image

from rawpilot.models import EditPlan
from rawpilot.quality import assess_render, recover_underexposed_plan


def test_rejects_output_that_collapses_into_black(tmp_path: Path):
    source = tmp_path / "source.jpg"
    output = tmp_path / "output.jpg"
    Image.new("RGB", (80, 80), (72, 72, 72)).save(source)
    Image.new("RGB", (80, 80), (4, 4, 4)).save(output)

    report = assess_render(source, output, "恢复暗部细节")
    assert not report.passed
    assert report.rendered.shadow_fraction > 0.8

    recovered = recover_underexposed_plan(
        EditPlan(exposure=-0.2, contrast=30, shadows=40, blacks=0),
        report,
    )
    assert recovered.exposure >= 0.8
    assert recovered.shadows >= 70
    assert recovered.blacks >= 10
    assert recovered.contrast <= 12


def test_dark_sky_recovery_does_not_undo_targeted_blue_treatment(tmp_path: Path):
    source = tmp_path / "source.jpg"
    output = tmp_path / "output.jpg"
    Image.new("RGB", (80, 80), (72, 72, 72)).save(source)
    Image.new("RGB", (80, 80), (4, 4, 4)).save(output)
    report = assess_render(source, output, "天空变黑但人物可见")
    plan = EditPlan()
    plan.color_mixer.blue.luminance = -70
    recovered = recover_underexposed_plan(
        plan, report, "天空变黑但人物可见"
    )
    assert recovered.color_mixer.blue.luminance == -70


def test_explicit_silhouette_intent_can_remain_dark(tmp_path: Path):
    source = tmp_path / "source.jpg"
    output = tmp_path / "output.jpg"
    Image.new("RGB", (40, 40), (80, 80, 80)).save(source)
    Image.new("RGB", (40, 40), (3, 3, 3)).save(output)

    assert assess_render(source, output, "把主体压成黑色剪影").passed
