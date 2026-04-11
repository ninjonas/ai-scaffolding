from app.api.dto.common import HealthResponseDTO


class HealthMapper:
    @staticmethod
    def to_response_dto() -> HealthResponseDTO:
        return HealthResponseDTO(status="ok")
