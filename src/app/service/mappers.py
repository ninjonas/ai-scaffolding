from app.agents.orchestrator.output_parser import AgentOutputParser


def chat_result_mapper(result: dict) -> dict:
    """Map chat agent output to domain result."""
    msg = AgentOutputParser.extract_last_message(result)
    return {
        "content": msg["content"],
        "tool_calls": msg["tool_calls"],
    }


def voice_result_mapper(result: dict) -> dict:
    """Map voice transcriber output to domain result."""
    return {"transcript": AgentOutputParser.extract_transcript(result)}
