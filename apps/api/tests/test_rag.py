import asyncio
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from datetime import UTC, datetime

from app.schemas.rag import Citation, RagSearchRequest
from app.services.rag import EMBEDDING_DIMENSIONS, EmbeddingClient, RagService, chunk_email_text


def test_chunking_preserves_content_and_limits_size() -> None:
    text = ("First paragraph contains an agreed plan. " * 25) + "\n\n" + (
        "Second paragraph contains the delivery date. " * 25
    )

    chunks = chunk_email_text(text, chunk_size=500, overlap=60)

    assert len(chunks) >= 2
    assert all(chunk.strip() for chunk in chunks)
    assert all(len(chunk) <= 562 for chunk in chunks)
    assert "agreed plan" in chunks[0]
    assert any("delivery date" in chunk for chunk in chunks)


def test_mock_embeddings_are_free_deterministic_and_1536_dimensions() -> None:
    client = EmbeddingClient(Settings(rag_embedding_mock_mode=True))

    first, second = asyncio.run(
        client.embed(["customer chose plan A", "customer chose plan A"])
    )

    assert len(first) == EMBEDDING_DIMENSIONS
    assert first == second
    assert sum(abs(value) for value in first) > 0


def test_thread_scope_requires_owned_reference_filter() -> None:
    with pytest.raises(ValidationError):
        RagSearchRequest(
            user_id=uuid4(),
            query="Which plan did the customer select?",
            scope="current_thread",
        )


def test_top_k_is_restricted_to_three_through_five() -> None:
    with pytest.raises(ValidationError):
        RagSearchRequest(user_id=uuid4(), query="plan", top_k=6)


def test_mock_ai_answer_uses_citation_and_spends_no_tokens() -> None:
    citation = Citation(
        citation_id="C1",
        chunk_id=uuid4(),
        email_id=uuid4(),
        thread_id=None,
        subject="Customer decision",
        sender="customer@example.com",
        sent_at=datetime.now(UTC),
        excerpt="The customer selected plan B for the October launch.",
        similarity=0.91,
    )

    answer = RagService._mock_answer("Which plan was selected?", [citation])

    assert "[C1]" in answer
    assert "plan B" in answer
    assert "零 Token" in answer


def test_mock_query_expands_common_chinese_search_terms() -> None:
    expanded = RagService._expand_mock_query("新加坡AI产品经理实习")

    assert "Singapore" in expanded
    assert "product manager" in expanded
    assert "intern" in expanded
