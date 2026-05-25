# RAPPORT COMPLET — Projet Daleel

**Plateforme RAG de Recherche Juridique Tunisienne**
*Projet de Fin d'Etudes (PFE)*
*Date de generation : 24 mai 2026 (Version 10 Sprints — 3 audits qualite)*

---

## 1. PRESENTATION GENERALE

**Daleel** est une plateforme intelligente d'assistance juridique pour le droit tunisien.
Elle permet l'upload, l'analyse, la recherche semantique et le Q&A sur des documents
juridiques (codes, lois, amendements) via une architecture **RAG** (Retrieval-Augmented
Generation) avec support **multilingue** (arabe, francais, anglais), y compris les PDF
scannes (OCR).

---

## 2. STACK TECHNIQUE

| Composant               | Technologie                                                        |
|-------------------------|--------------------------------------------------------------------|
| **API**                 | FastAPI 0.115+ / Uvicorn (ASGI)                                   |
| **Base de donnees**     | MongoDB 7+ (Motor async)                                          |
| **Embeddings**          | `paraphrase-multilingual-mpnet-base-v2` (768d) + modele fine-tune |
| **LLM**                | Ollama — `qwen2.5:7b`                                             |
| **OCR**                 | Tesseract 5.x (primaire) + EasyOCR (fallback)                     |
| **PDF**                 | PyMuPDF + pdfminer.six                                            |
| **Recherche vectorielle** | FAISS (IndexHNSWFlat, M=32, efConstruction=200) + fallback Python cosine |
| **Reranker**            | Cross-encoder `ms-marco-MiniLM-L-6-v2` (22M params)              |
| **Frontend**            | React.js + Vite (16 pages : 6 principales + 10 admin), i18n FR/AR/EN |
| **CI/CD**               | GitHub Actions — Ruff lint + pytest (Python 3.11/3.12/3.13)       |
| **Auth**                | JWT (HS256) — access token 30min, refresh 7j, blacklist JTI       |
| **Multi-tenant**        | Organisations, rôles (super_admin/owner/admin/member), invitations |
| **Voix**                | faster-whisper (STT) + Piper/Edge-TTS (TTS FR/EN/AR)             |

---

## 3. METRIQUES DU CODE SOURCE

| Composant              | Fichiers | Lignes de code |
|------------------------|----------|----------------|
| **Application** (`backend/app/`) | 65       | ~30 600        |
| **Tests** (`backend/tests/`)     | 37       | ~9 700         |
| **Training pipeline**            | 17       | ~3 800         |
| **Frontend** (React.js/Vite)     | 27       | ~3 700         |
| **Scripts & divers**             | 9        | ~1 000         |
| **TOTAL**                        | **155**  | **~48 800**    |

### Fichiers les plus volumineux
| Fichier                        | Lignes | Role                                  |
|--------------------------------|--------|---------------------------------------|
| `llm_service.py`               | 3 573  | Pipeline RAG, reranking, grounding    |
| `router.py`                    | 2 577  | 79 endpoints API (routeur principal)  |
| `document_service.py`          | 1 587  | Upload, extraction, chunking, cleanup |
| `schemas.py`                   | 755    | Modeles Pydantic (request/response)   |
| `graph_resolver.py`            | 734    | KG Light sur MongoDB (batch queries)  |
| `legal_retrieval_orchestrator` | 392    | Retrieval partitionne base/amendements|

---

## 4. ARCHITECTURE EN SPRINTS

### Sprint 1 — Documents & RAG Core

**Objectif** : Ingestion documentaire, chunking, embedding, recherche semantique, Q&A.

| Fonctionnalite                | Implementation                                                |
|-------------------------------|---------------------------------------------------------------|
| Upload PDF/DOCX/TXT/images    | `document_service.py` — detection format, hashing (dedup)    |
| Extraction texte              | 3 tiers : PyMuPDF -> pdfminer -> OCR (Tesseract/EasyOCR)    |
| Nettoyage texte juridique     | `legal_cleaner.py` — arabic reshaper, bidi, normalisation    |
| Chunking                      | Section-aware sliding window (1500 chars / 200 overlap)      |
| Embedding                     | `embedding_service.py` — SentenceTransformer 768d + LRU cache|
| Recherche vectorielle          | FAISS IndexFlatIP (inner product) + fallback cosine Python   |
| Q&A classique                 | RAG : retrieve top-k -> prompt LLM -> reponse fondee        |
| Q&A agentique                 | Boucle iterative de retrieval avec reformulation de query    |
| Q&A auto-mode                 | Routage automatique classic/agentic selon intent/keywords    |
| Feedback utilisateur          | Corrections stockees, injectees en few-shot dans les prompts |

**Endpoints (12)** : upload, bulk-upload, list, get, chunks, raw-pages, cleaned-pages, delete, search, ask, ask/agentic, ask/auto, feedback

### Sprint 2 — Profils & Applicabilite

**Objectif** : Modeliser l'entreprise et evaluer quelles exigences legales s'appliquent.

| Fonctionnalite                | Implementation                                                |
|-------------------------------|---------------------------------------------------------------|
| Profil entreprise             | CRUD (nom, secteur, taille, activites, juridiction)           |
| Extraction exigences          | LLM analyse chaque page -> obligation/interdiction/condition/sanction |
| Evaluation applicabilite      | LLM compare profil vs exigence -> applicable/non + confiance  |

**Endpoints (6)** : company-profiles (CRUD), exigences extract/list, applicability evaluate/get

### Sprint 3 — Lois, Articles & Versioning

**Objectif** : Structurer le corpus juridique en hierarchie Loi -> Article -> Version.

| Fonctionnalite                | Implementation                                                |
|-------------------------------|---------------------------------------------------------------|
| Gestion des lois              | CRUD + seed automatique (Code travail, Code societes)         |
| Segmentation automatique      | `article_segmenter.py` — regex titre/chapitre/section/article |
| Versioning immutable          | Chaque article a N versions (active/superseded/repealed)      |
| Extraction actions            | LLM decompose exigences -> actions precises + modalite        |

**Endpoints (8)** : lois CRUD, segment-document, articles list, versions list, actions extract/list

### Sprint 4 — Criticite & Feuille de Route

**Objectif** : Prioriser les actions par criticite et generer un plan de conformite.

| Fonctionnalite                | Implementation                                                |
|-------------------------------|---------------------------------------------------------------|
| Scoring criticite             | Moteur a regles (modalite, sanctions, confiance) -> critique/importante/secondaire |
| Dependencies entre actions    | Graphe DAG (prerequis/sequence/maintien)                      |
| Roadmap de conformite         | Tri topologique du DAG + export ordonne par priorite          |

**Endpoints (4)** : compute criticality, create dependency, get dependencies, roadmap

### Sprint 5 — Amendements & Audit

**Objectif** : Gerer les modifications legislatives avec tracabilite complete.

| Fonctionnalite                | Implementation                                                |
|-------------------------------|---------------------------------------------------------------|
| Classification document       | LLM determine si PDF = loi principale ou modificatif          |
| Extraction operations         | LLM extrait ADD/REPLACE/MODIFY/REPEAL avec article cible     |
| Application amendement        | Cree nouvelle version article, desactive l'ancienne           |
| Audit trail                   | Chaque operation tracee avec acteur, preuve, reference legale |
| Recalcul pipeline             | Amendement -> re-extraction exigences/actions/criticite       |

**Endpoints (7)** : classify, extract amendments, list, apply, apply-all, audit-logs, recalculate

### Sprint 6 — RAG Avance & Intelligence

**Objectif** : Ameliorer la qualite des reponses avec des techniques avancees.

| Fonctionnalite                | Implementation                                                |
|-------------------------------|---------------------------------------------------------------|
| **Domain Router**             | Routage lexical+LLM vers domaine juridique (travail, societes, donnees, investissement) |
| **Retrieval partitionne**     | Separation base law vs amendements selon intention (current/historical/compare/audit) |
| **Quality Guard**             | Triple controle post-generation : references, fidelite semantique, langue |
| **KG Light**                  | Graphe de connaissances leger sur MongoDB (Loi->Article->Exigence->Action) |
| **FAISS index**               | Index vectoriel in-memory, rebuild au boot, incremental add/remove |
| **Admin stats**               | Endpoint statistiques (documents, chunks, vecteurs)           |

### Sprint 7 — Case Management

**Objectif** : Gérer des dossiers de conformité (cases) avec gestion d'état, documents liés, actions et priorités.

| Fonctionnalite                | Implementation                                                |
|-------------------------------|---------------------------------------------------------------|
| Case CRUD                     | Création, suivi d'état (open/in_progress/resolved) et priorités|
| Document linking              | Rattachement de documents spécifiques au case                  |
| Findings & Actions            | Suivi des vulnérabilités découvertes et actions de remédiation |

**Endpoints** : cases, case-documents, case-findings, case-actions

### Sprint 8 — Compliance Steering

**Objectif** : Étendre Daleel en plateforme d'opérations de conformité. Mapping des exigences aux contrôles internes, analyse d'écarts (gap analysis), et registre d'exceptions.

| Fonctionnalite                | Implementation                                                |
|-------------------------------|---------------------------------------------------------------|
| Assessments                   | Gap analysis périodique ou déclenchée par un amendement        |
| Contrôles internes            | Mesures préventives/détectives avec scores d'efficacité        |
| Requirement-Control Links     | Jointure (many-to-many) calculant le taux de couverture        |
| Exceptions Register           | Registre d'acceptation des risques, waivers et compensations   |

**Endpoints** : assessments, controls, evidences, links, posture, exceptions

### Sprint 9 — Case Conversation

**Objectif** : Intégrer un système de messagerie interactive au sein d'un case de conformité.

| Fonctionnalite                | Implementation                                                |
|-------------------------------|---------------------------------------------------------------|
| Messaging thread              | Historique de conversation lié à un case spécifique            |
| Fact extraction               | Extraction de contexte conversationnel via LLM                 |

**Endpoints** : case-messages

### Sprint 10 — Orchestrator & Composer

**Objectif** : Orchestrer la résolution des cases via des arbres de décision et générer des réponses formatées.

| Fonctionnalite                | Implementation                                                |
|-------------------------------|---------------------------------------------------------------|
| Compliance Orchestrator       | Arbres de décision automatiques (ASK/CLARIFY/ACT/REVIEW)       |
| Advisor Composer              | Formatage strict Markdown (What I understood, Analysis, Actions)|
| LLM Track 1 & 2               | Intégration de modèles fine-tunés (Style & Reasoning)          |

**Endpoints** : orchestrate-case

---

## 5. COLLECTIONS MONGODB (35)

| Collection                 | Role                                        |
|---------------------------|----------------------------------------------|
| **Documents & RAG**       |                                              |
| `documents`               | Metadata des documents uploades              |
| `document_sources`        | Fichier source + hash (deduplication)        |
| `document_raw_pages`      | Pages brutes extraites                       |
| `document_cleaned_texts`  | Texte nettoye (arabic reshape, etc.)         |
| `chunks`                  | Chunks + embeddings 768d                     |
| `chat_history`            | Historique des conversations Q&A             |
| `qa_feedback`             | Feedback utilisateur pour apprentissage      |
| **Juridique**             |                                              |
| `lois`                    | Registre des lois                            |
| `articles`                | Articles de loi                              |
| `article_versions`        | Versions immutables des articles             |
| `exigences`               | Exigences reglementaires extraites           |
| `actions`                 | Actions reglementaires decomposees           |
| `action_criticalities`    | Scores de criticite                          |
| `action_dependencies`     | Graphe de dependances (DAG)                  |
| `amendment_operations`    | Operations d'amendement (ADD/REPLACE/etc.)   |
| `audit_logs`              | Journal d'audit complet                      |
| **Profils & Applicabilite** |                                            |
| `company_profiles`        | Profils d'entreprise                         |
| `exigence_applicabilities`| Resultats applicabilite profil/exigence      |
| **Case Management**       |                                              |
| `compliance_cases`        | Dossiers de conformite (Case Management)     |
| `case_messages`           | Fil de messages par dossier                  |
| `case_documents`          | Documents specifiques rattaches a un case    |
| `case_document_analyses`  | Analyses documentaires par case              |
| `case_findings`           | Constats de non-conformite par case          |
| `case_actions`            | Actions de remediation par case              |
| **Compliance Steering**   |                                              |
| `compliance_assessments`  | Evaluations de conformite (Gap Analysis)     |
| `controls`                | Mesures et controles internes                |
| `control_evidences`       | Preuves d'application des controles          |
| `requirement_control_links`| Mapping Exigences <-> Controles             |
| `exception_register`      | Registre des exceptions et risques acceptes  |
| **Auth & Multi-tenant**   |                                              |
| `users`                   | Comptes utilisateurs (bcrypt hash)           |
| `organizations`           | Organisations multi-tenant                   |
| `invitations`             | Invitations par email (token + expiration)   |
| `token_blacklist`         | JWT blacklist avec TTL index                 |
| `notifications`           | Notifications utilisateur                    |

---

## 6. PIPELINE DE TRAITEMENT DOCUMENTAIRE

```
PDF/DOCX/Image
    |
    v
[Extraction 3 tiers]
    PyMuPDF (rapide, texte digital)
      -> pdfminer.six (fallback, meilleur arabe)
        -> OCR Tesseract (~1s/page) / EasyOCR (~65s/page, fallback)
    |
    v
[Nettoyage]
    arabic-reshaper + python-bidi + normalisation unicode
    |
    v
[Chunking]
    Section-aware sliding window
    Taille: 1500 chars | Overlap: 200 chars | Min: 60 chars
    |
    v
[Embedding]
    paraphrase-multilingual-mpnet-base-v2 (768 dimensions)
    Cache LRU (512 entrees)
    |
    v
[Stockage]
    MongoDB (chunks collection) + FAISS index (in-memory, rebuild au boot)
```

---

## 7. PIPELINE RAG (Q&A)

```
Question utilisateur
    |
    v
[Detection langue] (ar/fr/en) — regex-based + markers
    |
    v
[Classification intent] (analysis/advice/solution/requirement_management)
    |
    v
[Domain Router] -> data_protection | labor | corporate | investment | cross_domain
    |
    v
[Retrieval partitionne]
    Base law retriever + Amendment retriever
    Mixing ratio selon intent (current/historical/compare/audit)
    |
    v
[Hybrid Reranking]
    Cosine similarity + BM25 lexical + anchor overlap + article ref matching
    |
    v
[KG Light Enrichment]
    Injection sous-graphe Loi->Article->Exigence->Action
    |
    v
[LLM Generation] (Ollama qwen2.5:7b)
    System prompt adapte au domaine + langue
    Feedback past corrections (few-shot)
    |
    v
[Quality Guard]
    1. Validation references (articles cites vs chunks retrieved)
    2. Fidelite semantique (LLM-juge)
    3. Conformite linguistique
    -> Reecriture conservative si echec
    |
    v
[Reponse]
    Answer + sources + metadata (domain, quality_guard_status, kg_enriched)
```

---

## 8. API — 152 ENDPOINTS

| Sprint / Module | Methodes | Exemples principaux                                            |
|-----------------|----------|----------------------------------------------------------------|
| 1               | 12       | upload, search, ask, ask/agentic, ask/auto, feedback           |
| 2               | 6        | company-profiles, exigences, applicability                     |
| 3               | 8        | lois, segment-document, articles, versions, actions            |
| 4               | 4        | criticality compute, dependencies, roadmap                     |
| 5               | 7        | classify, amendments extract/apply, audit-logs, recalculate    |
| 6               | ~29      | admin stats, vector-stats, domain-routing, export, etc.        |
| 7-10            | ~25      | cases, assessments, controls, orchestrate, case-messages       |
| Auth            | 19       | register, login, refresh, logout, me, password, invitations    |
| Compliance      | 22       | assessments, controls, evidences, links, posture, exceptions   |
| Case            | 21       | cases CRUD, findings, actions, documents, states               |
| Orchestrator    | 5        | orchestrate-case, decision trees                               |
| Voix            | 3        | transcribe (STT), synthesize (TTS), voice-chat                 |
| Case Conversation | 3      | case-messages (thread, send, history)                          |

**Securite** : JWT (HS256) access/refresh tokens, blacklist JTI, rate limiting (SlowAPI), bcrypt, XSS escaping.
**Multi-tenant** : Middleware organisation avec roles (super_admin/owner/admin/member).

---

## 9. FRONTEND (React.js + Vite)

| Page             | Fichier                | Description                                           |
|------------------|------------------------|-------------------------------------------------------|
| **Landing**      | `Landing.jsx`          | Page d'accueil, presentation de la plateforme         |
| **Login**        | `Login.jsx`            | Authentification (connexion / inscription)             |
| **Reset Password** | `ResetPassword.jsx`  | Reinitialisation du mot de passe                      |
| **Chat**         | `Chat.jsx`             | Interface Q&A, sources, historique, voix              |
| **Dashboard**    | `Dashboard.jsx`        | Tableau de bord principal utilisateur                 |
| **Invite**       | `Invite.jsx`           | Acceptation d'invitation a une organisation           |
| **Documents**    | `admin/Documents.jsx`  | Upload, gestion documents, stats, vector index        |
| **Users**        | `admin/Users.jsx`      | Gestion des utilisateurs et roles                     |
| **Organizations** | `admin/Organizations.jsx` | Gestion multi-tenant des organisations            |
| **Cases**        | `admin/Cases.jsx`      | Gestion des dossiers de conformite                    |
| **Amendments**   | `admin/Amendments.jsx` | Suivi des amendements legislatifs                     |
| **Company Profile** | `admin/CompanyProfile.jsx` | Profil entreprise pour applicabilite           |
| **Notifications** | `admin/Notifications.jsx` | Centre de notifications                           |
| **History**      | `admin/History.jsx`    | Historique des conversations                          |
| **Contract Analysis** | `admin/ContractAnalysis.jsx` | Analyse multi-passes de contrats (score, risques, clauses) |
| **Settings**     | `admin/Settings.jsx`   | Parametres de la plateforme                           |

**Stack** : React.js 19 + Vite, React Router v7, i18n (FR/AR/EN), CSS variables (dark theme), responsive.
**Build** : `npm run build` → `frontend/dist/` servi par FastAPI en production.

---

## 10. TESTS (604 tests, 37 fichiers)

| Fichier de test                          | Couverture                               |
|------------------------------------------|------------------------------------------|
| `test_api.py`                            | Endpoints principaux (CRUD, search, ask) |
| `test_auth.py`                           | JWT auth, register, login, refresh, roles |
| `test_chunker.py`                        | Chunking section-aware (SHA256 IDs)      |
| `test_reranker.py`                       | Cross-encoder reranking (async)          |
| `test_criticality_service.py`            | Scoring criticite                        |
| `test_domain_router.py`                  | Routage domaine juridique                |
| `test_embedding_cache.py`                | Cache LRU embeddings                     |
| `test_faiss_index.py`                    | Index FAISS                              |
| `test_graph_resolver.py`                 | KG Light (batch queries)                 |
| `test_integration_sprint6.py`            | Integration Sprint 6 end-to-end          |
| `test_legal_retrieval_orchestrator.py`   | Retrieval partitionne                    |
| `test_llm_grounding_validation.py`       | Validation du grounding LLM             |
| `test_llm_helpers.py`                    | Helpers LLM (detection langue, intent)   |
| `test_llm_retry.py`                      | Resilience LLM (retry, backoff)          |
| `test_llm_cache.py`                      | Cache des reponses LLM                   |
| `test_quality_guard_service.py`          | Quality Guard (hallucination)            |
| `test_search_service.py`                 | Service de recherche vectorielle         |
| `test_text_utils.py`                     | Utilitaires texte                        |
| `test_case_service.py`                   | Case Management CRUD                     |
| `test_case_document_service.py`          | Documents rattaches aux cases            |
| `test_case_conversation_service.py`      | Messages et threads case                 |
| `test_compliance_service.py`             | Compliance Steering (assessments, controls) |
| `test_compliance_case_orchestrator.py`   | Arbres de decision (Sprint 10)           |
| `test_advisor_response_composer.py`      | Formatage Advisor Markdown               |
| `test_amendment_service.py`              | Amendements (classify, extract, apply)   |
| `test_document_service_helpers.py`       | Helpers document (cleanup, extraction)   |
| `test_notification_service.py`           | Service de notifications                 |
| `test_feedback_service.py`              | Feedback utilisateur                     |
| `test_finetuned_models.py`               | Modeles fine-tunes (Track 1 & 2)        |
| `test_derja_normalizer.py`               | Normalisation dialecte tunisien          |
| `test_conversation_workflow.py`          | Workflow conversationnel end-to-end      |
| `test_context_rewrite_prompt.py`         | Rewriting de prompts contextuels         |
| `test_request.py`                        | Schemas de requetes                      |
| `test_request_final.py`                  | Validation schemas finale                |
| `conftest.py`                            | Fixtures partagees (MonkeyPatch MongoDB) |

**CI** : GitHub Actions (Python 3.11/3.12/3.13, MongoDB 7, Ruff lint, pytest).
**Resultat** : 604 tests, 0 failures.

---

## 11. PIPELINE D'ENTRAINEMENT (FINE-TUNING)

### Workflow en 4 etapes

| Script                     | Role                                               | Output                    |
|----------------------------|----------------------------------------------------|---------------------------|
| `01_build_eval_set.py`     | Export articles + annotation eval set (25 queries)  | `eval_set.jsonl`          |
| `02_build_train_set.py`    | Paires (query, positive) feedback + synthetique LLM | `train_set_filtered.jsonl`|
| `03_evaluate_retrieval.py` | Benchmark Recall@k, MRR@k, nDCG@k                  | JSON metriques            |
| `04_finetune_embeddings.py`| Fine-tuning MNR loss (PyTorch manuel)               | Modele .safetensors       |

### Donnees

| Fichier                    | Contenu                    | Taille      |
|----------------------------|----------------------------|-------------|
| `articles.jsonl`           | 2 344 articles du corpus   | 2.2 MB      |
| `eval_set.jsonl`           | 25 queries annotees        | 13 KB       |
| `train_set_filtered.jsonl` | 4 584 paires d'entrainement| 4.6 MB      |

### Configuration du fine-tuning

| Parametre        | Valeur                                                  |
|------------------|---------------------------------------------------------|
| Modele base      | `paraphrase-multilingual-mpnet-base-v2` (768d, 278M params) |
| Loss             | MultipleNegativesRankingLoss (contrastive)              |
| Optimizer        | AdamW (lr=2e-5)                                         |
| Scheduler        | Linear warmup 10%                                       |
| Epochs           | 2                                                       |
| Batch size       | 32                                                      |
| Device           | CPU (multi-thread)                                      |
| Duree totale     | ~110 minutes (CPU-only)                                 |
| Modele output    | `model.safetensors` (1.06 GB)                           |

### Resultats du fine-tuning

| Metrique     | Baseline | Fine-tune | **Delta** |
|-------------|----------|-----------|-----------|
| recall@1    | 0.2000   | **0.4800** | **+0.2800** |
| recall@5    | 0.3200   | **0.5600** | **+0.2400** |
| recall@10   | 0.4000   | **0.6000** | **+0.2000** |
| mrr@5       | 0.2400   | **0.5100** | **+0.2700** |
| mrr@10      | 0.2507   | **0.5150** | **+0.2643** |
| ndcg@5      | 0.2597   | **0.5225** | **+0.2628** |
| ndcg@10     | 0.2856   | **0.5351** | **+0.2495** |

**Par langue** :
- **Francais** : recall@5 `0.53 -> 0.87` (+0.33) | mrr@10 `0.42 -> 0.79` (+0.37)
- **Arabe** : recall@5 `0.00 -> 0.10` | mrr@10 `0.00 -> 0.10` (amelioration legere)

> **Interpretation** : +24 a +28 points de Recall@k et +26 points de MRR apres seulement
> 2 epochs. Le modele fine-tune est significativement meilleur pour retrouver les articles
> juridiques pertinents, surtout en francais. L'arabe reste faible (corpus OCR bruite).

### Fine-Tuning LLM (Tracks 1 & 2)

Pour améliorer l'orchestration et le formatage sans perturber le pipeline RAG déterministe, deux modèles spécialisés ont été intégrés (Fail-Safe / Passthrough) :

1.  **Track 1 : Response Style & Format** (`llm_style_formatter.py`)
    - *Objectif :* Stabiliser la sortie du Legal Advisor dans un format Markdown strict (7 sections).
    - *Technique :* LoRA / PEFT sur un petit modèle (Qwen2.5-1.5B / Mistral-7B).

2.  **Track 2 : Reasoning, Classification & Extraction** (`reasoning_model_service.py`)
    - *Objectif :* Améliorer le routage (Domain Router), le triage et l'extraction de faits.
    - *Technique :* Classifieur multi-tâches (XLM-RoBERTa-base) rapide (<50ms CPU).

---

## 12. CORPUS JURIDIQUE

| Document                            | Langue | Taille |
|-------------------------------------|--------|--------|
| Code des societes commerciales      | FR     | 1.6 MB |
| Code du travail                     | FR     | 1.4 MB |
| Loi 63-2004 (donnees personnelles)  | FR     | 0.1 MB |
| Loi societes commerciales (arabe)   | AR     | 1.7 MB |
| Code du travail (arabe)             | AR     | 0.9 MB |
| Exemple amendement 2025             | FR     | texte  |

**Total** : ~5.7 MB de PDFs juridiques -> 2 344 articles extraits.

---

## 13. CONTRIBUTIONS SCIENTIFIQUES (PFE)

Les modules Sprint 6+ incluent des commentaires "Contribution scientifique" qui
documentent les apports methodologiques :

1. **Domain-Adaptive RAG** (`domain_router.py`)
   Routage lexical+LLM vers domaines juridiques specialises, ajustant dynamiquement
   la configuration de recherche sans intervention humaine.

2. **Retrieval Partitionne** (`legal_retrieval_orchestrator.py`)
   Separation base law / amendements pour eviter le melange de sources contradictoires.
   Mixing ratio pilote par l'intention utilisateur.

3. **Quality Guard** (`quality_guard_service.py`)
   Triple controle post-generation (references, fidelite semantique, langue) pour
   reduire les hallucinations dans un contexte juridique critique.

4. **KG Light** (`graph_resolver.py`)
   Graphe de connaissances leger nativement integre a MongoDB, enrichissant le contexte
   RAG avec les relations Loi->Article->Exigence->Action sans base graphe externe.

5. **Fine-tuning domain-specific** (pipeline `training/`)
   Adaptation du modele d'embedding au vocabulaire juridique tunisien via MNR loss,
   avec benchmark quantitatif avant/apres (+28 points recall@1).

---

## 14. CONFIGURATION & DEPLOIEMENT

### Variables d'environnement (`.env`)

| Variable                                | Role                              | Defaut                    |
|-----------------------------------------|-----------------------------------|---------------------------|
| `DALEEL_MONGODB_URL`                     | URI MongoDB                       | `mongodb://localhost:27017` |
| `DALEEL_LLM_MODEL`                       | Modele Ollama                     | `qwen2.5:7b`             |
| `DALEEL_EMBEDDING_MODEL`                 | Modele embedding                  | HF mpnet-base-v2          |
| `DALEEL_VECTOR_SEARCH_BACKEND`           | Backend recherche                 | `faiss`                   |
| `DALEEL_API_KEY`                          | Cle API (vide = desactive)        | vide                      |
| `DALEEL_QUALITY_GUARD_ENABLED`           | Controle hallucination            | `true`                    |
| `DALEEL_DOMAIN_ROUTER_ENABLED`           | Routage domaine                   | `true`                    |
| `DALEEL_KG_LIGHT_ENABLED`               | Enrichissement KG                 | `true`                    |
| `DALEEL_PARTITIONED_RETRIEVAL_ENABLED`   | Retrieval partitionne             | `true`                    |

### Prerequis

- Python 3.11+
- MongoDB 7+
- Ollama + `qwen2.5:7b`
- Tesseract 5.x (optionnel, pour OCR)

### Lancement (developpement)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# -> http://localhost:8000/docs (Swagger)

# Frontend (dev server)
cd frontend
npm install && npm run dev
# -> http://localhost:5173

# Production (Docker)
docker-compose up --build -d
# -> http://localhost:8000 (app complete)
```

---

## 15. STRUCTURE DU PROJET

```
Daleel/
|-- .github/workflows/ci.yml              # CI GitHub Actions
|-- backend/
|   |-- app/
|   |   |-- main.py                        # Point d'entree FastAPI + lifespan + cleanup
|   |   |-- config.py                      # Settings Pydantic (~30 params)
|   |   |-- database.py                    # Motor client, indexes, seeds
|   |   |-- schemas.py                     # 40+ modeles Pydantic
|   |   |-- limiter.py                     # Rate limiting (SlowAPI)
|   |   |-- api/
|   |   |   |-- router.py                  # 79 endpoints principaux
|   |   |   |-- auth_router.py             # 19 endpoints auth (JWT, register, login)
|   |   |   |-- compliance_router.py       # 22 endpoints Compliance Steering
|   |   |   |-- case_router.py             # 21 endpoints Case Management
|   |   |   |-- case_conversation_router.py # 3 endpoints messages case
|   |   |   |-- case_orchestrator_router.py # 5 endpoints orchestration
|   |   |   |-- voice_router.py            # 3 endpoints STT/TTS
|   |   |   |-- auth.py                    # JWT auth + API Key (constant-time)
|   |   |   |-- tenant.py                  # Multi-tenant middleware (X-Org-Id)
|   |   |-- services/
|   |   |   |-- llm_service.py             # Pipeline RAG complet (~3500 lignes)
|   |   |   |-- compliance_case_orchestrator.py # Arbres de decision (Sprint 10)
|   |   |   |-- advisor_response_composer.py    # Formatage LLM (Sprint 10)
|   |   |   |-- case_service.py            # Case Management (Sprint 7)
|   |   |   |-- compliance_service.py      # Compliance Steering (Sprint 8)
|   |   |   |-- llm_style_formatter.py     # LLM Track 1 (LoRA/PEFT)
|   |   |   |-- reasoning_model_service.py # LLM Track 2 (XLM-RoBERTa)
|   |   |   |-- document_service.py        # Upload, extraction, chunking, cleanup
|   |   |   |-- search_service.py          # Recherche vectorielle
|   |   |   |-- embedding_service.py       # SentenceTransformer + cache + thread-safe
|   |   |   |-- reranker.py                # Cross-encoder async (asyncio.Lock)
|   |   |   |-- faiss_index.py             # Index FAISS in-memory
|   |   |   |-- voice_service.py           # STT (faster-whisper) + TTS (Piper/Edge)
|   |   |   |-- domain_router.py           # Routage domaine juridique
|   |   |   |-- legal_retrieval_orchestrator.py  # Retrieval partitionne
|   |   |   |-- quality_guard_service.py   # Anti-hallucination
|   |   |   |-- graph_resolver.py          # KG Light (batch $in queries)
|   |   |   |-- loi_service.py             # Gestion lois + segmentation
|   |   |   |-- action_service.py          # Extraction actions
|   |   |   |-- amendment_service.py       # Amendements (25KB)
|   |   |   |-- criticality_service.py     # Scoring criticite
|   |   |   |-- roadmap_service.py         # Feuille de route conformite
|   |   |   |-- applicability_service.py   # Evaluation applicabilite
|   |   |   |-- feedback_service.py        # Apprentissage par feedback
|   |   |   |-- audit_service.py           # Journal d'audit
|   |   |   |-- auth_service.py            # JWT tokens, bcrypt, blacklist
|   |   |   |-- email_service.py           # Emails HTML (XSS-safe)
|   |   |   |-- notification_service.py    # Notifications temps-reel
|   |   |   |-- recalculation_service.py   # Pipeline recalcul post-amendement
|   |   |   |-- analytics_service.py       # Stats admin
|   |   |   |-- export_service.py          # Export Excel/CSV
|   |   |   |-- index_consistency_service.py # Verification coherence FAISS/modele
|   |   |-- processing/
|   |   |   |-- extractor.py               # Extraction PDF/DOCX/images
|   |   |   |-- ocr.py                     # Tesseract + EasyOCR
|   |   |   |-- chunker.py                 # Chunking section-aware (SHA256)
|   |   |   |-- legal_cleaner.py           # Nettoyage texte arabe/francais
|   |   |   |-- article_segmenter.py       # Segmentation en articles
|   |   |   |-- text_utils.py              # Utilitaires texte
|   |-- tests/                             # 37 fichiers, ~9 700 lignes, 604 tests
|   |   |-- conftest.py                    # Fixtures partagees (MongoDB mock)
|   |   |-- test_api.py                    # Endpoints (CRUD, search, ask, agentic)
|   |   |-- test_auth.py                   # JWT auth complet
|   |   |-- test_reranker.py               # Cross-encoder async
|   |   |-- test_chunker.py                # Chunking + SHA256
|   |   |-- test_case_*.py                 # Case Management (3 fichiers)
|   |   |-- test_compliance_*.py           # Compliance (2 fichiers)
|   |   |-- test_advisor_response_composer.py
|   |   |-- ... (34 fichiers de test)
|   |-- requirements.txt                   # 30+ dependances
|-- frontend/
|   |-- src/
|   |   |-- pages/                         # 16 pages React (6 principales + 10 admin)
|   |   |-- components/                    # Composants reutilisables
|   |   |-- utils/                         # AuthContext, authFetch, helpers
|   |   |-- locales/                       # Traductions FR/AR/EN (react-i18next)
|   |-- vite.config.js                     # Configuration Vite
|   |-- package.json                       # React 19, Vite, react-i18next
|-- data/                                  # PDFs juridiques source (~5.7 MB)
|-- training/
|   |-- 01_build_eval_set.py               # Annotation eval set
|   |-- 02_build_train_set.py              # Generation train set
|   |-- 03_evaluate_retrieval.py           # Benchmark retrieval
|   |-- 04_finetune_embeddings.py          # Fine-tuning PyTorch
|   |-- INTEGRATION.md                     # Guide integration modele
|   |-- data/                              # Datasets (articles, eval, train)
|   |-- models/daleel-embedding-finetuned/ # Modele fine-tune (1.06 GB)
|-- Dockerfile                             # Image Docker multi-stage
|-- docker-compose.yml                     # Orchestration (app + MongoDB + Ollama)
|-- reset_and_rebuild.ps1                  # Script reinitialisation
```

---

## 16. SECURITE & AUDITS QUALITE

### Systeme d'authentification

| Composant                 | Implementation                                              |
|---------------------------|-------------------------------------------------------------|
| **Mots de passe**         | bcrypt (auto-salt, cost factor 12)                          |
| **Access token**          | JWT HS256, 30 min TTL, claims `jti` + `iat`                |
| **Refresh token**         | JWT HS256, 7 jours TTL                                      |
| **Blacklist**             | Collection MongoDB avec TTL index (expiration automatique)  |
| **Rate limiting**         | SlowAPI — 3/min sur `/me/password`, global configurable     |
| **XSS**                   | `html.escape()` sur les URLs injectees dans les emails HTML |
| **Multi-tenant**          | Isolation par `organization_id`, middleware `X-Org-Id`       |
| **Roles**                 | super_admin, owner, admin, member — avec verification RBAC  |

### 3 Audits de qualite realises

| Audit | Corrections | Themes principaux                                            |
|-------|-------------|--------------------------------------------------------------|
| **#1** | 15 taches  | Blacklist JWT, Dockerfile, code mort, indexes DB, CI/CD      |
| **#2** | 1 tache    | Session expiree frontend (authFetch)                         |
| **#3** | 10 taches  | Sécurité (MD5→SHA256, rate limiting, XSS), performance (N+1 queries, pagination, thread-safety), qualite (code mort, duplication, cleanup uploads) |

### Corrections notables (Audit #3)

| Categorie     | Avant                                    | Apres                                          |
|---------------|------------------------------------------|-------------------------------------------------|
| Hashing       | MD5 (chunk IDs)                          | SHA256 (16 chars)                               |
| Imports       | `__import__("pymongo")`                  | `from pymongo import ReturnDocument`            |
| Queries       | N+1 dans graph_resolver (3 boucles)      | Batch `$in` queries (1 requete par type)        |
| Pagination    | `to_list(length=None)` (unbounded)       | `to_list(length=5000)` (capped)                 |
| Concurrence   | `threading.Lock` dans code async         | `asyncio.Lock` (reranker) + thread-safe globals |
| Code mort     | `_get_detect_query_language()` (inutile) | Supprime                                        |
| Duplication   | 3 blocs AR/FR/EN (~105 lignes)           | `_SYNTHESIS_PARAMS` dict (config-driven)        |
| Cleanup       | Fichiers orphelins accumules             | `cleanup_orphaned_uploads()` au demarrage       |

---

## 17. DEPLOIEMENT DOCKER

### Architecture

```
docker-compose.yml
  |-- daleel-app     (Dockerfile multi-stage: Python + Node build)
  |-- mongo          (MongoDB 7 officiel)
  |-- ollama         (Ollama avec qwen2.5:7b)
```

### Dockerfile (multi-stage)

| Stage          | Role                                                      |
|----------------|-----------------------------------------------------------|
| **frontend**   | Node 22 : `npm ci && npm run build` → `/app/dist/`       |
| **backend**    | Python 3.11-slim : pip install, copie app + dist          |
| **runtime**    | Uvicorn sur port 8000, healthcheck `/api/v1/health`       |

### Commandes

```bash
# Build et lancement
docker-compose up --build -d

# Verification
curl http://localhost:8000/api/v1/health
```

---

## 18. RESUME QUANTITATIF

| Metrique                        | Valeur           |
|---------------------------------|------------------|
| Lignes de code total            | ~48 800          |
| Fichiers Python (app)           | 65               |
| Fichiers de test                | 37               |
| Tests unitaires                 | 604              |
| Endpoints API                   | 152              |
| Collections MongoDB             | 35               |
| Schemas Pydantic                | ~100+            |
| Services metier                 | 37               |
| Sprints implementes             | 10               |
| Audits qualite realises         | 3 (26 corrections)|
| Pages frontend React            | 15               |
| Documents juridiques            | 6 PDFs (5.7 MB)  |
| Articles extraits               | 2 344            |
| Paires d'entrainement           | 4 584            |
| Queries d'evaluation            | 25               |
| Taille modele fine-tune         | 1.06 GB          |
| Amelioration recall@1           | +140% (0.20->0.48)|
| Amelioration recall@5           | +75% (0.32->0.56) |
| Langues supportees              | FR, AR, EN       |

---

*Rapport genere depuis l'analyse du code source — derniere mise a jour : 24 mai 2026.*
