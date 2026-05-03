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

## Current Progress
* **Layer 1: Document Ingestion & Classification**: Supporting PDF, DOCX, and Images with heuristic classification.
* **Layer 2: Functional OCR**: Integrated `pdfplumber` and `pytesseract` with image preprocessing.
* **Layer 3: NLP & Criteria Extraction**: 3-Pass pipeline using Gemini LLM and spaCy entity extraction.
* **Layer 4: Evaluation Engine**: Rule-based matching (Financial/Compliance) with confidence scoring.
* **Layer 5: Production HITL**: Implementation of `/review-items` and `/review` workflows with expert decision state.
* **Layer 6: Audit Trail**: Centralized, append-only logging of all system actions and manual corrections.
* **Master Pipeline**: Fully automated asynchronous orchestration of the entire flow.
* **Security & Auth**: JWT-based authentication and role-based access control.
* **Deployment**: Dockerized system with relational database persistence.
* **Validation**: Comprehensive test suite in `/tests` covering end-to-end scenarios.

### Review Workflow (HITL)
- **Automatic Trigger**: Any evaluation criterion with a **Confidence Score < 0.85** is automatically flagged for manual review.
- **Review Queue**: The `/api/v1/hitl/review-items` endpoint lists all documents that have been processed but not yet finalized by an expert.
- **Expert Decision**: Experts use `/api/v1/hitl/review` to submit a final decision (`ELIGIBLE`/`NOT_ELIGIBLE`) and a justifying reason.
- **State Transition**: Upon submission, the document status moves from `processed` to `completed`, and the AI verdicts are archived as the "original evaluation".

### Audit System
- **Append-Only JSON Log**: Every significant system event and reviewer action is captured in an append-only JSON file (`data/audit/audit_trail.json`) and the `audit_logs` database table.
- **Audit Schema**: Every log entry includes:
    - `timestamp`: UTC ISO-8601 timestamp.
    - `action`: High-level event identifier (e.g., `BIDDER_EVALUATED`, `HITL_REVIEW`).
    - `user`: The actor responsible for the change (system engine or expert user ID).
    - `changes`: A structured payload detailing what was modified or calculated.
- **Accountability**: This ensures a complete and immutable chronological history of every document's lifecycle, satisfying regulatory and transparency requirements.

### Reporting System
- **Unified Intelligence**: The `/api/v1/reporting/report/{id}` endpoint aggregates:
    - **Tender Benchmarks**: The rules extracted from the parent tender.
    - **AI Verdicts**: The automated scores and findings.
    - **Evidence Chains**: Human-readable strings linking scores to specific document pages.
    - **Expert Review**: The final decision and reasoning provided by the HITL expert.
- **Multi-Format Export**:
    - **JSON**: Comprehensive raw data for system integration and dashboards.
    - **PDF**: A simple, formatted evaluation report suitable for offline review and archiving, available via `/api/v1/reporting/report/{id}/pdf`.
- **Vendor Analytics**: Support for multi-bidder comparison matrices and ranking based on eligibility scores.

### Testing Coverage
- **Unit Tests**: Coverage for API health, authentication, and ingestion logic in `tests/test_main.py` and `tests/test_ingestion.py`.
- **End-to-End Integration Tests**: Comprehensive validation in `tests/test_end_to_end.py`.
- **Validation Scenarios**:
    - **Criteria Extraction**: Verified by uploading a real PDF tender and ensuring rules are structured correctly.
    - **Evaluation Engine**: Verified by matching bidder evidence against extracted criteria.
    - **Explainability**: Verified by checking the presence and format of human-readable evidence chains.
- **Environment**: All tests run against an isolated SQLite database with automatic teardown.

### Known Bugs & Limitations
- Multi-page scanned PDFs require additional dependencies (Poppler/pdf2image)
- Fuzzy deduplication may merge similar clauses
- Numerical parsing may miss non-standard currency formats
- Performance bottleneck due to JSON persistence

## Critical Fixes Applied
- **Comparator Logic Fix**: The Evaluation Engine now correctly supports and respects criteria comparators (`>=`, `<=`, `==`, `>`, `<`) for financial checks, removing the previous hardcoded `>=` limitation.
- **Robust Failure Handling**: Pipelines now automatically transition document status to `failed` upon any internal exception, ensuring consistent database state and recording the error details in the Audit Log.
- **Sync Pipeline Support**: Added a `run_sync` parameter to the process API, enabling deterministic execution for demos and critical evaluation cycles, bypassing background task delays.
- **LLM Mock Fallback**: Implemented a deterministic criteria extractor that activates when a Gemini API key is missing. This ensures that test suites and offline demos remain functional with predefined benchmarks.
- **Evidence Chain Standard**: Enforced the strict `"Criterion → Extracted Value (Page X) → RESULT"` format for all evidence chains, ensuring high-fidelity transparency for procurement auditors.

## Technical Audit Summary
- Status: READY FOR DEMO / NOT READY FOR PRODUCTION

- Remaining Limitations:
  1. Performance bottleneck due to JSON persistence (non-critical for demo)
  2. Minor OCR limitations for multi-page scanned PDFs
  3. Fuzzy deduplication may merge similar clauses

- No critical blocking issues remain for demo or evaluation phase

## Progress Log
* **2026-05-03**: Final refinement of HITL, Audit, and Reporting layers. Implemented end-to-end test suite and achieved architecture-complete status.
