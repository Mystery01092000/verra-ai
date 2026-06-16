// Shared domain + orchestrator types (mirror docs/adr + System Design ERD).
export type TenantType = 'firm' | 'company' | 'individual';
export type ModuleName = 'tax' | 'books' | 'audit' | 'compliance' | 'assistant';

export interface RunRequest {
  tenantId: string;
  module: ModuleName;
  capability: string;            // e.g. 'tax_analysis'
  input: Record<string, unknown>;
  contextRefs?: string[];        // doc/ledger refs for grounding
  budget?: { maxUsd?: number; maxTokens?: number };
  approval?: { mode: 'required' | 'auto'; callback?: string };
  idempotencyKey?: string;
}

export type RunStatus =
  | 'planned' | 'routed' | 'executing' | 'verifying'
  | 'awaiting_approval' | 'done' | 'failed';

export interface Citation { docId: string; page?: number; rule?: string; }

export interface RunResult {
  runId: string;
  status: RunStatus;
  output?: unknown;
  citations: Citation[];
  cost: { usd: number; tokensIn: number; tokensOut: number };
  receiptId?: string;
}
