"""Domain Service: Standardized agent invocation with telemetry and resilience.

Part of the agent infrastructure layer. Encapsulates the cross-cutting concern
of invoking compiled agent graphs with centralized timing, structured logging,
error handling, and result mapping.

Lives in agents/ (not service/) because it's agent infrastructure.
"""

import time
from collections.abc import Callable
from typing import Any

import structlog

log = structlog.get_logger()


class AgentOrchestrator:
    """Domain Service: Standardized agent invocation with telemetry and resilience.

    Encapsulates the cross-cutting concern of invoking agent graphs with
    centralized timing, structured logging, error handling, and result mapping.
    """

    def __init__(self, agent_graph: Any) -> None:
        """Initialize with compiled agent graph.

        Args:
            agent_graph: Compiled LangGraph graph instance (received via DI).
        """
        self._agent_graph = agent_graph

    async def invoke_with_telemetry(
        self,
        operation_name: str,
        state_dict: dict,
        result_mapper: Callable[[dict], dict],
        **log_context: Any,
    ) -> dict:
        """Invoke agent graph with centralized timing, logging, error handling.

        Args:
            operation_name: Unique identifier for this invocation (e.g. "voice_transcribe").
            state_dict: Input state dict for agent.ainvoke().
            result_mapper: Pure function transforming agent output to domain result.
            **log_context: Structured logging fields (conversation_id, mime_type, etc.).

        Returns:
            Mapped result from result_mapper applied to agent output.

        Raises:
            Any exception from agent.ainvoke(); logged with duration_s and re-raised.
        """
        bound_log = log.bind(**log_context)
        bound_log.info(f"{operation_name}_start")

        start = time.monotonic()
        try:
            agent_result = await self._agent_graph.ainvoke(state_dict)
            mapped_result = result_mapper(agent_result)

            duration_s = time.monotonic() - start
            bound_log.info(f"{operation_name}_done", duration_s=round(duration_s, 3))

            return mapped_result
        except Exception as exc:
            duration_s = time.monotonic() - start
            bound_log.error(
                f"{operation_name}_error",
                duration_s=round(duration_s, 3),
                error=str(exc),
            )
            raise
