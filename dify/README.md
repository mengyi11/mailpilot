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
