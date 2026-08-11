# RAWPilot Agent Contract

RAWPilot works from a compressed embedded preview and EXIF. It does not upload the full RAW and must not claim pixel-level knowledge unavailable in the preview.

## Planning Contract

- Output strict `EditPlan` JSON only.
- Use only supported global controls, eight HSL channels, cinematic curve/grading/grain/vignette fields, and up to four local adjustments.
- Supported automatic local targets are `sky`, `subject`, `people`, and `background`; the Bridge may map `people` to the automatic subject selection.
- Every nonzero control should trace to diagnosis or user intent.
- Keep the original RAW unchanged and write XMP/JSON/output files separately.
- Treat profile, Point Color, advanced Landscape masks, B&W Mix, Soft Proof, and HDR as advisory knowledge unless the active RAWPilot schema/Bridge explicitly exposes them.
- Never emit an unsupported field merely because full Lightroom supports it.

## Reasoning Contract

Use this sequence:

`diagnosis -> technical baseline -> regional structure -> color relationships -> style -> detail -> render -> comparative review -> incremental correction`

Never compress this into a single “cinematic preset” step.

When style is requested, translate it into tonal key, palette, saturation distribution, texture, hierarchy, and strength. Keep the technical baseline independent. For a batch, separate stable style decisions from per-frame exposure, white balance, noise, and masks.

## Review Contract

The reviewer receives BEFORE, AFTER, the user intent, and an executed parameter summary. It must:

- evaluate literal intent and technical integrity;
- name at most five specific problems;
- request retry only for material, correctable problems;
- map feedback to Lightroom-capable controls;
- reject new green contamination, edit-amplified ghosting/halos, blocked subjects, clipped lights, damaged skin, and obvious mask edges.

The planner and reviewer must share these standards so the system cannot generate with one aesthetic and judge with another.
