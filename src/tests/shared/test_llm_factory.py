from langchain_openai import ChatOpenAI

from app.shared.config import Settings
from app.shared.llm import create_llm


def make_settings(**overrides: object) -> Settings:
    return Settings(llm_api_key="test", **overrides)


def test_factory_returns_openrouter() -> None:
    settings = make_settings()
    result = create_llm(settings)
    assert isinstance(result, ChatOpenAI)
