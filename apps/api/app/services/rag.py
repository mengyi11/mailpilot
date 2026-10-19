from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.db.models.email import Email, EmailChunk
from app.db.models.identity import EmailAccount
from app.schemas.rag import Citation, RagSearchRequest, RagSearchResponse, RetrievalScope


EMBEDDING_DIMENSIONS = 1536


def chunk_email_text(
    text: str, *, chunk_size: int = 1800, overlap: int = 240
) -> list[str]:
    """Create paragraph-aware chunks while preserving a small context overlap."""
    normalized = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not normalized:
        return []
    chunk_size = max(400, chunk_size)
    overlap = min(max(0, overlap), chunk_size // 3)
    paragraphs = [item.strip() for item in normalized.split("\n\n") if item.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        pieces = [
            paragraph[index : index + chunk_size]
            for index in range(0, len(paragraph), chunk_size)
        ] or [paragraph]
        for piece in pieces:
            candidate = f"{current}\n\n{piece}".strip() if current else piece
            if len(candidate) <= chunk_size:
                current = candidate
                continue
            if current:
                chunks.append(current)
                prefix = current[-overlap:] if overlap else ""
                current = f"{prefix}\n\n{piece}".strip()
            else:
                chunks.append(piece)
    if current:
        chunks.append(current)
    return chunks


class EmbeddingClient:
    def __init__(
        self, settings: Settings, *, http_client: httpx.AsyncClient | None = None
    ) -> None:
        self.settings = settings
        self._http_client = http_client

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.settings.rag_embedding_mock_mode:
            return [self._deterministic_embedding(text) for text in texts]
        if not self.settings.embedding_api_key:
            raise AppError(
                code="EMBEDDING_NOT_CONFIGURED",
                message="Real RAG indexing requires EMBEDDING_API_KEY.",
                status_code=503,
            )
        owns_client = self._http_client is None
        client = self._http_client or httpx.AsyncClient(timeout=60)
        try:
            response = await client.post(
                self.settings.embedding_api_url,
                headers={
                    "Authorization": f"Bearer {self.settings.embedding_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.settings.dify_embedding_model,
                    "input": texts,
                    "dimensions": EMBEDDING_DIMENSIONS,
                },
            )
        except httpx.HTTPError as exc:
            raise AppError(
                code="EMBEDDING_REQUEST_FAILED",
                message="The embedding provider is temporarily unavailable.",
                status_code=502,
            ) from exc
        finally:
            if owns_client:
                await client.aclose()
        if response.is_error:
            raise AppError(
                code="EMBEDDING_REQUEST_FAILED",
                message=f"Embedding provider returned HTTP {response.status_code}.",
                status_code=502,
            )
        payload = response.json().get("data", [])
        ordered = sorted(payload, key=lambda item: item["index"])
        vectors = [item["embedding"] for item in ordered]
        if len(vectors) != len(texts) or any(
            len(vector) != EMBEDDING_DIMENSIONS for vector in vectors
        ):
            raise AppError(
                code="EMBEDDING_OUTPUT_INVALID",
                message="Embedding provider returned an unexpected result.",
                status_code=502,
            )
        return vectors

    @staticmethod
    def _deterministic_embedding(text: str) -> list[float]:
        """Zero-cost test vector; production must use a semantic embedding model."""
        vector = [0.0] * EMBEDDING_DIMENSIONS
        lowered = text.lower()
        terms = re.findall(r"[a-z0-9_]+", lowered)
        # Chinese has no whitespace word boundary. Character bigrams make local
        # zero-cost search useful without pretending to be a semantic model.
        for run in re.findall(r"[\u4e00-\u9fff]+", lowered):
            terms.extend(run)
            terms.extend(run[index : index + 2] for index in range(len(run) - 1))
        for term in terms:
            digest = hashlib.sha256(term.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % EMBEDDING_DIMENSIONS
            vector[index] += 1.0 if digest[4] % 2 == 0 else -1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


@dataclass(frozen=True)
class IndexedEmail:
    email_id: UUID
    chunks_created: int


class RagService:
    def __init__(self, settings: Settings, embeddings: EmbeddingClient) -> None:
        self.settings = settings
        self.embeddings = embeddings

    async def index_email(
        self, db: Session, *, user_id: UUID, email_id: UUID
    ) -> IndexedEmail:
        email = self._owned_email(db, user_id=user_id, email_id=email_id)
        body = (email.cleaned_text or email.body_text or email.snippet or "").strip()
        attachment_text = "\n\n".join(
            f"Attachment: {item.filename}\n{item.extracted_text}"
            for item in email.attachments
            if item.extracted_text
        )
        source = "\n\n".join(item for item in [body, attachment_text] if item)
        chunks = chunk_email_text(
            source,
            chunk_size=self.settings.rag_chunk_size_chars,
            overlap=self.settings.rag_chunk_overlap_chars,
        )
        if not chunks:
            raise AppError(
                code="EMAIL_CONTENT_EMPTY",
                message="The email has no clean text to index.",
                status_code=422,
            )
        vectors = await self.embeddings.embed(chunks)
        sender = self._sender_text(email.sender)
        sent_at = email.sent_at or email.received_at
        db.execute(delete(EmailChunk).where(EmailChunk.email_id == email.id))
        for index, (content, embedding) in enumerate(zip(chunks, vectors, strict=True)):
            db.add(
                EmailChunk(
                    email_id=email.id,
                    chunk_index=index,
                    content=content,
                    token_count=max(1, len(content) // 4),
                    embedding=embedding,
                    chunk_metadata={
                        "user_id": str(user_id),
                        "email_id": str(email.id),
                        "thread_id": str(email.thread_id) if email.thread_id else None,
                        "sender": sender,
                        "sent_at": sent_at.isoformat(),
                        "subject": email.subject or "(no subject)",
                        "embedding_model": (
                            "deterministic-test-vector"
                            if self.settings.rag_embedding_mock_mode
                            else self.settings.dify_embedding_model
                        ),
                    },
                )
            )
        email.processing_metadata = {
            **email.processing_metadata,
            "rag_indexed": True,
            "rag_chunk_count": len(chunks),
            "rag_embedding_model": (
                "deterministic-test-vector"
                if self.settings.rag_embedding_mock_mode
                else self.settings.dify_embedding_model
            ),
        }
        db.commit()
        return IndexedEmail(email_id=email.id, chunks_created=len(chunks))

    async def search(self, db: Session, request: RagSearchRequest) -> RagSearchResponse:
        embedding_query = (
            self._expand_mock_query(request.query)
            if self.settings.rag_embedding_mock_mode
            else request.query
        )
        query_vector = (await self.embeddings.embed([embedding_query]))[0]
        top_k = min(request.top_k, self.settings.rag_max_top_k)
        distance = EmailChunk.embedding.cosine_distance(query_vector)
        statement = (
            select(EmailChunk, Email, distance.label("distance"))
            .join(Email, EmailChunk.email_id == Email.id)
            .join(EmailAccount, Email.email_account_id == EmailAccount.id)
            .where(
                EmailAccount.user_id == request.user_id,
                EmailChunk.embedding.is_not(None),
            )
        )

        reference_email: Email | None = None
        if request.email_id:
            reference_email = self._owned_email(
                db, user_id=request.user_id, email_id=request.email_id
            )
        if request.scope == RetrievalScope.current_thread:
            thread_id = request.thread_id or (
                reference_email.thread_id if reference_email else None
            )
            if thread_id is None:
                return self._no_results("The selected email has no thread history.")
            statement = statement.where(Email.thread_id == thread_id)
        elif request.scope == RetrievalScope.same_sender:
            sender = request.sender or (
                self._sender_text(reference_email.sender) if reference_email else None
            )
            statement = statement.where(
                Email.sender["email"].as_string() == self._sender_address(sender or "")
            )

        # Fetch extra candidate chunks, then keep only the best chunk per email.
        # Otherwise one long newsletter can occupy every visible citation.
        rows = db.execute(statement.order_by(distance).limit(top_k * 8)).all()
        citations: list[Citation] = []
        seen_email_ids: set[UUID] = set()
        for chunk, email, raw_distance in rows:
            if email.id in seen_email_ids:
                continue
            similarity = max(0.0, min(1.0, 1.0 - float(raw_distance)))
            minimum_similarity = (
                0.0
                if self.settings.rag_embedding_mock_mode
                else self.settings.rag_min_similarity
            )
            if similarity < minimum_similarity:
                continue
            seen_email_ids.add(email.id)
            citation_number = len(citations) + 1
            citations.append(
                Citation(
                    citation_id=f"C{citation_number}",
                    chunk_id=chunk.id,
                    email_id=email.id,
                    thread_id=email.thread_id,
                    subject=email.subject or "(no subject)",
                    sender=self._sender_text(email.sender),
                    sent_at=email.sent_at or email.received_at,
                    excerpt=chunk.content[:600],
                    similarity=round(similarity, 4),
                )
            )
            if len(citations) >= top_k:
                break
        if not citations:
            return self._no_results(
                "No sufficiently relevant historical email was found. Do not infer or fabricate a citation."
            )
        context = "\n\n".join(
            f"[{item.citation_id}] {item.subject} — {item.sender} — "
            f"{item.sent_at.isoformat()}\n{item.excerpt}"
            for item in citations
        )
        answer, answer_mode = await self._generate_answer(
            query=request.query,
            citations=citations,
            context=context,
            user_id=request.user_id,
        )
        return RagSearchResponse(
            answer=answer,
            answer_mode=answer_mode,
            answer_context=context,
            citations=citations,
            result_count=len(citations),
            no_results=False,
        )

    @staticmethod
    def _no_results(message: str) -> RagSearchResponse:
        return RagSearchResponse(
            answer="没有找到足够相关的邮件证据，因此无法可靠回答这个问题。",
            answer_mode="no_evidence",
            answer_context="",
            citations=[],
            result_count=0,
            no_results=True,
            message=message,
        )

    async def _generate_answer(
        self,
        *,
        query: str,
        citations: list[Citation],
        context: str,
        user_id: UUID,
    ) -> tuple[str, str]:
        """Answer only from retrieved evidence; local mock mode spends zero tokens."""
        if self.settings.dify_mock_mode:
            return self._mock_answer(query, citations), "local_mock"
        if not self.settings.dify_rag_api_key:
            raise AppError(
                code="DIFY_RAG_NOT_CONFIGURED",
                message="AI search requires DIFY_RAG_API_KEY when DIFY_MOCK_MODE is false.",
                status_code=503,
            )

        max_chars = max(1000, self.settings.rag_answer_max_context_chars)
        payload = {
            "inputs": {
                "query": query,
                "context": context[:max_chars],
                "instruction": (
                    "Answer only from context. Cite every factual claim with [C1], [C2]. "
                    "If evidence is insufficient, say so. Do not invent facts."
                ),
            },
            "response_mode": "blocking",
            "user": str(user_id),
        }
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.settings.dify_base_url.rstrip('/')}/workflows/run",
                    headers={
                        "Authorization": f"Bearer {self.settings.dify_rag_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise AppError(
                code="AI_SEARCH_UNAVAILABLE",
                message="The AI answer service is temporarily unavailable.",
                status_code=502,
            ) from exc
        if response.is_error:
            raise AppError(
                code="AI_SEARCH_FAILED",
                message=f"The AI answer workflow returned HTTP {response.status_code}.",
                status_code=502,
            )
        data = response.json().get("data", {})
        outputs = data.get("outputs") or {}
        answer = outputs.get("answer") or outputs.get("text")
        if data.get("status") != "succeeded" or not isinstance(answer, str) or not answer.strip():
            raise AppError(
                code="AI_SEARCH_OUTPUT_INVALID",
                message="The AI answer workflow returned an invalid answer.",
                status_code=502,
            )
        return answer.strip(), "dify"

    @staticmethod
    def _mock_answer(query: str, citations: list[Citation]) -> str:
        """Deterministic evidence summary for UI development without an LLM call."""
        evidence = citations[:3]
        lines = [
            "检索结论",
            f'已为“{query}”找到 {len(citations)} 封相关邮件。当前为零 Token 本地模拟模式，系统仅整理检索结果，不判断邮件优先级。',
            "",
            "关键发现",
        ]
        for item in evidence:
            excerpt = re.sub(r"\s+", " ", item.excerpt).strip()
            contains_markup = any(
                marker in excerpt
                for marker in (
                    "!important",
                    "{",
                    "}",
                    "/*",
                    "font-size:",
                    "width:",
                    "&tk=",
                    "&alid=",
                    "&bb=",
                    "DpdM&",
                )
            )
            if contains_markup:
                lines.append(
                    f"• [{item.citation_id}] {item.subject} — 发件人：{item.sender}。"
                )
            else:
                if len(excerpt) > 120:
                    excerpt = f"{excerpt[:117]}…"
                lines.append(f"• [{item.citation_id}] {item.subject} — {excerpt}")
        lines.extend(
            [
                "",
                "建议",
                "打开下方来源核对完整邮件。模拟模式不会补充邮件中不存在的信息。",
            ]
        )
        return "\n".join(lines)

    @staticmethod
    def _expand_mock_query(query: str) -> str:
        """Small bilingual aid for local UI tests; real mode uses embeddings."""
        aliases = {
            "人工智能": "AI artificial intelligence",
            "实习": "intern internship",
            "新加坡": "Singapore",
            "工作": "job jobs career",
            "职位": "job position role",
            "产品经理": "product manager",
            "工程师": "engineer engineering",
            "费用": "cost fee price pricing",
            "价格": "price pricing cost",
            "日期": "date time schedule",
            "日历": "calendar date schedule",
            "最近": "latest recent",
            "重要": "important priority",
        }
        additions = [english for chinese, english in aliases.items() if chinese in query]
        return " ".join([query, *additions])

    @staticmethod
    def _owned_email(db: Session, *, user_id: UUID, email_id: UUID) -> Email:
        email = db.scalar(
            select(Email)
            .join(EmailAccount, Email.email_account_id == EmailAccount.id)
            .where(Email.id == email_id, EmailAccount.user_id == user_id)
        )
        if email is None:
            raise AppError(
                code="EMAIL_NOT_FOUND",
                message="Email not found for this user.",
                status_code=404,
            )
        return email

    @staticmethod
    def _sender_text(sender: dict[str, Any]) -> str:
        name = str(sender.get("name") or "").strip()
        address = str(sender.get("email") or "").strip().lower()
        return f"{name} <{address}>" if name and address else address or name or "unknown"

    @staticmethod
    def _sender_address(value: str) -> str:
        match = re.search(r"<([^>]+)>", value)
        return (match.group(1) if match else value).strip().lower()
