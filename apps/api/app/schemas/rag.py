from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RetrievalScope(StrEnum):
    semantic = "semantic"
    current_thread = "current_thread"
    same_sender = "same_sender"


class RagSearchRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: UUID
    query: str = Field(min_length=2, max_length=2000)
    scope: RetrievalScope = RetrievalScope.semantic
    email_id: UUID | None = None
    thread_id: UUID | None = None
    sender: str | None = None
    top_k: int = Field(default=4, ge=3, le=5)

    @model_validator(mode="after")
    def validate_scope_filter(self) -> "RagSearchRequest":
        if self.scope == RetrievalScope.current_thread and not (
            self.thread_id or self.email_id
        ):
            raise ValueError("current_thread requires thread_id or email_id")
        if self.scope == RetrievalScope.same_sender and not (
            self.sender or self.email_id
        ):
            raise ValueError("same_sender requires sender or email_id")
        return self


class MailboxRagSearchRequest(BaseModel):
    """Browser contract: identity comes from the owned email, never the client."""

    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(min_length=2, max_length=2000)
    scope: RetrievalScope = RetrievalScope.semantic
    top_k: int = Field(default=4, ge=3, le=5)


class Citation(BaseModel):
    citation_id: str
    chunk_id: UUID
    email_id: UUID
    thread_id: UUID | None
    subject: str
    sender: str
    sent_at: datetime
    excerpt: str
    similarity: float = Field(ge=0, le=1)


class RagSearchResponse(BaseModel):
    answer: str
    answer_mode: str
    answer_context: str
    citations: list[Citation]
    result_count: int
    no_results: bool
    message: str | None = None


class RagIndexResponse(BaseModel):
    email_id: UUID
    chunks_created: int
    embedding_model: str
