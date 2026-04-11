"""Unit tests for KnowledgeService.enrich_metadata."""

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.entities.knowledge_file import SCOPE_PROJECT, KnowledgeFile
from app.service.knowledge import KnowledgeService

LLM_GENERATE_PATH = "app.service.knowledge.llm_generate"


def _make_file(file_id: str = "file-1") -> KnowledgeFile:
    return KnowledgeFile(
        id=file_id,
        name="Old Name",
        description="Old description.",
        content="file content",
        file_type="md",
        scope=SCOPE_PROJECT,
        tags=["old"],
        enriched=False,
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 1, 1),
    )


def _make_uow_factory(file: KnowledgeFile | None) -> Any:
    """Return a factory that yields an async context manager with a mock UoW."""
    mock_repo = AsyncMock()
    mock_repo.get_by_id = AsyncMock(return_value=file)
    mock_repo.save = AsyncMock()

    mock_uow = AsyncMock()
    mock_uow.knowledge = mock_repo
    mock_uow.commit = AsyncMock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=False)

    def factory():
        return mock_uow

    return factory, mock_uow


@pytest.mark.asyncio
async def test_enrich_metadata_patches_fields_and_sets_enriched() -> None:
    file = _make_file()
    factory, mock_uow = _make_uow_factory(file)
    llm = MagicMock()
    svc = KnowledgeService(uow_factory=factory, llm=llm)

    valid_result = ("New Name", "New description.", ["tag-a", "tag-b"])
    with patch(LLM_GENERATE_PATH, return_value=valid_result):
        await svc.enrich_metadata("file-1")

    # The last save call should include enriched=True
    save_calls = mock_uow.knowledge.save.call_args_list
    assert save_calls, "save was never called"
    saved: KnowledgeFile = save_calls[-1].args[0]
    assert saved.enriched is True


@pytest.mark.asyncio
async def test_enrich_metadata_sets_enriched_true_even_on_llm_failure() -> None:
    file = _make_file()
    factory, mock_uow = _make_uow_factory(file)
    llm = MagicMock()
    svc = KnowledgeService(uow_factory=factory, llm=llm)

    with patch(LLM_GENERATE_PATH, return_value=("", "", [])):
        await svc.enrich_metadata("file-1")

    save_calls = mock_uow.knowledge.save.call_args_list
    assert save_calls, "save was never called"
    saved: KnowledgeFile = save_calls[-1].args[0]
    assert saved.enriched is True


@pytest.mark.asyncio
async def test_enrich_metadata_does_not_raise_on_exception() -> None:
    """enrich_metadata must swallow all exceptions to stay safe as a background task."""
    broken_uow = AsyncMock()
    broken_uow.__aenter__ = AsyncMock(side_effect=RuntimeError("db down"))
    broken_uow.__aexit__ = AsyncMock(return_value=False)

    svc = KnowledgeService(uow_factory=lambda: broken_uow, llm=MagicMock())

    # Should not raise
    await svc.enrich_metadata("file-1")
