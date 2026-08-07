# FedLens Architecture

FedLens is organized around a strict abstraction boundary between natural-language reasoning and factual computation.

## Request Path

```text
Browser
  -> FastAPI /v1/chat
  -> LangGraph interpretation node
  -> typed query validation node
  -> PostgreSQL spending tool
  -> deterministic aggregation
  -> answer generation node
  -> response with figures, charts, sources, and activity
```

The model does not write SQL and does not invent spending values. It produces a typed query request. The tool layer owns agency lookup, date filtering, metric selection, aggregation, comparisons, and source metadata.

## Data Path

USAspending.gov is used by the separate ingestion command. The command resolves official agency codes, fetches annual budgetary-resource totals, normalizes fiscal-year dates, and upserts compact records into Neon PostgreSQL. Chat requests read from Neon and do not call the upstream government API.

## Provider Boundary

OpenRouter is accessed through the OpenAI-compatible ChatOpenAI interface. The interpreter requests structured JSON and normalizes common fiscal-year shorthand before Pydantic validation. If a free model returns malformed output or times out, the deterministic local interpreter and answerer preserve the data workflow.
