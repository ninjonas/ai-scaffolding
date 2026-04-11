from pathlib import Path

import structlog
from langchain_core.tools import tool

log = structlog.get_logger()

PROJECT_ROOT = Path.cwd()
ACCESS_DENIED_MSG = "Access denied: path is outside the project directory."


@tool
def read_file(path: str) -> str:
    """Read the contents of a file. Path is relative to the project root."""
    file_path = (PROJECT_ROOT / path).resolve()
    if not str(file_path).startswith(str(PROJECT_ROOT)):
        log.warning("file_access_denied", path=path)
        return ACCESS_DENIED_MSG

    if not file_path.exists():
        log.warning("file_not_found", path=path)
        return f"File not found: {path}"

    content = file_path.read_text()
    log.info("file_read", path=path, size=len(content))
    return content


@tool
def list_directory(path: str = ".") -> list[str]:
    """List files and directories at the given path. Path is relative to the project root."""
    dir_path = (PROJECT_ROOT / path).resolve()
    if not str(dir_path).startswith(str(PROJECT_ROOT)):
        log.warning("dir_access_denied", path=path)
        return [ACCESS_DENIED_MSG]

    if not dir_path.is_dir():
        log.warning("dir_not_found", path=path)
        return [f"Not a directory: {path}"]

    entries = sorted(str(p.relative_to(dir_path)) for p in dir_path.iterdir())
    log.info("dir_listed", path=path, count=len(entries))
    return entries
