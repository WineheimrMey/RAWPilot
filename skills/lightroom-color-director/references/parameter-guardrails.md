# Parameter Guardrails

These are planning defaults, not universal recipes. Image evidence and explicit intent may justify exceptions, but every exception needs a rationale and a successful rendered review.

## Normal First-Pass Envelope

- Exposure: usually within -1.0 to +1.0 EV.
- Basic tone controls: usually within ±35.
- Texture, Clarity, Dehaze: usually within ±15; night and high-ISO frames usually need less.
- Vibrance: usually within ±25; Saturation within ±12.
- HSL Hue: usually within ±20.
- HSL Saturation/Luminance: usually within ±30.
- Color Grading saturation: usually 0–18.
- Grain: usually 0–25.
- Vignette: usually 0 to -18.
- Local Exposure: usually within -1.0 to +1.0 EV.

Treat values over ±60 on a Lightroom -100..100 scale as exceptional and preferably local.

## Style-Layer Scaling

- Subtle: use roughly one-third of the proposed creative curve, grading, HSL, grain, and vignette effect.
- Balanced: use roughly two-thirds, then evaluate the rendered result.
- Strong: use the full bounded creative proposal only when intent is explicit and quality gates still pass.
- Never scale technical exposure recovery, clipping protection, lens correction, noise control, or skin/product safeguards with style strength.
- When reducing an overprocessed result, remove stacked effects before weakening every slider equally.

## Control Responsibilities

- Exposure: midtone/global brightness.
- Highlights/Whites: bright detail and white point.
- Shadows/Blacks: dark detail and black point.
- Contrast: separation after endpoints are stable.
- Texture: medium-frequency detail.
- Clarity: local contrast; easily creates halos and exaggerates blur.
- Dehaze: atmospheric contrast/color; easily oversaturates and blocks shadows.
- Vibrance: broad color cohesion with comparatively gentler skin impact.
- Saturation: global chroma; use sparingly.
- HSL/Point Color: a specific hue family.
- Tint: global green–magenta balance, not a local green-lamp fix.
- Curve/Color Grading: final tonal/color styling, not exposure rescue.

## Conflict Rules

- Dark sky + readable person: darken a sky mask and lift a subject/people mask; keep global tone safe.
- Bright lamps + dark room: compress highlight regions and recover useful midtones/shadows separately.
- Warm subject + neutral background: use masks or narrow color tools; do not warm the entire frame.
- Colorful fireworks + dark sky: protect point highlights, increase orange/yellow/red selectively, and avoid global saturation.
- Green LED contamination: neutralize the narrow green/yellow range or affected mask; do not push global Tint green.

## Night and High-ISO Safety

- Avoid aggressive Clarity, Dehaze, Texture, sharpening detail, and shadow saturation.
- Raise sharpening masking to keep smooth sky and skin from becoming gritty.
- Do not over-lift empty shadows; reveal important subject information and allow nonessential regions to remain dark.
- Preserve colored lamps without allowing clipped channels or neon spill to dominate.
- Never treat source motion blur as recoverable detail through sharpening.

## Genre-Specific Safety

- Wedding/portrait: reduce red/orange and people-mask changes before skin becomes uniform or plastic.
- Product/artwork: keep creative grading near zero unless requested; prioritize neutral references and material form.
- Food: use warmth selectively and keep whites/ceramics neutral.
- Black and white: separate source hue families through B&W Mix; do not compensate for poor separation with extreme global Contrast.
- Gallery batches: synchronize stable style controls only; recalculate exposure, white balance, masks, and noise per frame.
