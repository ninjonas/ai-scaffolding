"""Tests for checkpointer singleton factory."""

import pytest

from app.shared.config import Settings


@pytest.mark.asyncio
async def test_checkpointer_singleton_returns_same_instance(tmp_path):
    """get_checkpointer() must return the same instance on repeated calls."""
    import app.shared.checkpointer as cp_module

    cp_module._checkpointer = None

    settings = Settings(checkpoint_db_path=str(tmp_path / "checkpoints.db"))

    first = await cp_module.get_checkpointer(settings)
    second = await cp_module.get_checkpointer(settings)

    assert first is second


@pytest.mark.asyncio
async def test_checkpointer_creates_db_dir(tmp_path):
    """get_checkpointer() creates parent directories if they do not exist."""
    import app.shared.checkpointer as cp_module

    cp_module._checkpointer = None

    nested = tmp_path / "nested" / "dir" / "checkpoints.db"
    settings = Settings(checkpoint_db_path=str(nested))

    await cp_module.get_checkpointer(settings)

    assert nested.parent.exists()
