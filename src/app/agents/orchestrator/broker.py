"""Mediator/Facade for agent infrastructure.

Services only know domain concepts (content, audio_b64).
Broker handles state construction; Orchestrator handles execution.
"""

from typing import Any

from app.agents.orchestrator.orchestrator import AgentOrchestrator
from app.service.mappers import chat_result_mapper, voice_result_mapper


class AgentBroker:
    """Mediator/Facade pattern for agent infrastructure.

    Services only know domain concepts (content, audio_b64),
    Broker handles state construction, Orchestrator handles execution.
    """

    def __init__(self, orchestrator: AgentOrchestrator) -> None:
        """Initialize with an AgentOrchestrator instance.

        Args:
            orchestrator: Compiled agent orchestrator (received via DI).
        """
        self._orchestrator = orchestrator

    async def chat_response(
        self,
        content: str,
        images: list[str] | None = None,
        **context: Any,
    ) -> dict:
        """Invoke chat agent with domain-level parameters.

        Args:
            content: User message text.
            images: Optional list of base64-encoded images.
            **context: Additional context forwarded as structured log fields.

        Returns:
            Dict with 'content' and 'tool_calls' keys.
        """
        state_dict = {
            "messages": [{"role": "user", "content": content}],
            "images": images or [],
        }
        return await self._orchestrator.invoke_with_telemetry(
            "chat_response",
            state_dict,
            chat_result_mapper,
            **context,
        )

    async def voice_transcribe(
        self,
        audio_b64: str,
        mime_type: str,
        **context: Any,
    ) -> dict:
        """Invoke voice transcription agent with domain-level parameters.

        Args:
            audio_b64: Base64-encoded audio data.
            mime_type: Audio MIME type (e.g. "audio/webm").
            **context: Additional context forwarded as structured log fields.

        Returns:
            Dict with 'transcript' key.
        """
        state_dict = {
            "messages": [],
            "audio_b64": audio_b64,
            "mime_type": mime_type,
        }
        return await self._orchestrator.invoke_with_telemetry(
            "voice_transcribe",
            state_dict,
            voice_result_mapper,
            **context,
        )
