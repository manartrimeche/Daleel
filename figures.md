# Figures pour le rapport Daleel — sources Mermaid

> **Usage** : copier chaque bloc dans https://mermaid.live → exporter en PNG ou SVG → insérer dans le rapport à la place du diagramme ASCII.
> En local : extension VS Code "Markdown Preview Mermaid Support" affiche le rendu directement.

---

## Figure 1.1 — Cycle CRISP-DM appliqué à Daleel

À insérer dans la section **1.6.1.1** (remplace le schéma ASCII actuel).

```mermaid
flowchart TD
    P1[**Phase 1**<br/>Compréhension<br/>du métier<br/><br/>Besoins juristes / DSI<br/>5 domaines prioritaires]
    P2[**Phase 2**<br/>Compréhension<br/>des données<br/><br/>Corpus JORT 5.7 Mo<br/>2344 articles, ar/fr<br/>encodages, OCR]
    P3[**Phase 3**<br/>Préparation<br/>des données<br/><br/>Extraction 3 niveaux<br/>Nettoyage arabe 11 ét.<br/>Segmentation + chunks]
    P4[**Phase 4**<br/>Modélisation<br/><br/>Fine-tuning MPNet<br/>RAG 6 modules<br/>Agent ReAct 12 outils<br/>Garde-qualité<br/>Compliance Operations]
    P5[**Phase 5**<br/>Évaluation<br/><br/>Recall@k, MRR, nDCG<br/>Ablation modules<br/>Audit garde-qualité<br/>52 tests]
    P6[**Phase 6**<br/>Déploiement<br/><br/>Docker multi-stage<br/>GitHub Actions<br/>UI React<br/>Multi-tenant]

    P1 --> P2 --> P3 --> P4 --> P5 --> P6

    P5 -.itération 1<br/>fine-tuning.-> P4
    P4 -.itération 2<br/>renforcement<br/>nettoyage arabe.-> P3
    P5 -.itération 3<br/>ré-évaluation.-> P2

    classDef phase fill:#e0e7ff,stroke:#4338ca,stroke-width:2.5px,color:#1e1b4b;
    classDef iter stroke:#dc2626,color:#7f1d1d;
    class P1,P2,P3,P4,P5,P6 phase;
```

> Les flèches pointillées rouges illustrent les itérations effectives du projet — caractéristiques fondamentales de la méthodologie CRISP-DM, qui n'est pas un cycle linéaire en cascade.

---

## Figure 2.1 — Arbre de décision ASK / CLARIFY / ACT / REVIEW

À insérer dans la section **2.8.3** du rapport (remplace le schéma ASCII).

```mermaid
flowchart TD
    Start([Analyse du dossier de conformité]) --> CheckFacts{facts_missing > 2<br/>OU confiance < 0.60 ?}

    CheckFacts -->|Oui| ASK[/ASK<br/>Demander des informations<br/>complémentaires/]
    CheckFacts -->|Non| CheckDocs{Contradictions<br/>documentaires<br/>détectées ?}

    CheckDocs -->|Oui| CLARIFY[/CLARIFY<br/>Désambiguïser<br/>les sources/]
    CheckDocs -->|Non| CheckCrit{Constat critique<br/>avec confiance < 0.70 ?}

    CheckCrit -->|Oui| REVIEW[/REVIEW<br/>Revue humaine<br/>experte recommandée/]
    CheckCrit -->|Non| CheckReady{Faits ≥ 3<br/>ET confiance ≥ 0.70 ?}

    CheckReady -->|Oui| ACT[/ACT<br/>Procéder aux constats<br/>et plan d'action/]
    CheckReady -->|Non| CLARIFY

    classDef decision fill:#fff4e6,stroke:#d97706,stroke-width:2px;
    classDef action fill:#e0f2fe,stroke:#0369a1,stroke-width:2px;
    classDef start fill:#dcfce7,stroke:#15803d,stroke-width:2px;
    class Start start;
    class CheckFacts,CheckDocs,CheckCrit,CheckReady decision;
    class ASK,CLARIFY,ACT,REVIEW action;
```

---

## Figure 2.2 — Modèle conceptuel de la hiérarchie juridique

À insérer dans la section **2.9.1**.

```mermaid
flowchart LR
    Loi[Loi<br/>code, titre, date] --> Article[Article<br/>article_key, numéro]
    Article --> Version[ArticleVersion<br/>version_number<br/>is_current, is_base_version]
    Version --> Amendment[AmendmentOperation<br/>type: additive | substitutive<br/>modificative | abrogative]
    Amendment -.modifie.-> Version

    Version --> Exigence[Exigence<br/>type: obligation, sanction,<br/>condition, interdiction]
    Exigence --> Action[Action<br/>modalité, texte, contexte]
    Action --> Criticality[ActionCriticality<br/>level: critique / importante<br/>/ secondaire<br/>score, reasons]
    Action --> Dependency[ActionDependency<br/>depends_on_action_id]

    classDef ent fill:#e0e7ff,stroke:#4338ca,stroke-width:2px;
    classDef rel fill:#fef3c7,stroke:#d97706,stroke-width:1.5px,stroke-dasharray: 5 5;
    class Loi,Article,Version,Exigence,Action,Criticality ent;
    class Amendment,Dependency rel;
```

---

## Figure 2.3 — Modèle conceptuel du cycle de conformité

À insérer dans la section **2.9.2**.

```mermaid
flowchart TB
    Profile[CompanyProfile<br/>secteur, effectif, périmètre] --> Case[ComplianceCase<br/>contexte, statut]

    Case --> Msg[CaseMessage<br/>historique LLM]
    Case --> Doc[CaseDocument<br/>pièces analysées par OCR + LLM]
    Case --> Finding[CaseFinding<br/>severity, confidence_score]
    Case --> Assessment[ComplianceAssessment<br/>posture globale, score]

    Finding --> Action[CaseAction<br/>plan correctif, échéance]
    Action --> Evidence[ControlEvidence<br/>preuves de mise en conformité]
    Action --> Control[Control<br/>préventif / détectif / correctif]

    Profile -.applicabilité.-> Exigence[Exigence réglementaire]
    Exigence -.contrevenue par.-> Finding
    Exigence -.couverte par.-> Control

    Case --> Exception[ExceptionRegister<br/>acceptation de risque<br/>compensating control]

    classDef profil fill:#dcfce7,stroke:#15803d,stroke-width:2px;
    classDef case fill:#e0e7ff,stroke:#4338ca,stroke-width:2px;
    classDef artefact fill:#fef3c7,stroke:#d97706,stroke-width:1.5px;
    classDef exterieur fill:#f3e8ff,stroke:#7e22ce,stroke-width:1.5px,stroke-dasharray: 4 4;

    class Profile profil;
    class Case,Msg,Doc,Finding,Action,Assessment,Evidence,Control,Exception case;
    class Exigence exterieur;
```

---

## Figure bonus — Architecture globale en 5 couches × 2 volets (Fig 2.1 du rapport)

À insérer dans la section **2.2.2** (remplace le tableau seul par un schéma visuel + tableau).

```mermaid
flowchart TB
    subgraph Présentation
        UI1[Chatbot Chat.jsx]
        UI2[Admin Panel<br/>12 pages]
        UI3[Dashboard BI]
        UI4[Assistant vocal]
    end

    subgraph API_REST["API REST — FastAPI"]
        R1[router.py<br/>Legal RAG]
        R2[case_router<br/>Compliance]
        R3[auth_router<br/>JWT + MFA]
        R4[case_orchestrator_router]
    end

    subgraph Services["Services métier — 40 modules"]
        direction LR
        SR1["**Volet Legal RAG**<br/>search_service<br/>legal_retrieval_orchestrator<br/>autonomous_agent<br/>reranker, quality_guard<br/>embedding_service, llm_service"]
        SR2["**Volet Compliance Operations**<br/>compliance_case_orchestrator<br/>criticality_service, action_service<br/>applicability_service, roadmap_service<br/>case_service, audit_service"]
    end

    subgraph Processing["Traitement documentaire"]
        P1[Extractor 3 niveaux]
        P2[Nettoyage arabe 11 étapes]
        P3[Article segmenter]
        P4[Chunker]
        P5[Derja normalizer]
    end

    subgraph Persistance["Persistance"]
        DB[(MongoDB 7.0<br/>35 collections)]
        FAISS[(FAISS HNSW<br/>en mémoire<br/>M=32, efC=200)]
        CACHE[(Cache LRU<br/>embeddings 512<br/>+ LLM cache)]
    end

    Présentation --> API_REST
    API_REST --> Services
    Services --> Processing
    Services --> Persistance
    Processing --> Persistance

    classDef ui fill:#dbeafe,stroke:#1d4ed8;
    classDef api fill:#fef3c7,stroke:#d97706;
    classDef svc fill:#e0e7ff,stroke:#4338ca;
    classDef proc fill:#fce7f3,stroke:#be185d;
    classDef pers fill:#dcfce7,stroke:#15803d;

    class UI1,UI2,UI3,UI4 ui;
    class R1,R2,R3,R4 api;
    class SR1,SR2 svc;
    class P1,P2,P3,P4,P5 proc;
    class DB,FAISS,CACHE pers;
```

---

## Figure bonus — Pipeline RAG à 6 modules (flux d'une requête)

À insérer dans la section **2.4** (intro du pipeline).

```mermaid
flowchart LR
    Q[Question<br/>utilisateur] --> Norm[Détection langue<br/>+ derja normalizer]
    Norm --> Emb[Encodage<br/>768d MPNet finetuné<br/>cache LRU]

    Emb --> M1["Module 1<br/>Recherche hybride<br/>FAISS ∥ BM25<br/>RRF k=60"]
    M1 --> M2["Module 2<br/>Cross-encoder<br/>ms-marco-MiniLM-L-6-v2<br/>seuil -2.0"]
    M2 --> M3["Module 3<br/>Routeur de domaine<br/>5 domaines + fallback LLM"]
    M3 --> M4["Module 4<br/>Retrieval partitionné<br/>base vs amendement<br/>piloté par intention"]
    M4 --> M5["Module 5<br/>KG Light<br/>Loi → Article → Exigence<br/>→ Action → Criticité"]
    M5 --> LLM[qwen2.5:7b<br/>via Ollama<br/>T=0.15, top_p=0.9]
    LLM --> M6["Module 6<br/>Garde-qualité<br/>références + citations<br/>fenêtre glissante 4-8 mots"]
    M6 --> R[Réponse<br/>+ sources<br/>+ qg_status]

    classDef io fill:#dbeafe,stroke:#1d4ed8,stroke-width:2px;
    classDef mod fill:#e0e7ff,stroke:#4338ca,stroke-width:2px;
    classDef ext fill:#fef3c7,stroke:#d97706,stroke-width:2px;

    class Q,R io;
    class Norm,Emb,M1,M2,M3,M4,M5,M6 mod;
    class LLM ext;
```

---

## Figure bonus — Boucle ReAct de l'agent autonome

À insérer dans la section **2.5.1** ou **3.5.2**.

```mermaid
flowchart TD
    Start([Question<br/>+ profil entreprise]) --> Ctx[Construction du contexte<br/>system prompt + few-shot<br/>+ historique + langue]
    Ctx --> Call[Appel Ollama<br/>/api/chat avec tools<br/>retry exponentiel x3]
    Call --> Decide{Réponse contient<br/>tool_calls ?}

    Decide -->|Non — texte final| Format[_enforce_output_format<br/>4 blocs, ≤ 400 mots]
    Decide -->|Oui| Tools[Exécution outils en parallèle<br/>timeout par outil<br/>résultat tronqué 4000 chars]

    Tools --> Log[ToolCallRecord<br/>iteration, args, durée]
    Log --> Append[Injection résultat<br/>comme message tool]
    Append --> Budget{Itérations &lt; max<br/>ET temps &lt; timeout ?}

    Budget -->|Oui| Call
    Budget -->|Non| Force[Forcer réponse finale<br/>sans nouvel outil]
    Force --> Format

    Format --> LangCheck{Bonne langue ?}
    LangCheck -->|Non| Translate[Traduction LLM]
    LangCheck -->|Oui| QG[Garde-qualité<br/>audit_and_guard]
    Translate --> QG

    QG --> End([Réponse + sources<br/>+ tool_calls_log<br/>+ qg_status])

    classDef start fill:#dcfce7,stroke:#15803d,stroke-width:2px;
    classDef decision fill:#fff4e6,stroke:#d97706,stroke-width:2px;
    classDef action fill:#e0e7ff,stroke:#4338ca,stroke-width:2px;
    classDef end_ fill:#dbeafe,stroke:#1d4ed8,stroke-width:2px;

    class Start start;
    class End end_;
    class Decide,Budget,LangCheck decision;
    class Ctx,Call,Tools,Log,Append,Force,Format,Translate,QG action;
```

---

## Comment intégrer les figures dans Pandoc/PDF

Une fois les PNG/SVG exportés depuis mermaid.live, placer dans `figures/` à la racine et remplacer dans le rapport :

```markdown
**Figure 2.1 — Arbre de décision de l'orchestrateur Compliance Operations.**

![Arbre ASK/CLARIFY/ACT/REVIEW](figures/fig_2_1_decision_tree.png)
```

Pour Word/LibreOffice, importer les SVG directement (rendu vectoriel net à l'impression).
