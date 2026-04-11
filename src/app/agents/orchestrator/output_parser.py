"""Parse LangChain graph outputs into domain-neutral dicts.

This module isolates LangChain-specific message handling from service logic.
It transforms LangChain message objects into plain Python dicts that services
can work with, decoupling services from LangChain API changes.
"""

from app.shared.field_keys import FIELD_KEY_CONTENT


class AgentOutputParser:
    """Parses LangChain graph outputs → domain-neutral dicts.

    Handles all LangChain-specific attribute access and message extraction,
    providing a stable interface for service layer consumers.
    """

    @staticmethod
    def extract_last_message(result: dict) -> dict:
        """Extract and normalize last message from LangChain messages list.

        Safely handles LangChain AIMessage, HumanMessage, etc., converting
        to plain dict with content + tool_calls.

        Args:
            result: Agent graph output with 'messages' list key.

        Returns:
            Dict with 'content' (str) and 'tool_calls' (list) keys.
        """
        last_msg = result["messages"][-1]
        return {
            FIELD_KEY_CONTENT: getattr(last_msg, "content", str(last_msg)),
            "tool_calls": getattr(last_msg, "tool_calls", []),
        }

    @staticmethod
    def extract_transcript(result: dict) -> str:
        """Extract transcript from voice_transcriber graph output.

        Args:
            result: Voice agent graph output dict.

        Returns:
            Trimmed transcript string.
        """
        return result.get("transcript", "").strip()
