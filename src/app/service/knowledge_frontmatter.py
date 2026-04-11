"""Heuristic frontmatter generation for knowledge file uploads."""

import json
import re
from pathlib import Path

import structlog
import yaml

from app.shared.field_keys import CONTENT_TYPE_TEXT, FIELD_KEY_NAME

log = structlog.get_logger(__name__)

TEXT_EXTENSIONS = {"md", "txt", "json", "yml"}
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | IMAGE_EXTENSIONS
KEYS_PREFIX = "Keys: "
TOP_KEYS_SEPARATOR = ", "


def detect_file_type(filename: str) -> str:
    ext = Path(filename).suffix.lstrip(".").lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: .{ext}. Accepted: .md, .txt, .json, .yml, or image files")
    return ext


def _stem(filename: str) -> str:
    return Path(filename).stem.replace("-", " ").replace("_", " ")


def _from_md(filename: str, content: str) -> tuple[str, str, list[str]]:
    name = _stem(filename)
    heading_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if heading_match:
        name = heading_match.group(1).strip()

    description = ""
    for line in content.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            description = stripped[:200]
            break

    headings = re.findall(r"^#{1,3}\s+(.+)$", content, re.MULTILINE)
    tags = [h.strip().lower().replace(" ", "-") for h in headings[:5]]
    return name, description, tags


def _from_txt(filename: str, content: str) -> tuple[str, str, list[str]]:
    name = _stem(filename)
    description = ""
    for line in content.splitlines():
        stripped = line.strip()
        if stripped:
            description = stripped[:200]
            break
    return name, description, [CONTENT_TYPE_TEXT]


def _extract_from_mapping(filename: str, data_obj: object) -> tuple[str, str, list[str]]:
    """Shared logic for structured data formats (JSON, YAML)."""
    name = _stem(filename)
    tags: list[str] = []
    description = ""
    if isinstance(data_obj, dict):
        # "name" is a data key (JSON/YAML field), not a repeated app string constant
        candidate = data_obj.get(FIELD_KEY_NAME)
        if isinstance(candidate, str):
            name = candidate
        top_keys = list(data_obj.keys())[:8]
        tags = top_keys
        description = (KEYS_PREFIX + TOP_KEYS_SEPARATOR.join(top_keys))[:200]
    return name, description, tags


def _from_json(filename: str, content: str) -> tuple[str, str, list[str]]:
    try:
        return _extract_from_mapping(filename, json.loads(content))
    except Exception as exc:
        log.warning(
            "knowledge_frontmatter_json_parse_error",
            filename=filename,
            error=str(exc),
            exc_info=exc,
        )
        return _stem(filename), "", []


def _from_yml(filename: str, content: str) -> tuple[str, str, list[str]]:
    try:
        return _extract_from_mapping(filename, yaml.safe_load(content))
    except Exception as exc:
        log.warning(
            "knowledge_frontmatter_yml_parse_error",
            filename=filename,
            error=str(exc),
            exc_info=exc,
        )
        return _stem(filename), "", []


def _from_image(filename: str, content: str) -> tuple[str, str, list[str]]:
    return _stem(filename), "Image attached in conversation", ["image"]


_GENERATORS = {
    "md": _from_md,
    "txt": _from_txt,
    "json": _from_json,
    "yml": _from_yml,
    **{ext: _from_image for ext in IMAGE_EXTENSIONS},
}


def is_image(file_type: str) -> bool:
    """Return True if the file type is an image format."""
    return file_type in IMAGE_EXTENSIONS


def generate(filename: str, content: str, file_type: str) -> tuple[str, str, list[str]]:
    """Return (name, description, tags) using heuristics for the given file type."""
    return _GENERATORS[file_type](filename, content)
