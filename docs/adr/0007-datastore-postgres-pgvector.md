# ADR-0007: PostgreSQL + pgvector as primary datastore
**Status:** Accepted
## Context
We need relational state, an audit store, and vector search for RAG, with strong consistency and
multi-tenancy.
## Decision
**PostgreSQL** for relational state + immutable audit; **pgvector** for embeddings initially. Revisit
a dedicated vector DB only if scale demands. Object storage (S3-compatible) for documents.
## Consequences
+ One well-understood store; transactions; RLS for tenancy; fewer moving parts at start.
− pgvector has scale limits → revisit per ADR process.
