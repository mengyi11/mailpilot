# MailPilot Dify workflows

## Main email analysis

The workflow must return one output variable named `analysis`. Its value is JSON
matching [`email-analysis.schema.json`](./email-analysis.schema.json). The
FastAPI service treats all Dify output as untrusted and validates it again with
Pydantic before any calendar draft is created.

## Strong schema repair

`MailPilot Schema Repair` is a separate workflow used only after strict
validation and deterministic local repair both fail. It accepts:

- `email_id`: the expected MailPilot email UUID.
- `raw_analysis`: the invalid analysis JSON, not the original email or OAuth data.

Its LLM node uses the strong model and Dify Structured Output with the same JSON
schema. It must never invent missing facts; unsupported actions and dates are
dropped. The End node exposes `structured_output` as `analysis`.

Publish the workflow, place its secret in `DIFY_REPAIR_API_KEY`, and keep the key
only in `apps/api/.env`. If the repair workflow is unavailable or still returns
invalid data, MailPilot returns a summary-only read-only result with no actions
or calendar candidates.

## Historical email RAG tool

FastAPI owns chunking, embeddings, pgvector retrieval, user isolation, and
citations. Import [`rag-tool.openapi.yaml`](./rag-tool.openapi.yaml) as a Dify
Custom Tool after replacing its server URL with the deployed HTTPS API URL.
Configure `X-RAG-Tool-Key` in Dify's encrypted tool credentials and store the
same secret as `RAG_TOOL_API_KEY` on FastAPI. Never place it in workflow inputs.

The workflow/agent must follow this contract:

1. Pass the authenticated `user_id`; use `current_thread` or `same_sender` only
   with the corresponding filter.
2. Cite claims as `[C1]`, `[C2]`, and so on, using only citations returned by the
   tool.
3. When `no_results=true`, say that no supporting historical email was found.
   It must not answer from model memory or manufacture a source.

Dify Cloud cannot call `localhost`. The tool can be imported now, but end-to-end
cloud execution requires the FastAPI service to be deployed on HTTPS (or exposed
temporarily through an authenticated development tunnel).

## Unified Tool Registry

Import [`tool-registry.openapi.yaml`](./tool-registry.openapi.yaml) after replacing
its server URL with the deployed FastAPI HTTPS URL. Store the same secret in
Dify's encrypted `X-Tool-Api-Key` credential and FastAPI's
`DIFY_TOOL_API_KEY`; never pass it as a workflow variable or prompt text.

The registry exposes `get_email`, `get_email_thread`, `search_emails`,
`retrieve_related_emails`, `get_user_preferences`, `create_task`, and
`create_reply_draft` as separate Dify operations. Every call requires a stable
`idempotencyKey`. FastAPI checks the configured permission, scopes email queries
to `userId`, applies a timeout, writes an `agent_runs` and `tool_calls` audit
record, and returns a structured `ToolResult`. A repeated successful key returns
the cached result instead of repeating a write.

`create_reply_draft` only saves a reviewable draft; it never sends an email.
Treat `ok=false` as a Tool failure and use `error.retryable` to decide whether
the workflow may retry.
