# mailpilot
AI Email-to-Action Agent powered by Dify, FastAPI and Next.js

## Local port allocation

| Project | Frontend | Backend |
| --- | --- | --- |
| MailPilot | http://localhost:3000 | FastAPI: http://localhost:8000 |
| SmartStep | http://localhost:3001 | Integrated Vinext/Cloudflare Worker: http://localhost:3001 |

SmartStep does not run a separate FastAPI service. Keep port 8000 reserved for
MailPilot; its frontend API URL and Google OAuth callback use that port.

## One-command local stack

Copy `apps/api/.env.example` to `apps/api/.env`, then start the complete
production-shaped stack (Next.js, FastAPI, PostgreSQL/pgvector, Redis and the
worker):

```bash
docker compose up --build
```

Open [http://localhost:3000](http://localhost:3000). FastAPI is available at
[http://localhost:8000/docs](http://localhost:8000/docs). The API container
runs `alembic upgrade head` before starting, and PostgreSQL data is persisted
in the `mailpilot_postgres_data` volume. Stop the stack with
`docker compose down`; add `-v` only when you intentionally want to delete
the local database volume.

## Deployment shape

The same images can be deployed as a web service and API/worker services on
Railway or Render. The recommended portfolio setup is Vercel for `apps/web`,
Railway/Render for FastAPI and worker, and Supabase PostgreSQL with the
`vector` extension. Set `DATABASE_URL`, OAuth credentials, Dify keys and
`CORS_ORIGINS` as platform secrets; never put them in `NEXT_PUBLIC_*` values.
Production Google OAuth must use the exact HTTPS callback URL configured in
Google Cloud. A deployment checklist and CI smoke checks live in
`docs/deployment.md`.

## Quality and portfolio evidence

GitHub Actions runs API tests, web lint/build and Docker builds on every push.
The `evals/` directory contains the 20-case benchmark and reproducible report.
For a three-minute demo, show: Gmail sync, bilingual summary, calendar
approval, AI search with citations, and Agent Trace cost/latency inspection.

## Local database

Start PostgreSQL:

```bash
docker compose up -d postgres
```

Check its status:

```bash
docker compose ps
```

The database initialization scripts enable the `vector` extension for semantic
search. Verify it with:

```bash
docker compose exec postgres psql -U mailpilot -d mailpilot \
  -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
```

Stop it without deleting local data:

```bash
docker compose stop postgres
```

## Email history RAG

MailPilot stores paragraph-aware email chunks and 1536-dimensional embeddings in
PostgreSQL/pgvector. Retrieval always joins through `email_accounts.user_id`, so
one user cannot retrieve another user's email. It supports semantic, current
thread, and same-sender scopes and returns at most 3-5 source citations.

Local tests default to deterministic zero-cost vectors. To create real semantic
embeddings, set `RAG_EMBEDDING_MOCK_MODE=false` and configure
`EMBEDDING_API_KEY` only in `apps/api/.env`, then run:

```bash
cd apps/api
source .venv/bin/activate
python scripts/index_existing_emails.py
```

The Dify tool contract is documented in `dify/rag-tool.openapi.yaml`. When no
relevant result passes the similarity threshold, the API returns
`no_results=true` and no citations rather than allowing a fabricated source.

The Inbox also exposes a zero-LLM-token search UI through
`POST /rag/emails/{email_id}/search`. The browser never supplies a `user_id`;
FastAPI derives it from the connected email account before applying semantic,
current-thread, or same-sender retrieval. Each result includes a citation that
can open the original synchronized email.
