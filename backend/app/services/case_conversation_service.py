"""
Case Conversation Service — progressive fact-gathering workflow.

Orchestrates compliance case creation and conversation management.
Each user message triggers:
  1. Message persistence (via case_service)
  2. LLM-based context extraction (facts, matter type, urgency)
  3. Generation of the next clarification question
  4. Assistant message persistence

The extracted context is stored on the compliance_cases document
in a ``conversation_context`` sub-document so it survives across turns.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

from app.config import get_settings
from app.database import get_collection
from app.services import audit_service, case_service
from app.services.llm_service import call_ollama, _detect_query_language

logger = logging.getLogger(__name__)
_collection = get_collection


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ─────────────────────────────────────────────────────────────
# LLM prompts for structured extraction
# ─────────────────────────────────────────────────────────────

_EXTRACTION_SYSTEM_PROMPT = {
    "fr": """Vous êtes un assistant juridique de conformité tunisien, structuré et conservateur.
Votre rôle est d'analyser la conversation entre un utilisateur et l'assistant pour extraire des informations structurées sur le dossier de conformité, dans le cadre du droit tunisien (Code du Travail, Code des Sociétés Commerciales, Code des Obligations et des Contrats, etc.).

Vous devez répondre UNIQUEMENT avec un objet JSON valide (sans texte supplémentaire, sans blocs markdown) ayant exactement cette structure :
{
  "title": "Titre court et descriptif du dossier (max 120 caractères)",
  "facts_known": ["fait 1", "fait 2", ...],
  "facts_missing": ["information manquante 1", "information manquante 2", ...],
  "matter_type": "un parmi: labour_compliance, corporate_formation, corporate_governance, contract_dispute, regulatory_compliance, tax_compliance, intellectual_property, data_protection, other",
  "urgency": "un parmi: critical, high, medium, low, unknown",
  "article_references": ["Art. 14 du Code du Travail", ...],
  "next_question": "La prochaine question de clarification la plus importante à poser"
}

Règles :
- Soyez conservateur : ne déduisez que les faits explicitement mentionnés par l'utilisateur.
- Les faits connus doivent couvrir : le type d'entité (SARL, SA, etc.), le secteur d'activité, le nombre d'employés, la localisation, les dates pertinentes, les parties impliquées.
- Les faits manquants doivent être ceux nécessaires pour une analyse juridique complète selon le droit tunisien.
- Les références d'articles doivent mentionner le code source (ex: "Art. 14 du Code du Travail").
- La question suivante doit être précise et ciblée, formulée de manière professionnelle.
- Ne posez qu'UNE SEULE question à la fois.
- L'urgence doit refléter : critical = risque pénal imminent, high = délai légal proche, medium = situation à traiter, low = question informative.
- Répondez en français pour les valeurs textuelles du JSON.

Exemple de sortie attendue :
{
  "title": "Non-conformité contrats de travail — SARL Tunis",
  "facts_known": ["L'entreprise est une SARL basée à Tunis", "3 employés travaillent sans contrat écrit", "L'entreprise opère dans le secteur textile"],
  "facts_missing": ["Durée d'emploi des salariés sans contrat", "Existence d'un règlement intérieur", "Nombre total de salariés"],
  "matter_type": "labour_compliance",
  "urgency": "high",
  "article_references": ["Art. 6 du Code du Travail"],
  "next_question": "Depuis combien de temps ces employés travaillent-ils dans votre entreprise sans contrat signé ?"
}""",

    "ar": """أنت مساعد قانوني تونسي للامتثال، منظم ومحافظ.
دورك هو تحليل المحادثة بين المستخدم والمساعد لاستخراج معلومات منظمة حول ملف الامتثال، في إطار القانون التونسي (مجلة الشغل، مجلة الشركات التجارية، مجلة الالتزامات والعقود، إلخ).

يجب أن تجيب فقط بكائن JSON صالح (بدون نص إضافي، بدون كتل markdown) بهذا الشكل بالضبط:
{
  "title": "عنوان قصير ووصفي للملف (أقصى 120 حرف)",
  "facts_known": ["حقيقة 1", "حقيقة 2", ...],
  "facts_missing": ["معلومة ناقصة 1", "معلومة ناقصة 2", ...],
  "matter_type": "واحد من: labour_compliance, corporate_formation, corporate_governance, contract_dispute, regulatory_compliance, tax_compliance, intellectual_property, data_protection, other",
  "urgency": "واحد من: critical, high, medium, low, unknown",
  "article_references": ["الفصل 14 من مجلة الشغل", ...],
  "next_question": "السؤال التوضيحي التالي الأهم الذي يجب طرحه"
}

القواعد:
- كن محافظاً: استنتج فقط الحقائق المذكورة صراحة من قبل المستخدم.
- الحقائق المعروفة يجب أن تشمل: نوع الكيان (شركة ذات مسؤولية محدودة، شركة خفية الاسم، إلخ)، القطاع، عدد الموظفين، الموقع، التواريخ، الأطراف المعنية.
- المعلومات الناقصة يجب أن تكون تلك اللازمة لتحليل قانوني شامل وفق القانون التونسي.
- مراجع الفصول يجب أن تذكر المصدر (مثال: "الفصل 6 من مجلة الشغل").
- السؤال التالي يجب أن يكون دقيقاً ومركزاً، بأسلوب مهني.
- اطرح سؤالاً واحداً فقط في كل مرة.
- الاستعجال: critical = خطر جزائي وشيك، high = أجل قانوني قريب، medium = وضع يتطلب معالجة، low = سؤال استعلامي.
- اكتب القيم النصية في JSON بالعربية.""",

    "en": """You are a structured, conservative Tunisian legal compliance assistant.
Your role is to analyse the conversation between a user and the assistant to extract structured information about the compliance case, within the framework of Tunisian law (Labour Code, Commercial Companies Code, Code of Obligations and Contracts, etc.).

You must respond ONLY with a valid JSON object (no extra text, no markdown blocks) with exactly this structure:
{
  "title": "Short descriptive case title (max 120 chars)",
  "facts_known": ["fact 1", "fact 2", ...],
  "facts_missing": ["missing info 1", "missing info 2", ...],
  "matter_type": "one of: labour_compliance, corporate_formation, corporate_governance, contract_dispute, regulatory_compliance, tax_compliance, intellectual_property, data_protection, other",
  "urgency": "one of: critical, high, medium, low, unknown",
  "article_references": ["Art. 14 of the Labour Code", ...],
  "next_question": "The single most important clarification question to ask next"
}

Rules:
- Be conservative: only infer facts explicitly stated by the user.
- Known facts should cover: entity type (SARL, SA, etc.), industry sector, employee count, location, relevant dates, parties involved.
- Missing facts should be those needed for a complete legal analysis under Tunisian law.
- Article references must mention the source code (e.g. "Art. 6 of the Labour Code").
- The next question must be precise and targeted, worded professionally.
- Ask only ONE question at a time.
- Urgency: critical = imminent criminal risk, high = approaching legal deadline, medium = situation requiring attention, low = informational query.

Example output:
{
  "title": "Employment contract non-compliance — SARL Tunis",
  "facts_known": ["The company is a SARL based in Tunis", "3 employees work without written contracts", "The company operates in the textile sector"],
  "facts_missing": ["Duration of employment for workers without contracts", "Existence of internal regulations", "Total number of employees"],
  "matter_type": "labour_compliance",
  "urgency": "high",
  "article_references": ["Art. 6 of the Labour Code"],
  "next_question": "How long have these employees been working at your company without a signed contract?"
}""",
}


_VALID_MATTER_TYPES = {
    "labour_compliance", "corporate_formation", "corporate_governance",
    "contract_dispute", "regulatory_compliance", "tax_compliance",
    "intellectual_property", "data_protection", "other",
}

_VALID_URGENCY = {"critical", "high", "medium", "low", "unknown"}


# ─────────────────────────────────────────────────────────────
# LLM context extraction
# ─────────────────────────────────────────────────────────────

def _build_extraction_messages(
    conversation: list[dict],
    detected_lang: str,
) -> list[dict]:
    """Build the LLM message list for context extraction."""
    system = _EXTRACTION_SYSTEM_PROMPT.get(
        detected_lang, _EXTRACTION_SYSTEM_PROMPT["en"]
    )
    messages: list[dict] = [{"role": "system", "content": system}]

    # Inject conversation history as a single user message for analysis
    conv_lines: list[str] = []
    for msg in conversation:
        role_label = msg.get("role", "user").upper()
        content = msg.get("content", "")
        conv_lines.append(f"[{role_label}]: {content}")

    conv_block = "\n\n".join(conv_lines)

    instruction = {
        "fr": "Analysez la conversation suivante et extrayez les informations structurées du dossier. Répondez UNIQUEMENT en JSON.",
        "ar": "حلّل المحادثة التالية واستخرج المعلومات المنظمة للملف. أجب فقط بصيغة JSON.",
        "en": "Analyse the following conversation and extract structured case information. Respond ONLY with JSON.",
    }.get(detected_lang, "Analyse the following conversation and extract structured case information. Respond ONLY with JSON.")

    messages.append({
        "role": "user",
        "content": f"{instruction}\n\n---\n{conv_block}\n---",
    })

    return messages


def _parse_llm_json(raw: str) -> dict:
    """Best-effort parse of LLM JSON output, tolerating markdown fences."""
    text = raw.strip()
    # Strip markdown code fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find the first { ... } block
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    logger.warning("Failed to parse LLM JSON output: %s", text[:200])
    return {}


def _sanitize_context(parsed: dict) -> dict:
    """Normalise and validate the extracted context fields."""
    matter_type = str(parsed.get("matter_type") or "other").lower().strip()
    if matter_type not in _VALID_MATTER_TYPES:
        matter_type = "other"

    urgency = str(parsed.get("urgency") or "unknown").lower().strip()
    if urgency not in _VALID_URGENCY:
        urgency = "unknown"

    def _to_str_list(val: Any) -> list[str]:
        if isinstance(val, list):
            return [str(v).strip() for v in val if str(v).strip()]
        return []

    return {
        "title": str(parsed.get("title") or "")[:512] or None,
        "facts_known": _to_str_list(parsed.get("facts_known")),
        "facts_missing": _to_str_list(parsed.get("facts_missing")),
        "matter_type": matter_type,
        "urgency": urgency,
        "article_references": _to_str_list(parsed.get("article_references")),
        "next_question": str(parsed.get("next_question") or "").strip() or None,
    }


async def extract_context_from_conversation(
    conversation: list[dict],
    detected_lang: str,
) -> dict:
    """Call the LLM to extract structured case context from conversation."""
    settings = get_settings()
    model = settings.llm_model.strip()

    messages = _build_extraction_messages(conversation, detected_lang)

    from app.services import reasoning_model_service
    user_text = " ".join([m["content"] for m in conversation if m.get("role") == "user"])
    case_type, conf = reasoning_model_service.classify_case_type(user_text)
    extra_facts = reasoning_model_service.extract_facts(user_text)

    try:
        raw = await call_ollama(
            model=model,
            messages=messages,
            temperature=0.1,
            base_url=settings.llm_base_url,
        )
        parsed = _parse_llm_json(raw)
        
        # Merge fine-tuned extraction
        if reasoning_model_service.is_confident(conf) and case_type:
            parsed["matter_type"] = case_type
            
        if extra_facts and extra_facts.get("_confidence", 0.0) >= settings.reasoning_confidence_threshold:
            known = parsed.get("facts_known") or []
            if extra_facts.get("parties"):
                known.append(f"Parties: {', '.join(extra_facts['parties'])}")
            if extra_facts.get("dates"):
                known.append(f"Dates: {', '.join(extra_facts['dates'])}")
            if extra_facts.get("amounts"):
                known.append(f"Amounts: {', '.join(extra_facts['amounts'])}")
            parsed["facts_known"] = known
            
        return _sanitize_context(parsed)
    except Exception as e:
        logger.error("Context extraction LLM call failed: %s", e)
        return _sanitize_context({})


# ─────────────────────────────────────────────────────────────
# Conversation context persistence
# ─────────────────────────────────────────────────────────────

async def _save_conversation_context(case_id: str, context: dict) -> None:
    """Persist the extracted conversation context on the case document."""
    context["updated_at"] = _now()
    await _collection("compliance_cases").update_one(
        {"id": case_id},
        {"$set": {
            "conversation_context": context,
            "updated_at": _now(),
        }},
    )


async def _load_conversation_context(case_id: str) -> dict:
    """Load the stored conversation context from the case document."""
    case = await _collection("compliance_cases").find_one({"id": case_id})
    if not case:
        return {}
    return case.get("conversation_context") or {}


# ─────────────────────────────────────────────────────────────
# Core workflow functions
# ─────────────────────────────────────────────────────────────

async def create_case_from_conversation(
    db,
    *,
    situation: str,
    company_profile_id: Optional[str] = None,
    created_by: str = "user",
) -> dict:
    """
    Create a new compliance case from an initial user situation description.

    Flow:
      1. Analyse the situation via LLM → extract context
      2. Create the case with an auto-generated title
      3. Store the user message
      4. Generate and store the assistant's clarification question
      5. Persist the conversation context on the case
      6. Return the full turn result
    """
    detected_lang = _detect_query_language(situation)

    # Step 1: Extract context from the initial situation
    initial_conversation = [{"role": "user", "content": situation}]
    context = await extract_context_from_conversation(
        initial_conversation, detected_lang
    )

    # Step 2: Create the case
    title = context.get("title") or _generate_fallback_title(situation)
    priority = _urgency_to_priority(context.get("urgency", "unknown"))

    case = await case_service.create_case(
        db,
        title=title,
        description=situation[:4000],
        company_profile_id=company_profile_id,
        priority=priority,
        tags=["conversation", context.get("matter_type", "other")],
        created_by=created_by,
    )
    case_id = case["id"]

    # Step 3: Store user message
    user_msg = await case_service.add_message(
        db, case_id, role="user", content=situation,
        metadata={"turn": 1, "is_initial_situation": True},
    )

    # Step 4: Build and store assistant response
    assistant_text = _build_assistant_response(context, detected_lang)
    assistant_msg = await case_service.add_message(
        db, case_id, role="assistant", content=assistant_text,
        metadata={
            "turn": 1,
            "matter_type": context.get("matter_type"),
            "facts_known_count": len(context.get("facts_known", [])),
            "facts_missing_count": len(context.get("facts_missing", [])),
        },
    )

    # Step 5: Persist context
    await _save_conversation_context(case_id, context)

    # Update case status to in_progress
    await case_service.update_case(db, case_id, status="in_progress")

    await audit_service.log_event(
        db,
        "case_conversation_started",
        actor=created_by,
        details={
            "case_id": case_id,
            "matter_type": context.get("matter_type"),
            "facts_known_count": len(context.get("facts_known", [])),
            "facts_missing_count": len(context.get("facts_missing", [])),
        },
    )

    logger.info(
        "Case created from conversation: id=%s matter=%s facts_known=%d facts_missing=%d",
        case_id,
        context.get("matter_type"),
        len(context.get("facts_known", [])),
        len(context.get("facts_missing", [])),
    )

    return {
        "case_id": case_id,
        "user_message": user_msg,
        "assistant_message": assistant_msg,
        "context": _context_to_output(context),
    }


async def process_user_message(
    db,
    case_id: str,
    *,
    content: str,
) -> dict:
    """
    Process a follow-up user message within an existing case conversation.

    Flow:
      1. Validate the case exists
      2. Store the user message
      3. Load full conversation history
      4. Re-extract context via LLM (with full history)
      5. Generate and store the assistant's clarification/response
      6. Persist updated context
      7. Return the turn result
    """
    case = await case_service.get_case(db, case_id)
    if not case:
        raise ValueError(f"Case '{case_id}' not found")

    detected_lang = _detect_query_language(content)

    # Step 2: Store user message
    messages_list, total = await case_service.list_messages(db, case_id)
    turn_number = (total // 2) + 1

    user_msg = await case_service.add_message(
        db, case_id, role="user", content=content,
        metadata={"turn": turn_number},
    )

    # Step 3: Build full conversation history
    conversation = []
    for msg in messages_list:
        conversation.append({
            "role": msg["role"],
            "content": msg["content"],
        })
    # Append the newly added user message
    conversation.append({"role": "user", "content": content})

    # Step 4: Extract updated context
    context = await extract_context_from_conversation(conversation, detected_lang)

    # Merge with existing context (preserve previously known facts)
    existing_context = await _load_conversation_context(case_id)
    merged_context = _merge_contexts(existing_context, context)

    # Step 5: Build and store assistant response
    assistant_text = _build_assistant_response(merged_context, detected_lang)
    assistant_msg = await case_service.add_message(
        db, case_id, role="assistant", content=assistant_text,
        metadata={
            "turn": turn_number,
            "matter_type": merged_context.get("matter_type"),
            "facts_known_count": len(merged_context.get("facts_known", [])),
            "facts_missing_count": len(merged_context.get("facts_missing", [])),
        },
    )

    # Step 6: Persist context
    await _save_conversation_context(case_id, merged_context)
    merged_context["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Update case priority if urgency changed
    new_priority = _urgency_to_priority(merged_context.get("urgency", "unknown"))
    if new_priority != case.get("priority"):
        await case_service.update_case(db, case_id, priority=new_priority)

    logger.info(
        "Case conversation turn %d: id=%s facts_known=%d facts_missing=%d",
        turn_number, case_id,
        len(merged_context.get("facts_known", [])),
        len(merged_context.get("facts_missing", [])),
    )

    return {
        "case_id": case_id,
        "user_message": user_msg,
        "assistant_message": assistant_msg,
        "context": _context_to_output(merged_context),
    }


async def get_case_conversation_summary(db, case_id: str) -> dict | None:
    """
    Return a structured summary of the case's conversational context.
    """
    case = await case_service.get_case(db, case_id)
    if not case:
        return None

    context = await _load_conversation_context(case_id)

    return {
        "case_id": case_id,
        "title": case.get("title", ""),
        "status": case.get("status", ""),
        "priority": case.get("priority", ""),
        "context": _context_to_output(context),
        "message_count": case.get("message_count", 0),
        "created_at": case.get("created_at"),
        "updated_at": case.get("updated_at"),
    }


async def build_case_context_for_rag(
    db,
    case_id: str,
    detected_lang: str = "fr",
) -> str | None:
    """
    Build a context string from the case conversation that can be injected
    into the RAG pipeline's system prompt to ground the legal answer in
    the case's known facts and open questions.

    This is the integration point for llm_service.ask() and ask_agentic().
    """
    context = await _load_conversation_context(case_id)
    if not context:
        return None

    facts_known = context.get("facts_known", [])
    facts_missing = context.get("facts_missing", [])
    matter_type = context.get("matter_type", "unknown")
    urgency = context.get("urgency", "unknown")
    article_refs = context.get("article_references", [])

    if detected_lang == "ar":
        lines: list[str] = []
        lines.append("# سياق ملف الامتثال")
        lines.append(f"نوع المسألة: {matter_type}")
        lines.append(f"الاستعجال: {urgency}")
        if facts_known:
            lines.append("\n## الحقائق المثبتة")
            for i, fact in enumerate(facts_known, 1):
                lines.append(f"  {i}. {fact}")
        if facts_missing:
            lines.append("\n## المعلومات الناقصة")
            for i, fact in enumerate(facts_missing, 1):
                lines.append(f"  {i}. {fact}")
        if article_refs:
            lines.append(f"\n## الفصول المرجعية: {', '.join(article_refs)}")
        lines.append(
            "\nهام: ابنِ تحليلك القانوني على الحقائق المثبتة أعلاه فقط. "
            "لا تفترض حقائق لم يؤكدها المستخدم."
        )
        return "\n".join(lines)

    if detected_lang == "fr":
        lines: list[str] = []
        lines.append("# Contexte du dossier de conformité")
        lines.append(f"Type de dossier : {matter_type}")
        lines.append(f"Urgence : {urgency}")
        if facts_known:
            lines.append("\n## Faits établis")
            for i, fact in enumerate(facts_known, 1):
                lines.append(f"  {i}. {fact}")
        if facts_missing:
            lines.append("\n## Informations encore nécessaires")
            for i, fact in enumerate(facts_missing, 1):
                lines.append(f"  {i}. {fact}")
        if article_refs:
            lines.append(f"\n## Articles référencés : {', '.join(article_refs)}")
        lines.append(
            "\nIMPORTANT : Fondez votre analyse juridique sur les faits établis ci-dessus. "
            "Ne présumez aucun fait non confirmé par l'utilisateur."
        )
        return "\n".join(lines)

    # English fallback
    lines: list[str] = []
    lines.append("# Compliance Case Context")
    lines.append(f"Matter type: {matter_type}")
    lines.append(f"Urgency: {urgency}")
    if facts_known:
        lines.append("\n## Established Facts")
        for i, fact in enumerate(facts_known, 1):
            lines.append(f"  {i}. {fact}")
    if facts_missing:
        lines.append("\n## Information Still Needed")
        for i, fact in enumerate(facts_missing, 1):
            lines.append(f"  {i}. {fact}")
    if article_refs:
        lines.append(f"\n## Referenced Articles: {', '.join(article_refs)}")
    lines.append(
        "\nIMPORTANT: Ground your legal analysis on the established facts above. "
        "Do not assume facts that have not been confirmed by the user."
    )
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────

def _generate_fallback_title(situation: str) -> str:
    """Generate a short title from the first sentence of the situation."""
    text = (situation or "").strip()
    # Take first sentence or first 80 chars
    first_sentence = re.split(r"[.!?\n]", text)[0].strip()
    if len(first_sentence) > 100:
        first_sentence = first_sentence[:97] + "..."
    return first_sentence or "New Compliance Case"


def _urgency_to_priority(urgency: str) -> str:
    """Map urgency assessment to case priority."""
    mapping = {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low",
        "unknown": "medium",
    }
    return mapping.get(urgency, "medium")


def _merge_contexts(existing: dict, new: dict) -> dict:
    """Merge new extracted context with the existing one, preserving history."""
    # Union of known facts (deduplicated)
    existing_facts = set(existing.get("facts_known", []))
    new_facts = new.get("facts_known", [])
    merged_known = list(existing_facts)
    for fact in new_facts:
        if fact not in existing_facts:
            merged_known.append(fact)

    # Missing facts: use the new extraction (LLM sees full history)
    merged_missing = new.get("facts_missing", [])

    # Article refs: union
    existing_refs = set(existing.get("article_references", []))
    new_refs = new.get("article_references", [])
    merged_refs = list(existing_refs)
    for ref in new_refs:
        if ref not in existing_refs:
            merged_refs.append(ref)

    # Prefer new values for matter_type, urgency, next_question
    return {
        "title": new.get("title") or existing.get("title"),
        "facts_known": merged_known,
        "facts_missing": merged_missing,
        "matter_type": new.get("matter_type") or existing.get("matter_type", "other"),
        "urgency": new.get("urgency") or existing.get("urgency", "unknown"),
        "article_references": merged_refs,
        "next_question": new.get("next_question") or existing.get("next_question"),
    }


def _context_to_output(context: dict) -> dict:
    """Normalise context dict for API output."""
    return {
        "facts_known": context.get("facts_known", []),
        "facts_missing": context.get("facts_missing", []),
        "matter_type": context.get("matter_type"),
        "urgency": context.get("urgency", "unknown"),
        "next_question": context.get("next_question"),
        "article_references": context.get("article_references", []),
        "updated_at": context.get("updated_at"),
    }


def _build_assistant_response(context: dict, detected_lang: str) -> str:
    """
    Build a structured, professional assistant response from the extracted context.
    Tone: conservative legal compliance advisor, not a casual chatbot.
    """
    facts_known = context.get("facts_known", [])
    facts_missing = context.get("facts_missing", [])
    next_question = context.get("next_question")
    matter_type = context.get("matter_type", "other")

    _MATTER_LABELS_FR = {
        "labour_compliance": "Conformité du droit du travail",
        "corporate_formation": "Constitution de société",
        "corporate_governance": "Gouvernance d'entreprise",
        "contract_dispute": "Litige contractuel",
        "regulatory_compliance": "Conformité réglementaire",
        "tax_compliance": "Conformité fiscale",
        "intellectual_property": "Propriété intellectuelle",
        "data_protection": "Protection des données",
        "other": "Autre",
    }
    _MATTER_LABELS_AR = {
        "labour_compliance": "الامتثال لقانون الشغل",
        "corporate_formation": "تأسيس شركة",
        "corporate_governance": "حوكمة الشركات",
        "contract_dispute": "نزاع تعاقدي",
        "regulatory_compliance": "الامتثال التنظيمي",
        "tax_compliance": "الامتثال الضريبي",
        "intellectual_property": "الملكية الفكرية",
        "data_protection": "حماية البيانات",
        "other": "أخرى",
    }
    _MATTER_LABELS_EN = {
        "labour_compliance": "Labour compliance",
        "corporate_formation": "Corporate formation",
        "corporate_governance": "Corporate governance",
        "contract_dispute": "Contract dispute",
        "regulatory_compliance": "Regulatory compliance",
        "tax_compliance": "Tax compliance",
        "intellectual_property": "Intellectual property",
        "data_protection": "Data protection",
        "other": "Other",
    }

    if detected_lang == "fr":
        matter_label = _MATTER_LABELS_FR.get(matter_type, matter_type)
        lines = [f"J'ai bien pris note de votre situation. **Domaine identifié : {matter_label}.**\n\nVoici mon analyse préliminaire :"]
        if facts_known:
            lines.append("\n**Éléments établis :**")
            for fact in facts_known:
                lines.append(f"  • {fact}")
        if facts_missing:
            lines.append("\n**Informations complémentaires nécessaires :**")
            for fact in facts_missing:
                lines.append(f"  • {fact}")
        if next_question:
            lines.append(f"\n**Question :** {next_question}")
        else:
            lines.append(
                "\nJe dispose désormais des éléments essentiels pour procéder "
                "à l'analyse juridique de votre dossier."
            )
        return "\n".join(lines)

    if detected_lang == "ar":
        matter_label = _MATTER_LABELS_AR.get(matter_type, matter_type)
        lines = [f"لقد أخذت علماً بوضعكم. **المجال المحدد: {matter_label}.**\n\nفيما يلي تحليلي الأولي:"]
        if facts_known:
            lines.append("\n**العناصر المثبتة:**")
            for fact in facts_known:
                lines.append(f"  • {fact}")
        if facts_missing:
            lines.append("\n**المعلومات الإضافية اللازمة:**")
            for fact in facts_missing:
                lines.append(f"  • {fact}")
        if next_question:
            lines.append(f"\n**سؤال:** {next_question}")
        else:
            lines.append(
                "\nأصبح لديّ العناصر الأساسية للمضي في التحليل القانوني لملفكم."
            )
        return "\n".join(lines)

    # English fallback
    matter_label = _MATTER_LABELS_EN.get(matter_type, matter_type)
    lines = [f"I have noted your situation. **Identified domain: {matter_label}.**\n\nHere is my preliminary analysis:"]
    if facts_known:
        lines.append("\n**Established facts:**")
        for fact in facts_known:
            lines.append(f"  • {fact}")
    if facts_missing:
        lines.append("\n**Additional information needed:**")
        for fact in facts_missing:
            lines.append(f"  • {fact}")
    if next_question:
        lines.append(f"\n**Question:** {next_question}")
    else:
        lines.append(
            "\nI now have the essential elements to proceed with the legal "
            "analysis of your case."
        )
    return "\n".join(lines)
