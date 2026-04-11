"""Sync .claude/ markdown into docs/ and update mkdocs.yml nav.

Copies:
    .claude/rules/   → docs/guidelines/
    .claude/agents/  → docs/agents/
    .claude/skills/  → docs/skills/

Scans (nav only, no copy):
    docs/plans/

Regenerates the nav between BEGIN/END markers in mkdocs.yml.
Called automatically by docs recipes (start, restart, build).
"""

import re
import shutil
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
MKDOCS_YML = REPO_ROOT / "mkdocs.yml"
DOCS_DIR = REPO_ROOT / "docs"

BEGIN_MARKER = "  # BEGIN GENERATED NAV"
END_MARKER = "  # END GENERATED NAV"

FRONTMATTER_RE = re.compile(r"^---\n.*?^---\n", re.MULTILINE | re.DOTALL)
HEADING_RE = re.compile(r"^#{1,6}\s+(.+)", re.MULTILINE)


def extract_heading(path: Path) -> str:
    """Extract the first markdown heading, skipping YAML frontmatter."""
    text = path.read_text()
    text = FRONTMATTER_RE.sub("", text, count=1)
    match = HEADING_RE.search(text)
    if match:
        return match.group(1).strip()
    return path.stem


def sync_flat(
    src_dir: Path,
    dest_dir: Path,
    nav_label: str,
    index_title: str,
    index_desc: str,
) -> list[dict]:
    """Copy *.md from src into dest, generate index.md, return nav entries."""
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True)

    dest_rel = dest_dir.relative_to(DOCS_DIR)

    for src_file in sorted(src_dir.glob("*.md")):
        shutil.copy2(src_file, dest_dir / src_file.name)

    index_lines = [f"# {index_title}\n", f"\n{index_desc}\n\n"]
    nav_items: list[dict] = [{nav_label: build_nav_items(dest_dir, dest_rel, index_lines)}]
    (dest_dir / "index.md").write_text("".join(index_lines))
    return nav_items


def sync_skills(
    src_dir: Path,
    dest_dir: Path,
    nav_label: str,
    index_title: str,
    index_desc: str,
) -> list[dict]:
    """Flatten SKILL.md files from subdirectories, return nav entries."""
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True)

    dest_rel = dest_dir.relative_to(DOCS_DIR)

    for skill_dir in sorted(src_dir.iterdir()):
        skill_file = skill_dir / "SKILL.md"
        if skill_file.is_file():
            shutil.copy2(skill_file, dest_dir / f"{skill_dir.name}.md")

    index_lines = [f"# {index_title}\n", f"\n{index_desc}\n\n"]
    nav_items: list[dict] = [{nav_label: build_nav_items(dest_dir, dest_rel, index_lines)}]
    (dest_dir / "index.md").write_text("".join(index_lines))
    return nav_items


def nav_from_dir(docs_subdir: Path, nav_label: str) -> list[dict]:
    """Generate nav entries from an existing docs/ subdirectory (no copying)."""
    if not docs_subdir.is_dir():
        return []

    dest_rel = docs_subdir.relative_to(DOCS_DIR)
    items: list[dict] = []

    for f in sorted(docs_subdir.glob("*.md")):
        heading = extract_heading(f)
        items.append({heading: str(dest_rel / f.name)})

    if not items:
        return []
    return [{nav_label: items}]


def build_nav_items(
    dest_dir: Path,
    dest_rel: Path,
    index_lines: list[str],
) -> list[dict]:
    """Build nav item list and append to index_lines for non-index files."""
    items: list[dict] = [{"Overview": str(dest_rel / "index.md")}]

    for f in sorted(dest_dir.glob("*.md")):
        if f.name == "index.md":
            continue
        heading = extract_heading(f)
        items.append({heading: str(dest_rel / f.name)})
        index_lines.append(f"- [{heading}]({f.name})\n")

    return items


def update_mkdocs_nav(nav_sections: list[dict]) -> None:
    """Replace content between BEGIN/END markers in mkdocs.yml."""
    content = MKDOCS_YML.read_text()

    begin_idx = content.index(BEGIN_MARKER)
    end_idx = content.index(END_MARKER) + len(END_MARKER)

    # Render nav YAML and indent to match mkdocs.yml (2-space base indent)
    nav_yaml = yaml.dump(nav_sections, default_flow_style=False, allow_unicode=True)
    indented = "\n".join(f"  {line}" if line.strip() else line for line in nav_yaml.splitlines())

    replacement = f"{BEGIN_MARKER}\n{indented}\n{END_MARKER}"
    content = content[:begin_idx] + replacement + content[end_idx:]

    MKDOCS_YML.write_text(content)


def main() -> None:
    nav_sections: list[dict] = []

    # Scan existing docs/ subdirectories
    nav_sections.extend(nav_from_dir(DOCS_DIR / "plans", "Plans"))
    nav_sections.extend(nav_from_dir(DOCS_DIR / "functional", "Functional Docs"))
    nav_sections.extend(nav_from_dir(DOCS_DIR / "technical", "Technical Docs"))

    # Sync .claude/ into docs/
    nav_sections.extend(
        sync_flat(
            REPO_ROOT / ".claude" / "rules",
            DOCS_DIR / "guidelines",
            "Guidelines",
            "Coding Guidelines",
            "Auto-generated from `.claude/rules/`. Defines how we write and organize code.",
        )
    )
    nav_sections.extend(
        sync_flat(
            REPO_ROOT / ".claude" / "agents",
            DOCS_DIR / "agents",
            "Agents",
            "Agents",
            "Auto-generated from `.claude/agents/`. Defines the specialized agents available in this project.",
        )
    )
    nav_sections.extend(
        sync_skills(
            REPO_ROOT / ".claude" / "skills",
            DOCS_DIR / "skills",
            "Skills",
            "Skills",
            "Auto-generated from `.claude/skills/`. Defines the skills (slash commands) available in this project.",
        )
    )

    update_mkdocs_nav(nav_sections)
    print("Synced .claude/ → docs/{guidelines,agents,skills}/ and updated mkdocs.yml nav")


if __name__ == "__main__":
    main()
