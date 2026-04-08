import structlog
from langchain_openai import ChatOpenAI

from app.shared.config import Settings

log = structlog.get_logger()


def create_llm(settings: Settings) -> ChatOpenAI:
    log.info(
        "creating_llm",
        model=settings.llm_model,
        base_url=settings.llm_base_url,
    )
    return ChatOpenAI(
        model=settings.llm_model,
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
    )
