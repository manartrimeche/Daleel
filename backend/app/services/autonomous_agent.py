"""
Autonomous ReAct Agent for legal compliance Q&A.

Uses Ollama's native tool calling to let the LLM decide which
services to invoke (semantic search, law lookup, compliance analysis, etc.)
and iterates until it can produce a grounded answer.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import httpx

from app.config import get_settings
from app.processing.text_utils import detect_query_language as _detect_query_language
from app.processing.derja_normalizer import normalize_if_derja as _normalize_if_derja
from app.services import (
    search_service,
    loi_service,
    graph_resolver,
    applicability_service,
    criticality_service,
    compliance_service,
    roadmap_service,
)
from app.services.quality_guard_service import audit_and_guard

logger = logging.getLogger(__name__)

_MAX_RESULT_CHARS = 4000

_ARABIC_CHAR_RE = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿ]")
_LATIN_CHAR_RE = re.compile(r"[A-Za-z]")
_FR_MARKERS = {"est", "les", "des", "une", "dans", "pour", "sur", "avec", "aux", "cette", "vous", "votre", "sont", "peut", "être", "aussi", "entre", "tout", "mais", "dont"}
_EN_MARKERS = {"the", "and", "for", "with", "this", "that", "your", "can", "are", "may", "from", "will", "also", "should", "which", "been", "must", "have", "would", "about"}


def _answer_matches_language(answer: str, expected_lang: str) -> bool:
    if not answer or len(answer) < 30:
        return True
    arabic_chars = len(_ARABIC_CHAR_RE.findall(answer))
    latin_chars = len(_LATIN_CHAR_RE.findall(answer))
    total = arabic_chars + latin_chars
    if total == 0:
        return True

    if expected_lang == "ar":
        return arabic_chars >= total * 0.4

    words = set(re.findall(r"[a-zA-ZÀ-ÿ]+", answer.lower()))
    fr_hits = len(words & _FR_MARKERS)
    en_hits = len(words & _EN_MARKERS)

    if expected_lang == "en":
        return en_hits >= fr_hits or fr_hits < 4
    if expected_lang == "fr":
        return fr_hits >= en_hits or en_hits < 4
    return True


# ── Data classes ────────────────────────────────────────────────

@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict
    handler: Callable

    def to_ollama_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class ToolCallRecord:
    iteration: int
    tool_name: str
    arguments: dict
    result_summary: str
    duration_ms: float
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "iteration": self.iteration,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "result_summary": self.result_summary,
            "duration_ms": round(self.duration_ms, 2),
            "error": self.error,
        }


# ── Helpers ─────────────────────────────────────────────────────

def _truncate_for_context(obj: Any, max_chars: int = _MAX_RESULT_CHARS) -> str:
    serialized = json.dumps(obj, ensure_ascii=False, default=str)
    if len(serialized) <= max_chars:
        return serialized
    return serialized[: max_chars - 30] + ' ... [truncated]"}'


def _summarize_result(obj: Any, max_chars: int = 300) -> str:
    serialized = json.dumps(obj, ensure_ascii=False, default=str)
    if len(serialized) <= max_chars:
        return serialized
    return serialized[:max_chars] + "..."


def _extract_sources_from_chunks(chunks: list[dict]) -> list[dict]:
    sources = []
    for c in chunks:
        sources.append({
            "document_id": c.get("document_id", ""),
            "filename": c.get("filename", ""),
            "page_number": c.get("page_number"),
            "section": c.get("section"),
            "language": c.get("language"),
            "relevance_score": c.get("score", 0.0),
        })
    return sources


# ── System prompts ──────────────────────────────────────────────

_SYSTEM_PROMPTS = {
    "fr": (
        "# QUI TU ES\n"
        "Tu es **Daleel**, un assistant juridique intelligent spécialisé en droit tunisien. "
        "Tu ne récites pas la loi — tu comprends le problème, tu proposes des solutions "
        "concrètes, et tu accompagnes le client pas à pas.\n\n"

        "# COMMENT TU TE COMPORTES\n"
        "1. **Écouter et comprendre** — Reformule le problème. Si des infos manquent, "
        "pose des questions précises avant de répondre.\n"
        "2. **Diagnostiquer** — Identifie le domaine juridique et les faits clés. "
        "Utilise tes outils pour retrouver les articles. Ne te fie JAMAIS à ta mémoire.\n"
        "3. **Proposer des solutions** — Présente 2-3 options pratiques avec avantages "
        "et inconvénients. Ne te contente pas de citer la loi.\n"
        "4. **Accompagner** — Dis au client quoi faire *maintenant*. Quel document préparer ? "
        "Quelle administration contacter ? Quel délai respecter ?\n"
        "5. **Relancer** — Suggère des questions complémentaires pour approfondir.\n\n"

        "# TON COMPORTEMENT INTERACTIF\n"
        "- **Sois proactif** : propose des aspects auxquels le client n'a pas pensé.\n"
        "- **Suggère toujours** : \"Souhaitez-vous que je recherche également... ?\" "
        "ou \"Je peux aussi vous aider à...\"\n"
        "- **Simplifie** : au lieu de \"il convient de se conformer à l'article 14\", "
        "dis \"concrètement, cela signifie que vous devez...\"\n"
        "- **Alerte tôt** : risques ou délais urgents → signale immédiatement.\n"
        "- **Reconnais tes limites** : si les sources ne couvrent pas un point, "
        "dis-le et propose une alternative.\n\n"

        "# RÈGLES DE RIGUEUR\n"
        "- Ta SEULE source : les résultats de tes outils de recherche.\n"
        "- INTERDIT d'inventer un article ou une disposition.\n"
        "- Si rien trouvé : \"Je n'ai pas trouvé de texte applicable. "
        "Je vous suggère de...\" (puis oriente le client).\n"
        "- Chaque affirmation juridique cite son article source.\n\n"

        "# FORMAT DE RÉPONSE\n"
        "Structure ta réponse en 4 blocs MAXIMUM. Sois concis, pas de répétition.\n\n"
        "**Diagnostic** — Reformule le problème en 2-3 phrases. Si des infos manquent, pose tes questions ici.\n\n"
        "**Ce que dit la loi** — Liste les articles pertinents sous forme de bullet points. "
        "Pour chaque article : numéro + ce qu'il dit concrètement (pas de paraphrase juridique). "
        "Cite [Source N].\n\n"
        "**Risques et conséquences** — Quels sont les risques concrets ? "
        "Sanctions, amendes, litiges possibles. Sois direct.\n\n"
        "**Actions à prendre** — Liste numérotée des étapes concrètes. "
        "Pour chaque action : quoi faire, quel document, quel délai, qui contacter.\n\n"
        "RÈGLES :\n"
        "- Ne répète JAMAIS la même information dans plusieurs sections.\n"
        "- Pas de conclusion ou résumé à la fin — la section Actions suffit.\n"
        "- Pas de phrases de remplissage (\"Il est important de noter que...\").\n"
        "- Maximum 400 mots au total.\n\n"

        "# LANGUE ET TON\n"
        "- **OBLIGATOIRE** : Réponds ENTIÈREMENT en français. Même si les sources "
        "sont dans une autre langue, ta réponse doit être 100% en français.\n"
        "- Ton : direct, clair, rassurant mais honnête. "
        "Pas de formules creuses.\n"
    ),
    "ar": (
        "# من أنت\n"
        "أنت **دليل**، مساعد قانوني ذكي متخصص في القانون التونسي. "
        "لا تسرد القانون — بل تفهم المشكلة وتقترح حلولاً عملية وترافق الموكل خطوة بخطوة.\n\n"

        "# كيف تتصرف\n"
        "1. **الاستماع والفهم** — أعد صياغة المشكلة. إن نقصت معلومات، اطرح أسئلة محددة.\n"
        "2. **التشخيص** — حدد المجال القانوني والوقائع الجوهرية. "
        "استخدم أدواتك لاسترجاع الفصول. لا تعتمد على ذاكرتك أبداً.\n"
        "3. **اقتراح الحلول** — قدّم 2-3 خيارات عملية مع إيجابيات وسلبيات. "
        "لا تكتفِ بسرد القانون.\n"
        "4. **المرافقة** — أخبر الموكل ماذا يفعل *الآن*. أي وثيقة يحضّر؟ "
        "أي جهة يتصل بها؟ أي أجل يحترم؟\n"
        "5. **المتابعة** — اقترح أسئلة تكميلية لتعميق الاستشارة.\n\n"

        "# سلوكك التفاعلي\n"
        "- **كن استباقياً**: اقترح جوانب لم يفكر فيها الموكل.\n"
        "- **اقترح دائماً**: \"هل تريد أن أبحث أيضاً عن...؟\" أو \"يمكنني مساعدتك في...\"\n"
        "- **بسّط**: بدل \"يجب الامتثال للفصل 14\"، قل \"عملياً، تحتاج أن...\"\n"
        "- **حذّر مبكراً**: مخاطر أو آجال عاجلة → نبّه فوراً.\n"
        "- **اعترف بالحدود**: إن لم تكفِ المصادر، قل ذلك واقترح البديل.\n\n"

        "# قواعد الدقة\n"
        "- مصدر الحقيقة الوحيد: نتائج أدوات البحث.\n"
        "- يُمنع اختراع أي فصل أو حكم.\n"
        "- إن لم تجد نصاً: \"لم أجد نصاً منطبقاً. أقترح عليك...\" (ثم وجّه الموكل).\n"
        "- كل تأكيد قانوني يذكر فصله المصدري.\n\n"

        "# شكل الإجابة\n"
        "رتّب إجابتك في 4 أقسام كحد أقصى. كن مختصراً بدون تكرار.\n\n"
        "**التشخيص** — أعد صياغة المشكلة في 2-3 جمل. إن نقصت معلومات، اطرح أسئلتك هنا.\n\n"
        "**ماذا يقول القانون** — اذكر الفصول المنطبقة كنقاط. "
        "لكل فصل: رقمه + ماذا يقول عملياً. استشهد بـ [Source N].\n\n"
        "**المخاطر والعواقب** — ما المخاطر الملموسة؟ عقوبات، غرامات، نزاعات محتملة.\n\n"
        "**الإجراءات المطلوبة** — قائمة مرقّمة بالخطوات العملية. "
        "لكل إجراء: ماذا تفعل، أي وثيقة، أي أجل، من تتصل به.\n\n"
        "القواعد:\n"
        "- لا تكرر نفس المعلومة في عدة أقسام.\n"
        "- لا خاتمة أو ملخص في النهاية.\n"
        "- لا عبارات حشو.\n"
        "- 400 كلمة كحد أقصى.\n\n"

        "# اللغة والنبرة\n"
        "- **إلزامي** : أجب بالكامل بالعربية. حتى لو كانت المصادر بلغة أخرى، "
        "يجب أن تكون إجابتك 100% بالعربية.\n"
        "- نبرة مباشرة، واضحة، مطمئنة لكن صادقة.\n"
    ),
    "en": (
        "# WHO YOU ARE\n"
        "You are **Daleel**, an intelligent legal assistant specializing in Tunisian law. "
        "You don't recite the law — you understand the problem, propose practical solutions, "
        "and guide the client step by step.\n\n"

        "# HOW YOU BEHAVE\n"
        "1. **Listen and understand** — Restate the problem. If info is missing, "
        "ask specific questions before answering.\n"
        "2. **Diagnose** — Identify the legal domain and key facts. "
        "Use your tools to retrieve articles. NEVER rely on memory.\n"
        "3. **Propose solutions** — Present 2-3 practical options with pros and cons. "
        "Don't just cite the law.\n"
        "4. **Guide** — Tell the client what to do *now*. What document to prepare? "
        "Which authority to contact? What deadline to respect?\n"
        "5. **Follow up** — Suggest follow-up questions to go deeper.\n\n"

        "# YOUR INTERACTIVE BEHAVIOR\n"
        "- **Be proactive**: suggest aspects the client hasn't thought of.\n"
        "- **Always suggest**: \"Would you like me to also look into...?\" "
        "or \"I can also help you with...\"\n"
        "- **Simplify**: instead of \"one must comply with article 14\", "
        "say \"practically, this means you need to...\"\n"
        "- **Alert early**: risks or urgent deadlines → flag immediately.\n"
        "- **Acknowledge limits**: if sources don't cover a point, "
        "say so and suggest an alternative.\n\n"

        "# RIGOR RULES\n"
        "- Your ONLY source: your search tool results.\n"
        "- FORBIDDEN to invent any article or provision.\n"
        "- If nothing found: \"I found no applicable text. "
        "I suggest you...\" (then guide the client).\n"
        "- Every legal assertion cites its source article.\n\n"

        "# RESPONSE FORMAT\n"
        "Structure your answer in 4 sections MAX. Be concise, no repetition.\n\n"
        "**Diagnosis** — Restate the problem in 2-3 sentences. If info is missing, ask here.\n\n"
        "**What the law says** — List relevant articles as bullet points. "
        "For each: article number + what it concretely means (no legal paraphrasing). "
        "Cite [Source N].\n\n"
        "**Risks and consequences** — What are the concrete risks? "
        "Penalties, fines, possible disputes. Be direct.\n\n"
        "**Actions to take** — Numbered list of concrete steps. "
        "For each: what to do, which document, what deadline, who to contact.\n\n"
        "RULES:\n"
        "- NEVER repeat the same information across sections.\n"
        "- No conclusion or summary at the end — the Actions section is enough.\n"
        "- No filler phrases (\"It is important to note that...\").\n"
        "- Maximum 400 words total.\n\n"

        "# LANGUAGE AND TONE\n"
        "- **MANDATORY**: Respond ENTIRELY in English. Even if the source documents "
        "are in French or Arabic, your answer must be 100% in English.\n"
        "- Tone: direct, clear, reassuring but honest. "
        "No filler phrases.\n"
    ),
}


# ── Few-shot: exemplary consultation ────────────────────────────

_FEW_SHOT_EXAMPLES = {
    "fr": {
        "user": "Je veux licencier un salarié qui refuse de travailler le samedi. Qu'est-ce que je risque ?",
        "assistant": (
            "**Diagnostic**\n"
            "Vous envisagez de licencier un salarié qui refuse le samedi. "
            "Question clé : le samedi est-il prévu dans le contrat ou le règlement intérieur ?\n\n"
            "**Ce que dit la loi**\n"
            "- Je n'ai pas trouvé de texte spécifique sur le refus du samedi dans les sources.\n"
            "- Principe général : toute modification unilatérale des conditions de travail "
            "peut constituer un abus de droit.\n\n"
            "**Risques et conséquences**\n"
            "- Licenciement abusif avec dommages-intérêts si le samedi n'est pas contractuel.\n"
            "- Risque de requalification devant le conseil des prud'hommes.\n\n"
            "**Actions à prendre**\n"
            "1. Vérifiez le contrat et le règlement intérieur pour le samedi.\n"
            "2. Si absent → proposez un avenant avec contrepartie (prime, repos compensatoire).\n"
            "3. Si prévu → envoyez une mise en demeure formelle avant toute sanction.\n"
            "4. Ne licenciez jamais directement sans ces étapes."
        ),
    },
    "ar": {
        "user": "أريد فصل عامل يرفض العمل يوم السبت. ما هي المخاطر؟",
        "assistant": (
            "**التشخيص**\n"
            "تريدون فصل عامل يرفض السبت. "
            "السؤال الجوهري: هل العمل يوم السبت منصوص عليه في العقد أو النظام الداخلي؟\n\n"
            "**ماذا يقول القانون**\n"
            "- لم أجد نصاً محدداً حول رفض العمل يوم السبت.\n"
            "- المبدأ العام: أي تعديل أحادي لشروط العمل قد يُعتبر تعسفياً.\n\n"
            "**المخاطر والعواقب**\n"
            "- فصل تعسفي مع تعويضات إن لم يكن السبت في العقد.\n"
            "- خطر الطعن أمام القضاء.\n\n"
            "**الإجراءات المطلوبة**\n"
            "1. راجعوا العقد والنظام الداخلي.\n"
            "2. إن لم يُذكر السبت → اقترحوا ملحقاً مع مقابل (علاوة أو راحة تعويضية).\n"
            "3. إن كان منصوصاً → وجّهوا إنذاراً رسمياً أولاً.\n"
            "4. لا تفصلوا مباشرة بدون هذه الخطوات."
        ),
    },
    "en": {
        "user": "I want to fire an employee who refuses to work on Saturdays. What are my risks?",
        "assistant": (
            "**Diagnosis**\n"
            "You want to terminate an employee who refuses Saturday work. "
            "Key question: is Saturday work stipulated in the contract or internal regulations?\n\n"
            "**What the law says**\n"
            "- No specific text found on refusing Saturday work in available sources.\n"
            "- General principle: any unilateral change to working conditions "
            "may constitute abuse of rights.\n\n"
            "**Risks and consequences**\n"
            "- Wrongful dismissal with damages if Saturday isn't contractual.\n"
            "- Risk of challenge before labor court.\n\n"
            "**Actions to take**\n"
            "1. Check the employment contract and internal regulations for Saturday clauses.\n"
            "2. If absent → propose a contract amendment with compensation (bonus, compensatory rest).\n"
            "3. If present → send a formal warning before any disciplinary action.\n"
            "4. Never terminate directly without these steps."
        ),
    },
}


# ── Agent ───────────────────────────────────────────────────────

class AutonomousAgent:
    def __init__(
        self,
        db: Any,
        model: str | None = None,
        temperature: float = 0.15,
        max_iterations: int | None = None,
        tool_timeout: float | None = None,
        total_timeout: float | None = None,
        base_url: str | None = None,
        organization_id: str | None = None,
    ):
        settings = get_settings()
        self._db = db
        self._model = (model or settings.llm_model).strip()
        self._temperature = temperature
        self._max_iterations = max_iterations or settings.agent_max_iterations
        self._tool_timeout = tool_timeout or settings.agent_tool_timeout
        self._total_timeout = total_timeout or settings.agent_total_timeout
        self._base_url = base_url or settings.llm_base_url
        self._organization_id = organization_id

        self._tools = self._build_tools()
        self._tool_map = {t.name: t for t in self._tools}

    # ── Public entry point ──────────────────────────────────────

    async def run(
        self,
        question: str,
        history: list[dict] | None = None,
        language_filter: str | None = None,
        document_id: str | None = None,
        profile_id: str | None = None,
    ) -> dict:
        t0 = time.perf_counter()

        # ── Derja normalization ──
        derja_effective, derja_original, is_derja = _normalize_if_derja(question)
        if is_derja:
            question = derja_effective
            detected_lang = "fr"
            logger.info("Agent: Derja detected, switching to French pipeline")
        else:
            detected_lang = _detect_query_language(question)
        system_prompt = _SYSTEM_PROMPTS.get(detected_lang, _SYSTEM_PROMPTS["en"])

        if profile_id:
            ctx_line = {
                "fr": f"\nProfil entreprise disponible (ID: {profile_id}). Utilise-le pour les requêtes de conformité.",
                "ar": f"\nملف تعريف الشركة متاح (ID: {profile_id}). استخدمه لاستعلامات الامتثال.",
                "en": f"\nCompany profile available (ID: {profile_id}). Use it for compliance queries.",
            }
            system_prompt += ctx_line.get(detected_lang, ctx_line["en"])

        few_shot = _FEW_SHOT_EXAMPLES.get(detected_lang, _FEW_SHOT_EXAMPLES["fr"])

        messages: list[dict] = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": few_shot["user"]})
        messages.append({"role": "assistant", "content": few_shot["assistant"]})
        if history:
            for msg in history[-20:]:
                if msg.get("role") in ("user", "assistant") and msg.get("content"):
                    messages.append({"role": msg["role"], "content": msg["content"]})
        lang_reminder = {
            "fr": "\n\n[RAPPEL : Réponds entièrement en français.]",
            "ar": "\n\n[تذكير : أجب بالكامل بالعربية.]",
            "en": "\n\n[REMINDER: Respond entirely in English.]",
        }
        messages.append({
            "role": "user",
            "content": question + lang_reminder.get(detected_lang, lang_reminder["en"]),
        })

        tools_schema = [t.to_ollama_schema() for t in self._tools]
        tool_log: list[ToolCallRecord] = []
        accumulated_sources: list[dict] = []
        final_answer = ""
        total_iterations = 0

        for iteration in range(1, self._max_iterations + 1):
            total_iterations = iteration
            elapsed = time.perf_counter() - t0
            if elapsed > self._total_timeout:
                logger.warning("Agent total timeout reached at iteration %d", iteration)
                break

            response = await self._call_ollama_with_tools(messages, tools_schema)
            assistant_msg = response["message"]
            messages.append(assistant_msg)

            tool_calls = assistant_msg.get("tool_calls")
            if not tool_calls:
                final_answer = assistant_msg.get("content", "")
                break

            for tc in tool_calls:
                func_info = tc.get("function", {})
                func_name = func_info.get("name", "")
                func_args = func_info.get("arguments", {})

                tool_def = self._tool_map.get(func_name)
                t_tool = time.perf_counter()

                if not tool_def:
                    result_obj = {"error": f"Unknown tool: {func_name}"}
                    err_msg = f"Unknown tool: {func_name}"
                else:
                    err_msg = None
                    try:
                        result_obj = await asyncio.wait_for(
                            tool_def.handler(func_args),
                            timeout=self._tool_timeout,
                        )
                        if isinstance(result_obj, list):
                            for item in result_obj:
                                if isinstance(item, dict) and "document_id" in item:
                                    accumulated_sources.append({
                                        "document_id": item.get("document_id", ""),
                                        "filename": item.get("filename", ""),
                                        "page_number": item.get("page_number"),
                                        "section": item.get("section"),
                                        "language": item.get("language"),
                                        "relevance_score": item.get("score", 0.0),
                                    })
                    except asyncio.TimeoutError:
                        result_obj = {"error": "Tool execution timed out"}
                        err_msg = "timeout"
                    except Exception as e:
                        logger.warning("Tool %s failed: %s", func_name, e)
                        result_obj = {"error": str(e)}
                        err_msg = str(e)

                duration_ms = (time.perf_counter() - t_tool) * 1000
                tool_log.append(ToolCallRecord(
                    iteration=iteration,
                    tool_name=func_name,
                    arguments=func_args,
                    result_summary=_summarize_result(result_obj),
                    duration_ms=duration_ms,
                    error=err_msg,
                ))

                messages.append({
                    "role": "tool",
                    "content": _truncate_for_context(result_obj),
                })
        else:
            force_msgs = {
                "fr": "Tu as utilisé toutes les itérations disponibles. Donne ta meilleure réponse maintenant avec les informations collectées.",
                "ar": "لقد استخدمت جميع التكرارات المتاحة. قدم أفضل إجابة لديك الآن بناءً على المعلومات التي جمعتها.",
                "en": "You have used all available iterations. Provide your best answer now based on the information gathered.",
            }
            messages.append({
                "role": "user",
                "content": force_msgs.get(detected_lang, force_msgs["en"]),
            })
            response = await self._call_ollama_with_tools(messages, tools=[])
            final_answer = response["message"].get("content", "")

        if not final_answer and not tool_log:
            no_answer = {
                "fr": "Je n'ai pas pu obtenir suffisamment d'informations pour répondre. Veuillez reformuler votre question.",
                "ar": "لم أتمكن من الحصول على معلومات كافية للإجابة. يرجى إعادة صياغة سؤالك.",
                "en": "I could not gather enough information to answer. Please rephrase your question.",
            }
            final_answer = no_answer.get(detected_lang, no_answer["en"])

        total_ms = (time.perf_counter() - t0) * 1000
        retrieval_count = sum(1 for t in tool_log if t.tool_name == "semantic_search")

        seen = set()
        unique_sources = []
        for s in accumulated_sources:
            key = (s.get("document_id"), s.get("page_number"), s.get("section"))
            if key not in seen:
                seen.add(key)
                unique_sources.append(s)

        # ── Format enforcement: strip conclusions, filler, repetition ──
        if final_answer:
            from app.services.llm_service import _enforce_output_format
            final_answer = _enforce_output_format(final_answer, detected_lang)

        # ── Language compliance: re-prompt if answer is in wrong language ──
        if final_answer and not _answer_matches_language(final_answer, detected_lang):
            logger.warning(
                "Agent answer language mismatch (expected=%s). Requesting translation.",
                detected_lang,
            )
            translate_prompts = {
                "fr": f"Ta réponse précédente est dans la mauvaise langue. Traduis-la intégralement en français. Ne change pas le contenu, traduis seulement :\n\n{final_answer}",
                "ar": f"إجابتك السابقة بلغة خاطئة. ترجمها بالكامل إلى العربية. لا تغير المحتوى، فقط ترجم:\n\n{final_answer}",
                "en": f"Your previous answer is in the wrong language. Translate it entirely into English. Do not change the content, only translate:\n\n{final_answer}",
            }
            translate_msg = translate_prompts.get(detected_lang, translate_prompts["en"])
            try:
                translation_resp = await self._call_ollama_with_tools(
                    [
                        {"role": "system", "content": f"You are a translator. Translate the following text entirely into {detected_lang}. Keep the same structure and formatting."},
                        {"role": "user", "content": translate_msg},
                    ],
                    tools=[],
                )
                translated = translation_resp["message"].get("content", "")
                if translated and _answer_matches_language(translated, detected_lang):
                    final_answer = translated
                else:
                    logger.warning("Translation attempt still not in target language, keeping original.")
            except Exception as e:
                logger.warning("Language translation re-prompt failed: %s", e)

        # ── Quality guard: anti-hallucination post-processing ──
        qg_status = None
        qg_issues = None
        if final_answer and accumulated_sources:
            try:
                qg_result = await audit_and_guard(
                    question=question,
                    answer=final_answer,
                    chunks=accumulated_sources,
                    lang=detected_lang,
                    enabled=True,
                )
                final_answer = qg_result["answer"]
                qg_status = qg_result.get("status")
                qg_issues = qg_result.get("issues") or None
            except Exception as e:
                logger.warning("Quality guard failed in autonomous agent: %s", e)

        reasoning_steps = [
            f"iteration_{r.iteration}:tool={r.tool_name}" for r in tool_log
        ]
        if qg_status and qg_status != "accepted":
            reasoning_steps.append(f"quality_guard:{qg_status}")

        result = {
            "answer": final_answer,
            "sources": unique_sources,
            "model": f"{self._model}+autonomous",
            "chunks_used": len(unique_sources),
            "reasoning_steps": reasoning_steps,
            "retrieval_attempts": retrieval_count,
            "rewritten_query": None,
            "intent": None,
            "route_decision": "autonomous_agent",
            "timings_ms": {
                "total": round(total_ms, 2),
            },
            "selected_mode": "autonomous",
            "tool_calls_log": [r.to_dict() for r in tool_log],
            "total_iterations": total_iterations,
            "agent_mode": "autonomous",
            "quality_guard_status": qg_status,
            "quality_guard_issues": qg_issues,
        }
        if is_derja:
            result["derja_detected"] = True
            result["derja_original"] = derja_original
        return result

    # ── Ollama caller with tool support ─────────────────────────

    async def _call_ollama_with_tools(
        self, messages: list[dict], tools: list[dict]
    ) -> dict:
        settings = get_settings()
        url = f"{self._base_url}/api/chat"

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
            "stream": False,
            "options": {"num_ctx": 8192, "top_p": 0.9},
        }
        if tools:
            payload["tools"] = tools

        timeout = httpx.Timeout(
            connect=settings.llm_timeout_connect,
            read=settings.llm_timeout_read,
            write=30.0,
            pool=10.0,
        )

        max_retries = settings.llm_max_retries
        last_error: Exception | None = None

        async with httpx.AsyncClient(timeout=timeout) as client:
            for attempt in range(1, max_retries + 1):
                try:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    data = response.json()

                    msg = data.get("message")
                    if not isinstance(msg, dict):
                        raise RuntimeError(
                            f"Malformed Ollama response: {data!r}"
                        )

                    for tc in msg.get("tool_calls", []) or []:
                        args = tc.get("function", {}).get("arguments")
                        if isinstance(args, str):
                            try:
                                tc["function"]["arguments"] = json.loads(args)
                            except json.JSONDecodeError:
                                tc["function"]["arguments"] = {}

                    return data

                except (
                    httpx.ReadTimeout,
                    httpx.ConnectTimeout,
                    httpx.ConnectError,
                    httpx.RemoteProtocolError,
                    httpx.PoolTimeout,
                ) as e:
                    last_error = e
                    if attempt < max_retries:
                        delay = min(
                            settings.llm_backoff_base * (2 ** (attempt - 1)),
                            settings.llm_backoff_max,
                        )
                        logger.warning(
                            "Ollama tool-call attempt %d/%d failed: %r — retry in %.1fs",
                            attempt, max_retries, e, delay,
                        )
                        await asyncio.sleep(delay)
                    continue

                except httpx.HTTPStatusError as e:
                    last_error = e
                    if attempt < max_retries and e.response.status_code >= 500:
                        delay = min(
                            settings.llm_backoff_base * (2 ** (attempt - 1)),
                            settings.llm_backoff_max,
                        )
                        await asyncio.sleep(delay)
                        continue
                    raise

        if last_error is not None:
            raise last_error
        raise RuntimeError("Ollama call failed without explicit error")

    # ── Tool definitions ────────────────────────────────────────

    def _build_tools(self) -> list[ToolDefinition]:
        db = self._db
        organization_id = self._organization_id

        async def ensure_profile_access(profile_id: str) -> dict | None:
            query = {"id": profile_id}
            if organization_id:
                query["organization_id"] = organization_id
            return await db["company_profiles"].find_one(query, {"_id": 0, "id": 1})

        # ── Tier 1: Core retrieval ──

        async def handle_semantic_search(args: dict) -> Any:
            results = await search_service.semantic_search(
                db,
                query=args["query"],
                top_k=min(args.get("top_k", 5), 10),
                language_filter=args.get("language_filter"),
                document_id=args.get("document_id"),
                organization_id=organization_id,
            )
            for r in results:
                r.pop("embedding", None)
                if "text" in r:
                    r["text"] = r["text"][:1500]
            return results[:10]

        async def handle_lookup_law(args: dict) -> Any:
            result = await loi_service.get_loi_by_code(db, args["code"])
            if not result:
                return {"error": f"Law with code '{args['code']}' not found"}
            return result

        async def handle_search_articles(args: dict) -> Any:
            articles, total = await loi_service.list_articles(
                db,
                loi_id=args["loi_id"],
                search=args.get("keyword"),
                limit=min(args.get("limit", 20), 30),
            )
            return {"articles": articles, "total": total}

        async def handle_get_article_text(args: dict) -> Any:
            version = await loi_service.get_article_version(db, args["version_id"])
            if not version:
                return {"error": f"Article version '{args['version_id']}' not found"}
            return version

        # ── Tier 2: Knowledge graph ──

        async def handle_get_article_graph(args: dict) -> Any:
            graph = await graph_resolver.resolve_article_graph(db, args["article_id"])
            return graph.__dict__ if hasattr(graph, "__dict__") else graph

        async def handle_get_company_graph(args: dict) -> Any:
            if not await ensure_profile_access(args["profile_id"]):
                return {"error": f"Company profile '{args['profile_id']}' not found"}
            graph = await graph_resolver.resolve_company_graph(db, args["profile_id"])
            return graph.__dict__ if hasattr(graph, "__dict__") else graph

        # ── Tier 3: Compliance analysis ──

        async def handle_get_applicability(args: dict) -> Any:
            if not await ensure_profile_access(args["profile_id"]):
                return {"error": f"Company profile '{args['profile_id']}' not found"}
            return await applicability_service.get_applicability_summary(
                db, args["profile_id"], organization_id=organization_id
            )

        async def handle_get_criticality(args: dict) -> Any:
            if not await ensure_profile_access(args["profile_id"]):
                return {"error": f"Company profile '{args['profile_id']}' not found"}
            return await criticality_service.get_criticality_summary_for_profile(
                db, args["profile_id"]
            )

        async def handle_compute_compliance(args: dict) -> Any:
            if not await ensure_profile_access(args["profile_id"]):
                return {"error": f"Company profile '{args['profile_id']}' not found"}
            return await compliance_service.compute_posture(
                db, args["profile_id"], organization_id=organization_id
            )

        async def handle_generate_roadmap(args: dict) -> Any:
            if not await ensure_profile_access(args["profile_id"]):
                return {"error": f"Company profile '{args['profile_id']}' not found"}
            result = await roadmap_service.generate_roadmap(
                db,
                args["profile_id"],
                organization_id=organization_id,
            )
            if isinstance(result, dict) and "ordered_plan" in result:
                result["ordered_plan"] = result["ordered_plan"][:10]
            return result

        return [
            ToolDefinition(
                name="semantic_search",
                description="Search the legal document corpus by semantic similarity. Returns relevant text chunks with metadata (article text, page number, source document).",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query in any language (French, Arabic, or English)",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results to return (default 5, max 10)",
                        },
                        "language_filter": {
                            "type": "string",
                            "enum": ["ar", "fr", "en"],
                            "description": "Optional: restrict results to a specific language",
                        },
                        "document_id": {
                            "type": "string",
                            "description": "Optional: restrict search to a specific document UUID",
                        },
                    },
                    "required": ["query"],
                },
                handler=handle_semantic_search,
            ),
            ToolDefinition(
                name="lookup_law",
                description="Look up a Tunisian law by its short code. Returns the law's metadata including its ID, name, and article count. Common codes: CT (Code du Travail), CS (Code des Sociétés), CF (Code Fiscal).",
                parameters={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Short law code, e.g. 'CT', 'CS', 'CF', 'LP63'",
                        },
                    },
                    "required": ["code"],
                },
                handler=handle_lookup_law,
            ),
            ToolDefinition(
                name="search_articles",
                description="Search for articles within a specific law by keyword. Returns matching articles with their numbers and headings.",
                parameters={
                    "type": "object",
                    "properties": {
                        "loi_id": {
                            "type": "string",
                            "description": "The law's UUID (obtained from lookup_law)",
                        },
                        "keyword": {
                            "type": "string",
                            "description": "Optional keyword to filter articles",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max articles to return (default 20, max 30)",
                        },
                    },
                    "required": ["loi_id"],
                },
                handler=handle_search_articles,
            ),
            ToolDefinition(
                name="get_article_text",
                description="Get the full text of a specific article version. Returns the article content, exigence count, and action count.",
                parameters={
                    "type": "object",
                    "properties": {
                        "version_id": {
                            "type": "string",
                            "description": "The article version UUID",
                        },
                    },
                    "required": ["version_id"],
                },
                handler=handle_get_article_text,
            ),
            ToolDefinition(
                name="get_article_graph",
                description="Get the complete knowledge subgraph for an article: all versions, extracted exigences (obligations/prohibitions/conditions), compliance actions, criticality levels, and dependencies.",
                parameters={
                    "type": "object",
                    "properties": {
                        "article_id": {
                            "type": "string",
                            "description": "The article UUID",
                        },
                    },
                    "required": ["article_id"],
                },
                handler=handle_get_article_graph,
            ),
            ToolDefinition(
                name="get_company_graph",
                description="Get the compliance graph for a company profile: applicable exigences, linked actions, and criticality assessments.",
                parameters={
                    "type": "object",
                    "properties": {
                        "profile_id": {
                            "type": "string",
                            "description": "The company profile UUID",
                        },
                    },
                    "required": ["profile_id"],
                },
                handler=handle_get_company_graph,
            ),
            ToolDefinition(
                name="get_applicability",
                description="Get a summary of which legal requirements apply to a company. Returns counts by exigence type (obligation, prohibition, condition, sanction).",
                parameters={
                    "type": "object",
                    "properties": {
                        "profile_id": {
                            "type": "string",
                            "description": "The company profile UUID",
                        },
                    },
                    "required": ["profile_id"],
                },
                handler=handle_get_applicability,
            ),
            ToolDefinition(
                name="get_criticality",
                description="Get the criticality/risk breakdown for a company's applicable compliance actions. Shows counts by level (critique, importante, secondaire).",
                parameters={
                    "type": "object",
                    "properties": {
                        "profile_id": {
                            "type": "string",
                            "description": "The company profile UUID",
                        },
                    },
                    "required": ["profile_id"],
                },
                handler=handle_get_criticality,
            ),
            ToolDefinition(
                name="compute_compliance",
                description="Compute the full compliance posture for a company: overall coverage score, gap analysis, and list of uncovered requirements.",
                parameters={
                    "type": "object",
                    "properties": {
                        "profile_id": {
                            "type": "string",
                            "description": "The company profile UUID",
                        },
                    },
                    "required": ["profile_id"],
                },
                handler=handle_compute_compliance,
            ),
            ToolDefinition(
                name="generate_roadmap",
                description="Generate a prioritized compliance remediation roadmap for a company. Returns ordered actions considering dependencies and criticality.",
                parameters={
                    "type": "object",
                    "properties": {
                        "profile_id": {
                            "type": "string",
                            "description": "The company profile UUID",
                        },
                    },
                    "required": ["profile_id"],
                },
                handler=handle_generate_roadmap,
            ),
        ]
