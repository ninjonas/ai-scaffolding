#!/usr/bin/env python3
"""Check Python files for proper data mapper usage patterns.

Warns if:
- Dict literals or DTO instantiation in src/app/api/** route handlers
- Dict literals or DTO instantiation in src/app/service/** service classes
  (except src/app/service/mappers.py and src/app/service/agent_orchestrator.py)
- Inline dataclass instantiation in routes

Fails if:
- Mapper files (containing *Mapper classes) exist outside src/app/infrastructure/mappers/

Exceptions (allowed):
- Type hints (ResponseDTO in function signatures)
- Imports and import statements
- Comments
- dict() calls in logging/serialization context (if caught)
- src/app/service/mappers.py (mappers live here)
- src/app/service/agent_orchestrator.py (orchestrator is allowed)
- Test files

Usage:
    check_mapper_patterns.py [--file <path>]  # check specific file
    check_mapper_patterns.py [--dir <path>]   # check specific directory
    check_mapper_patterns.py                   # check api/ and service/ files
"""

import ast
import re
import sys
from pathlib import Path

RED = "\033[0;31m"
YELLOW = "\033[1;33m"
GREEN = "\033[0;32m"
NC = "\033[0m"


class MapperPatternChecker(ast.NodeVisitor):
    """AST visitor for detecting mapper pattern violations."""

    def __init__(self, file_path: Path, source_lines: list[str], check_type: str):
        self.file_path = file_path
        self.source_lines = source_lines
        self.violations = []
        self.check_type = check_type  # "api" or "service"
        self.current_function = None
        self.current_class = None
        self.imported_dto_names = set()
        self._extract_imports()

    def _extract_imports(self) -> None:
        """Extract DTO/dataclass names from imports."""
        for line in self.source_lines:
            # from app.api.dto.X import YDTO
            match = re.search(r"from\s+[\w.]+\s+import\s+(.+?)(?:\s|$)", line)
            if match:
                imports = match.group(1).split(",")
                for imp in imports:
                    name = imp.strip().split(" as ")[0].strip()
                    if "DTO" in name or "Response" in name or "Request" in name:
                        self.imported_dto_names.add(name)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Track current class context."""
        prev_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = prev_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check function for violations."""
        prev_func = self.current_function
        self.current_function = node.name
        self._check_function_body(node)
        self.generic_visit(node)
        self.current_function = prev_func

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Check async function for violations."""
        prev_func = self.current_function
        self.current_function = node.name
        self._check_function_body(node)
        self.generic_visit(node)
        self.current_function = prev_func

    def _check_function_body(self, func_node) -> None:
        """Analyze function body for violations."""
        # Skip routes that are route handlers or test functions
        if self._is_route_handler(func_node):
            self._check_route_body(func_node)
            self._check_route_signature(func_node)
        else:
            self._check_service_body(func_node)

    def _is_route_handler(self, func_node) -> bool:
        """Check if this is a route handler (has decorators like @router.post)."""
        for dec in func_node.decorator_list:
            if isinstance(dec, ast.Attribute):
                if dec.attr in ("get", "post", "put", "delete", "patch"):
                    return True
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Attribute):
                    if dec.func.attr in ("get", "post", "put", "delete", "patch"):
                        return True
        return False

    def _check_route_body(self, func_node) -> None:
        """Check route handler for dict/DTO construction."""
        for node in ast.walk(func_node):
            # Check for dict literals
            if isinstance(node, ast.Dict):
                source_line = self._get_source_line(node.lineno)
                # Skip if it's in a type hint or logging context
                if not self._is_type_hint_context(node) and not self._is_logging_context(
                    source_line
                ):
                    self._add_violation(
                        node.lineno,
                        "dict_in_route",
                        "Dict construction in route handler",
                        "Extract mapper to src/app/infrastructure/mappers/",
                        severity="warn",
                    )

            # Check for DTO/dataclass instantiation
            if isinstance(node, ast.Call):
                if self._is_dto_instantiation(node):
                    source_line = self._get_source_line(node.lineno)
                    if not self._is_type_hint_context(node):
                        self._add_violation(
                            node.lineno,
                            "dto_in_route",
                            "DTO instantiation in route handler",
                            "Use mapper function instead",
                            severity="warn",
                        )

    def _check_route_signature(self, func_node) -> None:
        """Warn when route handler has bare primitive query params instead of a QueryDTO."""
        PRIMITIVE_NAMES = {"str", "int", "bool"}
        EXCLUDED_PARAM_NAMES = {"request", "background_tasks"}

        # Build a mapping from arg name -> default node (None means no default = path param)
        args = func_node.args.args
        defaults = func_node.args.defaults
        # defaults aligns to the tail of args
        defaults_offset = len(args) - len(defaults)
        arg_defaults: dict[str, ast.AST | None] = {}
        for i, arg in enumerate(args):
            default_index = i - defaults_offset
            arg_defaults[arg.arg] = defaults[default_index] if default_index >= 0 else None

        for arg in func_node.args.args:
            name = arg.arg
            annotation = arg.annotation

            # Skip self/cls and known dependency names
            if name in ("self", "cls") or name in EXCLUDED_PARAM_NAMES:
                continue

            # Skip path params: primitives with no default are path parameters, not query params
            if arg_defaults.get(name) is None:
                continue

            # Skip params ending in "Dep" (typed dependency aliases)
            if name.endswith("Dep") or (annotation and self._annotation_ends_with_dep(annotation)):
                continue

            # Skip params injected via Annotated[..., Depends(...)]
            if annotation and self._is_depends_annotated(annotation):
                continue

            # Skip params whose type names suggest a DTO or FastAPI type
            if annotation and self._annotation_is_dto_or_fastapi(annotation):
                continue

            # Check if the annotation is a bare primitive or primitive | None
            if annotation and self._is_primitive_annotation(annotation, PRIMITIVE_NAMES):
                self._add_violation(
                    func_node.lineno,
                    "primitive_query_param",
                    f"Bare primitive query param '{name}' in route handler signature",
                    "Group query params into a Pydantic QueryDTO and inject via Depends()",
                    severity="warn",
                )

    def _is_primitive_annotation(self, annotation: ast.AST, primitives: set[str]) -> bool:
        """Return True if annotation is a bare primitive or primitive | None."""
        # str, int, bool
        if isinstance(annotation, ast.Name):
            return annotation.id in primitives
        # str | None, int | None, etc.
        if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
            left = annotation.left
            right = annotation.right
            left_is_prim = isinstance(left, ast.Name) and left.id in primitives
            right_is_none = isinstance(right, ast.Constant) and right.value is None
            right_is_none_name = isinstance(right, ast.Name) and right.id == "None"
            if left_is_prim and (right_is_none or right_is_none_name):
                return True
        return False

    def _is_depends_annotated(self, annotation: ast.AST) -> bool:
        """Return True if annotation is Annotated[..., Depends(...)]."""
        if not (isinstance(annotation, ast.Subscript) and isinstance(annotation.value, ast.Name)):
            return False
        if annotation.value.id != "Annotated":
            return False
        # Walk the slice looking for a Depends() call
        for node in ast.walk(annotation.slice):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "Depends":
                    return True
                if isinstance(func, ast.Attribute) and func.attr == "Depends":
                    return True
        return False

    def _annotation_ends_with_dep(self, annotation: ast.AST) -> bool:
        """Return True if the annotation Name ends with 'Dep'."""
        if isinstance(annotation, ast.Name):
            return annotation.id.endswith("Dep")
        return False

    def _annotation_is_dto_or_fastapi(self, annotation: ast.AST) -> bool:
        """Return True if annotation looks like a DTO, FastAPI, or known non-primitive type."""
        SAFE_NAMES = {"Request", "BackgroundTasks", "Response"}
        DTO_SUFFIXES = ("DTO", "Response", "Request", "Form", "Body", "Query")

        def check_name(name: str) -> bool:
            if name in SAFE_NAMES:
                return True
            return any(name.endswith(s) for s in DTO_SUFFIXES)

        if isinstance(annotation, ast.Name):
            return check_name(annotation.name if hasattr(annotation, "name") else annotation.id)
        if isinstance(annotation, ast.Attribute):
            return check_name(annotation.attr)
        # Optional[X] or X | None where X is non-primitive handled elsewhere
        return False

    def _check_service_body(self, func_node) -> None:
        """Check service method for dict/DTO construction."""
        for node in ast.walk(func_node):
            # Check for dict literals
            if isinstance(node, ast.Dict):
                source_line = self._get_source_line(node.lineno)
                if not self._is_type_hint_context(node) and not self._is_logging_context(
                    source_line
                ):
                    self._add_violation(
                        node.lineno,
                        "dict_in_service",
                        "Dict construction in service",
                        "Extract mapper to src/app/infrastructure/mappers/",
                        severity="warn",
                    )

            # Check for DTO/dataclass instantiation
            if isinstance(node, ast.Call):
                if self._is_dto_instantiation(node):
                    source_line = self._get_source_line(node.lineno)
                    if not self._is_type_hint_context(node):
                        self._add_violation(
                            node.lineno,
                            "dto_in_service",
                            "DTO instantiation in service",
                            "Extract mapper to src/app/infrastructure/mappers/",
                            severity="warn",
                        )

    def _is_dto_instantiation(self, node: ast.Call) -> bool:
        """Check if this is a DTO or dataclass instantiation."""
        if isinstance(node.func, ast.Name):
            name = node.func.id
            # Check if it looks like a DTO or data class
            if any(pattern in name for pattern in ["DTO", "Response", "Request", "Result"]):
                return True
            # Check if it's an imported DTO
            if name in self.imported_dto_names:
                return True
        return False

    def _is_type_hint_context(self, node: ast.AST) -> bool:
        """Heuristic: check if node is in a type hint context."""
        # This is a heuristic; a full implementation would need parent tracking
        # For now, we assume dicts/calls in certain positions are safe
        return False

    def _is_logging_context(self, source_line: str) -> bool:
        """Check if line is a logging call (usually safe for dict)."""
        return any(method in source_line for method in ["log.", "logger.", "print(", "print{"])

    def _get_source_line(self, lineno: int) -> str:
        """Get source line by line number (1-indexed)."""
        if 0 < lineno <= len(self.source_lines):
            return self.source_lines[lineno - 1]
        return ""

    def _add_violation(
        self,
        lineno: int,
        violation_type: str,
        description: str,
        suggestion: str,
        severity: str = "fail",
    ) -> None:
        """Add a violation to the list."""
        self.violations.append(
            {
                "file": self.file_path,
                "lineno": lineno,
                "type": violation_type,
                "description": description,
                "suggestion": suggestion,
                "severity": severity,
            }
        )


def check_mapper_files(repo_root: Path) -> list[dict]:
    """Check for mapper files in wrong locations."""
    violations = []

    # Find all files with Mapper classes or mapper naming
    for file_path in repo_root.rglob("*.py"):
        if skip_file(file_path):
            continue

        # Skip test files
        if "test" in str(file_path):
            continue

        # Skip checker scripts and scripts/lib/
        if "scripts/lib" in str(file_path):
            continue

        # Check if file is already in correct location
        if "src/app/infrastructure/mappers" in str(file_path):
            continue

        # Allow src/app/service/mappers.py (agent result mappers)
        if "src/app/service/mappers.py" in str(file_path):
            continue

        # Allow src/app/api/mappers/ (API DTO mappers: domain → response DTO)
        if "src/app/api/mappers" in str(file_path):
            continue

        # Check if file looks like a mapper
        if is_mapper_file(file_path):
            violations.append(
                {
                    "file": file_path.relative_to(repo_root),
                    "lineno": 1,
                    "type": "misplaced_mapper",
                    "description": f"Mapper file in wrong location: {file_path.name}",
                    "suggestion": "Move to src/app/infrastructure/mappers/",
                    "severity": "fail",
                }
            )

    return violations


def is_mapper_file(file_path: Path) -> bool:
    """Check if file contains mapper classes or is a mapper file."""
    # Check naming
    if "_mapper" in file_path.name or file_path.name == "mappers.py":
        # But skip if it's in the correct location or in tests
        if "src/app/infrastructure/mappers" not in str(file_path):
            if "test" not in str(file_path):
                return True

    # Check content
    try:
        content = file_path.read_text(encoding="utf-8")
        # Look for class definitions that end with "Mapper"
        if re.search(r"^class\s+\w+Mapper", content, re.MULTILINE):
            if "src/app/infrastructure/mappers" not in str(file_path):
                return True
    except Exception:
        pass

    return False


def skip_file(file_path: Path) -> bool:
    """Check if file should be skipped."""
    skip_patterns = [
        "__pycache__",
        ".pyc",
        "conftest.py",
        "spikes/",
        ".venv",
    ]
    return any(pattern in str(file_path) for pattern in skip_patterns)


def check_file(file_path: Path, repo_root: Path, check_type: str) -> list[dict]:
    """Check a single Python file for mapper pattern violations."""
    if skip_file(file_path):
        return []

    # Skip test files for the pattern checks (but not for mapper file checks)
    if "test_" in file_path.name or "conftest" in file_path.name:
        return []

    # Skip scripts/lib/ directory
    if "scripts/lib" in str(file_path):
        return []

    # Skip checker scripts themselves
    if file_path.name.startswith("check_"):
        return []

    # Skip DTOs and mapper files themselves (they're allowed to construct)
    if "dto/" in str(file_path) or "mappers/" in str(file_path):
        return []

    # Determine check type from path if not specified
    if "src/app/api" in str(file_path):
        check_type = "api"
    elif "src/app/service" in str(file_path):
        check_type = "service"
    else:
        return []

    # Skip allowlisted service files
    if check_type == "service":
        if file_path.name in ("agent_orchestrator.py", "mappers.py"):
            return []

    try:
        content = file_path.read_text(encoding="utf-8")
        source_lines = content.split("\n")
        tree = ast.parse(content, filename=str(file_path))
    except SyntaxError as e:
        print(
            f"  {YELLOW}WARN{NC} Could not parse {file_path}: {e}",
            file=sys.stderr,
        )
        return []

    checker = MapperPatternChecker(file_path, source_lines, check_type)
    checker.visit(tree)

    # Relativize paths
    for v in checker.violations:
        v["file"] = v["file"].relative_to(repo_root)

    return checker.violations


def format_violation(v: dict, repo_root: Path, severity_color: str) -> str:
    """Format a violation for display."""
    level = f"{severity_color}{v['severity'].upper()}{NC}"
    location = f"{v['file']}:{v['lineno']}"
    desc = v["description"]
    sugg = v["suggestion"]
    return f"    {level} {location}: {desc}\n         -> {sugg}"


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent.parent

    # Parse command line arguments
    file_paths: list[Path] = []
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--file":
            if i + 1 < len(sys.argv):
                p = Path(sys.argv[i + 1])
                if not p.is_absolute():
                    p = repo_root / p
                if p.exists() and p.suffix == ".py":
                    file_paths.append(p)
                else:
                    print(
                        f"  {YELLOW}WARN{NC} Skipping {sys.argv[i + 1]}: not a valid Python file",
                        file=sys.stderr,
                    )
                i += 2
            else:
                i += 1
        elif sys.argv[i] == "--dir":
            if i + 1 < len(sys.argv):
                p = Path(sys.argv[i + 1])
                if not p.is_absolute():
                    p = repo_root / p
                if p.exists() and p.is_dir():
                    file_paths.extend(
                        [
                            f
                            for f in p.rglob("*.py")
                            if not skip_file(f)
                            and ("src/app/api" in str(f) or "src/app/service" in str(f))
                        ]
                    )
                else:
                    print(
                        f"  {YELLOW}WARN{NC} Skipping {sys.argv[i + 1]}: not a valid directory",
                        file=sys.stderr,
                    )
                i += 2
            else:
                i += 1
        else:
            i += 1

    # Default: check src/app/api/ and src/app/service/
    if not file_paths:
        api_dir = repo_root / "src" / "app" / "api"
        service_dir = repo_root / "src" / "app" / "service"
        if api_dir.exists():
            file_paths.extend([f for f in api_dir.rglob("*.py") if not skip_file(f)])
        if service_dir.exists():
            file_paths.extend([f for f in service_dir.rglob("*.py") if not skip_file(f)])

    if not file_paths:
        api_dir = repo_root / "src" / "app" / "api"
        service_dir = repo_root / "src" / "app" / "service"
        if not api_dir.exists() and not service_dir.exists():
            print(f"  {YELLOW}WARN{NC} src/app/api/ or src/app/service/ not found")
            return 0

    print("Checking mapper patterns...")

    all_violations = []
    for fp in file_paths:
        all_violations.extend(check_file(fp, repo_root, ""))

    # Check for misplaced mapper files
    all_violations.extend(check_mapper_files(repo_root))

    if all_violations:
        # Separate by severity and type
        failures = [v for v in all_violations if v["severity"] == "fail"]
        warnings = [v for v in all_violations if v["severity"] == "warn"]

        # Display failures
        if failures:
            print(f"\n  {RED}Failures: {len(failures)} violation(s){NC}")
            by_type = {}
            for v in failures:
                by_type.setdefault(v["type"], []).append(v)
            for vtype, violations in sorted(by_type.items()):
                label = vtype.replace("_", " ").title()
                print(f"    {RED}{label}: {len(violations)}{NC}")
                for v in violations[:10]:
                    print(format_violation(v, repo_root, RED))
                if len(violations) > 10:
                    print(f"    ... and {len(violations) - 10} more")

        # Display warnings
        if warnings:
            print(f"\n  {YELLOW}Warnings: {len(warnings)} violation(s){NC}")
            by_type = {}
            for v in warnings:
                by_type.setdefault(v["type"], []).append(v)
            for vtype, violations in sorted(by_type.items()):
                label = vtype.replace("_", " ").title()
                print(f"    {YELLOW}{label}: {len(violations)}{NC}")
                for v in violations[:10]:
                    print(format_violation(v, repo_root, YELLOW))
                if len(violations) > 10:
                    print(f"    ... and {len(violations) - 10} more")

        WARN_THRESHOLD = 15

        if failures:
            print(f"\n{RED}{len(failures)} mapper pattern violation(s) found (FAIL).{NC}")
            return 1
        elif len(warnings) >= WARN_THRESHOLD:
            print(f"\n{RED}{len(warnings)} warning(s) found — threshold of {WARN_THRESHOLD} exceeded.{NC}")
            return 1
        else:
            print(f"\n{YELLOW}{len(warnings)} warning(s) found (PASS).{NC}")
            return 0

    print(f"{GREEN}All mapper patterns valid.{NC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
