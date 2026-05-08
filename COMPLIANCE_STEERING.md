# Compliance Steering Module — Architecture Notes

## Overview

The Compliance Steering module extends Daleel from a legal document RAG platform
into a compliance operations platform.  It adds five new MongoDB collections on
top of the existing case-management layer (Sprint 7) and the requirement /
action / criticality pipeline (Sprints 2–4).

---

## Entity–Concept Mapping

| Collection                 | Compliance Concept         | Description                                                                 |
|---------------------------|---------------------------|-----------------------------------------------------------------------------|
| `compliance_assessments`  | **Gap analysis**          | A periodic or triggered evaluation of a company's compliance posture.       |
| `controls`                | **Control mapping**       | Internal controls a company implements to satisfy legal requirements.       |
| `control_evidences`       | **Evidence management**   | Proof artifacts demonstrating a control operates effectively.               |
| `requirement_control_links` | **Control mapping (join)** | Many-to-many link between exigences and controls, with coverage scoring.   |
| `exception_register`      | **Remediation tracking**  | Formal register of accepted risks, waivers, and deferred compliance items. |

---

## Collection Schemas

### 1. `compliance_assessments`

Represents a **gap analysis** exercise — either initial, periodic, or triggered
by a regulatory change (e.g. an amendment).

| Field                | Type       | Description                                             |
|---------------------|------------|---------------------------------------------------------|
| `id`                | str (uuid) | Primary key                                             |
| `company_profile_id`| str        | FK → `company_profiles`                                 |
| `title`             | str        | Human-readable label                                    |
| `description`       | str?       | Scope narrative                                         |
| `assessment_type`   | enum       | `initial` / `periodic` / `triggered`                    |
| `status`            | enum       | `draft` / `in_progress` / `completed` / `archived`      |
| `owner`             | str?       | Responsible person or team                               |
| `risk_level`        | enum       | `critical` / `high` / `medium` / `low`                  |
| `overall_coverage_score` | float | 0.0–1.0, computed from linked requirement coverage      |
| `review_frequency`  | enum       | `monthly` / `quarterly` / `semi_annual` / `annual`      |
| `due_date`          | datetime?  | Next review deadline                                    |
| `completed_at`      | datetime?  | When the assessment was completed                       |
| `created_by`        | str        | Actor who created the assessment                        |
| `created_at`        | datetime   | Auto                                                    |
| `updated_at`        | datetime   | Auto                                                    |

### 2. `controls`

Represents an **internal control** — a process, policy, or technical measure
that mitigates a compliance risk.

| Field                  | Type       | Description                                          |
|-----------------------|------------|------------------------------------------------------|
| `id`                  | str (uuid) | Primary key                                          |
| `company_profile_id`  | str        | FK → `company_profiles`                              |
| `title`               | str        | Control name                                         |
| `description`         | str        | What the control does                                |
| `control_type`        | enum       | `preventive` / `detective` / `corrective`            |
| `implementation_status`| enum      | `planned` / `in_progress` / `implemented` / `not_effective` |
| `owner`               | str?       | Responsible person or team                            |
| `risk_level`          | enum       | `critical` / `high` / `medium` / `low`               |
| `effectiveness_score` | float      | 0.0–1.0, self-assessed or audited                    |
| `review_frequency`    | enum       | `monthly` / `quarterly` / `semi_annual` / `annual`   |
| `last_reviewed_at`    | datetime?  | Last time this control was evaluated                 |
| `next_review_date`    | datetime?  | Scheduled next review                                |
| `created_at`          | datetime   | Auto                                                 |
| `updated_at`          | datetime   | Auto                                                 |

### 3. `control_evidences`

Evidence artifacts attached to a control — documents, certificates, logs, etc.

| Field            | Type       | Description                                           |
|-----------------|------------|-------------------------------------------------------|
| `id`            | str (uuid) | Primary key                                           |
| `control_id`    | str        | FK → `controls`                                       |
| `title`         | str        | Evidence label                                        |
| `description`   | str?       | What this evidence demonstrates                       |
| `evidence_type` | enum       | `document` / `screenshot` / `log` / `certificate` / `attestation` / `report` |
| `file_reference`| str?       | File path, URL, or external ref                       |
| `document_id`   | str?       | FK → `documents` (optional link)                      |
| `collected_by`  | str        | Who collected this evidence                           |
| `collected_at`  | datetime   | When the evidence was collected                       |
| `valid_from`    | datetime?  | Start of validity window                              |
| `valid_until`   | datetime?  | End of validity window                                |
| `status`        | enum       | `pending` / `accepted` / `rejected` / `expired`       |
| `review_notes`  | str?       | Reviewer comments                                     |
| `created_at`    | datetime   | Auto                                                  |
| `updated_at`    | datetime   | Auto                                                  |

### 4. `requirement_control_links`

Many-to-many join between **exigences** (legal requirements) and **controls**.
This is the heart of the control-mapping / gap-analysis computation.

| Field              | Type       | Description                                         |
|-------------------|------------|-----------------------------------------------------|
| `id`              | str (uuid) | Primary key                                         |
| `exigence_id`     | str        | FK → `exigences`                                    |
| `control_id`      | str        | FK → `controls`                                     |
| `assessment_id`   | str?       | FK → `compliance_assessments` (scoping)             |
| `coverage_status` | enum       | `not_covered` / `partially_covered` / `fully_covered` |
| `coverage_score`  | float      | 0.0–1.0                                             |
| `gap_description` | str?       | What is missing                                     |
| `justification`   | str?       | Why this mapping is considered adequate              |
| `linked_by`       | str        | Actor who created the link                          |
| `created_at`      | datetime   | Auto                                                |
| `updated_at`      | datetime   | Auto                                                |

**Unique constraint:** `(exigence_id, control_id, assessment_id)` — one link
per requirement–control pair per assessment.

### 5. `exception_register`

Tracks requirements that **cannot** be fully met — risk acceptances, waivers,
deferred remediation, or compensating controls.

| Field                   | Type       | Description                                      |
|------------------------|------------|--------------------------------------------------|
| `id`                   | str (uuid) | Primary key                                      |
| `exigence_id`          | str        | FK → `exigences`                                 |
| `company_profile_id`   | str        | FK → `company_profiles`                          |
| `control_id`           | str?       | FK → `controls` (if compensating)                |
| `title`                | str        | Exception label                                  |
| `description`          | str        | What the exception covers                        |
| `exception_type`       | enum       | `risk_acceptance` / `compensating_control` / `deferred` / `waiver` |
| `status`               | enum       | `requested` / `approved` / `rejected` / `expired` / `remediated` |
| `risk_level`           | enum       | `critical` / `high` / `medium` / `low`           |
| `justification`        | str        | Why the exception is acceptable                  |
| `approved_by`          | str?       | Who approved (if approved)                       |
| `approval_date`        | datetime?  | When approved                                    |
| `expiry_date`          | datetime?  | Exception validity end                           |
| `remediation_action_id`| str?       | FK → `actions` (linked remediation)              |
| `review_frequency`     | enum       | `monthly` / `quarterly` / `semi_annual` / `annual` |
| `created_at`           | datetime   | Auto                                             |
| `updated_at`           | datetime   | Auto                                             |

---

## Relationships to Existing Collections

```
company_profiles
  ├── compliance_assessments  (1:N)
  ├── controls                (1:N)
  └── exception_register      (1:N)

exigences
  ├── requirement_control_links (1:N)
  └── exception_register        (1:N)

controls
  ├── requirement_control_links (1:N)
  ├── control_evidences         (1:N)
  └── exception_register        (0..1)

compliance_assessments
  └── requirement_control_links (1:N, optional scoping)

actions
  └── exception_register.remediation_action_id (0..1)

documents
  └── control_evidences.document_id (0..1)
```

---

## API Routes (prefix: `/api/v1/compliance`)

### Assessments
- `POST   /assessments`                         — Create assessment
- `GET    /assessments`                          — List assessments (filter by company_profile_id, status)
- `GET    /assessments/{id}`                     — Get assessment detail
- `PATCH  /assessments/{id}`                     — Update assessment
- `GET    /assessments/{id}/posture`             — Compute coverage posture

### Controls
- `POST   /controls`                             — Create control
- `GET    /controls`                              — List controls (filter by company_profile_id, status)
- `GET    /controls/{id}`                         — Get control detail
- `PATCH  /controls/{id}`                         — Update control

### Evidences
- `POST   /controls/{control_id}/evidences`      — Attach evidence to control
- `GET    /controls/{control_id}/evidences`       — List evidences for a control
- `PATCH  /evidences/{id}`                        — Update evidence metadata

### Requirement–Control Links
- `POST   /links`                                 — Link requirement to control
- `GET    /links`                                  — List links (filter by exigence_id, control_id, assessment_id)
- `PATCH  /links/{id}`                             — Update link coverage
- `DELETE /links/{id}`                             — Remove link

### Gap Analysis
- `GET    /posture/{company_profile_id}`          — Full compliance posture for a company
- `GET    /gaps/{company_profile_id}`             — List uncovered / partially covered requirements

### Exceptions
- `POST   /exceptions`                            — Register exception
- `GET    /exceptions`                             — List exceptions (filter by company_profile_id, status)
- `PATCH  /exceptions/{id}`                        — Update exception (approve, reject, remediate)

### Remediation
- `POST   /remediation-actions`                   — Create a remediation action linked to a gap/exception

---

## Coverage / Gap Computation Algorithm

```
For a given company_profile_id:
  1. Fetch all applicable exigences (from exigence_applicabilities where is_applicable=true)
  2. For each exigence, find requirement_control_links
  3. Coverage status per exigence:
     - "fully_covered"    if ANY link has coverage_status == "fully_covered"
     - "partially_covered" if ANY link exists but none are "fully_covered"
     - "not_covered"      if NO links exist
     - "excepted"         if an approved exception exists
  4. overall_coverage_score = count(fully_covered + excepted) / total_applicable
  5. Gaps = exigences where status is "not_covered" or "partially_covered"
```

---

## Files Created / Modified

| File                                      | Action   |
|------------------------------------------|----------|
| `COMPLIANCE_STEERING.md`                 | Created  |
| `app/compliance_schemas.py`              | Modified (new schemas appended) |
| `app/services/compliance_service.py`     | Created  |
| `app/api/compliance_router.py`           | Created  |
| `app/database.py`                        | Modified (new indexes) |
| `app/main.py`                            | Modified (mount router) |
| `tests/test_compliance_service.py`       | Created  |
