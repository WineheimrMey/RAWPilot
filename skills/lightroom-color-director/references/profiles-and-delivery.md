# Profiles and Delivery

## Profiles First

- Choose a profile before detailed tone/color work because the profile defines the starting rendering.
- Prefer Adobe Color or a credible Camera Matching profile for general work; consider Adobe Neutral for high-dynamic-range recovery, portrait-oriented rendering for skin, or landscape rendering only when its saturation/contrast remain appropriate.
- Use creative profiles as a foundation, then reduce intensity when skin, products, or neutrals become implausible.
- Recheck exposure, highlight recovery, and color after changing profiles.
- RAWPilot's current strict plan does not emit profile names. It may recommend a profile in rationale, but must not claim the Bridge applied one unless the integration supports it.

## Black and White

- Convert with a monochrome profile or B&W treatment, then use B&W Mix to map source hues into distinct luminance values.
- Judge skin, sky, foliage, clothing, and architecture by tonal separation rather than original saturation.
- Use split toning/color grading only when the requested monochrome is intentionally warm, cool, or selenium-like.
- Treat grain as an output-scale texture decision, not an automatic synonym for monochrome.

## Web and Screen SDR

- Export sRGB unless the delivery platform specifies another color-managed space.
- Inspect the exported JPEG for clipped channels, shadow blocking, resizing artifacts, and over-sharpening.
- Avoid an HDR-flat recovery look; preserve convincing SDR contrast and highlight rolloff.

## Print

- Calibrate/profile the display and keep ambient viewing conditions stable.
- Use Soft Proof with the target printer/paper ICC profile and create a proof copy when print-specific adjustments are needed.
- Inspect gamut warnings, deep-shadow separation, saturated colors, paper white, and output sharpening.
- Do not overwrite the master style to solve one paper/profile limitation.

## HDR

- Treat HDR output as a distinct delivery branch with an HDR-capable display and format.
- Place extended highlights deliberately; do not push every bright region above SDR white.
- Check SDR compatibility/preview and provide a separate SDR export when required.
- RAWPilot currently exports sRGB JPEG through its Bridge, so do not claim HDR delivery from that path.

## Color-Critical Work

- State that preview-only analysis cannot guarantee colorimetric accuracy.
- Recommend a calibrated display and, when practical, a photographed color target for product, artwork, and demanding skin/product matching.
- Use perceptual review alongside metrics; numeric color distance alone does not prove that skin or a creative grade looks correct.
