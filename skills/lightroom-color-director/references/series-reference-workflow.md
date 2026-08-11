# Series and Reference Workflow

Use this workflow for wedding/event galleries, campaigns, bursts, multi-camera shoots, or matching a photographer-provided reference.

## Reference Matching

1. Describe the reference by tonal key, endpoint behavior, palette, saturation distribution, texture, and spatial hierarchy.
2. Normalize the active frame first. Correct its exposure, white balance, clipping, lens behavior, and noise before matching style.
3. Match perceptual attributes, not absolute sliders. Different sensors, profiles, light, and exposure require different values.
4. Use Lightroom Reference View when available to compare white balance, luminance relationships, profile rendering, and color families.
5. Preserve source truth that the reference does not share: skin, product color, weather, and motivated practical lights.

## Three-Layer Model

- **Technical baseline, per frame:** profile plausibility, lens correction, white balance, exposure, clipping recovery, noise, sharpening.
- **Stable style vector, shared cautiously:** curve shape, grading relationship, selected HSL tendencies, grain character, vignette philosophy.
- **Per-frame adaptation:** subject/sky/background masks, local exposure, nuisance color, crop, and frame-specific highlight control.

Never synchronize the whole plan blindly.

## Hero Frames and Lighting Clusters

1. Cluster frames by lighting setup, camera/profile, and location.
2. Select a technically representative hero frame for each cluster.
3. Obtain photographer approval or pass the full quality gates on that hero frame.
4. Propagate only the stable style vector.
5. Recalculate technical and local layers for every frame.

## Gallery Consistency Review

- Compare adjacent thumbnails for luminance and white-balance flicker.
- Compare the same person's skin across nearby frames without forcing different people to one hue.
- Verify white clothing, brand colors, walls, foliage, and practical lights across cameras.
- Sample the darkest, brightest, highest-ISO, and most color-contaminated frames before approving a batch.
- Keep per-image overrides visible in the project record so later revisions remain explainable.

## Style Strength and Per-Image Overrides

- Store style strength separately from technical correction.
- Reduce only creative controls when a frame becomes artificial.
- Let a per-image instruction override the shared style for subject visibility, skin, product color, or a unique light source.
- Preserve accepted stable controls during a correction pass.

## Delivery Continuity

- Review actual exported files, not only Develop previews.
- For a web gallery, inspect the sRGB result at representative screen sizes.
- For print, soft-proof representative hero and edge-case frames with the target profile.
- For HDR delivery, maintain a separate HDR intent and verify SDR compatibility; do not reuse an HDR contrast strategy for ordinary SDR JPEGs.
