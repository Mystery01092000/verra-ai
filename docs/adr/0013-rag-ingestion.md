# ADR-0013: pgvector RAG + chunk/rerank + OCR ingestion
**Status:** Accepted
## Context
Answers must be grounded in tenant documents with citations; documents include scanned PDFs/returns.
## Decision
Ingestion: OCR + structured extraction with page refs + confidence; chunk + embed into **pgvector**;
retrieval with reranking; citations carry source page. Deterministic validators check totals.
## Consequences
+ Grounded, cited answers; reuse across modules.
− OCR/extraction quality is a key risk → confidence thresholds + human review.
