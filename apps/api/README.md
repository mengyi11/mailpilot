# MailPilot API

FastAPI backend for MailPilot.

## Local Python environment

Create a project-local virtual environment from this directory:

```bash
python3 -m venv .venv
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

Confirm that the active interpreter belongs to this project:

```bash
which python
python --version
```

The `.venv` directory contains machine-specific dependencies and is intentionally excluded from Git. It must be recreated after cloning the repository.

Install the backend dependencies inside the active environment:

```bash
python -m pip install -r requirements.txt
```

The database stack uses SQLAlchemy for Python data access, Alembic for schema
versioning, and Psycopg as the PostgreSQL driver.

Run the development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`, with interactive documentation at `/docs` and a health check at `/health`.

## Google OAuth security boundary

Google OAuth is handled only by FastAPI:

- `GET /auth/google/connect` creates a signed, ten-minute OAuth state and the
  Google authorization URL.
- `GET /auth/google/callback` verifies state, exchanges the one-time code,
  reads the Gmail profile, and stores encrypted credentials.
- Expired access tokens are refreshed server-side with the encrypted refresh
  token.
- `POST /auth/google/accounts/{account_id}/disconnect` revokes Google access
  and removes the local credential.

The frontend receives connection status and account IDs only. Client secrets,
authorization codes, access tokens, and refresh tokens must never be returned
to the browser, logged, included in Dify inputs, or committed to Git.

## Environment configuration

Copy the public template before local development:

```bash
cp .env.example .env
```

The committed template contains safe development defaults only. Never add email content, OAuth tokens, client secrets, or API keys to `.env.example` or application logs.

`CORS_ORIGINS` is a JSON list of browser origins allowed to call the API. Production deployments must replace the localhost value with the deployed MailPilot frontend domain.

`DATABASE_URL` is the SQLAlchemy connection URL. The checked-in value is only
for the local Docker database; production credentials must be stored as secrets.

## Database migrations

Run migrations from `apps/api` after PostgreSQL is healthy:

```bash
alembic upgrade head
```

Check the current schema revision:

```bash
alembic current
```

After changing SQLAlchemy models, generate a reviewed migration:

```bash
alembic revision --autogenerate -m "describe schema change"
```

Changing a SQLAlchemy model does not change PostgreSQL by itself. Review the
generated migration and run `alembic upgrade head` to apply it.

## Email processing pipeline

Gmail synchronization keeps the original HTML for traceability, stores a
sanitized HTML copy for the browser, and produces `cleaned_text` as the only
body intended for Dify/LLM prompts. The processor removes active content,
remote tracking images, quoted history, common signatures, and disclaimers
while preserving visible dates, amounts, names, and links.

TXT, PDF, and DOCX attachments are downloaded server-side and converted to
text when they are within the configured count and size limits. Unsupported,
inline, oversized, and damaged files receive an explicit extraction status;
they do not fail the entire Gmail sync.

Each processed email records the original timezone, the user's preferred
timezone, and a reference date derived from the email's sent time. Relative
dates such as “tomorrow” must be interpreted from this reference date, not the
date when an AI job happens to run.

After migration `0010`, normalize emails that were already synchronized:

```bash
PYTHONPATH=. python scripts/process_existing_emails.py
```
