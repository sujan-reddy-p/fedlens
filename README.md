# FedLens

AI federal budget intelligence agent for exploring U.S. federal spending with grounded data, citations, charts, and an observable agent activity trace.

## Why This Exists

FedLens is a portfolio project aimed at demonstrating practical AI/ML engineering:

- Python/FastAPI backend development
- LLM agent orchestration with typed tools
- Structured government API integration
- PostgreSQL-ready caching and persistence boundaries
- Deterministic analysis around verified data
- ML model integration for anomaly detection
- Production-style documentation and deployment readiness

The MVP is intentionally narrow: answer a small set of U.S. agency spending questions reliably before adding broader data sources or document retrieval.

## Current Milestone

Milestone 1 builds the backend foundation:

- FastAPI service
- health endpoint
- typed chat request/response schemas
- service configuration
- USAspending client boundary
- first tests

## Project Layout

```text
backend/
  app/
    api/
    clients/
    schemas/
    services/
    tools/
  tests/
docs/
```

## Local Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## MVP Scope

Supported question families will start with:

- agency spending for one fiscal year
- agency spending comparison across fiscal years
- top federal accounts for an agency and fiscal year

Unsupported requests should receive a clear limitation message rather than a fabricated answer.
