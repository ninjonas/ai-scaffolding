import math

import structlog
from langchain_core.tools import tool

log = structlog.get_logger()

SAFE_NAMES: dict[str, object] = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "pow": pow,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "pi": math.pi,
    "e": math.e,
}


@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression.

    Supports basic arithmetic, exponents, and common math functions.
    """
    log.info("calculate", expression=expression)
    try:
        result = eval(expression, {"__builtins__": {}}, SAFE_NAMES)
        log.info("calculate_result", expression=expression, result=result)
        return str(result)
    except Exception as exc:
        log.warning("calculate_error", expression=expression, error=str(exc))
        return f"Error evaluating '{expression}': {exc}"
