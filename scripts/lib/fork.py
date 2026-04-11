#!/usr/bin/env python3
"""Fork scaffolding template: filtered copy, allowlisted rename, git init, optional gh."""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

EXCLUDE = frozenset({".git", "tmp", "logs", "__pycache__", ".venv", "node_modules"})
ALLOW_FILES = (
    "README.md",
    "docs/index.md",
    "mkdocs.yml",
    "docs/plans/001-langgraph-introduction.md",
    "src/web/src/components/Chat.tsx",
    "src/web/src/App.test.tsx",
    "src/app/main.py",
)
OLD = "scaffolding"


def case_variants(name: str) -> tuple[str, str, str]:
    lower = name.lower()

    def title_seg(m: re.Match[str]) -> str:
        s = m.group(0)
        return s[0].upper() + s[1:].lower()

    title = re.sub(r"[A-Za-z0-9]+", title_seg, lower)
    upper = re.sub(r"[A-Za-z0-9]+", lambda m: m.group(0).upper(), lower)
    return (lower, title, upper)


def _swap_case(text: str, old_v: tuple[str, str, str], new_v: tuple[str, str, str]) -> str:
    for o, n in sorted(zip(old_v, new_v, strict=True), key=lambda p: len(p[0]), reverse=True):
        text = text.replace(o, n)
    return text


def filtered_copy(src: Path, dest: Path, dry_run: bool) -> None:
    src, dest = src.resolve(), dest.resolve()
    if dry_run:
        return
    if dest.exists():
        raise SystemExit(f"Destination already exists: {dest}")
    src_s = str(src)
    for root, dirs, files in os.walk(src, topdown=True):
        dirs[:] = [d for d in dirs if d not in EXCLUDE]
        rel = root[len(src_s) :].lstrip(os.sep)
        target_root = dest / rel if rel else dest
        target_root.mkdir(parents=True, exist_ok=True)
        for fname in files:
            shutil.copy2(Path(root) / fname, target_root / fname)


def replace_in_files(dest: Path, old_name: str, new_name: str, dry_run: bool) -> None:
    if dry_run:
        return
    dest = dest.resolve()
    ov, nv = case_variants(old_name), case_variants(new_name)
    paths: list[Path] = [dest / p for p in ALLOW_FILES]
    agents = dest / ".claude" / "agents"
    if agents.is_dir():
        paths.extend(sorted(agents.glob("*.md")))
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        new_text = _swap_case(text, ov, nv)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")


def git_init(dest: Path) -> None:
    dest = dest.resolve()
    for cmd in (
        ["git", "init"],
        ["git", "add", "-A"],
        ["git", "commit", "-m", "chore: initial commit"],
    ):
        subprocess.run(cmd, cwd=dest, check=True)


def detect_gh() -> bool:
    return shutil.which("gh") is not None


def detect_gh_host() -> str | None:
    """Return the first non-github.com host from gh auth status, or None."""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
        )
        for line in result.stdout.splitlines():
            host = line.strip()
            if host and not host.startswith(" ") and host != "github.com":
                return host
    except Exception:
        pass
    return None


def create_github_repo(fork_name: str, dest: Path, gh_host: str | None = None) -> None:
    dest = dest.resolve()
    host = gh_host or detect_gh_host()
    cmd = ["gh", "repo", "create", fork_name, "--private", "--source=.", "--push"]
    env = {**__import__("os").environ, "GH_HOST": host} if host else None
    host_label = host or "github.com"
    try:
        subprocess.run(cmd, cwd=dest, check=True, env=env)
        print(f"Repo created on {host_label}.")
    except subprocess.CalledProcessError:
        print("gh failed. From the new repo directory, run:")
        print(f"  cd {dest}")
        gh_prefix = f"GH_HOST={host} " if host else ""
        print(f"  {gh_prefix}gh repo create {fork_name} --private --source=. --push")
        raise


def _print_manual_remote(fork_name: str, dest: Path) -> None:
    host = detect_gh_host()
    gh_prefix = f"GH_HOST={host} " if host else ""
    print("Create and push the remote when ready:")
    print(f"  cd {dest}")
    print(f"  {gh_prefix}gh repo create {fork_name} --private --source=. --push")


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser()
    ap.add_argument("--fork-name", default="")
    ap.add_argument("--source", type=Path, default=None)
    ap.add_argument("--dest-parent", type=Path, default=None)
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    fork_name = (args.fork_name or input("Fork name: ")).strip()
    if not fork_name:
        raise SystemExit("Fork name is required.")
    source = (args.source or Path.cwd()).resolve()
    dest_parent = (args.dest_parent or Path.cwd().parent).resolve()
    dest = dest_parent / fork_name
    print(
        f"Source: {source}\nDest: {dest}\n"
        f"Replace {OLD!r} with {fork_name!r} (case variants)\n"
        f"Excluded dirs (any depth): {sorted(EXCLUDE)}",
    )
    if not args.yes and input("Proceed? [y/N]: ").strip().lower() != "y":
        raise SystemExit("Aborted.")
    filtered_copy(source, dest, args.dry_run)
    replace_in_files(dest, OLD, fork_name, args.dry_run)
    if args.dry_run:
        print(f"Done. cd ../{fork_name}")
        _print_manual_remote(fork_name, dest)
        return
    git_init(dest)
    gh_ok = False
    if detect_gh() and input("Create GHE repo? [y/N]: ").strip().lower() == "y":
        try:
            create_github_repo(fork_name, dest)
            gh_ok = True
        except subprocess.CalledProcessError:
            sys.exit(1)
    if not gh_ok:
        _print_manual_remote(fork_name, dest)
    print(f"Done. cd ../{fork_name}")


if __name__ == "__main__":
    main()
