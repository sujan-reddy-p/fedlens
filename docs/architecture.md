# FedLens Architecture

FedLens uses a browser frontend, a FastAPI backend, and official government data APIs.

The backend owns all trusted execution:

- request validation
- agent routing
- typed tool calls
- source metadata
- deterministic calculations
- ML inference

The LLM may route, summarize, and explain verified tool output. It must not be the factual source for federal spending amounts.
