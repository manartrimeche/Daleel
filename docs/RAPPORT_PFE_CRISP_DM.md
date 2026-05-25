# RAPPORT DE PROJET DE FIN D'ÉTUDES

**Daleel — Plateforme RAG d'Intelligence Juridique Tunisienne**

*Élaboré par :* Manar Trimeche
*Organisme d'accueil :* Didax IT
*Année universitaire :* 2025–2026

---

> **Dédicaces**
>
> Je dédie ce travail à ...

> **Remerciements**
>
> Je remercie ...

---

## Table des matières

Introduction Générale

1. Présentation du projet
   - 1.1 Présentation de l'organisme d'accueil
   - 1.2 Contexte : le droit tunisien face au défi numérique
   - 1.3 Problématique
   - 1.4 Objectifs du projet
   - 1.5 Solution proposée
   - 1.6 Méthodologie : CRISP-DM appliquée à l'intelligence juridique

2. État de l'art et choix technologiques
   - 2.1 Limites des LLM classiques dans le domaine juridique
   - 2.2 Retrieval-Augmented Generation (RAG)
   - 2.3 Modèles d'embeddings multilingues
   - 2.4 Recherche vectorielle : FAISS
   - 2.5 Architecture Transformer
   - 2.6 LLM local : Ollama et Qwen 2.5
   - 2.7 Cross-Encoder pour le reranking
   - 2.8 Traitement OCR des documents juridiques
   - 2.9 Graphe de connaissances léger (KG Light)
   - 2.10 Technologies et rôles fonctionnels
   - 2.11 Étude comparative

3. Compréhension et préparation des données
   - 3.1 Architecture globale du système
   - 3.2 Pipeline d'ingestion documentaire
   - 3.3 Structuration juridique
   - 3.4 Normalisation du dialecte tunisien
   - 3.5 Gestion des amendements législatifs
   - 3.6 Base de données MongoDB
   - 3.7 Déploiement Docker

4. Modélisation : moteur RAG et intelligence conversationnelle
   - 4.1 Environnement de travail
   - 4.2 Pipeline RAG classique
   - 4.3 Garde-fou de qualité (Quality Guard)
   - 4.4 Composition des réponses
   - 4.5 Agent autonome ReAct
   - 4.6 Analyse automatisée de contrats
   - 4.7 Fine-tuning des modèles

5. Évaluation, conformité et déploiement
   - 5.1 Module de conformité réglementaire
   - 5.2 Gestion des cas juridiques
   - 5.3 Interface utilisateur
   - 5.4 Authentification et multi-tenancy
   - 5.5 Tests et intégration continue
   - 5.6 Évaluation du système
   - 5.7 Tableau récapitulatif

Conclusion Générale

Bibliographie

---

## Liste des acronymes

| Acronyme | Signification |
|----------|---------------|
| API | Application Programming Interface |
| ASGI | Asynchronous Server Gateway Interface |
| BCT | Banque Centrale de Tunisie |
| CI/CD | Continuous Integration / Continuous Deployment |
| CRISP-DM | Cross-Industry Standard Process for Data Mining |
| CRUD | Create, Read, Update, Delete |
| CSS | Cascading Style Sheets |
| DAG | Directed Acyclic Graph |
| FAISS | Facebook AI Similarity Search |
| GRC | Governance, Risk and Compliance |
| i18n | Internationalisation |
| IA | Intelligence Artificielle |
| INPDP | Instance Nationale de Protection des Données Personnelles |
| JORT | Journal Officiel de la République Tunisienne |
| JSON | JavaScript Object Notation |
| JWT | JSON Web Token |
| KG | Knowledge Graph |
| LLM | Large Language Model |
| LoRA | Low-Rank Adaptation |
| LRU | Least Recently Used |
| MNR | Multiple Negatives Ranking |
| MRR | Mean Reciprocal Rank |
| nDCG | normalized Discounted Cumulative Gain |
| NLP | Natural Language Processing |
| OCR | Optical Character Recognition |
| PDF | Portable Document Format |
| PFE | Projet de Fin d'Études |
| RAG | Retrieval-Augmented Generation |
| ReAct | Reasoning and Acting |
| REST | Representational State Transfer |
| RTL | Right-To-Left |
| SMTP | Simple Mail Transfer Protocol |
| SPA | Single Page Application |
| TTL | Time To Live |
| XSS | Cross-Site Scripting |

---

## Introduction Générale

Le cadre juridique tunisien se distingue par une densité réglementaire considérable. Le Code du travail, le Code des sociétés commerciales, la loi organique n° 63-2004 relative à la protection des données personnelles, le Code de l'investissement et les circulaires de la Banque Centrale de Tunisie forment autant de corpus que les entreprises doivent maîtriser simultanément. Cette complexité se double d'une dimension linguistique : les textes officiels coexistent en arabe et en français, les amendements publiés au Journal Officiel de la République Tunisienne modifient régulièrement des dispositions existantes, et la jurisprudence demeure largement inaccessible sous forme numérique.

Face à ce constat, les entreprises tunisiennes — en particulier les PME — ne disposent que de moyens limités pour assurer leur conformité réglementaire. L'accès au conseil juridique repose encore majoritairement sur des consultations ponctuelles auprès d'avocats, sans outil permettant d'automatiser le suivi des obligations, d'évaluer l'applicabilité des textes à un profil d'entreprise donné, ni de tracer l'impact des modifications législatives sur les exigences en vigueur.

Les avancées récentes en intelligence artificielle, notamment les grands modèles de langage (LLM) et la technique de Retrieval-Augmented Generation (RAG), ouvrent des perspectives prometteuses pour le domaine juridique. Toutefois, les LLM génériques présentent des limites documentées dans ce contexte : hallucinations factuelles, absence de traçabilité des sources, connaissances figées à la date d'entraînement, et difficultés à traiter des corpus bilingues arabe-français avec la rigueur qu'exige le droit.

C'est dans ce contexte que s'inscrit le projet **Daleel**, objet du présent projet de fin d'études. Daleel est une plateforme intelligente d'assistance juridique spécialisée pour le droit tunisien, conçue pour répondre à trois besoins fondamentaux :

- le **conseil juridique conversationnel**, fondé sur un pipeline RAG avancé avec ancrage strict des sources, routage par domaine juridique, et un agent autonome capable de raisonnement itératif (Agentic RAG) ;
- la **gestion de conformité réglementaire** (Compliance Operations), couvrant l'extraction automatique des exigences légales, l'évaluation de leur applicabilité, le scoring de criticité, la génération de feuilles de route, l'analyse d'écarts et l'analyse automatisée de contrats ;
- le **support multilingue natif**, incluant le traitement OCR de documents en arabe, le nettoyage spécialisé des textes juridiques bilingues, la normalisation du dialecte tunisien, et une interface trilingue (français, arabe, anglais) intégrant le support RTL.

La plateforme repose sur une architecture découplée : un backend FastAPI asynchrone connecté à MongoDB, un moteur d'embeddings multilingue fine-tuné pour le domaine juridique, un LLM local déployé via Ollama pour garantir la confidentialité des données, un index vectoriel FAISS pour la recherche sémantique, et un frontend React complet. L'ensemble est conteneurisé via Docker et soumis à une intégration continue (865 tests, 50 % de couverture).

Le développement a suivi la méthodologie **CRISP-DM** (Cross-Industry Standard Process for Data Mining), dont les six phases — compréhension métier, compréhension des données, préparation des données, modélisation, évaluation et déploiement — structurent le présent rapport en cinq chapitres :

- le **chapitre 1** présente le cadre général du projet, la problématique, les objectifs et la méthodologie CRISP-DM adoptée ;
- le **chapitre 2** dresse un état de l'art des technologies mobilisées ;
- le **chapitre 3** détaille la compréhension et la préparation des données : architecture, ingestion documentaire, structuration juridique et modèle de données ;
- le **chapitre 4** décrit la phase de modélisation : pipeline RAG, garde-fou de qualité, agent autonome, analyse de contrats et fine-tuning ;
- le **chapitre 5** couvre l'évaluation du système, les modules de conformité, l'interface utilisateur, les tests et le déploiement.

---

## Chapitre 1 — Présentation du projet

### Introduction

L'accès au droit constitue un enjeu majeur pour les entreprises tunisiennes. La multiplicité des textes législatifs, leur publication bilingue arabe-français, et la fréquence des amendements rendent le suivi de la conformité réglementaire particulièrement coûteux en temps et en expertise. Ce premier chapitre présente le cadre dans lequel s'inscrit le projet Daleel : l'organisme d'accueil, le contexte du droit tunisien, la problématique identifiée, les objectifs poursuivis, la solution proposée et la méthodologie de développement adoptée.

### 1.1 Présentation de l'organisme d'accueil

Didax IT est une entreprise de services informatiques établie à Dubaï en 2024. Son modèle d'affaires repose sur une clientèle internationale opérée depuis son bureau de Dubaï, qui joue le rôle d'antenne commerciale, tandis que les équipes techniques sont basées dans des pays à coût compétitif, notamment en Tunisie et en Inde. Cette organisation permet de proposer une offre globale à forte valeur ajoutée.

Ses activités couvrent quatre domaines principaux :

- **Conception et développement de logiciels sur mesure** : l'entreprise analyse les besoins métier de ses clients afin de proposer des solutions adaptées, incluant des applications intégrant l'intelligence artificielle pour l'automatisation de tâches répétitives et l'aide à la décision fondée sur l'analyse de données.
- **Transformation numérique** : Didax IT accompagne les organisations dans l'identification de leurs besoins puis l'intégration de logiciels principalement open source, offrant des solutions économiques et efficaces, en particulier pour les PME.
- **Gestion de projets E-learning** : l'entreprise conçoit des dispositifs de formation couvrant l'analyse des besoins, la conception pédagogique, le choix de la solution technique et le développement de contenus adaptés.
- **Représentation de sociétés éditrices de logiciels** : cette activité inclut le conseil, la revente de solutions logicielles orientées métier, l'implémentation, la formation des utilisateurs et la maintenance.

C'est dans le cadre de l'activité de développement de solutions intégrant l'intelligence artificielle que le projet Daleel a été initié, en réponse à un besoin identifié sur le marché tunisien : l'absence d'un outil numérique capable d'assister les entreprises dans la compréhension et le suivi de leurs obligations légales.

### 1.2 Contexte : le droit tunisien face au défi numérique

Le paysage juridique tunisien se compose de plusieurs corpus législatifs majeurs : le Code du travail, le Code des sociétés commerciales, la loi organique n° 63-2004 relative à la protection des données personnelles, le Code de l'investissement et les circulaires de la Banque Centrale de Tunisie. Ces textes régissent l'essentiel des obligations auxquelles sont soumises les entreprises opérant sur le territoire tunisien.

Plusieurs caractéristiques rendent ce cadre réglementaire particulièrement difficile à naviguer :

- **Le bilinguisme officiel** : les textes législatifs sont publiés en arabe, langue officielle, et en français, langue d'usage dans la pratique juridique et des affaires. Un même article peut nécessiter la lecture croisée des deux versions pour en saisir la portée exacte.
- **La fragmentation des sources** : les lois, décrets, circulaires et amendements sont publiés au JORT de manière échelonnée. Il n'existe pas de base de données unifiée et à jour regroupant l'ensemble des textes en vigueur avec leur historique de modifications.
- **La fréquence des amendements** : les modifications législatives — parfois partielles, par ajout, remplacement ou abrogation d'articles — imposent un suivi continu que les entreprises peinent à assurer sans ressources juridiques dédiées.

Dans ce contexte, la numérisation du droit tunisien reste limitée. Les outils existants se réduisent à des bases de données textuelles statiques, sans capacité d'analyse sémantique, de suivi automatique des modifications, ni d'évaluation de l'applicabilité des textes à un profil d'entreprise donné.

### 1.3 Problématique

Le projet Daleel part d'un constat : les entreprises tunisiennes, en particulier les PME, n'ont pas accès à un outil leur permettant de comprendre, suivre et appliquer efficacement le droit qui les concerne. Cette difficulté se décline en trois dimensions.

#### 1.3.1 Inaccessibilité et fragmentation des textes juridiques

Les textes législatifs tunisiens sont dispersés entre le JORT, les sites des ministères, les circulaires de la BCT et diverses publications sectorielles. Leur format — souvent des PDF scannés de qualité variable — rend l'extraction automatique du contenu non triviale, surtout pour les documents en langue arabe nécessitant un traitement OCR spécialisé.

#### 1.3.2 Complexité multilingue et structurelle

Un même code — par exemple le Code du travail — existe en version arabe et en version française, avec des numérotations d'articles qui ne correspondent pas toujours d'une version à l'autre. Les amendements peuvent modifier un article dans une version sans que la traduction correspondante soit immédiatement disponible. Cette dualité linguistique constitue un défi technique majeur pour tout système d'analyse automatisé.

#### 1.3.3 Absence d'outils de conformité automatisés

Les solutions existantes sur le marché — chatbots juridiques généralistes ou bases de données législatives — ne couvrent pas le droit tunisien de manière spécialisée. Aucune plateforme ne propose conjointement :

- une recherche sémantique dans les textes juridiques tunisiens ;
- une extraction automatique des exigences et leur évaluation d'applicabilité ;
- un suivi des amendements avec recalcul automatique des obligations ;
- une gestion de cas de conformité avec arbre de décision ;
- une analyse automatisée de contrats avec détection de risques et clauses manquantes.

### 1.4 Objectifs du projet

Le projet Daleel vise à concevoir et développer une plateforme intelligente d'assistance juridique couvrant trois axes complémentaires.

#### 1.4.1 Conseil juridique conversationnel ancré dans les sources

L'objectif premier est de permettre à un utilisateur de poser une question en langage naturel — en français, en arabe ou en anglais — et d'obtenir une réponse fondée exclusivement sur les textes juridiques tunisiens, avec citation précise des articles et traçabilité complète des sources. Le système doit refuser de répondre plutôt que d'inventer une disposition inexistante.

#### 1.4.2 Gestion de conformité réglementaire bout-en-bout

Au-delà du Q&A, la plateforme doit offrir un pipeline complet de Compliance Operations : extraction automatique des exigences légales à partir des textes, évaluation de leur applicabilité à un profil d'entreprise, scoring de criticité, génération de feuilles de route de conformité, analyse d'écarts, mapping des contrôles internes, et analyse multi-passes de contrats.

#### 1.4.3 Plateforme multilingue, multi-tenant et extensible

Le système doit traiter nativement l'arabe (y compris l'OCR sur documents scannés et la normalisation du dialecte tunisien), le français et l'anglais. Il doit supporter une architecture multi-tenant permettant à plusieurs organisations d'utiliser la plateforme de manière isolée. L'architecture doit être suffisamment modulaire pour intégrer de nouveaux domaines juridiques.

### 1.5 Solution proposée

La solution Daleel s'articule autour de trois composantes complémentaires.

#### 1.5.1 Pipeline RAG juridique avec ancrage strict

Le cœur de Daleel est un pipeline de Retrieval-Augmented Generation spécialisé pour le droit tunisien. Contrairement à un LLM générique qui s'appuie sur ses connaissances d'entraînement, le système récupère les passages juridiques pertinents via une recherche vectorielle (FAISS) avant de les injecter dans le contexte du LLM. Un garde-fou de qualité (Quality Guard) vérifie systématiquement que chaque article cité existe réellement dans les sources récupérées, réduisant le risque d'hallucination.

Le système intègre également un agent autonome de type ReAct (Agentic RAG) capable de raisonner de manière itérative : il décide dynamiquement quels outils invoquer — recherche sémantique, consultation du graphe de connaissances, évaluation d'applicabilité — et boucle jusqu'à obtenir une réponse suffisamment fondée.

#### 1.5.2 Moteur de Compliance Operations et analyse de contrats

Le second pilier structure le droit en une hiérarchie exploitable : Loi → Article → Exigence → Action. À partir d'un profil d'entreprise, le système évalue automatiquement quelles exigences s'appliquent, calcule leur criticité via un moteur à règles, et génère une feuille de route ordonnée par priorité via un tri topologique sur un graphe de dépendances (DAG).

Un module d'analyse automatisée de contrats complète cette offre. Il exécute un pipeline en cinq passes — extraction de clauses, détection de risques, identification de clauses manquantes, scoring global et recommandations — en s'appuyant à la fois sur le LLM et la base juridique RAG.

Le module intègre également la gestion des cas de conformité avec un orchestrateur à arbre de décision (ASK / CLARIFY / ACT / REVIEW) et un registre d'exceptions pour les risques acceptés.

#### 1.5.3 Interface trilingue complète

Le troisième composant est une interface utilisateur React comportant 16 pages : un chatbot conversationnel avec support vocal et pièces jointes, un tableau de bord d'administration avec indicateurs clés, et des modules dédiés à la gestion des documents, des lois, des amendements, des cas, de l'analyse de contrats, des utilisateurs, des organisations et des paramètres. L'interface est entièrement internationalisée en français, arabe (avec support RTL) et anglais via i18next.

### 1.6 Méthodologie : CRISP-DM appliquée à l'intelligence juridique

Le développement de Daleel suit la méthodologie **CRISP-DM** (Cross-Industry Standard Process for Data Mining), un cadre de référence pour les projets de science des données et d'intelligence artificielle. Ce choix se justifie par la nature du projet : Daleel est fondamentalement un système de traitement intelligent de données textuelles juridiques, où chaque phase — de la compréhension du corpus jusqu'à l'évaluation des résultats — conditionne la qualité de la suivante.

CRISP-DM se compose de six phases itératives :

#### Phase 1 — Compréhension métier (Business Understanding)

Cette phase a consisté à identifier les besoins des entreprises tunisiennes en matière de conformité juridique, à analyser le marché des solutions existantes et à définir les objectifs fonctionnels de la plateforme. Le résultat est la spécification des trois axes du projet : Q&A juridique, compliance operations et interface multilingue. Cette phase correspond au présent chapitre.

#### Phase 2 — Compréhension des données (Data Understanding)

Le corpus juridique tunisien a été inventorié et analysé : cinq documents PDF totalisant 5,7 Mo, bilingues arabe-français, incluant des PDF scannés de qualité variable. L'analyse a révélé les défis spécifiques — écriture bidirectionnelle, diacritiques parasites, variantes de numération d'articles entre versions linguistiques — et guidé les choix techniques de la phase suivante. L'état de l'art (chapitre 2) complète cette compréhension par l'étude des solutions technologiques disponibles.

#### Phase 3 — Préparation des données (Data Preparation)

Cette phase couvre le pipeline d'ingestion documentaire complet : extraction de texte à trois niveaux (PyMuPDF, pdfminer, OCR), nettoyage spécialisé pour l'arabe juridique, chunking sémantique sensible à la structure législative, génération d'embeddings 768 dimensions, segmentation en articles, et construction du graphe de connaissances. Le chapitre 3 détaille cette phase.

#### Phase 4 — Modélisation (Modeling)

La modélisation comprend la construction du pipeline RAG avec routage de domaine, reranking par cross-encoder, injection du contexte KG Light, génération LLM avec garde-fou de qualité, agent autonome ReAct, module d'analyse de contrats, et fine-tuning des embeddings et des modèles spécialisés. Le chapitre 4 couvre cette phase.

#### Phase 5 — Évaluation (Evaluation)

L'évaluation porte sur les métriques de retrieval (Recall@k, MRR, nDCG) avant et après fine-tuning, la validation du Quality Guard, et la couverture fonctionnelle de la plateforme. La suite de tests automatisés (865 tests, 50 % de couverture) et l'intégration continue complètent cette phase. Le chapitre 5 présente les résultats.

#### Phase 6 — Déploiement (Deployment)

Le déploiement est assuré par Docker Compose (trois services : API, MongoDB, Ollama), un Dockerfile multi-stage optimisé, et un pipeline CI/CD GitHub Actions vérifiant automatiquement lint, sécurité, tests et build frontend sur trois versions de Python. Les chapitres 3 et 5 couvrent ces aspects.

#### Caractère itératif

Conformément à CRISP-DM, le développement a suivi des cycles itératifs organisés en dix sprints. Chaque sprint traverse les phases 3 à 5 (préparation, modélisation, évaluation) pour un périmètre fonctionnel ciblé, permettant de valider progressivement chaque couche du système.

**Table 1.1 — Planning des sprints**

| Sprint | Périmètre fonctionnel | Phase CRISP-DM dominante |
|--------|----------------------|--------------------------|
| 1 | Documents, RAG Core, Q&A | Préparation + Modélisation |
| 2 | Profils d'entreprise, applicabilité | Modélisation |
| 3 | Lois, articles, versioning | Préparation |
| 4 | Criticité, feuille de route | Modélisation |
| 5 | Amendements, audit trail | Préparation + Modélisation |
| 6 | RAG avancé (Domain Router, Quality Guard, KG Light) | Modélisation |
| 7 | Case Management | Modélisation |
| 8 | Compliance Steering (gap analysis, contrôles) | Modélisation |
| 9 | Conversation progressive, extraction de contexte | Modélisation |
| 10 | Orchestrateur, composition de réponses, fine-tuning | Modélisation + Évaluation |

### Conclusion

Ce premier chapitre a posé le cadre du projet Daleel en présentant l'organisme d'accueil, le contexte juridique tunisien et les difficultés concrètes auxquelles font face les entreprises en matière de conformité réglementaire. La problématique, les objectifs et la solution proposée ont été définis, ainsi que la méthodologie CRISP-DM qui structure le développement en six phases itératives. Le chapitre suivant dressera un état de l'art des technologies mobilisées.

---

## Chapitre 2 — État de l'art et choix technologiques

### Introduction

La construction d'un assistant juridique intelligent pour le droit tunisien soulève des défis qui dépassent les capacités des systèmes de recherche textuelle classiques : compréhension sémantique multilingue, ancrage strict dans les sources légales, gestion des amendements et raisonnement structuré sur les obligations réglementaires. Ce chapitre examine d'abord les limites des grands modèles de langage appliqués au domaine juridique, puis présente les paradigmes et technologies qui permettent de les surmonter. Chaque technologie est présentée dans sa dimension théorique avant d'être mise en perspective avec les choix d'implémentation retenus pour Daleel.

### 2.1 Limites des LLM classiques dans le domaine juridique

Les grands modèles de langage ont transformé le traitement automatique du langage naturel. Toutefois, leur application directe au conseil juridique présente des limites documentées dans la littérature et confirmées par l'expérimentation.

#### 2.1.1 Hallucinations et absence de traçabilité

Un LLM générique peut produire des réponses syntaxiquement correctes mais factuellement fausses — par exemple citer un article de loi inexistant ou attribuer une disposition au mauvais code. Dans le domaine juridique, où chaque affirmation doit pouvoir être vérifiée, cette tendance constitue un risque majeur. Contrairement à un moteur de recherche qui retourne des documents existants, un LLM génère du texte sans mécanisme natif de traçabilité des sources.

#### 2.1.2 Connaissances figées et absence de mise à jour

Les LLM sont entraînés sur un corpus figé à une date donnée. Or, le droit tunisien évolue continuellement : amendements publiés au JORT, nouvelles circulaires de la BCT, décrets d'application. Un modèle entraîné avant la publication d'un amendement continuera de citer la version abrogée d'un article, sans possibilité de correction sans ré-entraînement complet.

#### 2.1.3 Difficultés avec le multilinguisme arabe-français

Le corpus juridique tunisien est bilingue. Les LLM généralistes traitent l'arabe et le français de manière inégale, avec une sous-représentation de l'arabe juridique tunisien dans les données d'entraînement. Les spécificités de l'écriture arabe — bidirectionnalité, diacritiques, variantes de normalisation — ajoutent une couche de complexité que les modèles pré-entraînés ne gèrent pas de manière fiable sans adaptation.

### 2.2 Retrieval-Augmented Generation (RAG)

#### 2.2.1 Principe du RAG

Le paradigme RAG, introduit par Lewis et al. (2020), propose une solution aux limites décrites ci-dessus en découplant la mémoire factuelle du modèle de sa capacité de génération. Au lieu de s'appuyer sur ses seules connaissances d'entraînement, le LLM reçoit en contexte des passages pertinents récupérés depuis une base documentaire externe. La réponse est ainsi ancrée dans des sources vérifiables.

Un pipeline RAG standard se décompose en trois étapes :

- **Indexation** : les documents sont découpés en chunks, transformés en vecteurs numériques (embeddings), puis stockés dans un index vectoriel.
- **Récupération** : la question de l'utilisateur est convertie en vecteur et comparée aux vecteurs stockés pour identifier les passages les plus similaires sémantiquement.
- **Génération** : les passages récupérés sont injectés dans le prompt du LLM, qui génère une réponse fondée sur ce contexte.

#### 2.2.2 Avantages du RAG pour le domaine juridique

Le RAG présente des avantages déterminants pour un assistant juridique :

- **Traçabilité des sources** : chaque passage récupéré est associé à un document, une page et un article identifiables.
- **Mise à jour sans ré-entraînement** : l'ajout d'un nouveau texte législatif se réduit à son indexation dans la base vectorielle.
- **Réduction des hallucinations** : en contraignant le LLM à raisonner sur un contexte explicite, le risque de fabrication d'articles inexistants diminue significativement.
- **Adaptation au bilinguisme** : les embeddings multilingues permettent de récupérer un article en arabe en réponse à une question en français.

#### 2.2.3 Du RAG classique au RAG agentique

Le RAG classique suit un flux linéaire unique : recherche → injection → génération. Cette approche atteint ses limites face à des questions complexes nécessitant plusieurs recherches successives ou la consultation de sources hétérogènes (articles de loi, exigences, profil d'entreprise).

Le RAG agentique (Agentic RAG) introduit une boucle de raisonnement itérative, inspirée du paradigme ReAct (Yao et al., 2022). L'agent LLM dispose d'un ensemble d'outils — recherche sémantique, consultation du graphe de connaissances, évaluation d'applicabilité — et décide à chaque itération quel outil invoquer. Il boucle jusqu'à disposer d'un contexte suffisant pour produire une réponse fondée.

### 2.3 Modèles d'embeddings multilingues

#### 2.3.1 Sentence-Transformers

Les modèles Sentence-Transformers (Reimers et Gurevych, 2019) produisent des représentations vectorielles denses de phrases ou de paragraphes, capturant leur sens sémantique dans un espace de dimension fixe. Daleel utilise le modèle `paraphrase-multilingual-mpnet-base-v2`, qui produit des vecteurs de 768 dimensions et couvre plus de 50 langues, dont l'arabe et le français. Ce choix permet la recherche cross-lingue : une question en français peut récupérer un article indexé en arabe.

#### 2.3.2 Fine-tuning d'embeddings pour le domaine juridique

Les modèles pré-entraînés n'ont pas été exposés au vocabulaire juridique tunisien spécifique (SARL, CNSS, convention collective). Le fine-tuning sur des paires (question juridique, article pertinent) adapte l'espace vectoriel au domaine cible.

La technique retenue est le MultipleNegativesRankingLoss (Henderson et al., 2017) : pour chaque paire (question, article positif) dans le batch, tous les autres articles servent de négatifs implicites. Les bonnes pratiques appliquées incluent un learning rate faible (2×10⁻⁵) pour préserver les capacités multilingues, un warmup de 10 % des steps, et un nombre limité d'epochs (2) pour éviter le catastrophic forgetting.

### 2.4 Recherche vectorielle : FAISS

FAISS (Facebook AI Similarity Search), développé par Meta AI (Johnson et al., 2019), est une bibliothèque optimisée pour la recherche de similarité dans de grands ensembles de vecteurs denses. Daleel utilise un index HNSW (Hierarchical Navigable Small World) avec M=32 connexions et ef_construction=200, offrant un bon compromis entre vitesse et qualité de recherche.

L'index est construit en mémoire au démarrage du serveur à partir des embeddings stockés dans MongoDB, puis mis à jour de manière incrémentale lors de l'ingestion ou la suppression de documents. Un index IndexFlatIP (produit scalaire exact) et une implémentation Python cosine servent de fallbacks.

### 2.5 Architecture Transformer

L'architecture Transformer (Vaswani et al., 2017) constitue le socle de l'ensemble des modèles utilisés dans Daleel : modèle d'embeddings, LLM de génération et cross-encoder de reranking. Son mécanisme d'attention multi-têtes permet au modèle de pondérer l'importance relative de chaque token en fonction du contexte complet, ce qui est particulièrement pertinent pour le langage juridique où la portée d'un mot (« sauf », « nonobstant », « sous réserve de ») peut modifier le sens de la phrase entière.

### 2.6 LLM local : Ollama et Qwen 2.5

#### 2.6.1 Ollama

Ollama est une plateforme de déploiement local de LLM qui permet d'exécuter des modèles sur l'infrastructure propre de l'utilisateur, sans recours à des API cloud. Ce choix répond à deux exigences :

- **Confidentialité des données** : les textes juridiques et les profils d'entreprise ne quittent jamais le serveur de l'utilisateur.
- **Indépendance opérationnelle** : le système fonctionne sans connexion internet.

Ollama expose une API HTTP locale compatible avec le format OpenAI, simplifiant l'intégration avec le pipeline RAG.

#### 2.6.2 Qwen 2.5 (7B)

Daleel utilise le modèle Qwen 2.5:7b comme moteur de génération principal. Ce choix résulte de plusieurs critères : capacité multilingue couvrant nativement l'arabe, le français et l'anglais ; taille raisonnable (7 milliards de paramètres) exécutable sur matériel standard ; support natif du tool calling pour l'agent ReAct ; et fenêtre de contexte étendue pour injecter simultanément les passages récupérés, le system prompt et l'historique de conversation.

### 2.7 Cross-Encoder pour le reranking

Le reranking par cross-encoder est une technique complémentaire à la recherche vectorielle. Alors que les embeddings bi-encodeur comparent indépendamment la question et chaque passage, un cross-encoder traite conjointement la paire question-passage à travers le Transformer, produisant un score de pertinence plus fin.

Daleel intègre de manière optionnelle le modèle `cross-encoder/ms-marco-MiniLM-L-6-v2` (22M paramètres), entraîné sur le benchmark MS-MARCO. Il intervient en seconde passe sur les top-k résultats de FAISS pour réordonner les passages par pertinence, avec un seuil minimal de score (-2.0) pour filtrer les résultats non pertinents.

### 2.8 Traitement OCR des documents juridiques

Une part significative du corpus juridique tunisien existe sous forme de PDF scannés. Daleel implémente une stratégie d'extraction à trois niveaux :

- **PyMuPDF** : extraction directe du texte intégré dans les PDF nativement numériques.
- **pdfminer.six** : fallback pour les PDF dont la couche texte est mal structurée.
- **OCR** : Tesseract 5.x comme moteur principal (avec les packs linguistiques arabe et français), et EasyOCR comme fallback.

Le texte extrait subit ensuite un pipeline de nettoyage spécialisé : normalisation des caractères arabes, suppression des diacritiques parasites, correction des lettres isolées, gestion de la bidirectionnalité et détection de texte incompréhensible (garbled).

### 2.9 Graphe de connaissances léger (KG Light)

Les systèmes RAG classiques récupèrent des passages textuels isolés, sans capturer les relations structurelles entre entités juridiques. Plutôt que d'adopter une base de données graphe externe (Neo4j, RDF), Daleel propose une approche KG Light exploitant les relations implicites entre les collections MongoDB existantes. Le module reconstruit à la demande un sous-graphe structuré (Loi → Article → Version → Exigence → Action → Criticité → Dépendance) injecté dans le contexte RAG pour enrichir le raisonnement du LLM.

### 2.10 Technologies et rôles fonctionnels

**Table 2.1 — Technologies et rôles fonctionnels**

| Technologie | Rôle dans Daleel |
|---|---|
| FastAPI 0.115+ / Uvicorn | API REST asynchrone (152 endpoints) |
| MongoDB 7+ (Motor async) | Stockage documents, embeddings, entités juridiques (35 collections) |
| `paraphrase-multilingual-mpnet-base-v2` | Embeddings multilingues 768d + modèle fine-tuné |
| Ollama + Qwen 2.5:7b | LLM local pour génération et analyse |
| FAISS (IndexHNSWFlat) | Recherche vectorielle in-memory |
| `ms-marco-MiniLM-L-6-v2` | Cross-encoder reranking optionnel |
| Tesseract 5.x / EasyOCR | OCR arabe et français |
| PyMuPDF + pdfminer.six | Extraction de texte PDF |
| React 19 + Vite | Frontend SPA (16 pages, i18n FR/AR/EN) |
| Docker Compose | Conteneurisation 3 services |
| GitHub Actions | CI/CD (lint, sécurité, tests, build frontend) |
| JWT (HS256) + bcrypt | Authentification et autorisation |
| SlowAPI | Rate limiting des endpoints |
| faster-whisper / Piper / Edge-TTS | STT et TTS trilingue |

### 2.11 Étude comparative

**Table 2.2 — Étude comparative des approches Legal AI**

| Critère | LLM générique (ChatGPT, etc.) | RAG classique | Base législative statique | **Daleel** |
|---|---|---|---|---|
| Ancrage dans les sources | Non | Partiel | Oui (texte brut) | **Oui (RAG + Quality Guard)** |
| Mise à jour sans ré-entraînement | Non | Oui | Oui | **Oui** |
| Multilinguisme ar/fr/en | Partiel | Selon modèle | Rarement | **Natif (OCR + i18n + RTL)** |
| Gestion des amendements | Non | Non | Manuelle | **Automatique (versioning immutable)** |
| Conformité réglementaire | Non | Non | Non | **Complète (applicabilité, criticité, roadmap)** |
| Raisonnement itératif | Limité | Non | Non | **Agent ReAct avec 7 outils** |
| Analyse de contrats | Générique | Non | Non | **Pipeline 5 passes spécialisé** |
| Graphe de connaissances | Non | Rarement | Non | **KG Light sur MongoDB** |
| Confidentialité (LLM local) | Non (cloud) | Variable | N/A | **Oui (Ollama local)** |

### Conclusion

Ce chapitre a présenté les fondements théoriques et technologiques sur lesquels repose Daleel. Les limites identifiées des LLM classiques — hallucinations, connaissances figées et multilinguisme insuffisant — justifient l'adoption du paradigme RAG, enrichi par des techniques avancées : embeddings fine-tunés, raisonnement agentique, graphe de connaissances léger et garde-fou de qualité post-génération. Le chapitre suivant détaille les phases de compréhension et de préparation des données selon CRISP-DM.

---

## Chapitre 3 — Compréhension et préparation des données

### Introduction

Ce chapitre correspond aux phases 2 (Data Understanding) et 3 (Data Preparation) de CRISP-DM. Il décrit l'architecture technique de Daleel et le pipeline de traitement des données, depuis l'upload d'un document juridique brut jusqu'à sa structuration en entités exploitables par le moteur RAG et le module de conformité. Chaque composant est présenté dans sa logique fonctionnelle, en détaillant les choix d'implémentation et leur justification.

### 3.1 Architecture globale du système

#### 3.1.1 Vue d'ensemble

Daleel adopte une architecture à trois tiers conteneurisée via Docker Compose :

- **daleel-api** : application FastAPI asynchrone développée en Python 3.12, exposant l'ensemble des 152 endpoints REST sur le port 8000. Elle orchestre le traitement documentaire, le pipeline RAG, la gestion de conformité et l'authentification.
- **mongodb** : base de données documentaire MongoDB 7.0, utilisée pour le stockage des métadonnées, des textes nettoyés, des embeddings et de l'ensemble des entités juridiques (35 collections).
- **ollama** : serveur d'inférence LLM local hébergeant le modèle Qwen 2.5:7b sur le port 11434. L'API HTTP compatible OpenAI simplifie l'intégration.

Les trois services communiquent via un réseau Docker dédié (`daleel-network`). Le service API dépend du health check MongoDB avant de démarrer, garantissant la disponibilité de la base de données.

#### 3.1.2 Séparation en quatre plans

L'architecture sépare strictement quatre plans :

- **Plan données** : MongoDB assure le stockage persistant, sans logique métier.
- **Plan applicatif** : FastAPI regroupe les services métier, les routeurs API et les endpoints. Toute la logique RAG, de conformité et d'orchestration est côté serveur.
- **Plan inférence** : Ollama exécute le LLM de manière isolée. Le modèle est interchangeable grâce au paramètre `LLM_MODEL`.
- **Plan présentation** : React 19 fournit une SPA indépendante, communiquant avec l'API via des appels REST authentifiés par JWT.

Cette séparation permet de faire évoluer chaque couche indépendamment : changer de modèle LLM, migrer la base de données ou remplacer le frontend sans impacter les autres composants.

### 3.2 Pipeline d'ingestion documentaire

L'ingestion d'un document juridique suit un pipeline en six étapes, de l'upload brut jusqu'à l'indexation vectorielle.

#### 3.2.1 Upload et détection de format

Le service `document_service.py` accepte les formats PDF, DOCX, TXT, JSONL et images (PNG, JPG). Chaque fichier uploadé est identifié par son extension et validé, hashé en SHA-256 pour la déduplication, et protégé par un verrou asynchrone par hash empêchant les uploads concurrents du même fichier. La taille maximale est configurable via `DALEEL_MAX_UPLOAD_MB` (100 Mo par défaut).

#### 3.2.2 Extraction de texte et OCR

L'extraction suit la stratégie à trois niveaux décrite au chapitre 2. Pour chaque page, le système vérifie si le texte extrait est incompréhensible via la fonction `is_text_garbled()`. Si c'est le cas, la page est retraitée par OCR. Chaque page brute est stockée dans la collection `document_raw_pages` avec l'indication `ocr_used`.

#### 3.2.3 Nettoyage juridique spécialisé

Le texte brut subit un pipeline de nettoyage implémenté dans `text_utils.py` avec traçabilité des transformations appliquées :

- **Normalisation Unicode** : application de NFKC pour uniformiser les variantes de caractères.
- **Nettoyage OCR arabe** : suppression des diacritiques parasites, correction des lettres arabes isolées par l'OCR, élimination des chiffres isolés et des symboles parasites, correction des erreurs OCR fréquentes dans le vocabulaire juridique (table de 28 corrections connues).
- **Détection et correction bidi** : gestion de la bidirectionnalité lorsque du texte arabe (RTL) est mêlé à des chiffres ou acronymes (LTR).
- **Filtrage des caractères non autorisés** : une expression régulière stricte élimine les symboles parasites tout en préservant l'arabe, le latin, les chiffres et la ponctuation juridique.

Chaque page nettoyée est stockée dans `document_cleaned_texts` avec la liste des règles appliquées.

#### 3.2.4 Chunking sémantique

Le service `ChunkingService` découpe le texte nettoyé en chunks exploitables. Le chunking est section-aware : il détecte les marqueurs de structure juridique dans trois langues (Article, Chapitre, Section, Titre en français ; الفصل, الباب, القسم en arabe ; Article, Section, Chapter en anglais).

Le processus suit les étapes : découpage en sections logiques à l'aide d'expressions régulières spécifiques, découpage en chunks de taille maximale configurable (1 500 caractères avec 200 caractères de chevauchement), fusion des chunks trop courts, rejet des pages de mauvaise qualité selon des critères de longueur, nombre de mots, diversité lexicale et ratio alphanumérique, et sliding window classique comme fallback.

#### 3.2.5 Génération d'embeddings et indexation FAISS

Chaque chunk est transformé en vecteur de 768 dimensions par le modèle MPNet multilingue via `embedding_service.py`. Le service implémente un cache LRU de 512 entrées pour les requêtes répétées et un ThreadPoolExecutor avec deux workers pour paralléliser l'encodage sans bloquer la boucle asyncio.

Les embeddings sont stockés dans la collection `chunks` puis ajoutés de manière incrémentale à l'index FAISS en mémoire. Le `FaissIndexManager` reconstruit l'index complet au démarrage et supporte les mises à jour incrémentales sans redémarrage.

### 3.3 Structuration juridique

Au-delà du chunking pour la recherche vectorielle, Daleel structure le corpus en entités exploitables par le module de conformité.

#### 3.3.1 Segmentation en articles

Le module `article_segmenter.py` segmente un texte juridique en articles individuels avec suivi hiérarchique complet. Il détecte la hiérarchie structurelle (Titre → Chapitre → Section → Article), les numéros d'articles y compris les formes composées (« Article 95 bis »), et génère la clé unique de chaque article (par exemple CT-Art-95). Le segmenteur supporte les chiffres arabes-indiques (٩٥ → 95) et les textes bilingues.

Chaque article segmenté contient le numéro, l'intitulé, le texte complet, la hiérarchie, les pages couvertes et la langue détectée.

#### 3.3.2 Extraction d'exigences et génération d'actions

Pour chaque page nettoyée, le LLM analyse le texte et extrait les exigences réglementaires classées en quatre types : obligation, prohibition, condition et sanction. Chaque exigence est validée par ancrage : le système vérifie que le texte et la référence d'article correspondent au texte source selon un seuil de chevauchement de tokens.

Les exigences sont ensuite décomposées en actions concrètes — les étapes opérationnelles qu'une entreprise doit accomplir pour se conformer. Chaque action est associée à une modalité (obligatoire, recommandée, optionnelle) et peut être liée à d'autres actions par des dépendances.

#### 3.3.3 Graphe de connaissances léger

Le `graph_resolver.py` reconstruit un sous-graphe relationnel à la demande en traversant les collections MongoDB : Loi → Article → Version → Exigence → Action → Criticité. Ce sous-graphe est injecté dans le contexte RAG lorsque le module KG Light est activé.

### 3.4 Normalisation du dialecte tunisien

Le module `derja_normalizer.py` traite une problématique spécifique au contexte tunisien : les utilisateurs posent parfois leurs questions juridiques en dialecte tunisien (derja), par exemple « chkoun ynajem yfaskh el contrat » au lieu de « qui peut résilier le contrat ».

Le module implémente :

- **Détection** (`detect_derja`) : identification des marqueurs dialectaux (morphèmes, mots-clés, patterns syntaxiques) avec seuil configurable.
- **Normalisation** (`normalize_derja_to_french`) : traduction des termes dialectaux vers le français standard via une table de correspondances juridiques.
- **Mode conditionnel** (`normalize_if_derja`) : normalisation uniquement si le dialecte est détecté, préservant les requêtes déjà formulées en français ou arabe standard.
- **Génération de contexte** (`build_derja_context_note`) : création d'une note explicative injectée dans le prompt RAG pour guider le LLM.

Ce module est couvert à 100 % par les tests unitaires et constitue une contribution originale du projet.

### 3.5 Gestion des amendements législatifs

Le droit tunisien est régulièrement modifié par des lois d'amendement. Daleel implémente un pipeline complet dans `amendment_service.py`.

#### 3.5.1 Classification des documents

Lors de l'upload, le LLM analyse le document et le classe comme loi principale ou texte modificatif, identifié par des marqueurs linguistiques spécifiques (« est modifié et rédigé comme suit », « il est ajouté », « est abrogé »).

#### 3.5.2 Extraction des opérations

Pour chaque texte modificatif, le LLM extrait les opérations individuelles selon quatre types :

**Table 3.1 — Types d'opérations d'amendement**

| Type | Description | Effet sur l'article cible |
|------|-------------|---------------------------|
| ADD | Ajout d'un nouvel article | Création d'une nouvelle version |
| REPLACE | Remplacement intégral du texte | Nouvelle version, ancienne superseded |
| MODIFY | Modification partielle | Nouvelle version avec texte fusionné |
| REPEAL | Abrogation | Version marquée repealed |

Chaque opération inclut le numéro d'article cible, le nouveau texte, un extrait de preuve, la référence légale et un score de confiance.

#### 3.5.3 Versionnement immutable et recalcul

L'application d'un amendement suit un principe de versionnement immutable : l'ancienne version n'est jamais modifiée. Elle passe au statut `superseded` (ou `repealed`) et une nouvelle version active est créée. Après l'application, le service `recalculation_service.py` déclenche automatiquement la ré-extraction des exigences et actions pour les articles modifiés, ainsi que le recalcul des scores de criticité.

### 3.6 Base de données MongoDB

#### 3.6.1 Schéma des collections

Daleel utilise 35 collections MongoDB organisées en six groupes fonctionnels :

**Table 3.2 — Collections par groupe fonctionnel**

| Groupe | Collections | Rôle |
|--------|-------------|------|
| Documents et RAG | `documents`, `document_sources`, `document_raw_pages`, `document_cleaned_texts`, `chunks`, `chat_history`, `qa_feedback` | Ingestion, stockage, recherche et feedback |
| Juridique | `lois`, `articles`, `article_versions`, `exigences`, `actions`, `action_criticalities`, `action_dependencies`, `amendment_operations`, `audit_logs` | Structuration et traçabilité du corpus |
| Profils et Applicabilité | `company_profiles`, `exigence_applicabilities` | Évaluation de l'applicabilité |
| Case Management | `compliance_cases`, `case_messages`, `case_documents`, `case_document_analyses`, `case_findings`, `case_actions` | Gestion des dossiers de conformité |
| Compliance Steering | `compliance_assessments`, `controls`, `control_evidences`, `requirement_control_links`, `exception_register` | Gap analysis et contrôles internes |
| Auth et Multi-tenant | `users`, `organizations`, `invitations`, `token_blacklist`, `password_reset_tokens`, `notifications` | Authentification et gestion multi-tenant |

#### 3.6.2 Justification du choix de MongoDB

Le choix de MongoDB comme base de données unique se justifie par : un schéma flexible adapté aux structures hétérogènes des documents juridiques, le stockage direct des vecteurs 768d dans les documents chunks, le driver asynchrone Motor intégré nativement avec FastAPI, et la simplicité opérationnelle d'une seule base à administrer.

### 3.7 Déploiement Docker

#### 3.7.1 Architecture multi-conteneurs

Le `docker-compose.yml` orchestre trois services : mongodb (port 27017, volume persistant), daleel-api (port 8000, volume uploads), et ollama (port 11434, volume modèles). Les services communiquent via un réseau bridge dédié.

#### 3.7.2 Build multi-stage

Le Dockerfile utilise trois stages pour minimiser la taille de l'image finale :

1. **Stage frontend-builder** : compilation du frontend React/Vite (Node 20) → production `dist/`.
2. **Stage builder** : installation des dépendances Python lourdes dans un virtualenv isolé.
3. **Stage runtime** : image Python 3.12-slim avec uniquement Tesseract OCR, packs de langue, virtualenv copié et code applicatif.

Un health check vérifie la disponibilité de l'API toutes les 30 secondes avec un délai de démarrage de 60 secondes.

#### 3.7.3 Configuration par variables d'environnement

L'ensemble de la configuration est pilotée par des variables préfixées `DALEEL_`, gérées par Pydantic Settings avec des valeurs par défaut sensibles. Une validation de production (`_validate_production_settings`) vérifie au démarrage que les clés API, le secret JWT et les origines CORS sont correctement configurés.

### Conclusion

Ce chapitre a détaillé les phases de compréhension et de préparation des données selon CRISP-DM. Le pipeline transforme un document brut — y compris les PDF scannés en arabe — en entités structurées (articles, versions, exigences, actions), tout en maintenant la traçabilité complète de chaque transformation. L'architecture conteneurisée, le versionnement immutable des articles et le recalcul automatique post-amendement constituent les fondations sur lesquelles s'appuie la phase de modélisation décrite au chapitre suivant.

---

## Chapitre 4 — Modélisation : moteur RAG et intelligence conversationnelle

### Introduction

Ce chapitre correspond à la phase 4 (Modeling) de CRISP-DM. Il détaille la couche d'intelligence qui exploite les données préparées au chapitre précédent : le pipeline RAG qui produit les réponses juridiques, les mécanismes de routage et de qualité qui encadrent la génération, l'agent autonome ReAct, le module d'analyse de contrats et les modèles fine-tunés qui spécialisent le système pour le domaine juridique tunisien.

### 4.1 Environnement de travail

#### 4.1.1 Configuration matérielle

Le développement et les tests ont été effectués sur une station de travail : processeur Intel Core (8 cœurs), 16 Go RAM DDR5, 512 Go NVMe SSD, GPU NVIDIA GeForce pour l'inférence Ollama avec quantification, sous Windows 11 x64.

#### 4.1.2 Configuration logicielle

**Table 4.1 — Configuration logicielle**

| Composant | Version |
|-----------|---------|
| Python | 3.11 / 3.12 / 3.13 |
| FastAPI | 0.115+ |
| MongoDB | 7.0 |
| Ollama | dernière version stable |
| Qwen 2.5 | 7B (quantifié) |
| Node.js | 20 LTS |
| React | 19 |
| Docker Compose | 3.8 |

### 4.2 Pipeline RAG classique

Le pipeline RAG classique, implémenté dans `llm_service.py` (3 573 lignes), suit un flux en six étapes pour les questions juridiques simples.

#### 4.2.1 Détection de langue et routage automatique

Lorsqu'une question arrive, le système détermine son mode de traitement. La détection de langue utilise une heuristique dans `text_utils.py` analysant la proportion de caractères arabes et les marqueurs lexicaux français. La fonction `detect_query_language` distingue l'arabe, le français et l'anglais avec une précision supérieure à la détection Unicode simple grâce à l'utilisation de marqueurs lexicaux juridiques.

Le routage automatique évalue la longueur de la question et des mots-clés d'intention trilingues pour orienter vers le mode classique ou agentique.

#### 4.2.2 Routage par domaine juridique

Le `domain_router.py` oriente chaque requête vers l'un des domaines juridiques supportés :

**Table 4.2 — Domaines juridiques de routage**

| Domaine | Corpus associé |
|---------|---------------|
| `labor` | Code du travail |
| `corporate` | Code des sociétés commerciales |
| `data_protection` | Loi 63-2004 |
| `investment` | Code de l'investissement |
| `banking` | Circulaires BCT |
| `cross_domain` | Requêtes multi-domaines |
| `general` | Fallback |

Le routage utilise une combinaison de correspondance lexicale et d'analyse LLM, ajustant dynamiquement la configuration de recherche sans intervention humaine.

#### 4.2.3 Récupération partitionnée

Le `legal_retrieval_orchestrator.py` sépare la récupération en deux flux : lois de base et amendements. Le ratio de mélange est piloté par l'intention détectée :

**Table 4.3 — Ratios de récupération selon l'intention**

| Intention | Base law | Amendements |
|-----------|----------|-------------|
| current | 80 % | 20 % |
| historical | 30 % | 70 % |
| compare | 50 % | 50 % |
| audit | 20 % | 80 % |

#### 4.2.4 Reranking hybride

Après la récupération initiale, un reranking multi-critères est appliqué : similarité cosinus, score lexical BM25, chevauchement d'ancres, correspondance de références d'articles, et optionnellement le cross-encoder `ms-marco-MiniLM-L-6-v2`.

#### 4.2.5 Injection de contexte et génération

Les passages récupérés sont injectés dans le prompt du LLM avec le sous-graphe KG Light, le system prompt adapté au domaine et à la langue, et les corrections passées de l'utilisateur (few-shot). Le LLM génère une réponse structurée avec citation des sources.

### 4.3 Garde-fou de qualité (Quality Guard)

Le `quality_guard_service.py` applique une triple vérification post-génération :

1. **Vérification des références** : contrôle que chaque article ou loi cité existe dans les chunks sources récupérés.
2. **Vérification des citations** : utilisation d'une fenêtre glissante pour détecter les verbatim attribués aux sources.
3. **Fidélité sémantique** : évaluation par LLM-juge de la cohérence globale entre la réponse et les passages récupérés.

Lorsqu'une anomalie est détectée, le système applique une réécriture ultra-conservative qui préserve uniquement les informations vérifiables, plutôt que de produire une réponse potentiellement hallucinée.

### 4.4 Composition des réponses

Le `advisor_response_composer.py` formate les réponses dans un format Markdown structuré en sections normalisées :

**Table 4.4 — Structure des réponses juridiques**

| Section | Contenu |
|---------|---------|
| Ce que j'ai compris | Reformulation de la question |
| Analyse juridique | Analyse fondée sur les textes |
| Articles applicables | Références précises |
| Actions recommandées | Étapes concrètes |
| Points d'attention | Risques et nuances |
| Sources | Documents et pages consultés |
| Avertissement | Recommandation de vérification par un juriste |

### 4.5 Agent autonome ReAct

#### 4.5.1 Architecture de l'agent

L'agent autonome, implémenté dans `autonomous_agent.py` (300 lignes), suit le paradigme ReAct. À chaque itération, il observe le contexte accumulé, raisonne sur l'étape suivante, et agit en invoquant l'un de ses outils. La boucle continue jusqu'à obtenir une réponse suffisamment fondée ou atteindre un seuil de timeout.

#### 4.5.2 Outils disponibles

**Table 4.5 — Outils de l'agent ReAct**

| Outil | Fonction |
|-------|----------|
| `search` | Recherche sémantique dans l'index vectoriel |
| `search_amendments` | Recherche spécifique dans les amendements |
| `kg_lookup` | Consultation du graphe de connaissances |
| `check_applicability` | Évaluation de l'applicabilité d'une exigence |
| `get_article` | Récupération du texte complet d'un article |
| `get_requirements` | Liste des exigences d'un article |
| `answer` | Production de la réponse finale |

#### 4.5.3 Boucle de raisonnement

L'agent exécute une boucle Thought → Action → Observation, où chaque appel d'outil enrichit le contexte. Le post-traitement nettoie les artefacts de raisonnement et vérifie la qualité de la réponse finale via le Quality Guard.

### 4.6 Analyse automatisée de contrats

Le `contract_analysis_service.py` (1 096 lignes) implémente un pipeline d'analyse de contrats en cinq passes :

#### 4.6.1 Pipeline en cinq passes

1. **Extraction de clauses** : le LLM identifie les clauses présentes dans le contrat avec leur catégorie et un extrait.
2. **Détection de risques** : chaque clause est évaluée pour identifier les risques juridiques (ambiguïté, non-conformité, clauses abusives).
3. **Identification de clauses manquantes** : comparaison avec les clauses obligatoires et recommandées selon le type de contrat, enrichie par le contexte RAG.
4. **Scoring global** : calcul d'un score de conformité sur 100, catégorisé en bon, attention ou critique.
5. **Recommandations** : génération de recommandations concrètes fondées sur l'analyse et le droit applicable.

#### 4.6.2 Types de contrats supportés

Le module gère huit types de contrats avec des clauses obligatoires et recommandées spécifiques à chaque type : contrat de travail, contrat commercial, bail, prestation de services, société (statuts), sous-traitance, NDA et contrat type générique.

### 4.7 Fine-tuning des modèles

#### 4.7.1 Fine-tuning des embeddings

Le pipeline d'entraînement en quatre scripts produit un modèle d'embeddings adapté au domaine juridique tunisien :

| Script | Rôle | Output |
|--------|------|--------|
| `01_build_eval_set.py` | Export articles + eval set (25 queries) | `eval_set.jsonl` |
| `02_build_train_set.py` | Paires (query, positive) + synthétique LLM | `train_set_filtered.jsonl` |
| `03_evaluate_retrieval.py` | Benchmark Recall@k, MRR@k, nDCG@k | Métriques JSON |
| `04_finetune_embeddings.py` | Fine-tuning MNR loss (PyTorch) | Modèle .safetensors |

**Configuration** : modèle base `paraphrase-multilingual-mpnet-base-v2` (278M paramètres), loss MNR (contrastive), AdamW (lr=2×10⁻⁵), linear warmup 10 %, 2 epochs, batch size 32, durée ~110 minutes CPU.

**Table 4.6 — Résultats du fine-tuning**

| Métrique | Baseline | Fine-tuné | Delta |
|----------|----------|-----------|-------|
| Recall@1 | 0.20 | **0.48** | +0.28 (+140 %) |
| Recall@5 | 0.32 | **0.56** | +0.24 (+75 %) |
| Recall@10 | 0.40 | **0.60** | +0.20 (+50 %) |
| MRR@5 | 0.24 | **0.51** | +0.27 |
| MRR@10 | 0.25 | **0.52** | +0.26 |
| nDCG@5 | 0.26 | **0.52** | +0.26 |
| nDCG@10 | 0.29 | **0.54** | +0.25 |

**Par langue** : français Recall@5 0.53 → 0.87 (+0.33), arabe Recall@5 0.00 → 0.10 (amélioration légère, corpus OCR bruité).

#### 4.7.2 Fine-tuning de style (Track 1)

Le `llm_style_formatter.py` intègre un modèle LoRA/PEFT spécialisé pour stabiliser la sortie du Legal Advisor dans le format Markdown strict à 7 sections. Le module fonctionne en mode fail-safe : si le modèle n'est pas disponible, le système retourne la réponse brute du LLM.

#### 4.7.3 Fine-tuning de raisonnement (Track 2)

Le `reasoning_model_service.py` implémente un classifieur multi-tâches (basé sur XLM-RoBERTa) pour améliorer le routage de domaine, le triage des cas et l'extraction de faits. L'inférence est rapide (<50 ms CPU) et le chargement du modèle utilise `local_files_only=True` pour la sécurité. Le module charge le modèle depuis un chemin local configurable et fonctionne également en mode passthrough.

### Conclusion

Ce chapitre a détaillé la phase de modélisation de CRISP-DM : le pipeline RAG complet avec ses mécanismes de routage et de qualité, l'agent autonome ReAct, le module d'analyse de contrats et les trois pistes de fine-tuning. L'amélioration de +140 % du Recall@1 après fine-tuning des embeddings valide l'approche d'adaptation au domaine. Le chapitre suivant évaluera l'ensemble du système et présentera les couches applicatives de conformité et d'interface.

---

## Chapitre 5 — Évaluation, conformité et déploiement

### Introduction

Ce chapitre couvre les phases 5 (Evaluation) et 6 (Deployment) de CRISP-DM. Il présente les modules de conformité réglementaire, la gestion des cas juridiques, l'interface utilisateur, l'authentification multi-tenant, la suite de tests et l'intégration continue, ainsi que l'évaluation quantitative du système.

### 5.1 Module de conformité réglementaire

#### 5.1.1 Évaluation d'applicabilité

Le service `applicability_service.py` évalue quelles exigences réglementaires s'appliquent à un profil d'entreprise donné. Le LLM compare le profil (secteur, taille, activités, juridiction) avec chaque exigence extraite et produit un verdict (applicable / non applicable) avec un score de confiance.

#### 5.1.2 Scoring de criticité

Le `criticality_service.py` implémente un moteur à règles déterministe pour scorer chaque action :

- **Score de base** par modalité : obligation (0.7), sanction (0.8), interdiction (0.75), condition (0.5).
- **Bonus par mots-clés** : termes de sanction (+0.15), montants monétaires (+0.1), domaine spécialisé (+0.05), pénalité conditionnelle (+0.1), mots-clés arabes.
- **Classification** : critique (≥ 0.7), importante (0.4–0.7), secondaire (< 0.4).
- **Score capé** à 1.0.

Ce moteur à règles — par opposition à un scoring par LLM — garantit la reproductibilité et la transparence des résultats, deux qualités essentielles dans un contexte juridique.

#### 5.1.3 Feuille de route de mise en conformité

Le service `roadmap_service.py` génère une feuille de route ordonnée par priorité via un tri topologique sur le graphe de dépendances (DAG) entre actions. L'export est disponible en CSV et XLSX. Les actions sont ordonnées par niveau de criticité (critique → importante → secondaire) puis par dépendances.

#### 5.1.4 Analyse d'écart et cartographie des contrôles

Le `compliance_service.py` implémente :

- **Assessments** : évaluations périodiques de conformité (gap analysis) ;
- **Contrôles internes** : mesures préventives/détectives avec scores d'efficacité ;
- **Liens exigences-contrôles** : mapping many-to-many calculant le taux de couverture ;
- **Registre d'exceptions** : acceptation des risques, waivers et compensations.

### 5.2 Gestion des cas juridiques

#### 5.2.1 Cycle de vie d'un cas

Le `case_service.py` gère cinq collections. Un cas suit un cycle structuré : ouvert → en cours → résolu → fermé, avec des attributs de priorité, d'assignation et de tags. Chaque cas agrège des messages conversationnels, des documents annexés, des constats et des actions correctives.

#### 5.2.2 Conversation progressive et extraction de contexte

Le `case_conversation_service.py` implémente un workflow de collecte progressive des faits. À chaque message utilisateur, le système exécute trois opérations séquentielles : persistance du message, extraction structurée par LLM, et génération de la prochaine question de clarification. Le contexte extrait est stocké dans un sous-document `conversation_context` du cas.

#### 5.2.3 Orchestrateur de cas

Le `compliance_case_orchestrator.py` transforme un cas vivant en constats, contrôles et actions de remédiation via un pipeline en sept étapes : collecte du contexte, analyse d'écart, vérification d'applicabilité, génération de constats, scoring de criticité, priorisation des actions, et cartographie des preuves.

L'orchestrateur prend ses décisions selon un arbre à quatre branches : ASK (demander plus d'informations), CLARIFY (clarifier un point ambigu), ACT (agir automatiquement) et REVIEW (demander une revue humaine). Les seuils de confiance déterminent la branche empruntée.

### 5.3 Interface utilisateur

Le frontend est développé en React 19 avec Vite. Il comprend 6 pages principales et 10 pages d'administration.

#### 5.3.1 Pages principales

| Page | Fichier | Fonction |
|------|---------|----------|
| Landing | `Landing.jsx` | Présentation de la plateforme |
| Login | `Login.jsx` | Authentification (connexion / inscription) |
| Reset Password | `ResetPassword.jsx` | Réinitialisation du mot de passe |
| Chat | `Chat.jsx` | Interface Q&A, sources, historique, voix |
| Dashboard | `Dashboard.jsx` | Tableau de bord principal |
| Invite | `Invite.jsx` | Acceptation d'invitation à une organisation |

#### 5.3.2 Pages d'administration

| Page | Fichier | Fonction |
|------|---------|----------|
| Documents | `admin/Documents.jsx` | Upload, gestion, stats, vector index |
| Users | `admin/Users.jsx` | Gestion des utilisateurs et rôles |
| Organizations | `admin/Organizations.jsx` | Gestion multi-tenant |
| Cases | `admin/Cases.jsx` | Gestion des dossiers de conformité |
| Amendments | `admin/Amendments.jsx` | Suivi des amendements législatifs |
| Company Profile | `admin/CompanyProfile.jsx` | Profil entreprise pour applicabilité |
| Contract Analysis | `admin/ContractAnalysis.jsx` | Analyse multi-passes de contrats |
| Notifications | `admin/Notifications.jsx` | Centre de notifications |
| History | `admin/History.jsx` | Historique des conversations |
| Settings | `admin/Settings.jsx` | Paramètres de la plateforme |

#### 5.3.3 Internationalisation et support RTL

L'internationalisation repose sur react-i18next avec trois fichiers de locale (français, arabe, anglais). Le mode RTL est activé automatiquement pour l'arabe, affectant l'alignement des composants, la disposition de la barre latérale et le sens de lecture.

### 5.4 Authentification et multi-tenancy

#### 5.4.1 Modèle d'authentification

L'authentification repose sur des tokens JWT (HS256) : un access token de 30 minutes pour les requêtes API et un refresh token de 7 jours pour le renouvellement transparent. Le système supporte la révocation individuelle (JTI blacklist) et globale des tokens, l'authentification par clé API pour les intégrations programmatiques, et la réinitialisation de mot de passe par email (token sécurisé, expiration 1 heure). Les mots de passe sont hashés avec bcrypt.

#### 5.4.2 Architecture multi-tenant

Chaque utilisateur appartient à une organisation avec gestion d'abonnement (mensuel/annuel) et expiration automatique. Quatre niveaux de rôles structurent les permissions :

| Rôle | Périmètre |
|------|-----------|
| `super_admin` | Visibilité transversale sur toutes les organisations |
| `owner` | Administration complète de son organisation |
| `admin` | Gestion des utilisateurs et invitations |
| `member` | Accès aux fonctionnalités de base |

Le système d'invitation permet aux administrateurs d'intégrer de nouveaux membres via un lien sécurisé avec expiration (72 heures par défaut).

### 5.5 Tests et intégration continue

#### 5.5.1 Suite de tests

La qualité du code est assurée par une suite de **865 tests unitaires** répartis sur **54 fichiers de tests**, couvrant **50 %** du code backend. La stratégie de test privilégie les fonctions pures (sérialiseurs, moteurs de scoring, validateurs, utilitaires de langue) testables sans infrastructure externe.

**Table 5.2 — Couverture par module (extraits)**

| Module | Couverture | Lignes testées |
|--------|-----------|----------------|
| `schemas.py` + `schemas_auth.py` | 100 % | 620/620 |
| `compliance_schemas.py` | 100 % | 224/224 |
| `config.py` | 98 % | 86/88 |
| `text_utils.py` | 98 % | 131/133 |
| `article_segmenter.py` | 94 % | 119/126 |
| `chunker.py` | 92 % | 196/212 |
| `analytics_service.py` | 100 % | 37/37 |
| `advisor_response_composer.py` | 92 % | 355/385 |
| `derja_normalizer.py` | 100 % | 34/34 |
| `criticality_service.py` | 44 % | 57/102 |
| `auth_service.py` | 53 % | 147/275 |
| `reranker.py` | 68 % | 54/79 |

Les techniques de mock utilisées incluent `AsyncMock` pour les appels MongoDB asynchrones, `MagicMock` pour les objets de configuration, `patch` pour l'isolation des dépendances externes, et `monkeypatch` pour les variables d'environnement.

#### 5.5.2 Intégration continue

Le pipeline CI/CD GitHub Actions exécute automatiquement sur chaque push :

**Job test** (matrice Python 3.11, 3.12, 3.13) :
- Service MongoDB 7 en conteneur
- Installation des dépendances depuis `requirements.txt`
- Exécution des 865 tests avec couverture
- Seuil minimal de couverture : 50 % (`--cov-fail-under=50`)

**Job lint** :
- Analyse statique Ruff (règles E, W, F)
- Scan de sécurité Bandit (niveau low-low)

**Job frontend** :
- Installation des dépendances npm (Node 20)
- Lint ESLint du code React
- Build de production Vite

#### 5.5.3 Validation de production

Le module `config.py` implémente une validation des paramètres au démarrage (`_validate_production_settings`) qui vérifie en environnement production/staging : la présence de la clé API, la présence de la clé admin, la robustesse du secret JWT (≥ 32 caractères), et le rejet du wildcard CORS.

### 5.6 Évaluation du système

#### 5.6.1 Métriques de retrieval

L'évaluation de la recherche sémantique a été conduite sur un jeu de 25 requêtes couvrant les domaines juridiques. Les résultats du fine-tuning sont présentés dans la table 4.6 (chapitre 4). Le Recall@1 passe de 0.20 à 0.48 (+140 %) et le Recall@5 de 0.32 à 0.56 (+75 %), confirmant l'utilité de l'adaptation au domaine juridique tunisien.

Par langue, le français montre des gains substantiels (Recall@5 : 0.53 → 0.87), tandis que l'arabe reste faible (Recall@5 : 0.00 → 0.10), principalement en raison du bruit OCR dans le corpus arabe.

#### 5.6.2 Fiabilisation par le Quality Guard

Le garde-qualité opère en post-génération sur chaque réponse. Les trois niveaux de vérification — fidélité des références, vérification des citations, fidélité sémantique — détectent et corrigent les anomalies avant la présentation à l'utilisateur. Le mode de réécriture conservative garantit qu'aucune information non vérifiable n'est présentée comme factuelle.

#### 5.6.3 Couverture fonctionnelle

**Table 5.3 — Couverture des endpoints par routeur**

| Routeur | Endpoints | Périmètre |
|---------|-----------|-----------|
| `router.py` | ~79 | Documents, RAG, search, ask, profils, lois, articles, exports |
| `auth_router.py` | 19 | Register, login, refresh, logout, profil, invitations |
| `compliance_router.py` | 22 | Assessments, contrôles, preuves, liens, posture, exceptions |
| `case_router.py` | 21 | Cases, findings, actions, documents, états |
| `case_orchestrator_router.py` | 5 | Orchestration, arbres de décision |
| `case_conversation_router.py` | 3 | Messages, thread, historique |
| `voice_router.py` | 3 | Transcribe (STT), synthesize (TTS), voice-chat |
| **Total** | **152** | |

### 5.7 Tableau récapitulatif

**Table 5.4 — Récapitulatif des composants applicatifs**

| Composant | Métrique |
|-----------|----------|
| Lignes de code (backend `app/`) | 31 878 |
| Lignes de code (frontend) | 3 451 |
| Lignes de tests | 11 969 |
| Fichiers de tests | 54 |
| Tests unitaires | 865 |
| Couverture de code | 50 % |
| Endpoints REST | 152 |
| Collections MongoDB | 35 |
| Pages frontend | 16 (6 principales + 10 admin) |
| Langues supportées | 3 (français, arabe, anglais) |
| Documents du corpus | 5 PDF (5,7 Mo) |
| Articles extraits | 2 344 |
| Paires d'entraînement | 4 584 |
| Versions Python CI | 3 (3.11, 3.12, 3.13) |
| Services Docker | 3 (API, MongoDB, Ollama) |

### Conclusion

Ce chapitre a couvert les phases d'évaluation et de déploiement de CRISP-DM. Le module de conformité réglementaire, avec son scoring de criticité déterministe et son orchestrateur décisionnel, l'interface utilisateur multilingue, et l'architecture multi-tenant constituent les couches applicatives du système. La suite de 865 tests avec 50 % de couverture et le pipeline CI/CD à trois jobs assurent la qualité continue du code. Les métriques de retrieval valident l'approche de fine-tuning domain-specific, avec un gain de +140 % du Recall@1 sur le corpus juridique tunisien.

---

## Conclusion Générale

Ce rapport a présenté la conception, le développement et l'évaluation de **Daleel**, une plateforme d'assistance juridique intelligente dédiée au droit tunisien, réalisée dans le cadre d'un stage de fin d'études chez Didax IT. Le développement a suivi la méthodologie CRISP-DM, dont les six phases — compréhension métier, compréhension des données, préparation des données, modélisation, évaluation et déploiement — ont structuré l'ensemble du projet en cycles itératifs.

Le **premier chapitre** a posé le cadre organisationnel et la problématique : l'accès aux textes juridiques tunisiens demeure fragmenté, souvent monolingue, et dépourvu d'outils d'analyse automatisée. La veille réglementaire repose encore largement sur un travail manuel coûteux et sujet à l'erreur.

Le **deuxième chapitre** a détaillé le cadre théorique et l'état de l'art. L'étude des architectures RAG, des embeddings multilingues, des LLM locaux et des techniques de fiabilisation post-génération a confirmé l'absence d'un outil spécifiquement adapté au corpus juridique tunisien trilingue.

Le **troisième chapitre** a couvert les phases de compréhension et de préparation des données. La chaîne de traitement à trois niveaux (PyMuPDF, pdfminer, OCR Tesseract/EasyOCR) avec nettoyage spécialisé pour l'arabe permet d'absorber des PDF scannés comme numériques. Le chunking sensible à la structure juridique produit des segments cohérents. La normalisation du dialecte tunisien (derja) et le versionnement immutable des articles complètent cette phase.

Le **quatrième chapitre** a présenté la phase de modélisation. Le routeur de domaine oriente chaque requête, le retrieval partitionné sépare lois de base et amendements, et le Quality Guard applique une triple vérification post-génération. L'agent autonome ReAct avec sept outils spécialisés permet un raisonnement itératif. Le module d'analyse de contrats en cinq passes offre un scoring de conformité contractuelle. Le fine-tuning des embeddings par perte MNR a amélioré le Recall@1 de +140 % et le Recall@5 de +75 %.

Le **cinquième chapitre** a couvert les phases d'évaluation et de déploiement. Le module de conformité réglementaire avec scoring de criticité déterministe, feuille de route par tri topologique et cartographie des contrôles, l'orchestrateur de cas avec arbre décisionnel, l'interface trilingue avec support RTL, et la suite de 865 tests avec intégration continue valident la qualité du système.

### Bilan quantitatif

Le système totalise environ 47 300 lignes de code réparties sur 155 fichiers : 31 878 lignes pour le backend applicatif, 3 451 pour le frontend React, et 11 969 pour les tests. Il expose 152 endpoints REST, gère 35 collections MongoDB, et supporte trois langues. Le pipeline d'entraînement a produit 4 584 paires et le modèle fine-tuné pèse 1,06 Go. L'ensemble est conteneurisé via Docker Compose, vérifié par 865 tests (50 % de couverture) et soumis à une intégration continue sur trois versions de Python.

### Limites et honnêteté scientifique

Le modèle de langage utilisé (Qwen 2.5:7b) reste un modèle généraliste de taille modeste. Les performances de génération dépendent fortement de la qualité du prompt et du contexte récupéré. Le Quality Guard atténue les hallucinations mais ne les élimine pas complètement, d'où la recommandation systématique de vérification humaine dans les réponses de l'assistant.

L'évaluation du retrieval a été conduite sur 25 requêtes — un échantillon suffisant pour valider les tendances mais insuffisant pour des conclusions statistiques robustes. Le scoring de criticité repose sur des règles heuristiques qui, bien que transparentes et reproductibles, ne remplacent pas l'expertise d'un juriste.

Le Recall en arabe reste faible (0.10 après fine-tuning) en raison du bruit OCR dans le corpus arabe. La couverture de test à 50 % est un seuil fonctionnel mais idéalement devrait atteindre 70 % pour un système de production.

### Perspectives

Plusieurs axes d'amélioration se dessinent :

- **Élargissement du corpus** : intégration du Journal Officiel de la République Tunisienne (JORT) et des décisions de jurisprudence pour enrichir la couverture documentaire.
- **Évaluation à grande échelle** : constitution d'un benchmark de référence pour le domaine juridique tunisien, avec annotation par des experts en droit.
- **Modèle de langue spécialisé** : fine-tuning complet d'un LLM sur le corpus juridique tunisien pour améliorer la précision terminologique, en particulier pour l'arabe dialectal et le français juridique tunisien.
- **Intégration de la jurisprudence** : extraction automatique des décisions de justice et enrichissement du graphe de connaissances avec les interprétations judiciaires.
- **Interface mobile** : développement d'une application mobile pour les professionnels du droit en déplacement.
- **Amélioration de l'OCR arabe** : utilisation de modèles OCR spécialisés pour le texte juridique arabe afin d'améliorer le Recall dans cette langue.

Daleel démontre qu'il est possible de construire un assistant juridique fiable et multilingue pour un droit national spécifique, en combinant des techniques de RAG avancé, un pipeline de fiabilisation rigoureux et une architecture modulaire. Le projet constitue une base technique solide sur laquelle des fonctionnalités supplémentaires pourront être greffées au fil de l'évolution du cadre réglementaire tunisien.

---

## Bibliographie

1. Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., ... & Kiela, D. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. *Advances in Neural Information Processing Systems*, 33, 9459-9474.

2. Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2022). ReAct: Synergizing Reasoning and Acting in Language Models. *arXiv preprint arXiv:2210.03629*.

3. Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. *Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing (EMNLP)*.

4. Henderson, M., Al-Rfou, R., Strope, B., Sung, Y. H., Lukács, L., Guo, R., ... & Kurzweil, R. (2017). Efficient Natural Language Response Suggestion for Smart Reply. *arXiv preprint arXiv:1705.00652*.

5. Johnson, J., Douze, M., & Jégou, H. (2019). Billion-scale similarity search with GPUs. *IEEE Transactions on Big Data*, 7(3), 535-547.

6. Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., ... & Polosukhin, I. (2017). Attention Is All You Need. *Advances in Neural Information Processing Systems*, 30.

7. Wirth, R., & Hipp, J. (2000). CRISP-DM: Towards a Standard Process Model for Data Mining. *Proceedings of the 4th International Conference on the Practical Applications of Knowledge Discovery and Data Mining*, 29-39.

8. Chapman, P., Clinton, J., Kerber, R., Khabaza, T., Reinartz, T., Shearer, C., & Wirth, R. (2000). CRISP-DM 1.0: Step-by-step data mining guide. *SPSS Inc.*

9. Malkov, Y. A., & Yashunin, D. A. (2018). Efficient and Robust Approximate Nearest Neighbor Search Using Hierarchical Navigable Small World Graphs. *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 42(4), 824-836.

10. Conneau, A., Khandelwal, K., Goyal, N., Chaudhary, V., Wenzek, G., Guzmán, F., ... & Stoyanov, V. (2020). Unsupervised Cross-lingual Representation Learning at Scale. *Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics*, 8440-8451.
