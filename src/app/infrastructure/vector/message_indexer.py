"""MessageIndexer: upsert chat messages into ChromaDB for semantic search."""

from typing import Any

import structlog

from app.shared.field_keys import CHROMA_COLLECTION_MESSAGES, EMBEDDING_MODEL_DEFAULT

log = structlog.get_logger()


class MessageIndexer:
    """Upserts chat messages into ChromaDB.

    Injected dependencies: chroma_client, settings.
    """

    def __init__(self, chroma_client: Any, settings: Any) -> None:
        self._client = chroma_client
        self._settings = settings

    def _get_collection(self) -> Any:
        from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

        ef = OpenAIEmbeddingFunction(
            api_key=self._settings.llm_api_key,
            model_name=EMBEDDING_MODEL_DEFAULT,
        )
        return self._client.get_or_create_collection(
            name=CHROMA_COLLECTION_MESSAGES,
            embedding_function=ef,
        )

    async def index(
        self,
        message_id: str,
        content: str,
        role: str,
        conversation_id: str,
        created_at: str,
    ) -> None:
        """Upsert a single chat message into the chat_messages collection.

        Args:
            message_id: Unique identifier for the message.
            content: Text content of the message.
            role: 'user' or 'assistant'.
            conversation_id: ID of the conversation this message belongs to.
            created_at: ISO-formatted timestamp string.
        """
        collection = self._get_collection()
        collection.upsert(
            ids=[message_id],
            documents=[content],
            metadatas=[
                {
                    "message_id": message_id,
                    "conversation_id": conversation_id,
                    "role": role,
                    "created_at": created_at,
                }
            ],
        )
        log.info("message_indexed", message_id=message_id, conversation_id=conversation_id)
