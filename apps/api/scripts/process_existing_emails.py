"""Backfill normalized AI input for emails synchronized before migration 0010."""

from sqlalchemy import select

from app.core.config import get_settings
from app.db.models.email import Email
from app.db.models.identity import EmailAccount
from app.db.models.productivity import UserPreference
from app.db.session import SessionLocal
from app.services.email_processing import process_email_content


def main() -> None:
    settings = get_settings()
    processed_count = 0
    with SessionLocal() as db:
        emails = db.scalars(select(Email).order_by(Email.received_at)).all()
        timezone_by_user: dict[object, str] = {}

        for email in emails:
            # Resolve the owning user's preference through the account relationship
            # only when needed; configuration is a safe local fallback.
            user_timezone = settings.email_user_timezone
            owner_id = db.scalar(
                select(EmailAccount.user_id).where(
                    EmailAccount.id == email.email_account_id
                )
            )
            if owner_id is not None:
                if owner_id not in timezone_by_user:
                    timezone_by_user[owner_id] = db.scalar(
                        select(UserPreference.timezone).where(
                            UserPreference.user_id == owner_id
                        )
                    ) or settings.email_user_timezone
                user_timezone = timezone_by_user[owner_id]

            raw_html = email.raw_body_html or email.body_html
            result = process_email_content(
                body_html=raw_html,
                body_text=email.body_text,
                sent_at=email.sent_at or email.received_at,
                user_timezone=user_timezone,
            )
            email.raw_body_html = raw_html
            email.body_html = result.safe_html
            email.body_text = result.plain_text
            email.cleaned_text = result.cleaned_text
            email.original_timezone = result.original_timezone
            email.user_timezone = result.user_timezone
            email.reference_date = result.reference_date
            email.processing_metadata = {
                "removed_sections": result.removed_sections,
                "processor_version": "email-processing-v1",
                "backfilled": True,
            }
            processed_count += 1

        db.commit()
    print(f"Processed {processed_count} existing emails.")


if __name__ == "__main__":
    main()
