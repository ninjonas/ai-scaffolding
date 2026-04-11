#!/usr/bin/env python3
"""Check for literal strings that should be constants.

Rules:
- src/app/: Flag string literals that appear 2+ times (should be constants)
- src/tests/: Flag string literals that match an existing constant in src/app/
  (tests must use the constant, not re-type the raw string)

Exempt:
- Docstrings and comments
- Test assertions with unique strings (not matching app constants)
- Empty strings and single-character strings
- Strings that are only digits or whitespace
- __all__, __name__, __main__ and other dunder strings

Thresholds:
- Warn at 2 occurrences
- Fail at 3+ occurrences (in app code)
- Always fail when test uses a string that exists as a constant in app

Usage:
    check_literal_strings.py [file ...]   # check specific files
    check_literal_strings.py              # check all src/ files
"""

import ast
import sys
from collections import defaultdict
from pathlib import Path

RED = "\033[0;31m"
YELLOW = "\033[1;33m"
GREEN = "\033[0;32m"
NC = "\033[0m"

SKIP_PATTERNS = ["__pycache__", "node_modules", "dist", ".pyc"]

# Minimum length for a string to be considered
MIN_STRING_LENGTH = 2

# Strings that are intentional pairs (e.g. a field default and a named constant
# that happen to share the same value). These are excluded from duplicate checks.
EXEMPT_LITERALS = {
    "INFO",  # config.py log_level default + logging.py configure_logging default
    "messages",  # ORM relationship names (unavoidable SQLAlchemy backref pattern)
    "args",
    "assets",
    "llm",
    "tool_calls",
    "/{file_id}",  # FastAPI route path parameter — decorator argument, intentionally repeated
    "---",  # YAML/markdown front matter delimiter
    ", ",  # generic separator — not a domain constant
    "- **",  # markdown bullet syntax
    "[]",  # SQLAlchemy column default for list fields
}

# Strings to always ignore
IGNORE_STRINGS = {
    "__all__",
    "__name__",
    "__main__",
    "__init__",
    "__str__",
    "__repr__",
    "utf-8",
    "utf8",
    "rb",
    "wb",
    "r",
    "w",
    "a",
}


def is_docstring(node: ast.Constant, parent_map: dict) -> bool:
    """Check if a string constant is a docstring."""
    parent = parent_map.get(id(node))
    if isinstance(parent, ast.Expr):
        grandparent = parent_map.get(id(parent))
        if isinstance(
            grandparent, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            # Check if this Expr is the first statement in the body
            if hasattr(grandparent, "body") and grandparent.body and grandparent.body[0] is parent:
                return True
    return False


def is_logging_call(node: ast.Constant, parent_map: dict) -> bool:
    """Check if string is inside a logging call."""
    parent = parent_map.get(id(node))
    if isinstance(parent, ast.Call):
        func = parent.func
        # logger.info("..."), logger.debug("..."), etc.
        if isinstance(func, ast.Attribute) and func.attr in (
            "debug",
            "info",
            "warning",
            "error",
            "critical",
            "exception",
            "log",
        ):
            return True
    return False


def is_decorator_or_type_hint(node: ast.Constant, parent_map: dict) -> bool:
    """Check if string is in a decorator or type annotation."""
    parent = parent_map.get(id(node))
    # Decorator arguments
    if isinstance(parent, ast.Call):
        grandparent = parent_map.get(id(parent))
        if isinstance(grandparent, ast.Attribute):
            # @app.get("/path") etc.
            return True
        if isinstance(grandparent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # @field_validator("tags") — Call is in decorator_list
            if parent in grandparent.decorator_list:
                return True
    # Type hint strings
    if isinstance(parent, ast.Subscript):
        return True
    return False


def is_dict_key_local(node: ast.Constant, parent_map: dict) -> bool:
    """Check if string is a dictionary key in local scope."""
    parent = parent_map.get(id(node))
    if isinstance(parent, (ast.Dict,)):
        # Check if this constant is a key (not a value)
        if hasattr(parent, "keys") and node in parent.keys:
            return True
    return False


def should_ignore_string(value: str) -> bool:
    """Check if a string should be ignored."""
    if len(value) < MIN_STRING_LENGTH:
        return True
    if value in IGNORE_STRINGS:
        return True
    if value in EXEMPT_LITERALS:
        return True
    if value.strip().isdigit():
        return True
    if not value.strip():
        return True
    # Dunder strings
    if value.startswith("__") and value.endswith("__"):
        return True
    return False


def build_parent_map(tree: ast.AST) -> dict:
    """Build a map of node id -> parent node."""
    parent_map = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parent_map[id(child)] = node
    return parent_map


def extract_string_literals(file_path: Path, repo_root: Path) -> list[tuple[str, int, str]]:
    """Extract non-exempt string literals from a Python file.

    Returns list of (string_value, line_number, relative_path).
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))
    except SyntaxError:
        return []

    parent_map = build_parent_map(tree)
    rel_path = str(file_path.relative_to(repo_root))
    literals = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant):
            continue
        if not isinstance(node.value, str):
            continue

        value = node.value

        if should_ignore_string(value):
            continue
        if is_docstring(node, parent_map):
            continue
        if is_logging_call(node, parent_map):
            continue
        if is_decorator_or_type_hint(node, parent_map):
            continue
        if is_dict_key_local(node, parent_map):
            continue

        literals.append((value, node.lineno, rel_path))

    return literals


def extract_constants_from_app(app_dir: Path, repo_root: Path) -> dict[str, str]:
    """Extract defined constants from app code.

    Returns dict of constant_value -> "FILE:LINE CONST_NAME".
    """
    constants = {}

    for py_file in app_dir.rglob("*.py"):
        if any(p in str(py_file) for p in SKIP_PATTERNS):
            continue

        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(py_file))
        except SyntaxError:
            continue

        rel_path = str(py_file.relative_to(repo_root))

        for node in ast.walk(tree):
            # Module-level assignments: CONSTANT_NAME = "value"
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        if isinstance(node.value, ast.Constant) and isinstance(
                            node.value.value, str
                        ):
                            constants[node.value.value] = f"{rel_path}:{node.lineno} {target.id}"

    return constants


def check_app_duplicates(
    app_literals: list[tuple[str, int, str]],
) -> tuple[list[dict], list[dict]]:
    """Check for repeated string literals in app code."""
    by_value: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for value, line, rel_path in app_literals:
        by_value[value].append((line, rel_path))

    errors = []
    warnings = []

    for value, occurrences in sorted(by_value.items()):
        count = len(occurrences)
        if count >= 3:
            errors.append(
                {
                    "value": value,
                    "count": count,
                    "locations": occurrences,
                }
            )
        elif count == 2:
            warnings.append(
                {
                    "value": value,
                    "count": count,
                    "locations": occurrences,
                }
            )

    return errors, warnings


def check_test_uses_constants(
    test_literals: list[tuple[str, int, str]],
    app_constants: dict[str, str],
) -> list[dict]:
    """Check that tests use constants defined in app, not raw strings."""
    violations = []

    for value, line, rel_path in test_literals:
        if value in app_constants:
            violations.append(
                {
                    "value": value,
                    "line": line,
                    "file": rel_path,
                    "constant_ref": app_constants[value],
                }
            )

    return violations


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent.parent
    app_dir = repo_root / "src" / "app"
    tests_dir = repo_root / "src" / "tests"

    if len(sys.argv) > 1:
        files = []
        for arg in sys.argv[1:]:
            p = Path(arg)
            if not p.is_absolute():
                p = repo_root / p
            if p.exists() and p.suffix == ".py":
                files.append(p)
        app_files = [f for f in files if "src/app" in str(f)]
        test_files = [f for f in files if "src/tests" in str(f)]
    else:
        app_files = list(app_dir.rglob("*.py")) if app_dir.exists() else []
        test_files = list(tests_dir.rglob("*.py")) if tests_dir.exists() else []
        app_files = [f for f in app_files if not any(p in str(f) for p in SKIP_PATTERNS)]
        test_files = [f for f in test_files if not any(p in str(f) for p in SKIP_PATTERNS)]

    if not app_files and not test_files:
        print("No files to check.")
        return 0

    print("Checking literal strings...")

    # Collect app literals
    app_literals = []
    for fp in app_files:
        app_literals.extend(extract_string_literals(fp, repo_root))

    # Check app duplicates
    app_errors, app_warnings = check_app_duplicates(app_literals)

    # Extract constants from app for test checking
    app_constants = extract_constants_from_app(app_dir, repo_root) if app_dir.exists() else {}

    # Collect test literals and check against app constants
    test_literals = []
    for fp in test_files:
        test_literals.extend(extract_string_literals(fp, repo_root))

    test_violations = check_test_uses_constants(test_literals, app_constants)

    # Print results
    exit_code = 0

    if app_errors:
        print(f"\n  {RED}Repeated literals in app code (3+ occurrences):{NC}")
        for err in app_errors[:20]:
            truncated = err["value"][:50] + "..." if len(err["value"]) > 50 else err["value"]
            print(f'    {RED}FAIL{NC} "{truncated}" appears {err["count"]} times:')
            for line, path in err["locations"][:5]:
                print(f"         {path}:{line}")
            if len(err["locations"]) > 5:
                print(f"         ... and {len(err['locations']) - 5} more")
        exit_code = 1

    if app_warnings:
        print(f"\n  {YELLOW}Repeated literals in app code (2 occurrences):{NC}")
        for warn in app_warnings[:20]:
            truncated = warn["value"][:50] + "..." if len(warn["value"]) > 50 else warn["value"]
            print(f'    {YELLOW}WARN{NC} "{truncated}" appears {warn["count"]} times:')
            for line, path in warn["locations"]:
                print(f"         {path}:{line}")

    if test_violations:
        print(f"\n  {RED}Tests using raw strings instead of app constants:{NC}")
        for v in test_violations[:20]:
            truncated = v["value"][:50] + "..." if len(v["value"]) > 50 else v["value"]
            print(f'    {RED}FAIL{NC} {v["file"]}:{v["line"]}: "{truncated}"')
            print(f"         -> Use constant from {v['constant_ref']}")
        if len(test_violations) > 20:
            print(f"    ... and {len(test_violations) - 20} more")
        exit_code = 1

    WARN_THRESHOLD = 16

    total_errors = len(app_errors) + len(test_violations)
    total_warnings = len(app_warnings)

    if total_errors > 0:
        print(f"\n{RED}{total_errors} error(s) and {total_warnings} warning(s) found.{NC}")
    elif total_warnings >= WARN_THRESHOLD:
        print(f"\n{RED}{total_warnings} warning(s) found — threshold of {WARN_THRESHOLD} exceeded.{NC}")
        exit_code = 1
    elif total_warnings > 0:
        print(f"\n{YELLOW}{total_warnings} warning(s) found (no errors).{NC}")
    else:
        print(f"{GREEN}No repeated literal strings found.{NC}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
