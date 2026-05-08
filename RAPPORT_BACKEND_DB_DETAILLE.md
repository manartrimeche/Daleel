# Rapport backend + base de donnees (version tres detaillee)

## Resume executif
Ce rapport detaille decrit le backend et la base de donnees du projet Daleel, une plateforme RAG juridique et Compliance Ops. Il couvre l architecture technique, les services metier, les flux fonctionnels, les schemas MongoDB, la logique d integrite, les indexes, ainsi que les risques et recommandations. Le backend est concu en couches (API, services, processing, persistence) avec un pipeline RAG multi-etapes et un module de compliance avance. Les points forts sont la separation claire des responsabilites, la robustesse du pipeline RAG et la tracabilite via audit logs. Les principaux risques concernent la securite operationnelle (rate limiting, CSP), la dette technique (modules monolithiques) et la scalabilite de la recherche vectorielle (IndexFlatIP pour grands volumes).

## Table des matieres
1. Contexte et objectifs
2. Architecture generale du backend
3. Couche API
4. Couche services metier
5. Couche processing documentaire
6. Couche persistence et acces aux donnees
7. Modele de donnees MongoDB
8. Flux RAG detaille (question-reponse)
9. Flux compliance detaille (case orchestration)
10. Amendements, versioning et audit
11. Indexation et performance
12. Securite backend
13. Observabilite et monitoring
14. Tests et qualite
15. Limites, risques, recommandations
16. Conclusion
17. Annexes

## 1. Contexte et objectifs
Le backend de Daleel doit remplir deux objectifs complementaires:
- RAG juridique: ingestion de documents, extraction de contenu, recherche vectorielle, generation de reponses guidees par sources.
- Compliance Ops: gestion de cas, evaluation de conformite, evidences, exceptions, et orchestration de remediation.

Ce double objectif impose un backend a la fois robuste (multi-etapes, validation) et tracable (audit et sources). Le choix d une architecture en couches et d une base de donnees documentaire (MongoDB) permet de modeliser efficacement des objets complexes et heterogenes.

## 2. Architecture generale du backend
L architecture suit un schema en couches:
- API Layer: endpoints FastAPI, validation des inputs, orchestration.
- Service Layer: logique metier, pipeline RAG, compliance, orchestration.
- Processing Layer: extraction, OCR, nettoyage, chunking.
- Persistence Layer: acces MongoDB, indexes, seed, audit.

Le lifecycle applicatif est centralise dans l application principale (initialisation DB, rebuild index FAISS, fermeture propre). Cela garantit la coherence entre la couche persistante et la couche de recherche vectorielle.

## 3. Couche API
### 3.1. Role
La couche API est responsable de:
- valider les donnees entrantes (schemas Pydantic)
- appliquer l authentification (API key)
- router les requetes vers les services appropries
- normaliser les reponses (format JSON, erreurs standard)

### 3.2. Organisation des routeurs
Les routeurs sont segmentes par domaine:
- documents et RAG
- profils entreprise et applicabilite
- lois, articles, versions et actions
- amendements et audit
- compliance cases
- compliance steering
- orchestration

### 3.3. Gestion des erreurs
Le backend retourne des erreurs standardisees (HTTPException). Les erreurs metier sont encapsulees, avec un message clair. Le traitement LLM renvoie des messages generiques en cas de panne, afin de ne pas exposer des details internes.

## 4. Couche services metier
### 4.1. Services documentaires
- document_service: ingestion, validation, extraction multi-niveaux, nettoyage, chunking.
- embedding_service: conversion texte-vecteurs, cache LRU.
- search_service: retrieval vectoriel, fallback cosine.
- faiss_index: index vectoriel in-memory, rebuild au boot.

### 4.2. Services RAG
- llm_service: pipeline complet detection langue, intent, routing, retrieval, reranking, prompt, generation, validation.
- quality guard: validation references, fidelite semantique, conformite linguistique.

### 4.3. Services compliance
- case_service: CRUD des cas, findings, actions.
- case_conversation_service: extraction facts, gestion des messages.
- compliance_case_orchestrator: pipeline decisionnel ASK/ACT/REVIEW.
- compliance_service: assessments, controls, evidences, exceptions.

### 4.4. Services transverses
- audit_service: journalisation des operations critiques.
- criticality_service: scoring de criticite des actions.
- roadmap_service: generation de roadmap a partir d un DAG.

## 5. Couche processing documentaire
### 5.1. Extraction
Extraction multi-etapes pour maximiser la couverture:
1. PyMuPDF (rapide, PDF natifs)
2. pdfminer (fallback pour layout complexe)
3. OCR (Tesseract, puis EasyOCR)

### 5.2. Nettoyage
Nettoyage du texte juridique, avec gestion des particularites arabes (reshaper, bidi) et normalisation unicode.

### 5.3. Chunking
Chunking par fenetre glissante, section-aware:
- taille chunk: 1500 caracteres
- overlap: 200 caracteres
- seuil minimum pour eviter les chunks trop courts

Ce choix privilegie la stabilite et la reproductibilite.

## 6. Couche persistence et acces aux donnees
### 6.1. MongoDB
MongoDB est utilise pour stocker des documents heterogenes: textes, metadonnees, embeddings, audit logs, objets compliance.

### 6.2. Indexes
Les indexes sont definis au boot, afin de garantir:
- deduplication (hash document)
- performance sur collections critiques
- unicite des relations (requirement-control links)

### 6.3. Coherence des donnees
La coherence est assuree par:
- IDs uniques (UUID)
- versioning immutable des articles
- audit logs pour operations sensibles
- recalculs automatiques apres amendements

## 7. Modele de donnees MongoDB
### 7.1. Bloc Documents et RAG
Collections principales:
- documents
- document_sources
- document_raw_pages
- document_cleaned_texts
- chunks
- qa_feedback

Roles:
- documents: metadata et statut
- document_sources: fichier source et hash
- raw_pages: texte brut extrait
- cleaned_texts: texte nettoye
- chunks: segments vectorises + references
- qa_feedback: corrections utilisateur

### 7.2. Bloc corpus juridique structure
Collections:
- lois
- articles
- article_versions
- exigences
- actions
- action_criticalities
- action_dependencies

Roles:
- lois: registre des lois
- articles: elements structuraux
- article_versions: versioning immuable
- exigences: obligations extraites
- actions: actions reglementaires
- criticalities: scores de criticite
- dependencies: graph DAG

### 7.3. Bloc amendments et audit
Collections:
- amendment_operations
- audit_logs

Roles:
- operations: ADD, REPLACE, MODIFY, REPEAL
- audit_logs: trace de toute modification

### 7.4. Bloc compliance cases
Collections:
- compliance_cases
- case_messages
- case_documents
- case_findings
- case_actions

Roles:
- cases: metadonnees du cas
- messages: conversation context
- documents: documents rattaches
- findings: non-conformites
- actions: remediation

### 7.5. Bloc compliance steering
Collections:
- compliance_assessments
- controls
- control_evidences
- requirement_control_links
- exception_register

Roles:
- assessments: gap analysis
- controls: controles internes
- evidences: preuves associees
- links: mapping exigence-control
- exceptions: waivers et risk acceptance

## 8. Flux RAG detaille
### 8.1. Etapes
1. Detection langue (ar/fr/en)
2. Classification intent
3. Domain routing (5 domaines)
4. Retrieval partitionne (base law vs amendments)
5. Reranking hybride (vector + lexical + anchors)
6. Injection KG light
7. LLM generation (Ollama)
8. Quality guard (references, fidelite, langue)
9. Reponse finale + sources

### 8.2. Points forts
- validation post generation
- reranking multi-signaux
- conservatisme face aux doutes

### 8.3. Limites
- pas de cross-encoder
- pas de cache de reponses finales
- index vectoriel brute force

## 9. Flux compliance detaille (case orchestration)
### 9.1. Etapes
1. Collecte contexte (facts + docs)
2. Gap analysis (LLM)
3. Applicability check
4. Finding generation
5. Criticality scoring
6. Action proposal
7. Evidence mapping
8. Decision ASK/ACT/REVIEW

### 9.2. Sorties
- findings proposes
- actions proposees
- controls proposes
- evidences requises
- niveau de risque
- recommandations

### 9.3. Valeur ajoutee
Le pipeline orchestre une resolution structuree avec justification, ce qui facilite l audit et la responsabilisation.

## 10. Amendements, versioning et audit
### 10.1. Versioning
Chaque article est versionne de facon immuable: une modification cree une nouvelle version, l ancienne est conservee.

### 10.2. Amendements
Les operations d amendement sont extraites et appliquees (ADD, MODIFY, REPEAL). Les recalculs associes garantissent la coherence des exigences et actions.

### 10.3. Audit logs
Toutes les operations critiques sont journalisees, ce qui permet une tracabilite complete.

## 11. Indexation et performance
### 11.1. Indexes Mongo
Les indexes sont indispensables pour la rapidite des queries sur chunks, articles, actions et links.

### 11.2. FAISS
FAISS IndexFlatIP est utilise pour la recherche vectorielle. Rapide sur volumes faibles a moyens, mais O(N).

### 11.3. Scalabilite
Pour des volumes plus grands, un index HNSW ou IVF serait recommande, ou une base vectorielle dediee.

## 12. Securite backend
### 12.1. Points solides
- API key avec constant-time compare
- multi-tenant optionnel
- validation taille fichier

### 12.2. Vulnerabilites identifiees
- absence de rate limiting
- bulk upload path arbitraire
- pas de CSP ni sanitization stricte du contenu LLM

### 12.3. Recommendations
- limiter les requetes (slowapi)
- restreindre bulk upload a un path autorise
- ajouter CSP et sanitation frontend

## 13. Observabilite et monitoring
Le backend expose des endpoints admin pour:
- stats documents
- stats index vectoriel
- analytics Q&A

Cela permet de surveiller l etat global du systeme.

## 14. Tests et qualite
### 14.1. Points forts
- 28 fichiers de tests
- tests async
- CI multi-version Python

### 14.2. Manques
- tests end-to-end complets
- tests de charge
- couverture partielle sur certains services

## 15. Limites, risques, recommandations
### 15.1. Risques
- surchauffe LLM sans rate limiting
- dette technique (modules massifs)
- index vectoriel brute force a grande echelle

### 15.2. Recommandations prioritaires
1. Rate limiting global
2. Modularisation llm_service et router
3. Tests E2E upload to ask
4. Index vectoriel scalable

## 16. Conclusion
Le backend de Daleel est robuste, bien structure, et adapte a un environnement juridique exigeant. Il combine une logique RAG avancee et un module compliance complet. Les prochaines evolutions doivent se concentrer sur la securite operationnelle, la modularisation et la scalabilite du retrieval.

## 17. Annexes
### 17.1. Sources internes
- [README.md](README.md)
- [AUDIT_COMPLET.md](AUDIT_COMPLET.md)
- [RAPPORT_PROJET.md](RAPPORT_PROJET.md)
- [COMPLIANCE_STEERING.md](COMPLIANCE_STEERING.md)
- [docs/CASE_ORCHESTRATION.md](docs/CASE_ORCHESTRATION.md)
- [training/README.md](training/README.md)
- [training/FINETUNING_INTEGRATION_OVERVIEW.md](training/FINETUNING_INTEGRATION_OVERVIEW.md)
- [training/FINETUNING_PLAN.md](training/FINETUNING_PLAN.md)
- [training/INTEGRATION.md](training/INTEGRATION.md)
- [CHANGELOG.md](CHANGELOG.md)
