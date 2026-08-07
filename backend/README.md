# FedLens Backend

FastAPI backend for the FedLens agent.

## Current MVP

The backend currently provides:

- FastAPI health and chat endpoints
- typed request and response schemas
- a LangGraph workflow that interprets, validates, executes, and explains queries
- OpenRouter-compatible LLM configuration through `ChatOpenAI`
- an offline deterministic interpreter for local development
- a PostgreSQL/Neon data-tool boundary with annual spending analysis and comparisons
- official USAspending ingestion with provenance and ingestion-run tracking
- focused unit tests for parsing, tools, ingestion, and API behavior

The chat path reads from Neon; it does not call USAspending during a user request. The
scheduled ingestion job is the separate path that refreshes official annual aggregates.
