---
name: verra-document-ingestion
description: >
  Implement or reason about Verra's document ingestion & parsing pipeline (1040s, returns, statements,
  GST/VAT). Use for OCR/extraction, classification, confidence scoring, and the client tax profile.
---

# Verra document ingestion

## Pipeline
1. **Acquire:** uploads or connectors (ledger, bank, CRM, email).
2. **OCR/parse:** extract structured line items; keep **page-level source refs** + **confidence scores**.
3. **Classify:** document type + jurisdiction + tax year; detect duplicates.
4. **Reconcile:** cross-check across sources; flag missing/inconsistent fields for human review.
5. **Profile:** build a **versioned client tax profile** keyed by tax year + jurisdiction.

## Rules
- Low-confidence fields (< threshold) are flagged, never silently trusted.
- Every extracted figure is traceable to a source page (for downstream citations).
- PII minimized in prompts; respect zero-retention + data-residency settings.
- Deterministic validators check totals/cross-foots; the LLM does not do arithmetic of record.
