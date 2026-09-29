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

Run the development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`, with interactive documentation at `/docs` and a health check at `/health`.
