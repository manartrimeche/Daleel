# Changelog

All notable changes to the Daleel project are documented in this file.

## [1.0.0] — 2026-05-03

### Sprint 10 — Structured Legal Compliance Response Composer
- Added `advisor_response_composer.py` — 8-section structured legal response
  (`what_i_understood`, `what_is_missing`, `legal_basis`, `compliance_risks`,
  `recommended_actions`, `required_evidence`, `confidence_assessment`,
  `human_review_recommendation`)
- Added `POST /cases/{id}/orchestrate/advise` endpoint
- Markdown rendering + Pydantic validation via `AdvisorResponseOut`
- 33 async unit tests

### Sprint 9 — Case-Centered Conversational Workflow
- Added `case_conversation_service.py` — progressive fact-gathering for compliance cases
- Added `POST /cases/{id}/conversation` + `POST /cases/{id}/conversation/answer`
- LLM-powered question generation based on case state and missing facts
- Schema updates in `case_schemas.py`

### Sprint 8 — Compliance Steering Module
- 5 new MongoDB collections:
  `compliance_assessments`, `controls`, `control_evidences`,
  `requirement_control_links`, `exception_register`
- Added `compliance_service.py` + `compliance_router.py` + `compliance_schemas.py`
- Assessment lifecycle, control mapping, exception register
- Full test suite (`test_compliance_service.py`)
- Added `COMPLIANCE_STEERING.md` documentation

### Sprint 7 — Compliance Case Management
- 5 new MongoDB collections:
  `compliance_cases`, `case_messages`, `case_documents`,
  `case_findings`, `case_actions`
- Added `case_service.py` + `case_router.py` + `case_schemas.py`
- Case CRUD, document attachment, finding/action tracking
- Full test suite (`test_case_service.py`)

### Sprint 6 — Domain-Aware RAG & Quality Guard
- **Domain Router**: lexical + LLM routing to 5 legal domains
  (data_protection, labor, corporate, investment, credit_info)
- **Quality Guard**: reference fidelity + semantic fidelity + language compliance
  + conservative rewrite on failure
- **KG Light Enrichment**: `Loi → Article → Exigence → Action` graph context injection
- **Partitioned Retrieval**: separates base-law from amendment retrieval
- Admin stats + vector stats endpoints
- Full test coverage for router, retrieval orchestrator, graph resolver

### Sprint 5 — Amendments & Audit Logs
- Document amendment classification (ADD / REPLACE / MODIFY / REPEAL)
- Immutable versioning for article amendments
- Audit logging collection (`audit_logs`)
- Auto-recalculation pipeline on amendment application
- Amendment impact notifications for company profiles

### Sprint 4 — Criticality Scoring & Compliance Roadmap
- Rule-based action criticality scoring
- Action dependency graph with topological sort
- Compliance roadmap generation from profile + applicable exigences

### Sprint 3 — Lois, Articles & Segmentation
- Loi / Article / ArticleVersion hierarchy
- Document segmentation into article-level units
- Action extraction from articles
- `lois`, `articles`, `article_versions`, `actions`, `action_criticalities`,
  `action_dependencies` collections

### Sprint 2 — Company Profiles & Applicability
- Company profile creation with sector/size/jurisdiction
- LLM-powered applicability evaluation
- `company_profiles`, `exigence_applicabilities` collections

### Sprint 1 — Core RAG Pipeline
- Document upload (PDF, DOCX, TXT, images)
- 3-tier extraction: PyMuPDF → pdfminer → OCR (Tesseract + EasyOCR)
- Smart chunking (section-aware + sliding window 1500/200)
- Embedding generation (768-d multilingual)
- FAISS in-memory vector search + Python cosine fallback
- RAG Q&A: classic mode, agentic mode, auto-mode routing
- User feedback learning (stored corrections injected as few-shot examples)
- Streaming SSE responses
- 3-language support (Arabic / French / English)
