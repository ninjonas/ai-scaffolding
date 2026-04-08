from dataclasses import dataclass


@dataclass(frozen=True)
class OptimizedImage:
    data_base64: str
    format: str
    original_width: int
    original_height: int
    optimized_width: int
    optimized_height: int
    original_bytes: int
    optimized_bytes: int
