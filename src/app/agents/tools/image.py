import io
from dataclasses import dataclass

import structlog
from PIL import Image

log = structlog.get_logger()

MAX_DIMENSION = 1024
JPEG_QUALITY = 85


@dataclass(frozen=True)
class OptimizedImageResult:
    data: bytes
    format: str
    original_size: tuple[int, int]
    optimized_size: tuple[int, int]
    original_bytes: int
    optimized_bytes: int


def optimize_image(image_bytes: bytes) -> OptimizedImageResult:
    original_bytes = len(image_bytes)
    img = Image.open(io.BytesIO(image_bytes))
    original_size = img.size

    log.info(
        "optimizing_image",
        original_size=original_size,
        original_bytes=original_bytes,
        format=img.format,
    )

    if max(img.size) > MAX_DIMENSION:
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)

    if img.mode == "RGBA":
        output_format = "PNG"
    else:
        img = img.convert("RGB")
        output_format = "JPEG"

    buffer = io.BytesIO()
    save_kwargs: dict = {"format": output_format, "optimize": True}
    if output_format == "JPEG":
        save_kwargs["quality"] = JPEG_QUALITY
    img.save(buffer, **save_kwargs)

    optimized_bytes = buffer.tell()
    buffer.seek(0)

    log.info(
        "image_optimized",
        original_size=original_size,
        optimized_size=img.size,
        original_bytes=original_bytes,
        optimized_bytes=optimized_bytes,
        format=output_format,
    )

    return OptimizedImageResult(
        data=buffer.read(),
        format=output_format,
        original_size=original_size,
        optimized_size=img.size,
        original_bytes=original_bytes,
        optimized_bytes=optimized_bytes,
    )
