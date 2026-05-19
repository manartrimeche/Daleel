# Daleel — Plan de Fine-Tuning LLM (PFE)

> Deux pistes de fine-tuning **complémentaires** au RAG existant. Le RAG reste
> la source de vérité juridique (zéro hallucination de loi). Le fine-tuning
> n'apprend **ni des articles, ni des faits** — il apprend **la forme**
> (Track 1) et **la décision structurée** (Track 2).

---

## 1. Vue d'ensemble des deux pistes

### Track 1 — Response Style & Format

**But** : un petit modèle (ou adaptateur LoRA) qui transforme un brouillon
RAG + des findings en une reponse d'avocat-conseil en 7 sections fixes :

1. Ce que j'ai compris
2. Informations manquantes
3. Contexte légal / articles pertinents
4. Analyse / risques de non-conformité
5. Actions recommandées
6. Preuves / documents à rassembler
7. Nécessité d'une revue humaine

**Pourquoi un fine-tune et pas juste un prompt ?**
- Style stable FR / AR / EN sans dérive.
- Réduction des tokens (prompt système court).
- Conserve le ton « cautious legal advisor » même à basse température.

**Ce qu'il NE fait PAS** : il ne cite **aucun article qui n'est pas déjà dans
le brouillon ou le contexte**. Le quality_guard tourne après lui pour le vérifier.

### Track 2 — Reasoning / Classification & Extraction

**But** : un (ou deux) petit(s) modèle(s) spécialisés en **décision discrète** :

| Tâche | Labels | Appelé par |
|---|---|---|
| `classify_domain` | labor / data_protection / corporate / credit_info / other | `domain_router.py` |
| `classify_case_type` | question / complaint / incident / data_subject_request / other | `case_conversation_service.py` |
| `classify_risk` | low / medium / high | `compliance_case_orchestrator.py` |
| `extract_facts` | JSON {parties, dates, amounts, processing_type, legal_basis_keywords} | `case_conversation_service.py` |

**Pourquoi un fine-tune ici ?**
- Latence : un classifieur ~100M params répond en <50 ms vs 2-4 s d'un LLM
  généraliste.
- Robustesse FR/AR : moins de prompt-engineering.
- Sortie strictement contrainte (label unique, JSON valide).

**Ce qu'il NE fait PAS** : il ne remplace **jamais** la confirmation humaine
quand le score de confiance < seuil. Le système pose une question de
clarification (Human-in-the-loop), comportement déjà présent dans
`compliance_case_orchestrator._generate_clarification_question`.

---

## 2. Flux de données dans l'architecture existante

```
                        USER QUESTION
                             │
              ┌──────────────┴──────────────┐
              │   case_conversation_service │
              │   .extract_context(...)     │
              │   ───────────────────────   │
              │   Track 2 hooks ici :       │
              │   • classify_case_type      │
              │   • extract_facts           │
              └──────────────┬──────────────┘
                             │
              ┌──────────────┴──────────────┐
              │   domain_router             │
              │   .route_question(...)      │
              │   ───────────────────────   │
              │   Track 2 hook :            │
              │   • classify_domain         │
              │   (remplace/renforce le     │
              │    scoring lexical)         │
              └──────────────┬──────────────┘
                             │
              ┌──────────────┴──────────────┐
              │   llm_service.ask_*()       │
              │   RAG + génération brouillon│
              └──────────────┬──────────────┘
                             │
              ┌──────────────┴──────────────┐
              │  compliance_case_orchestrator│
              │  .analyze_and_orchestrate() │
              │   ───────────────────────   │
              │   Track 2 hook :            │
              │   • classify_risk           │
              │     (nourrit OrchestrationResult.risk_level)│
              └──────────────┬──────────────┘
                             │
              ┌──────────────┴──────────────┐
              │  advisor_response_composer  │
              │  .compose_from_orchestration│
              │   ───────────────────────   │
              │   Track 1 hook :            │
              │   • llm_style_formatter     │
              │     .format_advisor_answer()│
              │     remplace _refine_with_llm│
              │     (ou s'enchaîne après)   │
              └──────────────┬──────────────┘
                             │
              ┌──────────────┴──────────────┐
              │  quality_guard_service      │
              │  .audit_and_guard()         │
              │  (inchangé, tourne APRÈS    │
              │   le formatage de style)    │
              └──────────────┬──────────────┘
                             │
                       FINAL ANSWER
```

**Invariant clé** : le `quality_guard_service` est **toujours le dernier
maillon**. Il vérifie que les articles cités sont bien supportés par les
chunks. Le style model peut reformuler mais pas inventer.

---

## 3. Liste des fichiers à créer

### Sous `training/`

| Fichier | Rôle |
|---|---|
| `training/style_dataset_builder.py` | Assemble `style_train.jsonl` / `style_eval.jsonl` à partir de cas existants + exemples curés + synthèses LLM nettoyées. |
| `training/style_finetune.py` | Squelette LoRA / PEFT pour un petit modèle multilingue (Qwen2.5-1.5B / mT5-base / Mistral-7B-LoRA selon GPU). |
| `training/reasoning_dataset_builder.py` | Assemble `reasoning_train.jsonl` / `reasoning_eval.jsonl` (classification + extraction). |
| `training/reasoning_finetune.py` | Squelette d'entraînement classifieur (XLM-R / DistilBERT-multilingual + têtes multi-tâches). |
| `training/style_train.jsonl` | (généré) Données de style. |
| `training/style_eval.jsonl` | (généré) Eval style. |
| `training/reasoning_train.jsonl` | (généré) Données classification/extraction. |
| `training/reasoning_eval.jsonl` | (généré) Eval. |

### Sous `app/services/`

| Fichier | Rôle |
|---|---|
| `llm_style_formatter.py` | Service appelant le modèle Track 1 fine-tuné. Stub par défaut → pass-through markdown. |
| `reasoning_model_service.py` | Service appelant le(s) modèle(s) Track 2. Stubs par défaut → délégation au LLM/lexical existant. |

### Modifications minimales (1-3 lignes par fichier)

| Fichier existant | Modification |
|---|---|
| `advisor_response_composer.py` | Dans `compose_from_orchestration_result`, appeler `llm_style_formatter.format_advisor_answer()` juste avant le retour. |
| `domain_router.py` | Dans `route_question`, ajouter un appel optionnel à `reasoning_model_service.classify_domain()` avec fallback sur le scoring lexical actuel. |
| `case_conversation_service.py` | Dans `extract_context_from_conversation`, ajouter `reasoning_model_service.classify_case_type()` + `extract_facts()` pour enrichir la sortie. |
| `compliance_case_orchestrator.py` | Dans `_assess_risk_level` ou `analyze_and_orchestrate`, fusionner avec `reasoning_model_service.classify_risk()`. |
| `llm_service.py` | Aucune modification obligatoire. Possiblement, exposer une fonction `ask_draft()` que le composer utilisera comme entrée du style formatter. |

---

## 4. Schémas de données (JSONL)

### Track 1 — `style_train.jsonl`

```json
{
  "input": {
    "language": "fr",
    "user_question": "Notre société peut-elle licencier un salarié sans préavis ?",
    "extracted_facts": {
      "parties": ["employeur", "salarié"],
      "case_type": "question"
    },
    "legal_context": [
      {"article_ref": "Code du travail, Art. 14", "text": "..."},
      {"article_ref": "Code du travail, Art. 22", "text": "..."}
    ],
    "findings": [
      {"title": "Préavis non respecté", "severity": "high", "gap": "..."}
    ],
    "actions": [
      {"title": "Documenter le motif", "priority": "high"}
    ],
    "draft_answer": "Le licenciement sans préavis est encadré..."
  },
  "output": "## Ce que j'ai compris\n...\n## Informations manquantes\n...\n## Contexte légal\n- Art. 14 du Code du travail : ...\n## Analyse / risques\n...\n## Actions recommandées\n...\n## Preuves à rassembler\n...\n## Nécessité d'une revue humaine\n..."
}
```

### Track 2 — `reasoning_train.jsonl`

Classification multi-tâches :
```json
{
  "task": "classify",
  "text": "Un employé est venu déposer une réclamation pour heures supplémentaires non payées depuis mars 2024.",
  "language": "fr",
  "labels": {
    "domain": "labor",
    "case_type": "complaint",
    "risk": "medium"
  }
}
```

Extraction :
```json
{
  "task": "extract",
  "text": "Notre filiale à Sousse traite les CV des candidats sur un serveur hébergé en France depuis janvier 2025.",
  "language": "fr",
  "labels": {
    "parties": ["filiale Sousse", "candidats"],
    "dates": ["janvier 2025"],
    "amounts": [],
    "processing_type": "recrutement / RH",
    "legal_basis_keywords": ["transfert international", "données personnelles"]
  }
}
```

---

## 5. Choix techniques recommandés (PFE-friendly)

### Track 1 — modèle de style

| Critère | Recommandation |
|---|---|
| Base | `Qwen2.5-1.5B-Instruct` ou `Mistral-7B-Instruct-v0.3` |
| Méthode | LoRA (PEFT, `r=16`, `alpha=32`, target = q_proj/v_proj) |
| Données | 200-500 exemples suffisent pour du style |
| Hyperparams | LR=2e-4, batch=4 (grad-accum=4), epochs=3, fp16 |
| Eval | BLEU + section-coverage score (les 7 sections présentes ?) |
| Service | Servi via Ollama (export GGUF) ou vLLM local |

### Track 2 — modèles de raisonnement

| Critère | Recommandation |
|---|---|
| Base classification | `xlm-roberta-base` (270M, FR/AR/EN OK, Apache-2.0) |
| Tête | Multi-tâches : 3 têtes softmax (domain, case_type, risk) |
| Base extraction | `xlm-roberta-base` + tête seq2seq, OU instruction-tuning d'un petit LLM (1.5B) en mode JSON-only |
| Données | 300-1000 exemples par tâche |
| Hyperparams classif | LR=2e-5, batch=16, epochs=4, weight_decay=0.01 |
| Service | Serveur HF Transformers léger (`pipeline("text-classification")`) en process séparé, ou simplement chargé in-memory dans `reasoning_model_service.py` |

---

## 6. Bénéfices vs risques en contexte légal

### Bénéfices
- **Style cohérent** : les 7 sections apparaissent toujours, le client voit
  une reponse de qualité « cabinet d'avocats ».
- **Latence** : classification rapide → routing immédiat.
- **Sobriété** : prompts plus courts, moins de tokens, moins de coût.
- **Reproductibilité** : sortie déterministe à `temperature=0`, important pour
  l'audit légal.

### Risques (et comment les couvrir)
| Risque | Mitigation |
|---|---|
| Hallucination d'articles par le style model | Le `quality_guard_service` reste obligatoire **après** le formatage. Toute référence non supportée par les chunks est strippée. |
| Drift de classification (loi qui change) | Re-fine-tuning trimestriel + `confidence_threshold` qui force le LLM généraliste en fallback si < 0.7. |
| Surconfiance du classifieur de risque | Toujours marquer `requires_human_review=True` quand `risk=high`. |
| Données d'entraînement biaisées | Auditer la distribution des labels avant entraînement (script `reasoning_dataset_builder.py` log les histogrammes). |
| Conformité RGPD/INPDP des cas réels | `style_dataset_builder.py` doit pseudonymiser (parties → `EMPLOYEUR_A`, dates exactes → `2025-MM-DD`). |

### Comment ça reste compatible avec les guardrails existants
- `quality_guard_service.audit_and_guard` est appelé **après** le style model
  (inchangé).
- `domain_router.route_question` garde son scoring lexical comme **fallback
  par défaut** si le classifieur Track 2 est indisponible ou peu confiant.
- `compliance_case_orchestrator._generate_clarification_question` est
  déclenché si `extract_facts` retourne trop de champs vides.

---

## 7. Ordre de mise en œuvre recommandé

1. **Stubs d'intégration** (semaine 1) : créer les services `llm_style_formatter`
   et `reasoning_model_service` en mode pass-through. Vérifier que la pipeline
   marche sans modèles.
2. **Dataset builders** (semaine 2) : générer 200 exemples de style et 300
   exemples de classification depuis les cas existants en base.
3. **Train Track 2** (semaine 3) : XLM-R multi-tâches, le plus simple, gain
   immédiat sur le routing.
4. **Train Track 1** (semaine 4) : LoRA sur Qwen2.5-1.5B, exporter en GGUF
   pour Ollama.
5. **Eval bout-en-bout** (semaine 5) : comparer avant/après sur le benchmark
   `tests/benchmark_questions.txt`.
