# Patches d'intégration — minimal-invasive

Ce document rassemble les **patchs minimaux** à appliquer aux 4 services
existants pour brancher les modèles Track 1 et Track 2. Aucun de ces patchs
ne change la signature publique. Tous sont fail-safe : si le modèle fine-tuné
est absent, le comportement actuel est préservé.

---

## 1. `app/services/advisor_response_composer.py`

> Track 1 — appel du style formatter à la toute fin du composer.

```python
# en haut du fichier
from app.services import llm_style_formatter

# dans `compose_from_orchestration_result(...)`, JUSTE AVANT le return :
markdown = render_response_as_markdown(structured)

# 🔧 Track 1 hook
payload = llm_style_formatter.build_payload_from_orchestration(
    user_question=user_question,
    language=language,
    extracted_facts=extracted_facts,
    legal_context=legal_context,
    findings=structured.compliance_risks,        # ou la liste source
    actions=structured.recommended_actions,
    draft_answer=markdown,
)
markdown = await llm_style_formatter.format_advisor_answer(
    draft_markdown=markdown,
    payload=payload,
    language=language,
)

# stocker dans la structure pour la suite (quality_guard)
structured.formatted_text = markdown
return structured
```

**Important** : `quality_guard_service.audit_and_guard()` est appelé **après**
ce composer dans la pipeline. Il vérifiera que le style model n'a pas
introduit de référence d'article non supportée.

---

## 2. `app/services/domain_router.py`

> Track 2 — `classify_domain` en première ligne, scoring lexical en fallback.

```python
# en haut du fichier
from app.services import reasoning_model_service

# dans `route_question(...)`, en début de fonction :
pred_domain, conf = reasoning_model_service.classify_domain(question)
if pred_domain and reasoning_model_service.is_confident(conf):
    logger.info("domain_router: ML model decided '%s' (conf=%.2f)", pred_domain, conf)
    return RouteResult(
        domain=pred_domain,
        confidence=conf,
        source="reasoning_model",
        # … remplir le reste depuis get_domain_config(pred_domain)
    )
# sinon : on continue avec le scoring lexical existant (inchangé).
```

---

## 3. `app/services/case_conversation_service.py`

> Track 2 — enrichir `extract_context_from_conversation` avec
> `classify_case_type` + `extract_facts` ML.

```python
# en haut du fichier
from app.services import reasoning_model_service

# dans `extract_context_from_conversation(...)`, après l'appel LLM existant :
flat_text = " ".join(m.get("content", "") for m in conversation if m.get("role") == "user")

case_type, ct_conf = reasoning_model_service.classify_case_type(flat_text)
if case_type and reasoning_model_service.is_confident(ct_conf):
    parsed["case_type"] = case_type
    parsed["case_type_confidence"] = ct_conf

ml_facts = reasoning_model_service.extract_facts(flat_text)
# Fusion non destructive : ne pas écraser des champs déjà bien remplis par le LLM.
for k in ("parties", "dates", "amounts", "processing_type", "legal_basis_keywords"):
    existing = parsed.get(k)
    if not existing:
        parsed[k] = ml_facts.get(k)
parsed["_facts_source"] = ml_facts.get("_source", "llm")
```

**Garde-fou Human-in-the-loop** :

```python
# Si confiance trop basse pour case_type, déclencher une clarification
# au lieu de figer un label arbitraire.
if not case_type or not reasoning_model_service.is_confident(ct_conf):
    parsed["_needs_clarification"] = True
```

---

## 4. `app/services/compliance_case_orchestrator.py`

> Track 2 — fusionner la prédiction de risque avec l'évaluation existante.

```python
# en haut du fichier
from app.services import reasoning_model_service

# dans `_assess_risk_level(...)` ou avant `_determine_decision(...)` :
text_for_risk = (
    (case.get("description") or "")
    + "\n"
    + " ".join(f.get("title", "") for f in findings or [])
)
ml_risk, risk_conf = reasoning_model_service.classify_risk(text_for_risk)

heuristic_risk = _existing_heuristic_risk(...)   # logique actuelle inchangée
if ml_risk and reasoning_model_service.is_confident(risk_conf):
    # Conservatisme légal : on prend le MAX entre heuristique et ML.
    final_risk = _max_risk(heuristic_risk, ml_risk)
else:
    final_risk = heuristic_risk

orchestration_result.risk_level = final_risk
```

`_max_risk` est trivial :
```python
_RISK_ORDER = {"low": 0, "medium": 1, "high": 2}
def _max_risk(a: str, b: str) -> str:
    return a if _RISK_ORDER[a] >= _RISK_ORDER[b] else b
```

---

## 5. Variables d'environnement à ajouter dans `.env.example`

```env
# Track 1 — Style model (Ollama)
DALEEL_STYLE_MODEL=
DALEEL_STYLE_MODEL_TIMEOUT=30

# Track 2 — Reasoning model (chemin local)
DALEEL_REASONING_MODEL_PATH=
DALEEL_REASONING_CONFIDENCE_THRESHOLD=0.7
```

Et dans `app/config.py`, exposer les Settings correspondants :

```python
style_model: str = ""
style_model_timeout: float = 30.0
reasoning_model_path: str = ""
reasoning_confidence_threshold: float = 0.7
```

---

## 6. Quality guard reste l'arbitre final

Aucune modification de `quality_guard_service.py`. Son contrat reste :

> « Quelle que soit la source du texte (LLM générique, style model fine-tuné,
>   composer markdown), je vérifie que toutes les références d'articles
>   citées sont supportées par les chunks fournis ; sinon je strippe ou je
>   réécris en mode conservatif. »

C'est cette propriété qui rend le fine-tuning **safe pour le légal** :
le modèle de style peut être débridé stylistiquement, le guard
empêche toute hallucination juridique de sortir.
