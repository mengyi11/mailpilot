# mailpilot
AI Email-to-Action Agent powered by Dify, FastAPI and Next.js

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
