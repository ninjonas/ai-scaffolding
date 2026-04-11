#!/usr/bin/env python3
"""Check Python service layer files for AgentBroker pattern compliance.

Enforces the PofEAA Mediator pattern: services delegate to AgentBroker (not orchestrator).

Warns if:
- time.monotonic() used without # noqa: timing-allowed (operation-level timing OK with marker)
- Inline lambda result mappers (should extract to module-level functions)

Fails if:
- Service uses AgentOrchestrator directly (should use AgentBroker instead)
- Service calls self._orchestrator.invoke_with_telemetry() (use broker methods)
- await self._agent_graph.ainvoke() called directly in services
- Duplicate agent-invocation patterns across multiple service files

Exceptions (allowed):
- src/app/agents/orchestrator/ (orchestrator/broker infrastructure files)
- Lines with # noqa: timing-allowed comment (operation-level timing annotation)
- Test files (src/tests/)

Usage:
    check_service_patterns.py [--file <path>]  # check specific file
    check_service_patterns.py [--dir <path>]   # check specific directory
    check_service_patterns.py                   # check all src/app/service/ files
"""
import ast
import sys
from pathlib import Path

RED = "\033[0;31m"
YELLOW = "\033[1;33m"
GREEN = "\033[0;32m"
NC = "\033[0m"


class ServicePatternChecker(ast.NodeVisitor):
    """AST visitor for detecting service layer pattern violations."""

    def __init__(self, file_path: Path, source_lines: list[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.violations = []
        self.current_function = None
        self.current_class = None
        self.class_init_params = {}  # Track __init__ parameters by class
        self.imports = {}  # Track all imports in file

    def visit_Import(self, node: ast.Import) -> None:
        """Track direct imports."""
        for alias in node.names:
            name = alias.asname or alias.name
            self.imports[name] = alias.name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Track from...import imports."""
        module = node.module or ""
        for alias in node.names:
            name = alias.asname or alias.name
            self.imports[name] = f"{module}.{alias.name}"
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Track current class context and __init__ parameters."""
        prev_class = self.current_class
        self.current_class = node.name

        # Extract __init__ parameters for this class
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                params = {}
                for arg in item.args.args:
                    if arg.arg != "self":
                        # Try to get type annotation
                        if arg.annotation:
                            params[arg.arg] = ast.unparse(arg.annotation)
                        else:
                            params[arg.arg] = None
                self.class_init_params[node.name] = params

        # Check __init__ parameters for pattern violations
        if node.name in self.class_init_params:
            self._check_init_parameters(node)

        self.generic_visit(node)
        self.current_class = prev_class

    def _check_init_parameters(self, node: ast.ClassDef) -> None:
        """Check if __init__ uses AgentOrchestrator instead of AgentBroker."""
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                for arg in item.args.args:
                    if arg.arg != "self":
                        # Get annotation
                        if arg.annotation:
                            annotation_str = ast.unparse(arg.annotation)
                            # Check for AgentOrchestrator usage
                            if (
                                "AgentOrchestrator" in annotation_str
                                and "AgentBroker" not in annotation_str
                            ):
                                self._add_violation(
                                    arg.lineno,
                                    "orchestrator_injection",
                                    f"Service injects AgentOrchestrator",
                                    "Use AgentBroker instead (PofEAA Mediator pattern)",
                                    severity="fail",
                                )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check function for violations and track context."""
        prev_func = self.current_function
        self.current_function = node.name
        self._check_function_body(node)
        self.generic_visit(node)
        self.current_function = prev_func

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Check async function for violations and track context."""
        prev_func = self.current_function
        self.current_function = node.name
        self._check_function_body(node)
        self.generic_visit(node)
        self.current_function = prev_func

    def _check_function_body(self, func_node) -> None:
        """Analyze function body for violations."""
        # Check for direct orchestrator calls (bad pattern)
        self._check_direct_orchestrator_calls(func_node)

        # Check for direct timing + ainvoke pattern
        self._check_timing_and_ainvoke_pattern(func_node)

        # Check for inline lambda mappers
        for node in ast.walk(func_node):
            if isinstance(node, ast.Lambda):
                if self._is_mapper_lambda(node):
                    self._add_violation(
                        node.lineno,
                        "inline_lambda_mapper",
                        "Inline lambda result mapper",
                        f"Extract mapper function to module level "
                        f"({self.current_function}_result_mapper)",
                    )

    def _check_direct_orchestrator_calls(self, func_node) -> None:
        """Check for direct self._orchestrator.invoke_with_telemetry() calls."""
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                # Check for self._orchestrator.invoke_with_telemetry()
                if self._is_orchestrator_invoke_call(node):
                    self._add_violation(
                        node.lineno,
                        "orchestrator_invoke_direct",
                        "Direct orchestrator.invoke_with_telemetry() call in service",
                        "Use broker method instead (e.g., self._broker.chat_response(...))",
                        severity="fail",
                    )

    def _is_orchestrator_invoke_call(self, node: ast.Call) -> bool:
        """Check if this is self._orchestrator.invoke_with_telemetry() call."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "invoke_with_telemetry":
                if isinstance(node.func.value, ast.Attribute):
                    if node.func.value.attr == "_orchestrator":
                        if isinstance(node.func.value.value, ast.Name):
                            return node.func.value.value.id == "self"
        return False

    def _check_timing_and_ainvoke_pattern(self, func_node) -> None:
        """Check for time.monotonic() + await ainvoke() + time.monotonic() pattern."""
        has_timing = False
        has_ainvoke = False
        timing_line = None
        ainvoke_line = None

        for node in ast.walk(func_node):
            # Check for time.monotonic() calls
            if isinstance(node, ast.Call) and self._is_timing_call(node):
                # Check for timing annotation
                source_line = self._get_source_line(node.lineno)
                if "# timing:" in source_line:
                    # OK: operation-level timing with marker (e.g., "# timing: operation-level")
                    continue
                has_timing = True
                timing_line = node.lineno
                self._add_violation(
                    node.lineno,
                    "direct_timing",
                    "Direct timing logic (time.monotonic())",
                    "Annotate with # timing: operation-level for operation-level timing "
                    "(e.g., full send_message duration). Avoid agent-level timing.",
                    severity="warn",
                )

            # Check for await self._agent_graph.ainvoke()
            if isinstance(node, ast.Await):
                if isinstance(node.value, ast.Call):
                    if self._is_agent_ainvoke_call(node.value):
                        has_ainvoke = True
                        ainvoke_line = node.lineno
                        self._add_violation(
                            node.lineno,
                            "direct_ainvoke",
                            "Direct agent_graph.ainvoke() call",
                            "Use broker method instead (e.g., self._broker.transcribe(...))",
                            severity="fail",
                        )

    def _is_mapper_lambda(self, node: ast.Lambda) -> bool:
        """Check if lambda looks like a result mapper (dict/dictionary operations)."""
        # Lambda that returns a dict
        if isinstance(node.body, ast.Dict):
            return True
        # Lambda that calls methods on dict-like objects
        if isinstance(node.body, ast.Call):
            if isinstance(node.body.func, ast.Attribute):
                # e.g., lambda transforming dict results
                return True
        return False

    def _is_timing_call(self, node: ast.Call) -> bool:
        """Check if this is a time.monotonic() call."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "monotonic":
                if isinstance(node.func.value, ast.Name):
                    return node.func.value.id == "time"
        return False

    def _is_agent_ainvoke_call(self, node: ast.Call) -> bool:
        """Check if this is await self._agent_graph.ainvoke() call."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "ainvoke":
                if isinstance(node.func.value, ast.Attribute):
                    if node.func.value.attr == "_agent_graph":
                        if isinstance(node.func.value.value, ast.Name):
                            return node.func.value.value.id == "self"
        return False

    def _get_source_line(self, lineno: int) -> str:
        """Get source line by line number (1-indexed)."""
        if lineno <= len(self.source_lines):
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


def check_duplicate_patterns(all_violations: list[dict], repo_root: Path) -> list[dict]:
    """Check if duplicate timing+ainvoke patterns appear in multiple files."""
    additional_violations = []

    # Count direct_ainvoke violations by file
    ainvoke_by_file: dict[str, int] = {}
    for v in all_violations:
        if v["type"] == "direct_ainvoke":
            file_key = str(v["file"])
            ainvoke_by_file[file_key] = ainvoke_by_file.get(file_key, 0) + 1

    # If pattern appears in multiple files, add FAIL violation
    files_with_pattern = len([f for f in ainvoke_by_file if ainvoke_by_file[f] > 0])
    if files_with_pattern > 1:
        for file_path, count in ainvoke_by_file.items():
            if count > 0:
                additional_violations.append(
                    {
                        "file": Path(file_path),
                        "lineno": 1,
                        "type": "duplicate_pattern",
                        "description": f"Duplicate ainvoke pattern in {files_with_pattern} service file(s)",
                        "suggestion": "Extract to AgentOrchestrator for reuse across services",
                        "severity": "fail",
                    }
                )
                break  # Only add once

    return additional_violations


def skip_file(file_path: Path) -> bool:
    """Check if file should be skipped."""
    skip_patterns = [
        "__pycache__",
        ".pyc",
        "test_",
        "conftest.py",
        "spikes/",
        "orchestrator",  # skip orchestrator/broker infrastructure
        "broker.py",
    ]
    return any(pattern in str(file_path) for pattern in skip_patterns)


def check_file(file_path: Path, repo_root: Path) -> list[dict]:
    """Check a single Python file for service pattern violations."""
    if skip_file(file_path):
        return []

    # Skip non-service files
    if "src/app/service" not in str(file_path):
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

    checker = ServicePatternChecker(file_path, source_lines)
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
                        f"  {YELLOW}WARN{NC} Skipping {sys.argv[i+1]}: not a valid Python file",
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
                            if not skip_file(f) and "src/app/service" in str(f)
                        ]
                    )
                else:
                    print(
                        f"  {YELLOW}WARN{NC} Skipping {sys.argv[i+1]}: not a valid directory",
                        file=sys.stderr,
                    )
                i += 2
            else:
                i += 1
        else:
            i += 1

    # Default: check src/app/service/
    if not file_paths:
        service_dir = repo_root / "src" / "app" / "service"
        if not service_dir.exists():
            print(f"  {YELLOW}WARN{NC} src/app/service/ not found, skipping check")
            return 0
        file_paths = [
            f
            for f in service_dir.rglob("*.py")
            if not skip_file(f) and f.name != "agent_orchestrator.py"
        ]

    if not file_paths:
        print("No files to check.")
        return 0

    print("Checking service layer patterns...")

    all_violations = []
    for fp in file_paths:
        all_violations.extend(check_file(fp, repo_root))

    # Check for duplicate patterns across files
    all_violations.extend(check_duplicate_patterns(all_violations, repo_root))

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
            for vtype, violations in by_type.items():
                label = vtype.replace("_", " ").title()
                print(f"    {RED}{label}: {len(violations)}{NC}")
                for v in violations[:10]:
                    severity_color = RED
                    print(format_violation(v, repo_root, severity_color))
                if len(violations) > 10:
                    print(f"    ... and {len(violations) - 10} more")

        # Display warnings
        if warnings:
            print(f"\n  {YELLOW}Warnings: {len(warnings)} violation(s){NC}")
            by_type = {}
            for v in warnings:
                by_type.setdefault(v["type"], []).append(v)
            for vtype, violations in by_type.items():
                label = vtype.replace("_", " ").title()
                print(f"    {YELLOW}{label}: {len(violations)}{NC}")
                for v in violations[:10]:
                    severity_color = YELLOW
                    print(format_violation(v, repo_root, severity_color))
                if len(violations) > 10:
                    print(f"    ... and {len(violations) - 10} more")

        WARN_THRESHOLD = 15

        if failures:
            print(
                f"\n{RED}{len(failures)} service pattern violation(s) found (FAIL).{NC}"
            )
            return 1
        elif len(warnings) >= WARN_THRESHOLD:
            print(f"\n{RED}{len(warnings)} warning(s) found — threshold of {WARN_THRESHOLD} exceeded.{NC}")
            return 1
        else:
            print(f"\n{YELLOW}{len(warnings)} warning(s) found (PASS).{NC}")
            return 0

    print(f"{GREEN}All service patterns valid.{NC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
