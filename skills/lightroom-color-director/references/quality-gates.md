# Before/After Quality Gates

The render passes only when all applicable critical gates pass. Score aesthetics after technical and intent gates.

## Critical Gates

1. **Intent:** Each explicit user requirement is independently visible in AFTER.
2. **Readability:** The key subject/person is not lost in blocked shadows.
3. **Clipping:** No new large-area black or white clipping; intentional point-light clipping is evaluated separately.
4. **Color:** No new global green/magenta cast, fluorescent foliage, cyan skin, or uncontrolled lamp spill.
5. **Artifacts:** No edit-amplified halos, mask outlines, ghost-like blur, chroma speckling, brittle sharpening, or plastic texture.
6. **Locality:** A local request has not damaged unrelated regions.
7. **Style structure:** The result expresses the requested tonal key, palette, texture, and hierarchy rather than one stereotyped color cast.
8. **Delivery:** The actual export remains credible in the intended SDR, HDR, or print context.

Any critical failure requires revision even if the image is dramatic or visually novel.

## Comparative Review

- Compare the same regions at the same display scale.
- Ask whether a defect existed in BEFORE and whether AFTER amplified it.
- Compare subject luminance, not only full-frame average.
- Inspect neutral references, skin, practical lights, high-contrast edges, and smooth shadows.
- Verify palette relationships rather than judging global saturation alone.
- For a series, compare adjacent frames and the accepted hero for density, white balance, skin, and stable brand/wardrobe colors.
- For reference matching, compare perceptual attributes rather than slider values.

## Revision Mapping

- Too dark/blocked: raise Exposure only if midtones are low; otherwise raise Shadows/Blacks or the relevant mask. Reduce negative curve/vignette/dehaze stacking.
- Too flat: set endpoints and targeted local contrast before increasing global Contrast.
- Green cast/lights: correct global Tint only for a global cast; otherwise reduce green/yellow/aqua saturation or use a local/color-range mask.
- Halos/ghost emphasis: reduce Clarity, Dehaze, Texture, sharpening detail, or overstrong masks.
- Skin damage: restore red/orange hue/luminance/saturation and reduce global grading impact.
- Intent mismatch: revise the responsible region; do not compensate with unrelated global controls.
- Style mismatch: identify the failed axis—tonal key, palette, saturation distribution, texture, or hierarchy—and change only that layer.
- Batch mismatch: preserve the accepted style vector and recalculate frame-specific exposure, white balance, nuisance colors, noise, or masks.

## Retry Policy

- First failure: revise the smallest responsible control group.
- Second failure: make one conservative recovery pass.
- After two automatic retries: stop, preserve all versions, report remaining concrete issues, and ask for photographer direction.
