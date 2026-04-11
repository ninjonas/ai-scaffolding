import structlog
from fastapi import APIRouter

from app.api.dto.common import HealthResponseDTO
from app.infrastructure.mappers.health import HealthMapper

log = structlog.get_logger()

router = APIRouter()


@router.get("/health")
async def health() -> HealthResponseDTO:
    log.debug("health_check")
    return HealthMapper.to_response_dto()
