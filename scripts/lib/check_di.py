#!/usr/bin/env python3
"""Check Python files for proper dependency injection usage.

Warns if:
- Classes directly instantiate dependencies instead of receiving them via constructor
- Direct os.getenv() calls in production code (should use injected Settings)

Exceptions (allowed):
- Test files
- DI container/provider files (they create dependencies)
- Entry points (can create container)
- Spike code
- container.py (API container reads config at bootstrap)
- db/ (must read config for connection)
- scripts/lib/ (checker scripts are excluded)

Thresholds:
- Violations always fail (no warn-vs-fail threshold for DI)

Usage:
    check_di.py [file ...]       # check specific files
    check_di.py                  # check all src/app/ files
"""
import ast
import sys
from pathlib import Path

RED = "\033[0;31m"
YELLOW = "\033[1;33m"
GREEN = "\033[0;32m"
NC = "\033[0m"

# Dependencies that should be injected, not instantiated directly
FORBIDDEN_INSTANTIATIONS = {
    "ChatOpenAI": "Inject via provider",
    "OpenAI": "Inject via provider",
    "Logger": "Inject via logging provider",
    "getLogger": "Inject via logging provider",
}

# Direct config access that should use injected Settings
FORBIDDEN_CONFIG_ACCESS = {
    "os.getenv": "Use injected Settings instance",
    "os.environ": "Use injected Settings instance",
}

# Files/directories to skip
SKIP_PATTERNS = [
    "__pycache__",
    ".pyc",
    "test_",
    "conftest.py",
    "spikes/",
    "di/",
    "bootstrap.py",
    "dependencies.py",
    "container.py",
    "db/",
    "scripts/lib/",
]


def check_direct_instantiation(
    node: ast.Call, file_path: Path
) -> list[dict]:
    """Check for direct instantiation of dependencies."""
    violations = []

    if isinstance(node.func, ast.Name):
        class_name = node.func.id
        if class_name in FORBIDDEN_INSTANTIATIONS:
            violations.append(
                {
                    "type": "direct_instantiation",
                    "line": node.lineno,
                    "class": class_name,
                    "suggestion": FORBIDDEN_INSTANTIATIONS[class_name],
                }
            )

    # Check for getLogger calls
    if isinstance(node.func, ast.Name) and node.func.id == "getLogger":
        violations.append(
            {
                "type": "direct_logger_creation",
                "line": node.lineno,
                "suggestion": "Inject logger via logging provider",
            }
        )

    return violations


def check_config_access(node: ast.Call, file_path: Path) -> list[dict]:
    """Check for direct config access (os.getenv, os.environ)."""
    violations = []

    if isinstance(node.func, ast.Attribute):
        if isinstance(node.func.value, ast.Name) and node.func.value.id == "os":
            if node.func.attr in ("getenv", "environ"):
                key = f"os.{node.func.attr}"
                violations.append(
                    {
                        "type": "direct_config_access",
                        "line": node.lineno,
                        "method": key,
                        "suggestion": FORBIDDEN_CONFIG_ACCESS.get(
                            key, "Use injected Settings instance"
                        ),
                    }
                )

    return violations


def check_file(file_path: Path, repo_root: Path) -> list[dict]:
    """Check a single Python file for DI violations."""
    if any(pattern in str(file_path) for pattern in SKIP_PATTERNS):
        return []

    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))
    except SyntaxError as e:
        print(f"  {YELLOW}WARN{NC} Could not parse {file_path}: {e}", file=sys.stderr)
        return []

    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            violations.extend(check_direct_instantiation(node, file_path))
            violations.extend(check_config_access(node, file_path))

    for v in violations:
        v["file"] = str(file_path.relative_to(repo_root))

    return violations


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent.parent

    if len(sys.argv) > 1:
        file_paths = []
        for arg in sys.argv[1:]:
            p = Path(arg)
            if not p.is_absolute():
                p = repo_root / p
            if p.exists() and p.suffix == ".py":
                file_paths.append(p)
            else:
                print(
                    f"  {YELLOW}WARN{NC} Skipping {arg} (not a valid Python file)",
                    file=sys.stderr,
                )
    else:
        app_dir = repo_root / "src" / "app"
        if not app_dir.exists():
            print(f"  {YELLOW}WARN{NC} src/app/ not found, skipping DI check")
            return 0
        file_paths = [
            f
            for f in app_dir.rglob("*.py")
            if not any(p in str(f) for p in SKIP_PATTERNS)
        ]

    if not file_paths:
        print("No files to check.")
        return 0

    print("Checking dependency injection...")

    all_violations = []
    for fp in file_paths:
        all_violations.extend(check_file(fp, repo_root))

    if all_violations:
        by_type: dict[str, list[dict]] = {}
        for v in all_violations:
            by_type.setdefault(v["type"], []).append(v)

        for vtype, violations in by_type.items():
            print(
                f"\n  {RED}{vtype.replace('_', ' ').title()}: "
                f"{len(violations)} violation(s){NC}"
            )
            for v in violations[:20]:
                detail = ""
                if "class" in v:
                    detail = f"Direct instantiation of {v['class']}"
                elif "method" in v:
                    detail = f"Direct config access: {v['method']}"
                else:
                    detail = vtype
                print(f"    {RED}FAIL{NC} {v['file']}:{v['line']}: {detail}")
                print(f"         -> {v.get('suggestion', 'Use dependency injection')}")
            if len(violations) > 20:
                print(f"    ... and {len(violations) - 20} more")

        print(f"\n{RED}{len(all_violations)} DI violation(s) found.{NC}")
        return 1

    print(f"{GREEN}All dependencies properly injected.{NC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
