from __future__ import annotations

import json
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, register_namespace, tostring

from .models import EditPlan

NS = {
    "x": "adobe:ns:meta/",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "crs": "http://ns.adobe.com/camera-raw-settings/1.0/",
}
for prefix, uri in NS.items():
    register_namespace(prefix, uri)

XMP_FIELDS = {
    "exposure": "Exposure2012",
    "contrast": "Contrast2012", "highlights": "Highlights2012", "shadows": "Shadows2012",
    "whites": "Whites2012", "blacks": "Blacks2012", "texture": "Texture",
    "clarity": "Clarity2012", "dehaze": "Dehaze", "vibrance": "Vibrance",
    "saturation": "Saturation", "sharpening": "Sharpness",
    "sharpening_radius": "SharpenRadius",
    "sharpening_detail": "SharpenDetail",
    "sharpening_masking": "SharpenEdgeMasking",
    "luminance_noise_reduction": "LuminanceSmoothing", "color_noise_reduction": "ColorNoiseReduction",
}

COLOR_NAMES = {
    "red": "Red", "orange": "Orange", "yellow": "Yellow", "green": "Green",
    "aqua": "Aqua", "blue": "Blue", "purple": "Purple", "magenta": "Magenta",
}

CINEMATIC_FIELDS = {
    "curve_shadows": "ParametricShadows",
    "curve_darks": "ParametricDarks",
    "curve_lights": "ParametricLights",
    "curve_highlights": "ParametricHighlights",
    "shadow_hue": "SplitToningShadowHue",
    "shadow_saturation": "SplitToningShadowSaturation",
    "highlight_hue": "SplitToningHighlightHue",
    "highlight_saturation": "SplitToningHighlightSaturation",
    "split_balance": "SplitToningBalance",
    "grain_amount": "GrainAmount",
    "grain_size": "GrainSize",
    "vignette": "PostCropVignetteAmount",
}


def xmp_bytes(plan: EditPlan) -> bytes:
    root = Element(f"{{{NS['x']}}}xmpmeta")
    rdf = SubElement(root, f"{{{NS['rdf']}}}RDF")
    desc = SubElement(rdf, f"{{{NS['rdf']}}}Description")
    desc.set(f"{{{NS['rdf']}}}about", "")
    desc.set(f"{{{NS['crs']}}}Version", "15.0")
    desc.set(f"{{{NS['crs']}}}ProcessVersion", "15.4")
    desc.set(f"{{{NS['crs']}}}WhiteBalance", plan.white_balance)
    values = plan.model_dump()
    if plan.white_balance == "Custom":
        desc.set(f"{{{NS['crs']}}}Temperature", str(plan.temperature))
        desc.set(f"{{{NS['crs']}}}Tint", str(plan.tint))
    desc.set(
        f"{{{NS['crs']}}}AutoLateralCA",
        "1" if plan.remove_chromatic_aberration else "0",
    )
    desc.set(
        f"{{{NS['crs']}}}LensProfileEnable",
        "1" if plan.enable_profile_corrections else "0",
    )
    for field, tag in XMP_FIELDS.items():
        value = values[field]
        rendered = f"{value:+.2f}" if field == "exposure" else str(int(value))
        desc.set(f"{{{NS['crs']}}}{tag}", rendered)
    for color, adobe_color in COLOR_NAMES.items():
        channel = values["color_mixer"][color]
        desc.set(f"{{{NS['crs']}}}HueAdjustment{adobe_color}", str(int(channel["hue"])))
        desc.set(f"{{{NS['crs']}}}SaturationAdjustment{adobe_color}", str(int(channel["saturation"])))
        desc.set(f"{{{NS['crs']}}}LuminanceAdjustment{adobe_color}", str(int(channel["luminance"])))
    for field, tag in CINEMATIC_FIELDS.items():
        desc.set(f"{{{NS['crs']}}}{tag}", str(int(values["cinematic"][field])))
    header = '<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>\n'.encode("utf-8")
    return header + tostring(root, encoding="utf-8") + b'\n<?xpacket end="w"?>'


def write_xmp(raw_path: Path, plan: EditPlan, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    xmp_path = output_dir / f"{raw_path.stem}.xmp"
    plan_path = output_dir / f"{raw_path.stem}.edit_plan.json"
    xmp_path.write_bytes(xmp_bytes(plan))
    plan_path.write_text(json.dumps(plan.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    return xmp_path, plan_path
