import pytest

from app.shared.config import Settings
from app.shared.di import Container

# -- Settings defaults --


def test_settings_default_api_port():
    settings = Settings(api_port=8000)
    assert settings.api_port == 8000


def test_settings_default_web_port():
    settings = Settings()
    assert settings.web_port == 3000


def test_settings_default_docs_port():
    settings = Settings()
    assert settings.docs_port == 8100


def test_settings_default_llm_base_url():
    settings = Settings()
    assert settings.llm_base_url == "https://openrouter.ai/api/v1"


def test_settings_default_llm_api_key():
    settings = Settings(llm_api_key="sk-or-change-me")
    assert settings.llm_api_key == "sk-or-change-me"


def test_settings_default_database_url():
    settings = Settings()
    assert settings.database_url == "sqlite+aiosqlite:///data/app.db"


def test_settings_default_log_level():
    settings = Settings()
    assert settings.log_level == "INFO"


def test_settings_default_log_json():
    settings = Settings()
    assert settings.log_json is False


# -- Container LLM lazy creation --


def test_container_llm_is_created_lazily():
    container = Container()
    # LLM is not created until .llm is accessed
    from app.shared.di import _KEY_LLM

    assert _KEY_LLM not in container._instances


def test_container_llm_is_cached_after_first_access(monkeypatch):
    from unittest.mock import MagicMock

    mock_llm = MagicMock()
    monkeypatch.setattr("app.shared.di.create_llm", lambda _: mock_llm)
    container = Container()
    first = container.llm
    second = container.llm
    assert first is second


# -- Container __getattr__ --


def test_container_resolves_registered_service():
    container = Container()
    container._register("my_service", "service_value")
    assert container.my_service == "service_value"


def test_container_raises_attribute_error_for_unknown_service():
    container = Container()
    with pytest.raises(AttributeError, match="no service"):
        _ = container.nonexistent_service


def test_container_raises_attribute_error_for_private_name():
    container = Container()
    with pytest.raises(AttributeError):
        _ = container._nonexistent


def test_container_register_multiple_services():
    container = Container()
    container._register("svc_a", 1)
    container._register("svc_b", 2)
    assert container.svc_a == 1
    assert container.svc_b == 2


def test_container_register_overrides_existing_service():
    container = Container()
    container._register("svc", "original")
    container._register("svc", "updated")
    assert container.svc == "updated"
