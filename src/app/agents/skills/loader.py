from pathlib import Path
from typing import Any

import structlog
from langchain_core.tools import tool

from app.shared.field_keys import FIELD_KEY_DESCRIPTION, FIELD_KEY_NAME

log = structlog.get_logger()

SKILLS_DIR = Path(__file__).parent
SKILL_FILENAME = "SKILL.md"


def build_skill_catalog() -> list[dict[str, Any]]:
    catalog = []
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        skill_md = skill_dir / SKILL_FILENAME
        if skill_dir.is_dir() and skill_md.exists():
            frontmatter, description = _parse_skill_md(skill_md)
            catalog.append(
                {
                    FIELD_KEY_NAME: skill_dir.name,
                    FIELD_KEY_DESCRIPTION: description,
                    **frontmatter,
                }
            )
            log.debug("skill_cataloged", skill=skill_dir.name)
    log.info("skill_catalog_built", count=len(catalog))
    return catalog


def _parse_skill_md(path: Path) -> tuple[dict[str, str], str]:
    content = path.read_text()
    frontmatter: dict[str, str] = {}
    body = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    frontmatter[key.strip()] = value.strip()
            body = parts[2].strip()

    first_line = body.split("\n", 1)[0] if body else ""
    description = first_line.lstrip("# ").strip()
    return frontmatter, description


@tool
def load_skill(name: str) -> str:
    """Load full instructions for a skill by name."""
    skill_dir = SKILLS_DIR / name
    skill_md = skill_dir / SKILL_FILENAME

    if not skill_md.exists():
        log.warning("skill_not_found", skill=name)
        return f"Skill '{name}' not found."

    log.info("skill_loaded", skill=name)
    return skill_md.read_text()


@tool
def read_skill_file(name: str, filename: str) -> str:
    """Read a specific file from a skill directory."""
    skill_dir = SKILLS_DIR / name
    file_path = skill_dir / filename

    if not file_path.exists():
        log.warning("skill_file_not_found", skill=name, filename=filename)
        return f"File '{filename}' not found in skill '{name}'."

    log.info("skill_file_read", skill=name, filename=filename)
    return file_path.read_text()
