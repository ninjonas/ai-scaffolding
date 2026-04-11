"""Tests for KnowledgeIndexer chunking and KnowledgeSearcher filtering."""

from typing import ClassVar

import pytest

from app.domain.entities.knowledge_file import SCOPE_CONVERSATION, SCOPE_PROJECT
from app.infrastructure.vector.knowledge_indexer import (
    DOC_TYPE_SUMMARY,
    _build_summary_chunk,
    _chunk_text,
)
from app.infrastructure.vector.knowledge_searcher import (
    MIN_RELEVANCE_SCORE,
    MIN_RELEVANCE_SCORE_CONVERSATION,
    build_search_filter,
)


class TestChunkText:
    def test_short_text_single_chunk(self):
        chunks = _chunk_text("Hello world.")
        assert len(chunks) == 1
        assert chunks[0] == "Hello world."

    def test_empty_text_returns_empty(self):
        assert _chunk_text("") == []
        assert _chunk_text("   ") == []

    def test_splits_on_paragraph_boundaries(self):
        para = "A" * 600
        text = f"{para}\n\n{para}"
        chunks = _chunk_text(text)
        assert len(chunks) >= 2

    def test_long_text_produces_multiple_chunks(self):
        sentence = "This is a sentence. "
        text = sentence * 80  # ~1600 chars
        chunks = _chunk_text(text)
        assert len(chunks) >= 2

    def test_overlap_produces_shared_content(self):
        para = "Word " * 300  # ~1500 chars
        chunks = _chunk_text(para)
        assert len(chunks) >= 2
        # With 512 char overlap, chunks should share content
        if len(chunks) >= 2:
            set0 = set(chunks[0].split())
            set1 = set(chunks[1].split())
            assert set0 & set1, "Chunks should have overlapping content"


class TestBuildSummaryChunk:
    """Tests for the Multi-Vector summary chunk builder."""

    _BASE_META: ClassVar[dict[str, str]] = {
        "file_id": "f1",
        "name": "test",
        "file_type": "text/plain",
        "scope": "global",
        "conversation_id": "",
    }

    def test_returns_single_summary_chunk(self):
        ids, docs, metas = _build_summary_chunk(
            "f1",
            "My File",
            "A description",
            ["tag1", "tag2"],
            self._BASE_META,
        )
        assert len(ids) == 1
        assert ids[0] == "f1_summary"
        assert "My File" in docs[0]
        assert "A description" in docs[0]
        assert "tag1, tag2" in docs[0]
        assert metas[0]["doc_type"] == DOC_TYPE_SUMMARY
        assert metas[0]["chunk_index"] == 0

    def test_summary_with_no_tags(self):
        _ids, docs, metas = _build_summary_chunk(
            "f1",
            "Name",
            "Desc",
            None,
            self._BASE_META,
        )
        assert "Tags:" in docs[0]
        assert metas[0]["doc_type"] == DOC_TYPE_SUMMARY

    def test_summary_with_empty_description(self):
        _, docs, _ = _build_summary_chunk(
            "f1",
            "Name",
            "",
            ["t1"],
            self._BASE_META,
        )
        assert docs[0] == "Name.  Tags: t1"


class TestKnowledgeSearcherFiltering:
    """Test score filtering and deduplication logic inline (no ChromaDB)."""

    def test_min_relevance_score_is_defined(self):
        assert MIN_RELEVANCE_SCORE == 0.3

    def test_conversation_relevance_score_is_lower(self):
        assert MIN_RELEVANCE_SCORE_CONVERSATION == 0.15
        assert MIN_RELEVANCE_SCORE_CONVERSATION < MIN_RELEVANCE_SCORE

    def test_score_below_threshold_excluded(self):
        """Simulate the filtering logic from KnowledgeSearcher.search."""
        distances = [0.1, 0.8]  # scores: 0.9, 0.2
        hits = []
        for dist in distances:
            score = 1.0 - dist
            if score < MIN_RELEVANCE_SCORE:
                continue
            hits.append(score)
        assert len(hits) == 1
        assert hits[0] == pytest.approx(0.9)

    def test_conversation_scope_uses_lower_threshold(self):
        """Image summaries scoring 0.2 survive conversation threshold but not project."""
        distances = [0.1, 0.8]  # scores: 0.9, 0.2
        project_hits = [1.0 - d for d in distances if (1.0 - d) >= MIN_RELEVANCE_SCORE]
        convo_hits = [1.0 - d for d in distances if (1.0 - d) >= MIN_RELEVANCE_SCORE_CONVERSATION]
        assert len(project_hits) == 1
        assert len(convo_hits) == 2

    def test_deduplication_keeps_first_chunk(self):
        """Simulate the deduplication logic from KnowledgeSearcher.search."""
        metas = [
            {"file_id": "f1", "chunk_index": 0},
            {"file_id": "f1", "chunk_index": 1},
            {"file_id": "f2", "chunk_index": 0},
        ]
        seen: set[str] = set()
        kept = []
        for meta in metas:
            fid = meta["file_id"]
            if fid in seen:
                continue
            seen.add(fid)
            kept.append(meta)
        assert len(kept) == 2
        assert kept[0]["file_id"] == "f1"
        assert kept[0]["chunk_index"] == 0
        assert kept[1]["file_id"] == "f2"


class TestBuildSearchFilter:
    """Test build_search_filter produces correct ChromaDB where clauses."""

    def test_project_scope_simple_filter(self):
        result = build_search_filter(SCOPE_PROJECT)
        assert result == {"scope": SCOPE_PROJECT}

    def test_project_scope_ignores_conversation_id(self):
        result = build_search_filter(SCOPE_PROJECT, conversation_id="conv-1")
        assert result == {"scope": SCOPE_PROJECT}

    def test_conversation_scope_without_id_returns_none(self):
        result = build_search_filter(SCOPE_CONVERSATION)
        assert result is None

    def test_conversation_scope_with_id_uses_or_filter(self):
        result = build_search_filter(SCOPE_CONVERSATION, conversation_id="conv-1")
        assert "$or" in result
        branches = result["$or"]
        assert len(branches) == 2
        assert branches[0] == {
            "$and": [{"scope": SCOPE_CONVERSATION}, {"conversation_id": "conv-1"}],
        }
        assert branches[1] == {"scope": SCOPE_PROJECT}
