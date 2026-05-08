# Compliance Case Orchestration — Architecture & Integration Guide

**Sprint 10**: Unified case workflow that transforms live cases into compliance findings and remediation items.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           COMPLIANCE CASE ORCHESTRATOR                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐              │
│  │  Case Facts     │    │  Document        │    │  Company        │              │
│  │  + Messages     │───▶│  Analysis        │    │  Profile        │              │
│  └─────────────────┘    └──────────────────┘    └─────────────────┘              │
│           │                       │                      │                       │
│           ▼                       ▼                      ▼                       │
│  ┌─────────────────────────────────────────────────────────────────┐            │
│  │                    ORCHESTRATION PIPELINE                        │            │
│  ├─────────────────────────────────────────────────────────────────┤            │
│  │                                                                 │            │
│  │  1. Context Gathering    ──▶ case_service, conversation_service │            │
│  │  2. Gap Analysis       ──▶ llm_service (LLM-powered)          │            │
│  │  3. Applicability Check ──▶ applicability_service                 │            │
│  │  4. Finding Generation  ──▶ llm_service + case_service          │            │
│  │  5. Criticality Scoring ──▶ criticality_service                 │            │
│  │  6. Action Proposal     ──▶ action_service + roadmap_service   │            │
│  │  7. Evidence Mapping  ──▶ case_document_service               │            │
│  │  8. Decision Engine     ──▶ Business rules (see below)          │            │
│  │                                                                 │            │
│  └─────────────────────────────────────────────────────────────────┘            │
│                                    │                                             │
│           ┌────────────────────────┼────────────────────────┐                    │
│           ▼                        ▼                        ▼                    │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐              │
│  │   ASK       │          │    ACT      │          │   REVIEW    │              │
│  │(clarify)    │          │ (execute)   │          │ (escalate)  │              │
│  └─────────────┘          └─────────────┘          └─────────────┘              │
│                                                                                 │
│  Outputs:                                                                       │
│  • CaseFindings (legal/regulatory non-compliance)                              │
│  • CaseActions (remediation tasks)                                             │
│  • Controls (preventive/detective/corrective)                                   │
│  • EvidenceRequirements (audit trail)                                         │
│  • RiskAssessment (confidence + risk level)                                     │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Decision Flow

The orchestrator makes decisions based on these rules:

### Decision Triggers

| Decision | Condition | Action |
|----------|-----------|--------|
| **ASK** | `facts_missing > 2` OR `confidence < 0.6` with limited facts | Return clarification question |
| **CLARIFY** | Document contradictions detected | Flag for contradiction resolution |
| **ACT** | `confidence >= 0.7` AND sufficient facts | Generate findings + actions |
| **REVIEW** | Critical findings with `confidence < 0.75` OR `confidence < 0.6` overall | Escalate to human expert |

### Decision Flowchart

```
┌─────────────────┐
│  Start Analysis │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Gather Context  │
│ • Facts         │
│ • Documents     │
│ • Profile       │
└────────┬────────┘
         ▼
┌─────────────────┐     Yes     ┌─────────────────┐
│ facts_missing   │────────────▶│      ASK        │
│   > 2 ?         │             │ (More info      │
└────────┬────────┘             │  needed)        │
         │ No                   └─────────────────┘
         ▼
┌─────────────────┐     Yes     ┌─────────────────┐
│ Document        │────────────▶│    CLARIFY      │
│ contradictions? │             │ (Resolve        │
└────────┬────────┘             │  conflicts)     │
         │ No                   └─────────────────┘
         ▼
┌─────────────────┐     Yes     ┌─────────────────┐
│ confidence      │────────────▶│     REVIEW      │
│   < 0.6 ?       │             │ (Human expert   │
└────────┬────────┘             │  needed)         │
         │ No                   └─────────────────┘
         ▼
┌─────────────────┐     Yes     ┌─────────────────┐
│ Critical + low    │────────────▶│     REVIEW      │
│ confidence?       │             │ (Validate       │
└────────┬────────┘             │  critical)      │
         │ No                   └─────────────────┘
         ▼
┌─────────────────┐
│      ACT        │
│ • Findings      │
│ • Actions       │
│ • Controls      │
│ • Evidence map  │
└─────────────────┘
```

---

## Service Integration Matrix

| Orchestrator Function | Service | Purpose |
|----------------------|---------|---------|
| `_gather_case_context()` | `case_service` | Read case metadata |
| `_gather_case_context()` | `case_conversation_service` | Load conversation context |
| `_gather_case_context()` | `case_document_service` | Get document analyses |
| `_evaluate_applicability()` | `applicability_service` | Determine applicable exigences |
| `_perform_gap_analysis()` | `llm_service.call_ollama()` | LLM-powered gap analysis |
| `_generate_remediation_actions()` | `action_service` | Get existing actions for exigences |
| `_propose_controls()` | `llm_service` | Control design |
| `_map_evidences()` | `llm_service` | Evidence mapping |
| `_persist_findings()` | `case_service` | Create case_findings |
| `_persist_actions()` | `case_service` | Create case_actions |
| (internal) | `criticality_service` | Score action criticality |
| (internal) | `roadmap_service` | Prioritize actions |
| `analyze_and_orchestrate()` | `audit_service` | Log orchestration events |

---

## API Endpoints

### Run Orchestration Analysis

```http
POST /api/v1/cases/{case_id}/orchestrate
Authorization: Bearer {api_key}
Content-Type: application/json

{
  "auto_create_findings": false,
  "auto_create_actions": false
}
```

**Response:**

```json
{
  "case_id": "case-001",
  "decision": "act",
  "decision_reason": "Analysis complete with 2 findings identified",
  "proposed_findings": [
    {
      "title": "Violation: 15 employés sans contrat écrit",
      "description": "Les employés travaillent sans contrat signé, violation Art. 6",
      "severity": "major",
      "confidence": 0.92,
      "exigence_id": "exig-001"
    }
  ],
  "findings_created": [],
  "proposed_actions": [
    {
      "title": "Rédiger et signer les contrats pour 15 employés",
      "description": "Préparer les contrats conformément au modèle type",
      "priority": "high",
      "due_date": "2024-02-15T00:00:00Z"
    }
  ],
  "controls_proposed": [
    {
      "control_type": "preventive",
      "title": "Processus de signature systématique",
      "description": "Signature obligatoire avant prise de poste",
      "frequency": "continuous",
      "automation": "semi_automated",
      "owner_role": "DRH",
      "evidence_type": "Contrat signé scanné"
    }
  ],
  "evidences_required": [
    {
      "evidence_type": "document",
      "description": "Contrats de travail signés",
      "status": "missing",
      "acquisition_steps": ["Rédiger les contrats", "Organiser séance de signature"]
    }
  ],
  "confidence_assessment": {
    "overall": 0.88,
    "level": "high",
    "evidence_sufficiency": "sufficient"
  },
  "risk_level": "high",
  "next_steps": [
    "Review 2 identified findings",
    "Prioritize 3 remediation actions",
    "Assign actions to responsible parties",
    "Schedule follow-up assessment"
  ]
}
```

### Check Orchestration Status

```http
GET /api/v1/cases/{case_id}/orchestrate/status
```

**Response:**

```json
{
  "case_id": "case-001",
  "status": "in_progress",
  "ready_for_orchestration": true,
  "facts_known_count": 4,
  "facts_missing_count": 1,
  "findings_count": 0,
  "actions_count": 0,
  "orchestration_recommendation": "ready"
}
```

### Quick Assessment

```http
GET /api/v1/cases/{case_id}/orchestrate/assess
```

**Response:**

```json
{
  "case_id": "case-001",
  "readiness_score": 0.85,
  "readiness_level": "ready",
  "factors": {
    "facts_sufficiency": 0.8,
    "document_support": 1.0
  },
  "suggestions": [null, null],
  "estimated_analysis_quality": "high"
}
```

### Suggest Next Questions

```http
GET /api/v1/cases/{case_id}/orchestrate/questions?count=3
```

**Response:**

```json
{
  "case_id": "case-001",
  "questions": [
    "Pouvez-vous préciser : Nombre d'employés?",
    "Pouvez-vous préciser : Secteur d'activité?",
    "Pouvez-vous préciser : Chiffre d'affaires?"
  ]
}
```

---

## Data Flow Example

### Scenario: Labour Compliance Case

```
User Input:
"Je suis une SARL à Tunis avec 15 employés. Certains travaillent 
sans contrat écrit. Que dois-je faire?"

↓ Conversation Processing (case_conversation_service)

Extracted Context:
• facts_known: ["SARL", "Tunis", "15 employés", "sans contrat écrit"]
• facts_missing: ["Durée d'emploi", "Secteur", "Règlement intérieur"]
• matter_type: "labour_compliance"
• urgency: "high"
• article_references: ["Art. 6 du Code du Travail"]

↓ User attaches employment documents

Document Analysis (case_document_service):
• Document 1: Contrat type (analysis: contrat conforme)
• Document 2: Liste des employés (analysis: 15 employés confirmés,
                                  12 sans contrat)

↓ Orchestration Triggered

Gap Analysis (LLM-powered):
• Gap 1: 12 employés sans contrat → VIOLATION Art. 6
• Gap 2: Aucun règlement intérieur → MISSING DOCUMENT
• Confidence: 0.90

Decision: ACT (confidence sufficient, clear violations)

↓ Finding Generation

Case Finding Created:
• ID: finding-001
• Title: "Violation: 12 employés sans contrat écrit"
• Severity: major
• Exigence: Art. 6 du Code du Travail
• Evidence refs: ["doc-002"]

↓ Action Generation

Case Action Created:
• ID: action-001
• Finding ID: finding-001
• Title: "Rédiger et faire signer 12 contrats de travail"
• Priority: high
• Due date: 2024-02-15 (30 days)

↓ Control Proposal

Proposed Control:
• Type: preventive
• Title: "Processus signature contrats"
• Owner: DRH
• Frequency: continuous

↓ Evidence Mapping

Required Evidence:
• Type: document
• Description: "12 contrats signés"
• Status: missing
• Steps: ["Rédiger", "Signer", "Archiver"]

↓ Result to User

System Response:
"J'ai identifié 2 non-conformités majeures:
1. 12 employés sans contrat (Art. 6) — risque amende
2. Règlement intérieur manquant (Art. 14)

J'ai créé 3 actions de remediation prioritaires.
Confiance dans l'analyse: 90%"
```

---

## Integration with Existing Sprint Features

### Sprint 7: Case Management
The orchestrator extends the case management module by:
- Populating `case_findings` collection automatically
- Creating `case_actions` linked to findings
- Leveraging `case_documents` analysis for evidence
- Using `case_messages` context for fact extraction

### Sprint 8: Compliance Steering
The orchestrator integrates with compliance steering:
- `compliance_assessments` — orchestrator findings feed into assessments
- `controls` — proposed controls can be promoted to formal controls
- `control_evidences` — evidence mapping aligns with evidence requirements

### Sprint 9: Conversation Workflow
The orchestrator works with the conversation system:
- Consumes `conversation_context` for case facts
- Provides `clarification_question` when more info needed
- Uses `build_case_context_for_rag()` for grounded analysis

---

## Configuration

### Thresholds (configurable in code)

```python
# Minimum facts needed to proceed with analysis
MIN_FACTS_FOR_ANALYSIS = 3

# Maximum missing facts before asking for clarification
MAX_MISSING_FACTS_TOLERANCE = 2

# Minimum confidence for automatic action generation
MIN_CONFIDENCE_FOR_AUTO_ACT = 0.70

# Minimum confidence to create a finding
MIN_CONFIDENCE_FOR_FINDING = 0.60
```

### LLM Prompts

All LLM prompts are defined as module-level constants:

- `_GAP_ANALYSIS_PROMPT` — Legal gap identification
- `_CONTROL_PROPOSAL_PROMPT` — Control design
- `_EVIDENCE_MAPPING_PROMPT` — Evidence requirement mapping
- `_CLARIFICATION_QUESTION_PROMPT` — Question generation

---

## Audit Trail

Every orchestration run is logged to the audit log:

```json
{
  "event_type": "case_orchestrated",
  "actor": "system",
  "details": {
    "case_id": "case-001",
    "decision": "act",
    "findings_created": 2,
    "actions_created": 3,
    "confidence": 0.88
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Testing

Run the test suite:

```bash
cd c:\Users\RSCH\Daleel
python -m pytest tests/test_compliance_case_orchestrator.py -v
```

Test scenarios covered:
1. ✅ Sufficient info → findings + actions created
2. ✅ Missing info → clarification requested
3. ✅ Document evidence → richer output
4. ✅ Low confidence → human review recommended
5. ✅ Document contradictions → clarify decision

---

## Future Enhancements

1. **Batch Orchestration** — Process multiple cases simultaneously
2. **Learning Loop** — Use past corrections to improve future analysis
3. **Template Library** — Pre-defined control templates by domain
4. **Timeline Prediction** — ML-based remediation timeline estimates
5. **Integration with External Systems** — Export to GRC platforms
