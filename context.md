# TenderAI - Context

## Project Goal
TenderAI is a production-grade AI system designed for end-to-end tender evaluation. It automates the process of analyzing complex tender documents, extracting key requirements, and evaluating vendor responses with a focus on explainability and an evidence chain.

## Architecture Summary
The system follows a 6-layer architecture:
1. **Ingestion Layer**: Handles multi-format document uploads and metadata management.
2. **OCR Layer**: Converts scanned PDF/images into structured, searchable text.
3. **NLP Layer**: Performs Named Entity Recognition and 3-Pass Criteria Extraction.
4. **Evaluation Layer**: Matches bidder evidence against tender criteria using a rule-based engine.
5. **Human-in-the-loop (HITL) Layer**: Allows experts to review, correct, and finalize AI decisions.
6. **Audit Layer**: Logs every action for complete compliance, transparency, and explainability.

## Current Progress (Post-Commit Stability Improvements)
* **Professional Evaluation Portal**: Implemented a modern, interactive web interface at `/` for document ingestion and real-time evaluation.
* **Deterministic Demo Support**: Added `run_sync=true` to process APIs, enabling immediate feedback loops for live presentations.
* **Absolute Failsafe PDF Method**: Overhauled the reporting layer to use basic stream-based text writing (`pdf.write`). This eliminates all "horizontal space" and layout-related crashes in the `fpdf2` engine, ensuring reliable report generation for any input.
* **Binary PDF Streaming**: Completely overhauled the reporting layer to serve PDFs as direct binary streams, eliminating corruption issues caused by file-system locks.
* **Rigorous Text Sanitization**: Implemented a Latin-1 enforced sanitizer to ensure PDF compatibility across all document types.
* **Backend Stabilization**: Resolved critical `NameError` and `Regex` bugs in the core evaluation and pipeline services.
* **LLM Intelligence Mock**: Integrated a deterministic fallback for LLM extraction, ensuring demo stability even without active API keys.

### Review Workflow (HITL)
- **Automatic Trigger**: Any evaluation criterion with a **Confidence Score < 0.85** is automatically flagged for manual review.
- **Expert Decision**: Experts use the API or UI to submit final verdicts (`ELIGIBLE`/`NOT_ELIGIBLE`).

### Audit & Reporting
- **Audit Schema**: Every log entry includes timestamp, action, user, and modifications.
- **Evidence Chains**: High-fidelity strings linking AI scores to specific document evidence: `"Criterion -> Extracted Value (Page X) -> RESULT"`.
- **Multi-Format Export**: Supports comprehensive JSON data and professional PDF evaluation summaries.

## Critical Fixes Applied (Stability Phase)
- **Definitive PDF Stability Fix**: Resolved persistent PDF layout errors by switching to a stream-based text rendering system. Enforced Latin-1 encoding and replaced Unicode arrows ("→") with ASCII ("->") to prevent rendering crashes.
- **Backend NameError Fixes**: Resolved missing imports for `Session` and `DBDocument` in the pipeline and engine services.
- **Regex Logic Correction**: Fixed `re.error` by correctly placing flags in `re.finditer` and `re.split` calls.
- **Comparator Logic Fix**: Enabled full support for mathematical comparators (`>=`, `<=`, `==`, etc.) in the financial evaluation engine.

## Technical Audit Summary
- Status: **STABLE / READY FOR HACKATHON DEMO**
- UI Endpoint: `http://localhost:8000/`
- API Specs: `http://localhost:8000/docs`

## Progress Log
* **2026-05-04**: Final stabilization. Implemented Professional Evaluation Portal. Fixed PDF corruption and backend NameErrors. Achieved Demo-Ready status.
* **2026-05-03**: Architecture completion of HITL, Audit, and Reporting layers.
