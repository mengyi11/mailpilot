"""Index synchronized emails for RAG without exposing email content to the CLI."""

import asyncio

from sqlalchemy import select

from app.core.config import get_settings
from app.db.models.email import Email
from app.db.models.identity import EmailAccount
from app.db.session import SessionLocal
from app.services.rag import EmbeddingClient, RagService


async def main() -> None:
    settings = get_settings()
    service = RagService(settings, EmbeddingClient(settings))
    indexed = failed = chunks = 0
    with SessionLocal() as db:
        rows = db.execute(
            select(Email.id, EmailAccount.user_id)
            .join(EmailAccount, Email.email_account_id == EmailAccount.id)
            .order_by(Email.received_at.desc())
            .limit(settings.gmail_sync_limit)
        ).all()
        for email_id, user_id in rows:
            try:
                result = await service.index_email(
                    db, user_id=user_id, email_id=email_id
                )
                indexed += 1
                chunks += result.chunks_created
            except Exception as exc:  # keep indexing other owned emails
                failed += 1
                print(f"Failed to index {email_id}: {type(exc).__name__}")
    mode = "mock/test vectors" if settings.rag_embedding_mock_mode else settings.dify_embedding_model
    print(f"Indexed {indexed} emails into {chunks} chunks; failed={failed}; mode={mode}")


if __name__ == "__main__":
    asyncio.run(main())
