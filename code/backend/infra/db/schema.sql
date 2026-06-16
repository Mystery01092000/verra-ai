-- Verra schema (excerpt) — PostgreSQL + pgvector, RLS multi-tenancy (ADR-0007/0009/0015).
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE tenants (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  type text NOT NULL CHECK (type IN ('firm','company','individual')),
  jurisdictions text[] NOT NULL DEFAULT '{}',
  settings jsonb NOT NULL DEFAULT '{}', created_at timestamptz DEFAULT now());

CREATE TABLE users (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  role text NOT NULL, sso_subject text, permissions jsonb DEFAULT '{}');

CREATE TABLE clients (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  type text NOT NULL, jurisdictions text[] DEFAULT '{}', profile jsonb DEFAULT '{}');

CREATE TABLE documents (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  client_id uuid REFERENCES clients(id),
  type text, source text, parsed jsonb, page_refs jsonb, confidence numeric, version int DEFAULT 1);

CREATE TABLE doc_chunks (             -- RAG (ADR-0013)
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL, document_id uuid REFERENCES documents(id),
  content text, page int, embedding vector(1536));
CREATE INDEX ON doc_chunks USING ivfflat (embedding vector_cosine_ops);

CREATE TABLE engagements (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL, client_id uuid REFERENCES clients(id),
  type text CHECK (type IN ('tax','books','audit','compliance')), status text, deadlines jsonb);

CREATE TABLE obligations (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL, client_id uuid REFERENCES clients(id),
  jurisdiction text, form text, period text, due_date date, status text, rule_version text);

-- Orchestrator
CREATE TABLE runs (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL, engagement_id uuid,
  module text, capability text, status text,
  budget jsonb, cost_usd numeric DEFAULT 0, tokens_in int DEFAULT 0, tokens_out int DEFAULT 0,
  trace_id text, created_at timestamptz DEFAULT now());
CREATE TABLE plans (id uuid PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id uuid NOT NULL, run_id uuid REFERENCES runs(id), task_graph jsonb, template text, version text);
CREATE TABLE steps (id uuid PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id uuid NOT NULL, run_id uuid REFERENCES runs(id), agent text, model text, tools text[], status text, retries int DEFAULT 0, tokens int DEFAULT 0, cost_usd numeric DEFAULT 0, output_ref text);
CREATE TABLE routing_decisions (id uuid PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id uuid NOT NULL, step_id uuid REFERENCES steps(id), chosen jsonb, reason text, fallbacks_used jsonb);
CREATE TABLE agent_versions (id uuid PRIMARY KEY DEFAULT uuid_generate_v4(), name text, version text, manifest jsonb, eval_status text, lifecycle text);
CREATE TABLE tool_defs (id uuid PRIMARY KEY DEFAULT uuid_generate_v4(), name text, version text, json_schema jsonb, permissions text[], sandbox_profile text);
CREATE TABLE budgets (id uuid PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id uuid NOT NULL, scope text, limits jsonb, consumed jsonb, period text);

-- Append-only, hash-chained audit (ADR-0015)
CREATE TABLE audit_events (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL, run_id uuid, actor text, action text,
  sources jsonb, provider text, cost_usd numeric, tokens int,
  approval jsonb, prev_hash text, hash text, created_at timestamptz DEFAULT now());

-- RLS: every tenant table is isolated by tenant_id = current_setting('app.tenant_id')
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON clients USING (tenant_id::text = current_setting('app.tenant_id', true));
-- ... repeat ENABLE RLS + policy for every tenant-scoped table (generated in migrations).
