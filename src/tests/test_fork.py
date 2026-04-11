"""Tests for scripts/lib/fork.py (template fork utility)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS = str(REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from lib.fork import (  # noqa: E402
    case_variants,
    filtered_copy,
    main,
    replace_in_files,
)


def test_case_variants() -> None:
    assert case_variants("my-project") == ("my-project", "My-Project", "MY-PROJECT")


def test_case_variants_scaffolding() -> None:
    assert case_variants("scaffolding") == ("scaffolding", "Scaffolding", "SCAFFOLDING")


def test_filtered_copy_excludes(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / ".git").mkdir()
    (src / "tmp").mkdir()
    (src / "__pycache__").mkdir()
    (src / "keep.txt").write_text("x", encoding="utf-8")
    dest = tmp_path / "dest"
    filtered_copy(src, dest, dry_run=False)
    assert not (dest / ".git").exists()
    assert not (dest / "tmp").exists()
    assert not (dest / "__pycache__").exists()
    assert (dest / "keep.txt").read_text(encoding="utf-8") == "x"


def test_replace_in_file_lower(tmp_path: Path) -> None:
    dest = tmp_path / "d"
    dest.mkdir()
    readme = dest / "README.md"
    readme.write_text("hello scaffolding world", encoding="utf-8")
    replace_in_files(dest, "scaffolding", "my-project", dry_run=False)
    assert "my-project" in readme.read_text(encoding="utf-8")


def test_replace_in_file_title(tmp_path: Path) -> None:
    dest = tmp_path / "d"
    dest.mkdir()
    readme = dest / "README.md"
    readme.write_text("hello Scaffolding world", encoding="utf-8")
    replace_in_files(dest, "scaffolding", "my-project", dry_run=False)
    assert "My-Project" in readme.read_text(encoding="utf-8")


def test_chat_and_test_file_stay_in_sync(tmp_path: Path) -> None:
    dest = tmp_path / "fork"
    dest.mkdir()
    chat = dest / "src/web/src/components/Chat.tsx"
    appt = dest / "src/web/src/App.test.tsx"
    chat.parent.mkdir(parents=True, exist_ok=True)
    appt.parent.mkdir(parents=True, exist_ok=True)
    chat.write_text("<h1>Scaffolding Chat</h1>", encoding="utf-8")
    appt.write_text("expect(screen.getByText('Scaffolding Chat'))", encoding="utf-8")
    replace_in_files(dest, "scaffolding", "my-project", dry_run=False)
    c = chat.read_text(encoding="utf-8")
    a = appt.read_text(encoding="utf-8")
    assert "My-Project Chat" in c
    assert "My-Project Chat" in a
    assert c.count("My-Project Chat") == a.count("My-Project Chat")


def test_dry_run_no_writes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.chdir(repo)
    main(["--dry-run", "--yes", "--fork-name", "test-fork"])
    assert not (tmp_path / "test-fork").exists()
