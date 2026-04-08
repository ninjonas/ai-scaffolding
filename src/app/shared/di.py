from dataclasses import dataclass, field
from typing import Any

import structlog
from langchain_openai import ChatOpenAI

from app.shared.config import Settings
from app.shared.llm import create_llm

log = structlog.get_logger()


_KEY_LLM = "llm"


@dataclass
class Container:
    settings: Settings = field(default_factory=Settings)
    _instances: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def llm(self) -> ChatOpenAI:
        if _KEY_LLM not in self._instances:
            self._instances[_KEY_LLM] = create_llm(self.settings)
        return self._instances[_KEY_LLM]

    def _register(self, name: str, instance: object) -> None:
        self._instances[name] = instance
        log.debug("di_registered", name=name, type=type(instance).__name__)

    def _resolve(self, name: str) -> Any:
        return self._instances[name]

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self._instances[name]
        except KeyError:
            raise AttributeError(f"Container has no service '{name}'") from None


_container: Container | None = None
