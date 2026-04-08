import structlog
from fastapi import APIRouter

log = structlog.get_logger()

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    log.debug("health_check")
    return {"status": "ok"}
