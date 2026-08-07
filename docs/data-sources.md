# Data Sources

## USAspending.gov

USAspending.gov is FedLens's authoritative structured source for the current application. The ingestion flow uses official reference and budgetary-resources endpoints to resolve agencies and normalize annual obligations and outlays by fiscal year.

Each stored record keeps the upstream source URL, fiscal-year bounds, metric values, and ingestion status. The chat path reads those normalized records from Neon rather than calling the upstream API during a user request.

## Storage Strategy

FedLens stores compact aggregates needed for fast, reproducible analysis. It does not copy the national transaction corpus into Neon. This keeps the initial deployment small while leaving a clear extension point for account-level data, Treasury Fiscal Data, official budget documents, and a document retrieval layer.
