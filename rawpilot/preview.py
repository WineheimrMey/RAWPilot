from __future__ import annotations

import io
import tempfile
from pathlib import Path

import exifread
import rawpy
from PIL import Image, ImageOps


def extract_exif(raw_path: Path) -> dict[str, str]:
    with raw_path.open("rb") as stream:
        tags = exifread.process_file(stream, details=False, strict=False)
    wanted = (
        "Image Make", "Image Model", "EXIF LensModel", "EXIF ExposureTime",
        "EXIF FNumber", "EXIF ISOSpeedRatings", "EXIF FocalLength",
        "EXIF DateTimeOriginal", "EXIF WhiteBalance",
    )
    return {name: str(tags[name]) for name in wanted if name in tags}


def extract_preview(raw_path: Path, output_dir: Path | None = None) -> Path:
    output_dir = output_dir or Path(tempfile.gettempdir()) / "RAWPilot" / "previews"
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{raw_path.stem}_{abs(hash(str(raw_path))) & 0xfffffff:x}.jpg"
    with rawpy.imread(str(raw_path)) as raw:
        thumb = raw.extract_thumb()
        if thumb.format == rawpy.ThumbFormat.JPEG:
            image = Image.open(io.BytesIO(thumb.data))
        else:
            image = Image.fromarray(thumb.data)
        image = ImageOps.exif_transpose(image).convert("RGB")
        image.thumbnail((1024, 1024))
        image.save(target, "JPEG", quality=82, optimize=True)
    return target


def prepare_local_asset(raw_path: Path, output_dir: Path | None = None):
    from .models import RawAsset
    return RawAsset(
        path=raw_path,
        preview_path=extract_preview(raw_path, output_dir),
        exif=extract_exif(raw_path),
    )
