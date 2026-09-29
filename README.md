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
