---
name: lightroom-color-director
description: Diagnose photographs and design, match, or review bounded non-destructive Adobe Lightroom Classic edits. Use for RAW/JPEG assessment, natural-language-to-Lightroom edit plans, XMP recipes, professional scene and style direction, reference-image matching, wedding/event gallery consistency, portrait and skin-tone protection, commercial/product/food work, black-and-white and film-inspired looks, SDR/HDR/print delivery, and Before/After quality review—especially when an edit is too dark, has color casts, halos, ghosting, damaged skin tones, or misses the photographer's intent.
---

# Lightroom Color Director

Translate photographic intent into a controlled Lightroom workflow, then judge the rendered result against the source, the request, and the delivery context. Treat technical correction, creative style, and per-frame adaptation as separate layers. Prefer a small number of purposeful adjustments over a dramatic preset stack.

## Route the Task

- For a first edit, follow **Direct a first edit** and read [workflow.md](references/workflow.md).
- For a named mood or visual language, read [style-language.md](references/style-language.md). Describe the look by tonal, palette, texture, and hierarchy attributes rather than a preset name alone.
- For a specialized genre, read [scene-playbook.md](references/scene-playbook.md).
- For a reference image, wedding/event set, or other series, read [series-reference-workflow.md](references/series-reference-workflow.md).
- For web, print, HDR, monochrome, or profile decisions, read [profiles-and-delivery.md](references/profiles-and-delivery.md).
- For an existing render, follow **Review and refine** and read [quality-gates.md](references/quality-gates.md).
- For RAWPilot implementation, also read [agent-contract.md](references/agent-contract.md).

## Direct a First Edit

1. Inspect the image and available EXIF. State uncertainty when only a compressed preview is available.
2. Separate the request into technical corrections, subject hierarchy, palette/style, detail, and delivery.
3. Establish a neutral baseline before styling: choose a plausible profile, retain or correct white balance, set midtones with Exposure, and set bright/dark endpoints without clipping.
4. Use local masks whenever regions need opposing adjustments. Do not darken the frame to darken only a sky or brighten the frame to reveal only a person.
5. Correct color relationships before adding a look. Protect skin and neutrals; isolate nuisance lamps or narrow hue ranges instead of shifting global Tint.
6. Build style from a restrained tone shape, palette, saturation distribution, texture, and spatial hierarchy. Apply a requested strength only to this creative layer, not to exposure rescue, lens correction, noise control, or skin protection.
7. Set noise reduction before sharpening. Inspect detail at 100%; use stronger sharpening masking for high ISO, skies, skin, and other smooth areas.
8. Return a bounded edit plan and connect every material adjustment to an observed problem, stated intent, reference attribute, or delivery requirement.

## Review and Refine

1. Compare BEFORE and AFTER side by side at matched scale. For a series, also compare the accepted reference and adjacent frames.
2. Check technical failures first: clipping, blocked subject detail, implausible white balance, green/magenta contamination, damaged skin, halos, mask edges, chroma noise, and sharpening artifacts.
3. Check the intent literally and check the style structurally. A cinematic request is not satisfied merely by blue shadows; the expected tonal hierarchy and palette must both be present.
4. Distinguish source defects from edit-amplified defects. Do not call existing motion blur a new ghost, but reject extra microcontrast that makes it objectionable.
5. Change the fewest responsible controls. Preserve accepted regions and the stable style layer.
6. Re-render and re-evaluate. Permit at most two automatic corrective passes; then preserve the versions and report concrete remaining issues.

## Non-Negotiable Rules

- Keep all work non-destructive; never modify the original RAW.
- Do not claim Lightroom can replace skies or perform Photoshop-style pixel synthesis.
- Do not invent masks or parameters unsupported by the active integration.
- Do not stack several controls for the same visual purpose.
- Do not impose one universal skin color, one fixed Kelvin value, or one recipe on a mixed-light gallery.
- Do not copy a reference's absolute slider values. Match perceptual attributes after normalizing each source frame.
- Do not accept an aesthetically interesting result that violates subject readability, color fidelity, explicit intent, or delivery requirements.
- Read [parameter-guardrails.md](references/parameter-guardrails.md) before using extreme values.
