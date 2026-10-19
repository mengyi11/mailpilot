# MailPilot Evaluation Suite

This directory contains a reproducible, privacy-safe benchmark for the email
analysis workflow. The 20 cases are synthetic; no real mailbox content or OAuth
data is committed.

## Zero-cost evaluation

The default fixture mode validates the complete scoring and reporting pipeline
without calling Dify or consuming tokens:

```bash
python3 evals/run_evaluation.py --mode fixture
```

The generated files are written to `evals/reports/latest.json` and
`evals/reports/latest.md`. Fixture scores are labelled `fixture`; they must not
be presented as real model quality.

## Live Prompt V1 vs V2

Publish two Dify Workflow versions and provide their app API keys only through
environment variables. Never commit the keys.

```bash
export DIFY_V1_API_KEY=...
export DIFY_V2_API_KEY=...
python3 evals/run_evaluation.py --mode live
```

Optional variables:

- `DIFY_BASE_URL` defaults to `https://api.dify.ai/v1`.
- `DIFY_PRICE_PER_M_INPUT` and `DIFY_PRICE_PER_M_OUTPUT` calculate estimated
  cost when the provider exposes separate token counts. Otherwise the report
  records total tokens and leaves cost at zero rather than inventing a price.

The runner sends only the synthetic benchmark inputs. It evaluates
classification Macro F1, action F1, exact date accuracy, citation accuracy,
tool-selection accuracy, unsafe-action rate, summary key-fact recall, latency,
tokens, estimated cost, failures, and per-case error reasons.

## Tests

```bash
python3 -m unittest discover -s evals/tests -v
```
