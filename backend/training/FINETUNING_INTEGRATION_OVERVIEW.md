# LLM Fine-Tuning Integration for Daleel Platform

This document outlines the two specialized fine-tuning tracks integrated into the Daleel RAG platform. The goal is to enhance system performance (formatting, routing, and extraction) without disrupting the existing deterministic pipelines. Both tracks use a "Fail-Safe / Passthrough" design: if the fine-tuned models are unavailable or their confidence is low, the system gracefully falls back to existing LLM/lexical logic.

---

## Track 1: Response Style & Format Fine-Tuning

**Objective:** Stabilize the final output of the Legal Advisor into a strict 7-section Markdown format (What I understood, Missing info, Legal context, Analysis, Actions, Evidence, Human review) while preserving semantic fidelity.

*   **Training Strategy:** LoRA / PEFT fine-tuning on a small, fast model (e.g., Qwen2.5-1.5B or Mistral-7B). 
*   **Dataset:** Built via `training/style_dataset_builder.py` which aggregates real orchestrated cases from the DB and curates them into consistent JSONL examples.
*   **Runtime Integration:** 
    *   **Service:** `app/services/llm_style_formatter.py` wraps the Ollama call to the fine-tuned model (`DALEEL_STYLE_MODEL`).
    *   **Orchestrator:** `app/services/advisor_response_composer.py` calls the formatter during the `_refine_with_llm` step. It passes the raw drafted markdown and structured extraction payloads.
    *   **Fallback:** If the style model returns an error or empty text, the system uses the raw draft generated deterministically.
*   **Guardrails:** The outputs are passed through `quality_guard_service.py` to ensure the style model doesn't hallucinate non-existent articles or inject incorrect foreign languages.

---

## Track 2: Reasoning / Classification & Extraction Fine-Tuning

**Objective:** Enhance domain routing, intent triage, risk assessment, and fact extraction using a multi-task classification head or a small JSON-only instruction LLM.

*   **Training Strategy:** Fine-tune an XLM-RoBERTa-base classifier with multiple heads (Domain, Case Type, Risk) and extract key facts. This is extremely fast (<50ms CPU inference).
*   **Dataset:** Built via `training/reasoning_dataset_builder.py` which mines existing cases, priorities, and conversation contexts.
*   **Runtime Integration:** 
    *   **Service:** `app/services/reasoning_model_service.py` lazily loads the PyTorch model or Ollama endpoint. It provides methods like `classify_domain`, `classify_case_type`, `classify_risk`, and `extract_facts`.
    *   **Routing (`domain_router.py`):** Before performing lexical scoring, the router queries the reasoning model. If confidence ≥ threshold (e.g., 0.70), it routes immediately, skipping the expensive LLM fallback.
    *   **Extraction (`case_conversation_service.py`):** The context extraction combines the reasoning model's facts (parties, dates, amounts) and case type with the standard extraction JSON to provide highly accurate `conversation_context`.
    *   **Orchestration (`compliance_case_orchestrator.py`):** During gap analysis, `_assess_risk_level` queries the reasoning model on the known facts to intelligently label the case risk level, rather than just relying on generic severity mappings.

---

## Code Base Updates

The following files were extended to seamlessly integrate the fine-tuned models:
1.  **`app/config.py`**: Added configuration for model paths, URLs, enable toggles, and confidence thresholds.
2.  **`app/services/llm_style_formatter.py`**: Created/verified the style model facade.
3.  **`app/services/reasoning_model_service.py`**: Created/verified the reasoning and extraction model facade.
4.  **`app/services/advisor_response_composer.py`**: Intercepted `_refine_with_llm` to pass data to the style formatter.
5.  **`app/services/domain_router.py`**: Integrated `reasoning_model_service.classify_domain`.
6.  **`app/services/case_conversation_service.py`**: Intercepted extraction to merge facts from `reasoning_model_service.extract_facts`.
7.  **`app/services/compliance_case_orchestrator.py`**: Updated `_assess_risk_level` to use `reasoning_model_service.classify_risk`.
