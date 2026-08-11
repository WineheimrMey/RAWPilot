# Lightroom Classic Workflow

Use this order because later stages depend on the tonal and color baseline established earlier.

## 1. Diagnose

Record:

- scene, key subject, visual hierarchy, and important regions;
- likely exposure problem by midtones, highlights, and shadows separately;
- white-balance cast and mixed-light sources;
- clipped or near-clipped regions;
- skin, saturated lights, foliage, sky, and other color-critical areas;
- ISO-related luminance/chroma noise, motion blur, and lens issues;
- photographer's literal requirements and conflicts between regions.

Treat an embedded camera preview as evidence, not RAW truth. Camera JPEG curves may be brighter or more saturated than Lightroom's initial RAW rendering.

Classify the delivery and continuity context: single frame, series, reference match, web SDR, print, or HDR. Do not postpone this until export because it affects profile, contrast, and review decisions.

## 2. Technical Baseline

1. Enable profile corrections and chromatic-aberration removal unless a creative or compatibility reason says otherwise.
2. Preserve As Shot white balance when it is plausible. Use Custom only to correct an observed cast or fulfill an explicit mood.
3. Set Exposure from the principal midtones/subject, not from the brightest lamp or darkest corner.
4. Recover Highlights and set Whites while monitoring highlight clipping.
5. Open Shadows only enough to reveal useful structure. Set Blacks after Shadows so the image keeps a believable black point.
6. Avoid global Contrast while dynamic-range recovery is incomplete.

## 3. Regional Structure

Use a mask when a region needs a different direction from the frame:

- Subject/People: visibility, skin, clothing, and focal separation.
- Sky: luminosity, saturation, haze, and highlight control.
- Background: restraint and separation from the subject.
- Linear/radial/range masks: use when supported for gradual light or a tonal/color range.

Prefer Add/Subtract/Intersect refinements when mask boundaries touch hair, architecture, lamps, or a horizon. A local problem should not be solved globally.

## 4. Color Relationships

Work from broad to specific:

1. White Balance for the illuminant relationship.
2. Vibrance for restrained global cohesion.
3. HSL/Color Mixer for a real hue family.
4. Point Color or color-range masks for one nuisance light or narrow color.
5. Color Grading for subtle shadow/midtone/highlight relationships.

Protect skin in red/orange. Watch yellow/green contamination in mixed LED light. A negative Tint moves the entire frame toward green and is not a generic night-treatment control.

## 5. Style

Add the look only after the image is technically sound:

- Tone Curve: small, intentional tonal shaping. Avoid crushing recovered shadows.
- Color Grading: low saturation, with deliberate shadow/highlight hues and restrained blending.
- Texture/Clarity/Dehaze: use according to subject scale. Stop when edges halo or motion blur becomes conspicuous.
- Grain: use for texture cohesion, not to hide noise or poor exposure.
- Vignette: use to support composition, not to darken already weak corners.

Describe the style on five axes: tonal key, palette, saturation distribution, texture, and spatial hierarchy. Keep style strength separate from technical correction. Read [style-language.md](style-language.md) for professional style families and failure conditions.

## 6. Detail and Output

1. Judge noise and sharpening at 1:1.
2. Apply luminance and color noise reduction before sharpening.
3. Use lower sharpening radius for fine detail and stronger masking for smooth areas/high ISO.
4. Inspect lamp edges, hair, railings, tree branches, and horizons for halos.
5. Export to the requested color space and size, then review the actual rendered file.

## 7. Closed-Loop Review

Review BEFORE and AFTER together:

- technical integrity;
- literal intent match;
- subject hierarchy;
- palette coherence;
- natural detail.

If a gate fails, identify the smallest responsible control group, revise incrementally, and render again.

For a series, compare the current result with an accepted hero frame and adjacent frames. A technically acceptable single image can still fail because its white balance, skin, or density breaks gallery continuity.
