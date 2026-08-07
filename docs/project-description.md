# FedLens Project Description

FedLens solves a practical information problem: federal spending data is public, but answering a seemingly simple question often requires identifying the correct agency, fiscal-year boundaries, spending metric, aggregation, and source endpoint. FedLens gives a user a conversational interface for asking those questions and returns grounded answers with key figures, visual summaries, source provenance, and an activity trace.

The system uses a static HTML/CSS/JavaScript frontend, a FastAPI backend, LangGraph for workflow orchestration, OpenRouter's OpenAI-compatible API for natural-language interpretation and explanation, Pydantic for typed query contracts, SQLAlchemy asyncio with asyncpg for database access, and Neon PostgreSQL for persistence. USAspending.gov is used by a separate ingestion path that resolves official agency references and stores annual obligations and outlays as compact, auditable records. The agent does not allow the language model to invent SQL or factual values: it converts the question into a structured request, invokes a typed spending tool, performs deterministic calculations, and then explains the verified result.

My contribution covered the complete application path: designing the agent state and LangGraph nodes, implementing the OpenRouter provider boundary, building the PostgreSQL repository and spending-analysis tools, creating the USAspending ingestion and normalization flow, adding source and activity metadata to the API response, and building the browser workspace that renders answers and charts. I also added local configuration, CORS handling, deployment manifests for Render and Vercel, and focused tests for fiscal-year parsing, tool aggregation, agency comparisons, ingestion normalization, and malformed free-model responses.

The main engineering challenge was balancing flexible natural-language input with reliable data behavior. Users may say “NASA,” “the Department of Defense,” “FY2025,” “spent,” or “outlays,” while the database requires canonical agencies, exact fiscal-year date ranges, and an explicit metric. I addressed this with typed Pydantic contracts, query normalization, deterministic tool execution, explicit obligations-versus-outlays semantics, source URLs, and a local fallback when a free model returns malformed structured output. This architecture keeps the conversational layer useful while ensuring that the numbers come from the database and can be traced back to an official source.

## Role Alignment

- **Python and backend engineering:** FastAPI, async SQLAlchemy, asyncpg, repository boundaries, scripts, and tests.
- **LLM and agent development:** LangGraph state machine, OpenRouter integration, structured interpretation, fallback handling, and observable activity events.
- **Machine-learning-adjacent data work:** fiscal-year normalization, feature-like aggregation, metric selection, deterministic comparisons, and explainable analytical outputs.
- **Data systems:** Neon PostgreSQL, typed schemas, ingestion status, source provenance, and API contracts.
- **Production workflow:** local environment configuration, CORS, Render service and refresh job, Vercel static deployment, and operational README documentation.
