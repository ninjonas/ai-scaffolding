import base64
import io
import time
from dataclasses import dataclass

import structlog
from PIL import Image

log = structlog.get_logger(__name__)

MAX_DIMENSION = 1024
JPEG_QUALITY = 85
JPEG_FORMAT = "JPEG"


@dataclass(frozen=True)
class OptimizedImageResult:
    data: bytes
    format: str
    original_size: tuple[int, int]
    optimized_size: tuple[int, int]
    original_bytes: int
    optimized_bytes: int


def _resize_and_encode(img: Image.Image) -> tuple[Image.Image, str, io.BytesIO]:
    """Resize to MAX_DIMENSION if needed, convert to output format, encode to buffer."""
    if max(img.size) > MAX_DIMENSION:
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)
    if img.mode == "RGBA":
        output_format = "PNG"
    else:
        img = img.convert("RGB")
        output_format = JPEG_FORMAT
    buffer = io.BytesIO()
    save_kwargs: dict = {"format": output_format, "optimize": True}
    if output_format == JPEG_FORMAT:
        save_kwargs["quality"] = JPEG_QUALITY
    img.save(buffer, **save_kwargs)
    return img, output_format, buffer


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

    _resize_start = time.monotonic()
    img, output_format, buffer = _resize_and_encode(img)
    _resize_duration_ms = round((time.monotonic() - _resize_start) * 1000, 2)

    optimized_bytes = buffer.tell()
    buffer.seek(0)

    log.info(
        "image_optimized",
        original_size=original_size,
        optimized_size=img.size,
        original_bytes=original_bytes,
        optimized_bytes=optimized_bytes,
        format=output_format,
        duration_ms=_resize_duration_ms,
    )

    return OptimizedImageResult(
        data=buffer.read(),
        format=output_format,
        original_size=original_size,
        optimized_size=img.size,
        original_bytes=original_bytes,
        optimized_bytes=optimized_bytes,
    )


BASE64_JPEG_PREFIX = "data:image/jpeg;base64,"


def optimize_images_b64(images_b64: list[str]) -> list[str]:
    """Optimize a list of base64 image strings. Always outputs JPEG base64."""
    results = []
    for img_b64 in images_b64:
        raw = base64.b64decode(img_b64)
        result = optimize_image(raw)
        results.append(base64.b64encode(result.data).decode())
    return results
