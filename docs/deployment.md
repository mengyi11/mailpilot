# MailPilot deployment checklist

## Local

1. Copy `apps/api/.env.example` to `apps/api/.env` and add only local keys.
2. Run `docker compose up --build`.
3. Verify `GET /health`, `/docs`, the web UI, and the PostgreSQL vector extension.
4. Run `docker compose exec api alembic current` and confirm the latest migration.

## Cloud

- Supabase: create PostgreSQL, enable `vector`, set `DATABASE_URL`, and run
  `alembic upgrade head` from the API release command.
- Railway/Render: deploy `apps/api` with the API Dockerfile and deploy the
  same image as a worker using `python worker.py`.
- Vercel: deploy `apps/web`; set `NEXT_PUBLIC_API_BASE_URL` to the HTTPS API URL.
- Dify: set the published workflow URL/key on the API only.
- Google Cloud: add the exact production HTTPS callback URL to the OAuth web
  client and add the production origin to the consent screen.

## Smoke test

1. Connect Gmail and sync a small mailbox.
2. Analyze one email and verify the structured summary.
3. Approve one calendar draft and confirm the created event.
4. Run AI search and open a citation.
5. Open Agent Trace and verify steps, latency, tokens, cost and final status.

## Portfolio handoff

Record a short demo covering those five scenarios. Include the architecture
diagram, benchmark report, limitations (provider-reported vs estimated token
counts), privacy boundary, and next steps in the README.
