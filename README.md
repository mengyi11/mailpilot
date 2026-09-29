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

Stop it without deleting local data:

```bash
docker compose stop postgres
```
