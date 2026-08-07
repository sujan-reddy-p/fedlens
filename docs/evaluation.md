# Evaluation

FedLens should be evaluated on:

- whether answers are grounded in retrieved source data
- whether unsupported questions are rejected clearly
- whether calculations are deterministic and test-covered
- whether source metadata is complete enough to reproduce the result
- whether obligations and outlays are distinguished clearly
- whether malformed or unavailable model output falls back safely
- whether the frontend exposes the result, provenance, and workflow activity coherently

The current automated suite covers typed query parsing, fiscal-year normalization, data-tool aggregation, agency comparison, ingestion normalization, API behavior, and provider fallback behavior.
