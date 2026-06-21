# Rapport de Projet de Fin d'Études

**Daleel — Plateforme intégrée d'assistance juridique et de pilotage de la conformité réglementaire fondée sur l'intelligence artificielle, à vocation internationale et appliquée initialement au droit tunisien**

---

## Dédicace

Je dédie ce travail à mes parents, pour leur amour, leurs sacrifices, leur patience et leur confiance qui m'ont accompagnée tout au long de mon parcours.

À mes frères, pour leur soutien, leur présence et leurs encouragements constants.

À ma famille, pour son soutien constant, ses encouragements et sa présence dans les moments les plus importants.

À mes sœurs de cœur, pour leur affection, leur aide et leur présence précieuse.

À mes amis et à toutes les personnes qui m'ont apporté leur aide, leur motivation ou un mot d'encouragement durant cette aventure.

Je dédie également ce travail à toutes les personnes qui ont cru en moi et qui ont contribué, de près ou de loin, à l'aboutissement de ce Projet de Fin d'Études.

---

## Remerciements

Au terme de ce Projet de Fin d'Études, je tiens à exprimer ma profonde gratitude à toutes les personnes qui ont contribué, de près ou de loin, à la réalisation de ce travail.

Je remercie tout particulièrement mon encadrant académique, **Dr Nizar Omheni**, pour son accompagnement, ses conseils précieux, sa disponibilité et ses orientations tout au long de ce projet.

J'adresse également mes sincères remerciements à l'entreprise **Didax IT** pour son accueil, sa confiance et l'environnement professionnel stimulant qu'elle m'a offert durant cette expérience. Cette immersion m'a permis de consolider mes compétences techniques, de mieux comprendre les exigences d'un projet réel et de développer une solution à la fois utile, ambitieuse et concrète.

Je souhaite aussi remercier l'ensemble des enseignants de l'École Polytechnique de Sousse pour la qualité de la formation dispensée et pour les connaissances acquises durant mon parcours académique.

Enfin, j'exprime toute ma reconnaissance à ma famille et à mes proches pour leur soutien moral, leur patience, leurs encouragements et leur présence constante. Leur confiance a été une source essentielle de motivation tout au long de ce travail.

---

## Résumé

Ce Projet de Fin d'Études présente **Daleel**, une plateforme intégrée d'assistance juridique et de pilotage de la conformité réglementaire fondée sur l'intelligence artificielle, conçue pour une extension internationale et appliquée dans ce travail à un premier périmètre tunisien. La plateforme répond à un double besoin : d'une part, interroger en langage naturel (arabe, français, anglais) un corpus juridique fragmenté, multilingue et issu de sources hétérogènes (PDF natifs, documents numérisés, OCR) ; d'autre part, piloter de bout en bout le cycle opérationnel de conformité des entreprises. Le volet *Legal RAG* repose sur une architecture de génération augmentée par récupération avancée combinant une recherche hybride (signaux vectoriels FAISS et lexicaux fusionnés par pondération), un reranking par cross-encoder, un retrieval partitionné piloté par l'intention, graphe de connaissances léger, garde-qualité anti-hallucination multi-couches et un agent autonome ReAct à douze outils. Le *fine-tuning* d'un modèle d'embeddings multilingue sur le corpus juridique tunisien a produit des gains globaux de **+40 % en Recall@1** et **+34 % en MRR@10** (mesurés sur 30 requêtes gold couvrant le français et l'arabe), avec des gains particulièrement marqués sur le sous-corpus francophone (+50 % en Recall@1, +43 % en MRR@10) et une amélioration notable du rappel arabe en top-5 (+50 %). Le volet *Compliance Operations* orchestre la gestion des dossiers de non-conformité, des constats, des actions correctives et des preuves selon un arbre de décision ASK / CLARIFY / ACT / REVIEW. La conduite du projet a suivi la méthodologie CRISP-DM.

**Mots-clés :** intelligence artificielle, RAG, agent autonome, LLM, droit tunisien, extension internationale, conformité réglementaire, embeddings multilingues, fine-tuning, FAISS, LegalTech.

## Abstract

This graduation project presents **Daleel**, an integrated AI-powered platform for legal assistance and regulatory compliance management, designed for international expansion and initially applied to Tunisian law. The platform addresses a twofold need: querying a fragmented, multilingual legal corpus (Arabic, French, English) drawn from heterogeneous sources (native PDFs, scanned documents, OCR) in natural language; and managing the full operational compliance lifecycle of organizations. The *Legal RAG* component relies on an advanced Retrieval-Augmented Generation architecture combining hybrid search (vector FAISS and lexical signals merged through weighted fusion), cross-encoder reranking, intent-driven partitioned retrieval, a lightweight knowledge graph, a multi-layer anti-hallucination quality guard, and a twelve-tool autonomous ReAct agent. Fine-tuning a multilingual embedding model on the Tunisian legal corpus yielded overall gains of **+40 % in Recall@1** and **+34 % in MRR@10** (measured on 30 gold queries covering French and Arabic), with particularly strong gains on the French sub-corpus (+50 % in Recall@1, +43 % in MRR@10) and a notable improvement in Arabic top-5 recall (+50 %). The *Compliance Operations* component orchestrates non-compliance case management, findings, corrective actions and evidence following an ASK / CLARIFY / ACT / REVIEW decision tree. The project followed the CRISP-DM methodology.

**Keywords:** artificial intelligence, RAG, autonomous agent, LLM, Tunisian law, international expansion, regulatory compliance, multilingual embeddings, fine-tuning, FAISS, LegalTech.

---

## Table des matières

> *Les numéros de page sont générés automatiquement à la conversion en PDF (Pandoc `--toc` ou table des matières Word). Le plan ci-dessous reflète la structure du mémoire.*

**Introduction générale**

**1. Présentation du projet**
- Introduction
- 1.1 Présentation de l'entreprise d'accueil
- 1.2 Contexte métier et scientifique
- 1.3 Présentation générale de la plateforme Daleel
- 1.4 Problématique détaillée
- 1.5 Objectifs du projet
- 1.6 Méthodologie de projet (CRISP-DM)
- 1.7 Spécification des besoins
- Conclusion

**2. État de l'art**
- Introduction
- 2.1 Modèles de langage de grande taille
- 2.2 Architectures de génération augmentée par récupération (RAG)
- 2.3 Recherche hybride et reranking
- 2.4 Agents IA et paradigme ReAct
- 2.5 Ingénierie de prompts et anti-hallucination
- 2.6 Modèles d'embeddings multilingues et fine-tuning
- 2.7 LegalTech et assistance juridique fondée sur l'IA
- 2.8 Systèmes de gestion de la conformité réglementaire
- Conclusion

**3. Conception de la solution**
- Introduction
- 3.1 Architecture globale de la plateforme Daleel
- 3.2 Conception du pipeline d'ingestion documentaire
- 3.3 Conception du pipeline RAG avancé à six modules
- 3.4 Conception de l'agent autonome ReAct
- 3.5 Conception du fine-tuning des embeddings
- 3.6 Conception de la garde-qualité anti-hallucination
- 3.7 Conception du volet Compliance Operations
- 3.8 Modélisation conceptuelle des données
- 3.9 Choix technologiques (critères, comparaison des LLM candidats, synthèse)
- Conclusion

**4. Réalisation du volet Legal RAG**
- Introduction
- 4.1 Environnement de développement
- 4.2 Implémentation du pipeline d'ingestion documentaire
- 4.3 Fine-tuning du modèle d'embeddings
- 4.4 Implémentation du pipeline RAG à six modules
- 4.5 Implémentation de l'agent autonome ReAct
- 4.6 Démonstrations qualitatives
- Conclusion

**5. Compliance Operations, évaluation et déploiement**
- Introduction
- 5.1 Implémentation du cycle de conformité
- 5.2 Orchestrateur LLM ASK / CLARIFY / ACT / REVIEW
- 5.3 Interfaces utilisateur
- 5.4 Évaluation quantitative
- 5.5 Déploiement et intégration continue
- 5.6 Discussion critique : limites et perspectives
- Conclusion

**Conclusion générale**

**Bibliographie**

**Annexes**
- Annexe A — Cartographie complète de l'API REST (plus de 170 points d'accès)
- Annexe B — Catalogue de configuration de la plateforme (71 paramètres `DALEEL_*`)
- Annexe C — Spécification des douze outils de l'agent autonome ReAct
- Annexe D — Modèle de données détaillé : les 38 collections MongoDB
- Annexe E — Couverture de tests (55 fichiers) et chaîne d'intégration continue

---

## Liste des figures

| Figure | Intitulé |
|---|---|
| 1.1 | Cycle CRISP-DM appliqué au projet Daleel |
| 1.2 | Diagramme de cas d'utilisation général de la plateforme Daleel (vue synthétique) |
| 1.3 | Diagramme de cas d'utilisation détaillé : Authentification, gestion des comptes et emails transactionnels |
| 1.4 | Diagramme de cas d'utilisation détaillé : Assistant juridique IA (Legal RAG) |
| 1.5 | Diagramme de cas d'utilisation détaillé : Conformité, dossiers de non-conformité et feuille de route |
| 3.1 | Architecture globale de la plateforme Daleel : cinq couches et deux volets |
| 3.2 | Traitement d'une requête utilisateur dans le pipeline RAG Daleel |
| 3.3 | Arbre de décision de l'orchestrateur Compliance Operations |
| 3.4 | Modèle conceptuel de la hiérarchie juridique |
| 3.5 | Modèle conceptuel du cycle de conformité |
| 4.1 | Réponse du pipeline RAG classique dans le chatbot |
| 4.2 | Journal de raisonnement de l'agent autonome ReAct |
| 4.3 | Détection et normalisation d'une requête en derja tunisien |
| 5.1 | Interface du chatbot conversationnel multilingue |
| 5.2 | Panneau d'administration : gestion documentaire |
| 5.3 | Tableau de bord BI de la posture de conformité |
| 5.4 | Comparaison des métriques de retrieval avant et après fine-tuning |
| 5.5 | Schéma de déploiement Docker Compose de la plateforme Daleel |

---

## Liste des tableaux

| Tableau | Intitulé |
|---|---|
| 1.1 | Correspondance phases CRISP-DM ↔ chapitres du mémoire |
| 2.1 | Comparaison des solutions d'assistance juridique et de conformité existantes |
| 3.1 | Couches architecturales de Daleel et composants principaux |
| 3.2 | Paramètres clés du pipeline d'ingestion |
| 3.3 | Stratégie de mixing partitionnée par intention |
| 3.4 | Catalogue des outils de l'agent autonome ReAct |
| 3.5 | Hyperparamètres du fine-tuning du modèle d'embeddings |
| 3.6 | Composantes du score de criticité |
| 3.7 | Cartographie des 38 collections MongoDB par domaine |
| 3.8 | Comparaison des modèles de langage candidats au regard des contraintes de Daleel |
| 3.9 | Synthèse des technologies retenues et justification des choix |
| 4.1 | Configuration matérielle de la station de développement |
| 4.2 | Composants logiciels et leur rôle dans la plateforme |
| 5.1 | Services métier du volet Compliance Operations |
| 5.2 | Performance globale du modèle d'embeddings avant et après fine-tuning |
| 5.3 | Décomposition par langue des métriques de retrieval avant et après fine-tuning |
| 5.4 | Couverture des tests par couche |

---

## Liste des acronymes

| Acronyme | Signification |
|---|---|
| API | Application Programming Interface |
| ASGI | Asynchronous Server Gateway Interface |
| BI | Business Intelligence |
| BM25 | Best Matching 25 |
| CI/CD | Continuous Integration / Continuous Deployment |
| CPU | Central Processing Unit |
| CRISP-DM | Cross-Industry Standard Process for Data Mining |
| DOCX | Open XML Document Format |
| DPO | Data Protection Officer (délégué à la protection des données) |
| ERP | Enterprise Resource Planning |
| FAISS | Facebook AI Similarity Search |
| GED | Gestion Électronique de Documents |
| GPU | Graphics Processing Unit |
| GRC | Governance, Risk & Compliance |
| HNSW | Hierarchical Navigable Small World |
| INPDP | Instance Nationale de Protection des Données Personnelles |
| IORT | Imprimerie Officielle de la République Tunisienne |
| JORT | Journal Officiel de la République Tunisienne |
| JWT | JSON Web Token |
| KG | Knowledge Graph |
| LLM | Large Language Model |
| LRU | Least Recently Used |
| MFA | Multi-Factor Authentication |
| MNR | MultipleNegativesRankingLoss |
| MRR | Mean Reciprocal Rank |
| nDCG | Normalized Discounted Cumulative Gain |
| NFKC | Normalization Form KC (Unicode) |
| OCR | Optical Character Recognition |
| PDF | Portable Document Format |
| RAG | Retrieval-Augmented Generation |
| ReAct | Reasoning + Acting |
| REST | Representational State Transfer |
| RGPD | Règlement Général sur la Protection des Données |
| RRF | Reciprocal Rank Fusion |
| SBERT | Sentence-BERT |
| SLA | Service-Level Agreement |
| SSE | Server-Sent Events |
| UTF | Unicode Transformation Format |

---

## Introduction générale

La numérisation des activités juridiques et de conformité connaît une accélération sous l'effet des progrès de l'intelligence artificielle. Dans les secteurs traitant de grands volumes de documents, les professionnels doivent traiter quotidiennement des textes réglementaires volumineux lois, décrets, amendements, circulaires, procédures internes dans des délais limités. Les modèles de langage de grande taille (*Large Language Models*, LLMs) et les architectures de type *Retrieval-Augmented Generation* (RAG) ouvrent de nouvelles perspectives pour exploiter ces corpus complexes et en évolution continue. Il ne s'agit plus seulement de stocker l'information juridique, mais de la rendre interrogeable, contextualisée et exploitable dans un cadre opérationnel.

Le contexte tunisien illustre ces enjeux. Le cadre juridique national est riche et dynamique : codes, lois organiques, décrets, circulaires et jurisprudences se superposent et se modifient régulièrement, en français comme en arabe. Une partie essentielle de ces textes n'est disponible qu'en format PDF ou sous forme numérisée, rendant la recherche et l'analyse automatisées difficiles. Les juristes et les équipes de conformité s'appuient encore largement sur des méthodes manuelles : recherches lexicales dans des fichiers PDF, consultation de portails juridiques peu interactifs, ou appel systématique à des experts externes. Ces approches sont coûteuses en temps, sensibles à l'erreur humaine et peu adaptées au rythme des évolutions réglementaires.

L'intelligence artificielle appliquée au domaine juridique ne peut pas se limiter à l'utilisation directe de modèles génériques. Sans base documentaire solide, les LLMs produisent parfois des réponses convaincantes mais fausses, phénomène désigné sous le terme d'**hallucination**. Dans un contexte juridique et de conformité où une erreur peut entraîner des sanctions, des conflits ou une perte de confiance, ce risque est inacceptable. À ces enjeux s'ajoutent des contraintes structurelles : gestion du versionnement des textes et de leurs amendements, distinction entre texte de base et texte modifié, stabilité face à des données issues de l'OCR, et nécessité d'une traçabilité complète des traitements. Plus qu'un simple exercice de questions-réponses, la conformité repose sur un cycle complet allant de l'identification des exigences applicables à l'orchestration des actions correctives, en passant par l'évaluation des écarts et le suivi des preuves. À cela s'ajoute l'absence d'un cadre intégré de pilotage de la conformité : les organisations ne disposent d'aucun outil connectant directement les textes juridiques applicables à la gestion opérationnelle de leurs dossiers de non-conformité, de leurs actions correctives et de leurs contrôles internes.

La problématique principale de ce Projet de Fin d'Études peut être formulée comme suit : **comment concevoir une plateforme d'assistance juridique et de conformité, fondée sur l'intelligence artificielle, qui fournisse des réponses pertinentes, robustes, traçables et opérationnellement exploitables dans le contexte réglementaire tunisien ?**

Pour répondre à cette problématique, ce travail propose la conception et l'implémentation de **Daleel** (دليل, « le guide » en arabe), une plateforme intégrée de *Legal RAG* et de *Compliance Operations* à vocation internationale, appliquée initialement au droit tunisien. La plateforme repose sur deux volets complémentaires. Le premier volet *Legal RAG* permet d'interroger le corpus juridique tunisien en langage naturel arabe, français, anglais et de gérer le cycle de vie des textes de loi. Il repose sur une architecture RAG avancée combinant recherche hybride combinant signaux vectoriels et lexicaux par fusion pondérée, routage sémantique par domaine juridique, retrieval partitionné entre textes de base et amendements pondéré par l'intention de l'utilisateur, reranking par cross-encoder, enrichissement par graphe de connaissances léger, garde-qualité anti-hallucination multi-couches incluant une détection de citations fabriquées par fenêtre glissante, et un agent autonome ReAct doté de l'appel d'outils natif d'Ollama capable de raisonner itérativement sur douze outils spécialisés. L'ingénierie de prompts adopte un comportement d'assistant interactif proactif, orienté solutions, avec relance conversationnelle renforcé par un apprentissage en contexte (*few-shot*) trilingue et un ancrage disciplinaire strict assimilant l'invention d'un article à une faute professionnelle grave. Le fine-tuning d'un modèle d'embeddings multilingue sur le corpus juridique tunisien a permis des gains globaux mesurés de +40 % en Recall@1 et +34 % en MRR@10 par rapport au modèle de base (et jusqu'à +50 % et +43 % respectivement sur le sous-corpus francophone). Le second volet *Compliance Operations* couvre l'intégralité du cycle opérationnel de conformité : gestion des dossiers de non-conformité, identification des constats par sévérité, planification des actions correctives, suivi des preuves et des contrôles internes, registre des exceptions, et tableau de bord de la posture de conformité, le tout orchestré par un agent LLM structurant ses décisions selon un arbre ASK / CLARIFY / ACT / REVIEW.

Sur le plan technique, ces deux volets reposent sur **plus de 170 points d'accès REST organisés en 7 routeurs FastAPI**, **38 collections MongoDB**, un **index vectoriel FAISS HNSW** reconstruit en mémoire au démarrage, **41 services métier** et un total de **70 modules backend Python** déployés sous Docker Compose, ainsi que sur **34 composants React** côté frontend.

Le présent mémoire est organisé en cinq chapitres. Le **premier chapitre** pose le cadre général du projet : présentation de l'entreprise d'accueil Didax IT, analyse de la problématique, vue d'ensemble de la solution, méthodologie CRISP-DM adoptée, et **spécification des besoins fonctionnels et non fonctionnels** consolidée par un diagramme de cas d'utilisation général. Le **deuxième chapitre** présente l'**état de l'art** des composantes essentielles du projet : modèles de langage de grande taille, architectures de génération augmentée par récupération, techniques de recherche hybride et de reranking, agents IA et paradigme ReAct, ingénierie de prompts et garde-qualité, modèles d'embeddings multilingues et *fine-tuning*, LegalTech et systèmes de gestion de la conformité réglementaire. Le **troisième chapitre** détaille la **conception** de la plateforme Daleel : architecture globale, conception de chacun des modules clés (ingestion, RAG, agent, *fine-tuning*, garde-qualité, *Compliance Operations*), modélisation conceptuelle des données et justification comparative des choix technologiques, dont le choix du modèle de langage. Le **quatrième chapitre** décrit la **réalisation du volet Legal RAG** : implémentation du pipeline d'ingestion documentaire, *fine-tuning* du modèle d'embeddings sur le corpus juridique tunisien, mise en œuvre des six modules du pipeline RAG et de l'agent autonome ReAct, illustrée par trois démonstrations qualitatives. Le **cinquième chapitre** traite de la **réalisation du volet Compliance Operations**, des interfaces utilisateur, de l'évaluation quantitative des performances obtenues, du déploiement conteneurisé et de l'intégration continue, avant de conclure sur les limites identifiées et les perspectives d'évolution.

---

# Chapitre 1 — Présentation du projet

## Introduction

Ce premier chapitre définit le cadre général du Projet de Fin d’Études. Il présente l’entreprise d’accueil Didax IT et le contexte professionnel qui a conduit à la conception de la solution Daleel, expose les enjeux métier et scientifiques du projet, propose une vue d’ensemble de la solution dans ses deux dimensions Legal RAG et Compliance Operations, analyse en détail la problématique à laquelle elle répond, formule les objectifs du projet, décrit ses composantes principales, et présente la méthodologie de conduite de projet adoptée, fondée sur le cycle CRISP-DM adapté au développement d’une solution d’intelligence rtificielle appliquée au domaine juridique.

## 1.1 Présentation de l'entreprise d'accueil

**Didax IT** est une entreprise de services informatiques fondée à **Dubaï en 2024**. Son modèle économique repose sur une structure géographique hybride : un bureau commercial implanté à Dubaï servant d'antenne auprès d'une clientèle internationale, et des équipes techniques localisées dans des pays à coût compétitif, notamment la **Tunisie et l'Inde**, permettant de proposer une offre globale à la fois compétitive et de haute qualité technique.

Les activités de Didax IT se déclinent en quatre domaines :

- **Conception et développement de logiciels sur mesure** : analyse des besoins clients et proposition de solutions adaptées à leurs métiers, incluant des applications intégrant l'intelligence artificielle pour automatiser les tâches répétitives et assister la prise de décision fondée sur la donnée.
- **Transformation numérique et conseil** : accompagnement dans l'identification des besoins et l'intégration de solutions logicielles, principalement *open source*, offrant des alternatives économiques efficaces, particulièrement adaptées aux petites et moyennes entreprises.
- **Gestion de projets *e-learning*** : intervention auprès d'établissements d'enseignement et d'entreprises sur l'ensemble de la chaîne : analyse des besoins, conception pédagogique, conseil sur les outils, développement de contenus et accompagnement à la mise en œuvre.
- **Représentation de solutions logicielles métier** : conseil, revente, implémentation, formation des utilisateurs et maintenance de solutions spécialisées répondant à des besoins sectoriels précis.

C'est dans le cadre de sa mission de développement de solutions IA sur mesure que le projet **Daleel** a été initié, avec pour ambition de concevoir une plateforme d'assistance juridique et de conformité réglementaire à vocation internationale, expérimentée d'abord sur le marché et le droit tunisiens.

## 1.2 Contexte métier et scientifique

### 1.2.1 Contexte métier

La conformité réglementaire devient un défi stratégique majeur pour les entreprises tunisiennes. Soumises à un cadre juridique dense et en constante évolution, les directions juridiques, les cabinets d’avocats et les équipes de conformité doivent simultanément maîtriser plusieurs corpus législatifs Code du Travail, Code des Sociétés Commerciales, loi no 2004-63 sur la protection des données, Code de l’Investissement, réglementations de la Banque Centrale de Tunisie surveiller leurs amendements successifs, évaluer leur applicabilité selon le profil de chaque organisation, et documenter les actions correctives entreprises.

Dans ce contexte, les professionnels du droit en Tunisie manquent d’outils adaptés. Les sites juridiques existants, tels que le site de **l’Imprimerie Officielle de la République Tunisienne (IORT)** ou **le Journal Officiel de la République Tunisienne (JORT)**, permettent uniquement la consultation statique des textes, sans capacité de recherche sémantique, d’analyse d’applicabilité ou de pilotage de la conformité. Ce besoin crée une opportunité métier réelle : concevoir un assistant intelligent, basé sur les textes de référence officiels capable d’assister les professionnels aussi bien dans leurs recherches juridiques que dans la gestion opérationnelle de leur conformité.

### 1.2.2 Contexte scientifique

ur le plan scientifique, le projet s’inscrit dans le champ émergent de la *LegalTech* basée sur l’intelligence artificielle. Aujourd’hui, plusieurs avancées rendent techniquement possible la conception d’un assistant juridique fiable et spécialisé.

Les **modèles de langage de grande taille** (LLMs) sont capables de comprendre et de générer du texte en langage naturel, y compris dans des registres spécialisés tels que le langage juridique. Mais, utilisés seuls, ils souffrent du phénomène d’hallucination et ne disposent pas d’une connaissance actualisée des corpus normatifs locaux.
Les architectures de **Retrieval-Augmented Generation** (RAG) limitent les réponses du modèle à des sources documentaires vérifiables, récupérées dynamiquement au moment de la requête. Elles constituent le socle technique du pilier *Legal RAG* de Daleel.

Les **modèles d’embeddings multilingues** permettent de représenter des textes de langues différentes dans un espace vectoriel commun, rendant possible la recherche sémantique translingue entre des documents en arabe et des requêtes en français, ou vice versa.
Le fine-tuning de ces modèles sur un corpus domaine-spécifique, comme le corpus juridique tunisien, permet d’améliorer la pertinence de la récupération documentaire.

Les **agents IA autonomes**, fondés sur le paradigme ReAct (Reasoning + Acting), dépassent le simple question-réponse en permettant au modèle de raisonner sur un problème, d’appeler des outils spécialisés, d’observer les résultats et d’itérer jusqu’à construire une réponse complète. **L’appel d’outils natif** (native tool calling), désormais supporté par les LLMs récents, permet une intégration directe entre le raisonnement du modèle et les services applicatifs, constituant le socle d’une assistance juridique véritablement interactive.

Enfin, les **architectures d’orchestration de conformité** permettent d’automatiser des flux de travail complexes analyse d’un dossier de non-conformité, proposition de constats, formulation d’actions correctives constituant le socle du pilier *Compliance Operations* de Daleel.

## 1.3 Présentation générale de la plateforme Daleel

**Daleel** (دليل, « le guide » en arabe) est une plateforme intégrée de *Legal RAG* (*Retrieval-Augmented Generation*) et de *Compliance Operations*, spécialisée sur le corpus juridique tunisien. Elle permet à ses utilisateurs d'interroger en langage naturel un ensemble de textes de loi, de recevoir des réponses fondées sur des sources vérifiables, et de piloter l'intégralité de leur cycle de conformité réglementaire de bout en bout.

La plateforme repose sur **deux volets complémentaires** :

- **Volet 1 — Legal RAG** : moteur de recherche hybride multilingue (arabe, français, anglais) combinant recherche vectorielle FAISS HNSW et signaux lexicaux par fusion pondérée, reranking par cross-encoder, synthèse contextuelle par un modèle de langage qwen2.5 :7b déployé via Ollama, et gestion structurée du cycle de vie des textes (ingestion, segmentation, versionnement, traitement des amendements, traçabilité des modifications). Un agent autonome ReAct doté de douze outils spécialisés et utilisant l’appel d’outils natif d’Ollama permet un raisonnement itératif sur les requêtes complexes. Le système adopte un comportement d’assistant interactif proactif, orienté solutions, avec proposition de scénarios et relance conversationnelle, renforcé par un dispositif anti-hallucination multi-couches.
- **Volet 2 — Compliance Operations** : système complet de pilotage opérationnel de la conformité réglementaire gestion des dossiers de non-conformité, identification et scoring des constats (*findings*) par sévérité, planification des actions correctives, suivi des preuves de mise en œuvre, gestion des contrôles internes et des exceptions, tableau de bord de la posture de conformité, et orchestration automatisée des décisions par un agent LLM selon l’arbre ASK / CLARIFY / ACT / REVIEW.

Ces deux volets sont exposés via une API REST asynchrone de **plus de 170 points d'accès** répartis en 7 routeurs FastAPI, persistés dans une base documentaire **MongoDB de 38 collections**, soutenus par un **index vectoriel FAISS HNSW** en mémoire et **41 services métier** déployables sous Docker. Deux interfaces web complètent la plateforme : un **chatbot conversationnel** multilingue pour les utilisateurs finaux et un **panneau d'administration** pour la gestion du système, du corpus, des organisations et de la conformité, totalisant 34 composants React (dont 18 pages).

## 1.4 Problématique détaillée

### 1.4.1 Volume et fragmentation de l'information juridique

Le corpus juridique tunisien applicable aux entreprises est à la fois volumineux et fortement fragmenté. Il réunit les principaux codes juridiques : Code du Travail, Code des Sociétés Commerciales, Code de l’Investissement, des lois organiques spécifiques telles que la loi no 2004-63 relative à la protection des données à caractère personnel, aussi, un ensemble de décrets, arrêtés ministériels, circulaires et notes de la Banque Centrale de Tunisie. Ces textes sont disponibles sous des formats hétérogènes : PDF natifs, documents numérisés à qualité optique variable, et fichiers DOCX. Une fraction significative, les versions arabes, n’est accessible qu’en format scanné, rendant leur exploitation directe par les systèmes informatiques difficile.

Cette fragmentation crée une double difficulté : regrouper l’ensemble de ces sources dans un environnement commun, et assurer la cohérence lorsqu’un amendement modifie un ou plusieurs articles d’un texte existant. En l’absence d’outil dédié, les équipes juridiques et de conformité maintiennent manuellement la cohérence entre les différentes versions des textes processus long qui augmente les risques de lacunes.

### 1.4.2 Complexité structurelle et juridique

Les textes juridiques tunisiens présentent une structure hiérarchique dense : livres, titres,
chapitres, sections, articles, alinéas, dont la granularité varie d’un code à l’autre. Cette variabilité des structures complique la segmentation automatique des documents et la constitution
d’unités d’indexation cohérentes pour la recherche vectorielle.

À cette complexité formelle s’ajoute une complexité sémantique propre au langage juridique. Les obligations, interdictions, conditions et sanctions sont exprimées avec des nuances modales précises (« doit », « peut », « est tenu de ») portant des significations juridiques distinctes qu’un modèle générique non adapté risque d’ignorer ou de confondre. La gestion des amendements constitue une contrainte spécifique supplémentaire : les opérations peuvent être **additives** (insertion d'un article), **substitutives** (remplacement d'un alinéa), **modificatives** (retouche d'une formulation) ou **abrogatives** (suppression d'une disposition). 
Chacune doit être identifiée extraite et appliquée de façon traçable, tout en conservant l'historique des versions antérieures pour des besoins d'audit.

### 1.4.3 Incohérences de terminologie et de classification

Le corpus juridique tunisien est rédigé en deux langues officielles, le français et l’arabe, qui ne constituent pas toujours de simples traductions l’une de l’autre. Certains textes sont disponibles uniquement en arabe, d’autres uniquement en français, et d’autres dans les deux langues avec des formulations parfois divergentes. Cette situation crée des différences de vocabulaire qui compliquent la recherche sémantique translingue : un terme juridique en français (« licenciement pour motif économique ») n’a pas nécessairement d’équivalent direct dans la version arabe du même code.
De plus, l’arabe juridique tunisien présente des particularités d’écriture que les systèmes généraux ne gèrent pas correctement : combinaison des caractères, écriture de droite à gauche dans des environnements mixtes, et variations de normalisation Unicode entre différentes sources. Ces incohérences impactent négativement la qualité des embeddings vectoriels et la pertinence des résultats de recherche.

### 1.4.4 Qualité et hétérogénéité des données sources officielles

Le quatrième blocage technique est lié à la qualité propre des données collectées. Lestextes juridiques tunisiens ont été obtenus depuis les sources officielles de l'**Imprimerie Officielle de la République Tunisienne** et du **Journal Officiel de la République Tunisienne (JORT)**. Si ces sources font autorité sur le plan juridique, elles présentent des défis significatifs sur le plan du traitement automatique.

**Problèmes d'encodage des versions arabes.**  Les documents arabes téléchargés depuis les portails officiels utilisent des encodages hétérogènes : UTF-8, Windows-1256, CP1256, ISO-8859-6 ou Latin-1. En l’absence d’une déclaration d’encodage explicite dans les métadonnées du fichier, les systèmes de lecture standard échouent à interpréter correctement les caractères arabes, produisant des séquences illisibles. Le système doit tenter successivement plusieurs encodages avant d’obtenir un texte exploitable.

**Documents numérisés et artefacts OCR.** Une fraction significative des textes arabes n'est disponible qu'en version numérisée (images scannées sans couche textuelle). L'OCR produit un texte bruité : caractères parasites (lettres latines insérées par confusion visuelle), mots arabes éclatés (liaisons brisées), marques de direction Unicode invisibles qui perturbent le traitement, et bruit éditorial du JORT (références de publication, colophons) à supprimer sans affecter le contenu juridique.

**Hétérogénéité des structures de mise en forme.** La mise en forme varie selon les codes et les époques de publication (numérotation en chiffres arabes ou arabes-indiques, présence variable des titres de chapitres), rendent l'extraction automatique de la structure hiérarchique difficile et nécessitent des expressions régulières multilingues spécifiques.

Ces problèmes de qualité des données justifient la conception d'un pipeline de traitement documentaire à plusieurs niveaux, décrit en section 3.2, combinant extraction multi-moteurs, normalisation Unicode spécialisée pour l'arabe, détection automatique de texte dégradé et nettoyage juridique structuré.

### 1.4.5 Absence d'un cadre intégré de pilotage de la conformité

Au-delà de la recherche juridique, les organisations tunisiennes font face à un cinquième défi : l’absence d’un outil couvrant l’intégralité du cycle opérationnel de la conformité réglementaire. Il n’existe pas,jusqu’à présent, de solution accessible qui connecte directement les textes juridiques applicables à un profil d’entreprise donné à la gestion opérationnelle des dossiers de non-conformité, des actions correctives et des contrôles internes. Les équipes de conformité recourent généralement à des feuilles de calcul manuelles ou à des outils génériques de gestion de projet, qui ne sont ni capables d’évaluer automatiquement l’applicabilité d’une exigence réglementaire, ni d’orchestrer une analyse de conformité fondée sur les textes de référence, ni de maintenir un registre d’exceptions et un tableau de bord de la posture de conformité en temps réel. Cette absence d’intégration entre la veille juridique et le pilotage opérationnel de la conformité représente un manque fonctionnel majeur pour les entreprises soumises à des obligations réglementaires complexes.

## 1.5 Objectifs du projet

### 1.5.1 Prise en compte de la complexité structurelle et juridique

Le premier objectif est de concevoir un système capable de traiter la complexité structurelle et linguistique propre aux textes juridiques tunisiens. Cela implique un pipeline d'extraction documentaire robuste traitant indifféremment les PDF natifs, les fichiers DOCX et les documents numérisés en arabe ou en français, via une chaîne à plusieurs niveaux intégrant l'OCR. Il s'agit ensuite de segmenter automatiquement les textes en unités juridiques cohérentes (articles, alinéas), indépendamment des variations de mise en forme entre les codes. Enfin, le système doit comprendre le vocabulaire juridique tunisien en profondeur, ce qui nécessite le *fine-tuning* d'un modèle d'embeddings multilingue spécialisé sur ce corpus pour améliorer significativement la pertinence de la recherche sémantique.

### 1.5.2 Analyse temporelle et comparative

Le second objectif porte sur la dimension temporelle liée au droit : les textes évoluent, les articles sont amendés, des dispositions ne sont plus applicables et sont remplacées. Le système doit distinguer la version en vigueur d'un article de ses versions antérieures, identifier automatiquement la nature des opérations d'amendement (ajout, remplacement, modification, abrogation) et les appliquer de façon traçable avec un historique complet. Cette traçabilité est essentielle pour répondre à des questions portant sur l'état du droit à une date donnée ou pour comparer des versions successives d'un même article. Le système doit également permettre l'analyse comparative de l'applicabilité d'une exigence réglementaire à différents profils d'entreprises, selon leur secteur d'activité, leur taille et leur juridiction.

### 1.5.3 Scalabilité et intégration dans l'écosystème existant

Le troisième objectif est d'ordre architectural : la plateforme doit être conçue pour évoluer et s'intégrer dans des environnements de production réels. Cela nécessite une architecture modulaire permettant l'ajout de nouveaux corpus juridiques sans refonte du système, une API REST standardisée facilitant l'intégration avec des outils tiers (ERP, systèmes de gestion documentaire, portails RH), et un déploiement encapsulé sous Docker permettant une mise en production reproductible dans différents environnements. La plateforme doit également supporter le multi-tenant, l'isolement des données entre plusieurs organisations clientes, et être couverte par une suite de tests automatisés avec intégration continue garantissant la stabilité lors des évolutions du code.

### 1.5.4 Pilotage intégré du cycle de conformité

Le quatrième objectif est de répondre au verrou identifié en section 1.4.5 en offrant un système complet de gestion opérationnelle de la conformité, directement connecté aux textes juridiques indexés. Cela inclut la création et le suivi de dossiers de non-conformité avec analyse automatique des documents attachés, l'identification et le *scoring* des constats (*findings*) par sévérité et niveau de confiance, la planification des actions correctives avec gestion des dépendances, le suivi des preuves de mise en conformité, la gestion des contrôles internes (préventifs, détectifs, correctifs) et d'un registre d'exceptions (acceptations de risques, dérogations, *compensating controls*), ainsi que la production d'un tableau de bord de la posture de conformité par évaluation et par organisation. L'ensemble de ces flux est orchestré par le modèle de langage selon un arbre de décision structuré, garantissant une assistance à la fois analytique et opérationnellement exploitable.

## 1.6 Méthodologie de projet

### 1.6.1 Méthodologie CRISP-DM

#### 1.6.1.1 Vue d'ensemble de CRISP-DM

La méthodologie retenue pour conduire ce projet est **CRISP-DM** (*Cross-Industry Standard Process for Data Mining*) [29], un cadre de référence itératif largement adopté pour les projets d'intelligence artificielle et de science des données. Il décompose le cycle de vie d'un projet IA en six phases séquentielles mais réversibles : compréhension du problème métier, compréhension des données, préparation des données, modélisation, évaluation et déploiement.

La nature cyclique de CRISP-DM est particulièrement adaptée au projet Daleel, dont les exigences ont été précisées progressivement au fil des itérations, et dont les modules IA ont nécessité plusieurs cycles d'ajustement avant d'atteindre les niveaux de performance visés. L'implémentation concrète a suivi un découpage en **dix sprints fonctionnels**, chacun correspondant à une extension cohérente et testée de la plateforme, s'inscrivant dans les phases CRISP-DM détaillées ci-dessous.

![Cycle CRISP-DM appliqué au projet Daleel](captures/fig_1_1_crisp_dm.png)

**Figure 1.1 — Cycle CRISP-DM appliqué au projet Daleel.**

```
            ┌─────────────────────────────┐
            │ 1. Compréhension du métier  │
            │    (besoins juristes / DSI) │
            └──────────────┬──────────────┘
                           │
                           ▼
            ┌─────────────────────────────┐◄────────────┐
            │ 2. Compréhension des données│             │
            │    (corpus JORT, langues,   │             │
            │     OCR, structures)        │             │
            └──────────────┬──────────────┘             │
                           │                            │
                           ▼                            │
            ┌─────────────────────────────┐             │
            │ 3. Préparation des données  │◄────┐       │
            │   (extraction, nettoyage,   │     │       │
            │    segmentation, chunks)    │     │       │
            └──────────────┬──────────────┘     │       │
                           │                    │       │
                           ▼                    │       │
            ┌─────────────────────────────┐     │       │
            │ 4. Modélisation             │─────┘       │
            │  (fine-tuning, RAG, agent,  │             │
            │   garde-qualité, compliance)│             │
            └──────────────┬──────────────┘             │
                           │                            │
                           ▼                            │
            ┌─────────────────────────────┐             │
            │ 5. Évaluation               │─────────────┘
            │   (Recall@k, MRR, nDCG,     │
            │    ablation, garde-qualité) │
            └──────────────┬──────────────┘
                           │
                           ▼
            ┌─────────────────────────────┐
            │ 6. Déploiement              │
            │    (Docker, CI/CD, UI)      │
            └─────────────────────────────┘
```

Les flèches de retour illustrent les itérations effectives du projet : la phase d'évaluation a révélé un déficit de pertinence de la recherche vectorielle (Recall@1 = 0,20 sur le modèle de base), ce qui a déclenché un retour à la **phase 4** (fine-tuning du modèle d'embeddings) ; la modélisation de la garde-qualité, à son tour, a exposé des problèmes de bruit OCR dans certaines références citées, déclenchant un retour à la **phase 3** (renforcement du pipeline de nettoyage arabe).

**Tableau 1.1 — Correspondance phases CRISP-DM ↔ chapitres du mémoire.**

| Phase CRISP-DM | Chapitre principal | Sections concernées |
|---|---|---|
| 1. Compréhension du problème métier | Chapitre 1 | 1.2, 1.4, 1.5, 1.7 |
| 2. Compréhension des données | Chapitre 1 + Chapitre 2 | 1.6.1.3 (statistiques corpus), chap. 2 (état de l'art) |
| 3. Préparation des données | Chapitre 3 + Chapitre 4 | 3.2 (conception), 4.2 (réalisation) |
| 4. Modélisation | Chapitre 3 + Chapitres 4-5 | 3.3 à 3.7 (conception), 4.3 à 4.5 (réalisation), 5.1 à 5.2 (Compliance) |
| 5. Évaluation | Chapitre 5 | 5.4 (quantitative), démos qualitatives 4.6 |
| 6. Déploiement | Chapitre 5 | 5.5 (Docker + CI/CD), 5.3 (interfaces livrées) |

#### 1.6.1.2 Compréhension du problème métier

Cette phase initiale a consisté à analyser les besoins concrets des professionnels du droit et de la conformité en Tunisie. L'objectif était de comprendre les flux de travail existants, d'identifier les tâches à forte valeur ajoutée susceptibles d'être assistées par l'IA, et de délimiter le périmètre fonctionnel de la plateforme selon ses deux volets. Cette analyse a abouti à la définition de cinq domaines juridiques prioritaires (droit du travail, droit des sociétés, protection des données, fiscalité, sécurité au travail), à la modélisation du cycle complet de conformité, et à la formulation des indicateurs de succès : métriques de pertinence de la recherche (Recall@k, MRR@k, nDCG@k), qualité des réponses générées et couverture fonctionnelle du cycle de conformité.

#### 1.6.1.3 Compréhension des données

Cette phase a porté sur l'exploration et la caractérisation du corpus juridique tunisien collecté depuis l'IORT et le JORT. Le corpus initial représente environ **5,7 Mo de documents PDF** répartis entre français et arabe, totalisant après segmentation **2 344 articles** rattachés à cinq codes principaux (Code du Travail, Code des Sociétés Commerciales, Code de l'Investissement, loi 2004-63 sur la protection des données, et un sous-corpus fiscal). L'exploration statistique du corpus a fait ressortir les constats suivants :

- **Distribution linguistique asymétrique** : 58 % des articles en français, 71 % en arabe, seulement 29 % bilingues — motivant le choix d'un modèle d'embeddings multilingue translingue.
- **Qualité OCR hétérogène** : 23 % des PDF arabes sans couche textuelle exploitable, nécessitant un passage OCR ; parmi ceux-ci, 35 % présentent des artefacts critiques. Ce diagnostic a justifié le pipeline de nettoyage arabe en onze étapes.
- **Diversité d'encodages** : UTF-8, Windows-1256, CP1256, ISO-8859-6 et Latin-1 coexistent dans les PDF arabes, imposant une chaîne de décodage en cascade (section 3.2.1).
- **Amendements** : 14 % des articles amendés au moins une fois, justifiant le retrieval partitionné (section 3.3.4).
- **Densité d'exigences** : environ 1,8 exigence par article en moyenne, avec un maximum de 12 sur les articles à forte densité normative.

Ces statistiques ont également permis de calibrer le jeu d'évaluation de 30 requêtes gold (20 en français et 10 en arabe) en garantissant une couverture proportionnelle aux poids de chaque code et de chaque langue dans le corpus.

#### 1.6.1.4 Préparation des données

La préparation des données a constitué la phase la plus conséquente du projet. Elle comprend :

- la mise en place de la chaîne d'extraction documentaire à trois niveaux (PyMuPDF, pdfminer.six, OCR Tesseract + EasyOCR) ;
- le nettoyage et la normalisation des textes arabes en onze étapes spécialisées, complétés par une phase de lecture et de correction manuelle ;
- le découpage en *chunks* de taille maîtrisée (1 500 caractères) avec chevauchement (200 caractères) respectant les frontières d'articles ;
- la modélisation de la gestion des amendements avec extraction automatique des opérations (ajout, substitution, modification, abrogation) ;
- la constitution du jeu d'entraînement pour le *fine-tuning* du modèle d'embeddings.

#### 1.6.1.5 Modélisation

La phase de modélisation couvre quatre volets distincts : le *fine-tuning* du modèle `paraphrase-multilingual-mpnet-base-v2`, la conception du pipeline RAG avancé à six modules, la mise en place de l'agent autonome ReAct et les modules *Compliance Operations*. L'ensemble de la modélisation détaillée fait l'objet du chapitre 3.

#### 1.6.1.6 Évaluation

L'évaluation a été conduite sur deux dimensions complémentaires :

- **Performance de *retrieval*** : benchmark sur 30 requêtes gold mesurant Recall@k, MRR@k et nDCG@k, avant et après *fine-tuning*. Les résultats détaillés sont présentés au chapitre 5.
- **Couverture de tests** : 55 fichiers de tests couvrant les modules unitaires et les tests d'intégration de bout en bout, exécutés par la chaîne CI GitHub Actions sur trois versions de Python.

#### 1.6.1.7 Déploiement

La phase de déploiement a abouti à une infrastructure conteneurisée complète et reproductible :

- **Dockerfile multi-stage** : image *builder* Python 3.12 pour l'installation des dépendances, image *runtime* `python:3.12-slim` avec Tesseract OCR et `poppler-utils` préinstallés, minimisant la taille de l'image finale.
- **Docker Compose** : orchestration de trois services (MongoDB 7.0, Ollama servant `qwen2.5:7b`, FastAPI/Uvicorn) avec vérification de santé (*health check* HTTP toutes les 30 secondes) et persistance des volumes de données.
- **CI/CD GitHub Actions** : pipeline automatique de *lint* (Ruff) et de tests (pytest) déclenché à chaque *push*, sur une matrice Python 3.11/3.12/3.13, avec un service MongoDB 7 en conteneur.
- **Interfaces utilisateur** : chatbot conversationnel et panneau d'administration en React/Vite, accessibles directement via l'API FastAPI, intégrant un tableau de bord BI.

## 1.7 Spécification des besoins

Cette section consolide l'analyse fonctionnelle de la plateforme Daleel avant d'aborder, au chapitre suivant, sa conception détaillée. Elle identifie les acteurs, formalise leurs besoins fonctionnels par volet, énonce les contraintes non fonctionnelles, et synthétise l'ensemble dans un diagramme de cas d'utilisation général.

### 1.7.1 Identification des acteurs

La plateforme s'adresse à quatre catégories d'acteurs aux périmètres d'action distincts :

- **Visiteur** : utilisateur non authentifié qui découvre la plateforme. Il peut consulter la page d'accueil, s'inscrire en créant simultanément un compte personnel et une organisation, ou se connecter à un compte existant.
- **Membre** *(role : `member`)* : utilisateur authentifié appartenant à une organisation. Il interagit avec la plateforme dans un contexte de consultation : interrogation juridique, recherche dans le corpus, consultation des dossiers de conformité de son organisation et de son tableau de bord. Il ne peut pas modifier la configuration de l'organisation.
- **Owner** *(role : `owner`)* : propriétaire de l'organisation, également désigné « admin entreprise ». Il dispose des droits du membre, étendus à la gestion du compte organisationnel : invitation et révocation de membres, gestion du profil entreprise, téléversement de documents au corpus organisationnel, création et pilotage des dossiers de non-conformité, gestion des exceptions et des contrôles internes.
- **Super admin** *(plateforme)* : administrateur du service Daleel pour l'ensemble des organisations clientes. Son périmètre est restreint à la gouvernance de la plateforme : approbation des nouvelles inscriptions, suspension ou suppression d'organisations, gestion du corpus juridique global (lois, articles, amendements), configuration des paramètres système et accès aux statistiques agrégées. **Le super admin n'accède pas aux données métier des organisations** — historiques de conversation, dossiers de conformité, documents organisationnels — conformément au principe d'isolation des données documenté en section 3.1.

La hiérarchie des permissions est cumulative : un *owner* hérite des droits d'un *membre*, qui hérite des droits d'un *visiteur*. Le *super admin* opère sur un périmètre disjoint : il pilote le service mais ne consulte pas les données métier.

### 1.7.2 Besoins fonctionnels

Les besoins fonctionnels sont structurés par volet métier. Chaque besoin précise l'acteur principal et le résultat attendu côté utilisateur, sans préjuger des modules techniques sous-jacents (détaillés au chapitre 3).

**BF — Volet 1 : Legal RAG (assistance juridique)**

| Réf. | Besoin | Acteur |
|---|---|---|
| BF-1.1 | Poser une question juridique en langage naturel (arabe, français, anglais ou derja tunisien) et recevoir une réponse fondée sur les textes de loi indexés, accompagnée de la liste des sources citées | Membre |
| BF-1.2 | Activer un mode d'agent autonome capable de raisonner de façon itérative sur des requêtes complexes en exploitant plusieurs outils spécialisés (recherche, graphe d'articles, calcul de conformité) | Membre |
| BF-1.3 | Téléverser un document ponctuel (PDF, image scannée, DOCX) pour poser une question contextualisée sur son contenu, sans persistance dans le corpus organisationnel | Membre |
| BF-1.4 | Dicter une question vocalement, obtenir sa transcription, et recevoir la réponse synthétisée en parole | Membre |
| BF-1.5 | Consulter, renommer, archiver et supprimer ses propres conversations passées | Membre |

**BF — Volet 2 : Compliance Operations**

| Réf. | Besoin | Acteur |
|---|---|---|
| BF-2.1 | Téléverser et organiser les documents internes de l'organisation (politiques, procédures, contrats), avec déclenchement automatique du traitement (extraction, segmentation, indexation) | Owner |
| BF-2.2 | Créer un dossier de non-conformité, y rattacher des documents probants, et suivre son état d'avancement | Owner |
| BF-2.3 | Consulter les constats (*findings*) extraits automatiquement, leur sévérité, leur score de criticité et les actions correctives associées | Membre |
| BF-2.4 | Lancer une analyse d'applicabilité réglementaire en fonction du profil de l'organisation (secteur, taille, juridiction) et visualiser la posture de conformité résultante | Owner |
| BF-2.5 | Gérer un registre d'exceptions (acceptations de risques, dérogations) et un catalogue de contrôles internes (préventifs, détectifs, correctifs) | Owner |
| BF-2.6 | Consulter un tableau de bord BI temps réel agrégeant la posture de conformité, l'avancement des actions et les indicateurs clés | Membre, Owner |

**BF — Volet 3 : Administration**

| Réf. | Besoin | Acteur |
|---|---|---|
| BF-3.1 | Gérer le profil de l'organisation (nom, secteur, taille, juridiction) qui pilote le moteur d'applicabilité | Owner |
| BF-3.2 | Inviter de nouveaux membres par email et attribuer leur rôle | Owner |
| BF-3.3 | Consulter le journal d'audit des actions effectuées au sein de l'organisation | Owner |
| BF-3.4 | Approuver, suspendre ou supprimer une organisation cliente | Super admin |
| BF-3.5 | Gérer le corpus juridique global : lois, articles, amendements, opérations de versionnement | Super admin |
| BF-3.6 | Consulter les statistiques d'usage agrégées (nombre d'organisations, volume de requêtes, latence moyenne) sans accès aux données métier | Super admin |

### 1.7.3 Besoins non fonctionnels

Les exigences transverses qui contraignent la conception sont les suivantes :

| Catégorie | Exigence |
|---|---|
| **Multilinguisme** | Toutes les fonctions de questionnement, de recherche et de réponse doivent fonctionner en arabe littéraire, en français, en anglais, et accepter en entrée le dialecte tunisien (*derja*). |
| **Précision et traçabilité** | Toute réponse générée doit s'appuyer exclusivement sur les sources récupérées et citer explicitement les articles utilisés. Les hallucinations doivent être détectées et neutralisées avant restitution à l'utilisateur. |
| **Performance** | Latence de réponse cible inférieure à 10 secondes pour une requête RAG classique, inférieure à 25 secondes pour une requête traitée par l'agent autonome (95ᵉ percentile). |
| **Sécurité** | Authentification par JWT (access 30 min, refresh 7 jours), liste de révocation des jetons, MFA optionnel par TOTP, *rate limiting*, validation stricte des entrées, conformité aux principes OWASP. |
| **Isolation multi-tenant** | Cloisonnement strict des données métier entre organisations clientes. Aucun acteur, super admin inclus, ne peut accéder aux données métier d'une organisation tierce. |
| **Confidentialité** | Déploiement entièrement *on-premise* possible : aucun appel à une API LLM externe, aucune fuite des documents organisationnels vers un service tiers. |
| **Scalabilité** | Architecture modulaire permettant l'ajout de nouveaux corpus juridiques sans refonte, et le passage à l'échelle horizontal (montée en charge par augmentation du nombre de workers). |
| **Disponibilité** | Démarrage reproductible par Docker Compose avec vérifications de santé (*health checks*) sur chaque service avant exposition au public. |
| **Maintenabilité** | Code couvert par une suite de tests automatisés exécutés en intégration continue, journalisation structurée, configuration par variables d'environnement. |

### 1.7.4 Diagrammes de cas d'utilisation

#### Vue synthétique

La figure 1.2 synthétise les besoins fonctionnels ci-dessus en associant chaque acteur aux fonctionnalités qu'il peut déclencher. Les fonctionnalités sont regroupées en sept paquets — authentification et gestion des comptes, assistant juridique IA (Legal RAG), gestion documentaire, gestion législative et amendements, conformité et feuille de route, gestion des dossiers de non-conformité, notifications et emails transactionnels — qui correspondent aux périmètres d'autorisation. La hiérarchie d'héritage `visiteur ← membre ← admin/owner ← super admin` matérialise le cumul des permissions. Deux acteurs système complètent le diagramme : le *serveur SMTP* pour les emails transactionnels et le *moteur LLM* pour les traitements d'intelligence artificielle.

![Diagramme de cas d'utilisation général de la plateforme Daleel](captures/fig_1_2_use_case.png)

**Figure 1.2 — Diagramme de cas d'utilisation général de la plateforme Daleel (vue synthétique).** *18 cas d'utilisation répartis en 7 modules fonctionnels, 4 acteurs humains et 2 acteurs système.*

Les sous-sections suivantes détaillent les trois modules les plus structurants du projet. Pour chacun, un diagramme de cas d'utilisation détaillé précise les relations `<<include>>` et `<<extend>>` entre cas, ainsi que les notes explicatives sur les mécanismes techniques sous-jacents.

#### Module Authentification, gestion des comptes et emails transactionnels

La figure 1.3 décompose le paquetage *Authentification et gestion des comptes*. Ce module couvre l'intégralité du cycle de vie utilisateur — inscription, confirmation d'email, connexion, réinitialisation de mot de passe, vérification de téléphone par OTP — ainsi que la gestion des invitations par email et l'administration des organisations.

Un point notable est l'intégration d'un **service d'emails transactionnels complet** fondé sur SMTP. Cinq types d'emails sont générés automatiquement par la plateforme :

- **Email de confirmation** : envoyé à l'inscription, lien tokenisé avec expiration à 24 heures. Après confirmation, le compte attend l'approbation du super admin.
- **Email d'invitation** : envoyé par un admin/owner pour inviter un nouveau membre. Lien tokenisé avec expiration à 72 heures, template HTML responsive avec fallback texte brut.
- **Email de réinitialisation** : lien sécurisé pour réinitialiser le mot de passe, expiration à 1 heure.
- **Code OTP par email** : code de vérification du numéro de téléphone envoyé par email, expiration à 10 minutes.
- **Alerte de sécurité à la connexion** : notification automatique à chaque nouvelle connexion, détaillant l'adresse IP, la date/heure et le navigateur utilisé.

Tous les emails sont envoyés en **dual format** (HTML responsive + texte brut) via une exécution asynchrone pour ne pas bloquer le serveur.

![Diagramme de cas d'utilisation détaillé — Authentification et emails transactionnels](captures/fig_1_3_uc_auth.png)

**Figure 1.3 — Diagramme de cas d'utilisation détaillé : Authentification, gestion des comptes et emails transactionnels.** *18 cas d'utilisation, 5 types d'emails SMTP, relations include/extend avec notes explicatives.*

#### Module Assistant juridique IA (Legal RAG)

La figure 1.4 détaille le module *Legal RAG*, cœur fonctionnel de la plateforme. Le cas d'utilisation principal — *Poser une question juridique* — déclenche systématiquement trois sous-cas (`<<include>>`) : la détection de la langue et de l'intention, la récupération des sources pertinentes via le pipeline RAG à six modules, et l'application de la garde anti-hallucination. Le routage par domaine juridique et l'activation de l'agent autonome ReAct sont des extensions conditionnelles (`<<extend>>`).

Le diagramme distingue les différents modes d'interaction offerts à l'utilisateur : question classique, mode agentique, sélection automatique (le backend choisit le mode optimal), streaming SSE, question sur un document uploadé, et interaction vocale (STT/TTS). Chaque mode réutilise le pipeline RAG central via des relations `<<include>>`, ce qui garantit la cohérence du traitement quelle que soit la modalité d'entrée.

![Diagramme de cas d'utilisation détaillé — Legal RAG](captures/fig_1_4_uc_rag.png)

**Figure 1.4 — Diagramme de cas d'utilisation détaillé : Assistant juridique IA (Legal RAG).** *15 cas d'utilisation, pipeline RAG à 6 modules, agent ReAct à 12 outils, garde anti-hallucination à 3 couches.*

#### Module Conformité, dossiers de non-conformité et feuille de route

La figure 1.5 regroupe les deux volets opérationnels de la conformité : le *pilotage stratégique* (profil entreprise, applicabilité, feuille de route, contrôles, assessments, preuves, exceptions) et la *gestion tactique* des dossiers de non-conformité (création, constats, actions correctives, conversation guidée, orchestration LLM).

Le lien central entre ces deux volets est la **feuille de route de conformité**, qui inclut obligatoirement l'évaluation d'applicabilité et le calcul de criticité. L'orchestrateur de dossiers applique un arbre de décision à quatre phases — ASK (collecter les faits), CLARIFY (lever les ambiguïtés), ACT (proposer des actions), REVIEW (valider et conclure) — piloté par le moteur LLM.

![Diagramme de cas d'utilisation détaillé — Conformité et dossiers](captures/fig_1_5_uc_compliance.png)

**Figure 1.5 — Diagramme de cas d'utilisation détaillé : Conformité, dossiers de non-conformité et feuille de route.** *21 cas d'utilisation, orchestrateur ASK/CLARIFY/ACT/REVIEW, feuille de route dynamique.*

---

Cette spécification fixe le périmètre fonctionnel à concevoir et à réaliser. Le chapitre suivant présente, après un état de l'art, l'architecture qui répond conjointement à ces besoins fonctionnels et aux contraintes non fonctionnelles énoncées ci-dessus.

## Conclusion

Ce premier chapitre a établi le cadre complet du projet Daleel. L'entreprise d'accueil Didax IT, par son positionnement à l'intersection du développement logiciel sur mesure et de l'intelligence artificielle, offre un contexte favorable à la réalisation d'un projet ambitieux. Le contexte métier a mis en évidence le manque d'outils d'assistance juridique adaptés au droit tunisien, tandis que le contexte scientifique a positionné le projet dans le champ émergent de la *LegalTech* fondée sur les architectures RAG, les agents autonomes et les techniques d'ingénierie de prompts. L'analyse de la problématique a mis en évidence cinq volets principaux : le volume et la fragmentation du corpus juridique tunisien, la complexité structurelle et multilingue des textes, les incohérences terminologiques entre les versions arabes et françaises, la qualité hétérogène des données issues des sources officielles, et l'absence d'un cadre intégré de pilotage opérationnel de la conformité. Face à ces défis, la plateforme Daleel propose deux volets complémentaires — un moteur de *Legal RAG* avancé avec recherche hybride, agent autonome et comportement interactif, et un système de *Compliance Operations* — soutenus par un pipeline d'ingestion documentaire robuste, un agent IA à architecture multi-couches, et une infrastructure déployable sous Docker. La spécification fonctionnelle a formalisé quatre acteurs (visiteur, membre, owner, super admin), regroupé les besoins en trois domaines (Legal RAG, Compliance Operations, administration), et énoncé les contraintes non fonctionnelles structurantes (multilinguisme, traçabilité, sécurité, isolation multi-tenant, confidentialité *on-premise*). Le chapitre suivant est consacré à l'état de l'art en intelligence artificielle juridique et à la conception détaillée de l'architecture qui satisfait conjointement ces besoins et contraintes.

---

# Chapitre 2 — État de l'art

## Introduction

Ce chapitre positionne la plateforme Daleel dans son contexte technique et scientifique actuel. **Dans le cycle CRISP-DM présenté en section 1.6, il matérialise la phase de *compréhension du problème métier et des données* en consolidant les fondations théoriques de chacune des briques techniques mobilisées dans la suite du mémoire.**

Les huit sections qui suivent passent en revue : les **modèles de langage de grande taille** qui constituent le cœur génératif du système ; les **architectures de génération augmentée par récupération** (RAG) et leurs niveaux de sophistication ; les techniques de **recherche hybride et de reranking** ; le paradigme des **agents IA** et de l'appel d'outils natif ; les méthodes d'**ingénierie de prompts** et de prévention des hallucinations ; les **modèles d'embeddings multilingues** et le *fine-tuning* domaine-spécifique ; le champ de la **LegalTech** fondée sur l'IA ; et les **systèmes de gestion de la conformité réglementaire**. La conception détaillée de la plateforme, qui s'appuie sur cet état de l'art, fait l'objet du chapitre 3.

## 2.1 Modèles de langage de grande taille

Les **modèles de langage de grande taille** (*Large Language Models*, LLMs) représentent le socle de la génération de réponses en langage naturel. Apparus avec l'architecture Transformer de [1], ils ont connu une progression exponentielle en termes de capacités depuis BERT [2], passant par les modèles génératifs GPT [3] et s'étendant à une large famille de modèles ouverts et fermés : Llama, Mistral, Qwen, Phi, Gemma.

Pour des usages exécutés en local, sans recours à une API externe, les modèles de la famille **Qwen2.5**, développés par l'équipe Alibaba Cloud, constituent un choix particulièrement adapté au contexte du projet [4]. Le variant retenu, `qwen2.5:7b-instruct`, est un modèle décodeur Transformer de **7,6 milliards de paramètres** organisés en 28 couches d'attention de type *Grouped Query Attention* (GQA) avec 28 têtes de requête pour 4 têtes de clé/valeur, configuration qui réduit fortement l'empreinte mémoire de l'inférence sans dégrader la qualité du raisonnement. Sa fenêtre de contexte atteint **32 768 tokens** (extensible à 128 K via interpolation de position), permettant d'injecter dans un seul prompt l'historique de conversation, plusieurs *chunks* juridiques volumineux et le sous-graphe de connaissances.

Le pré-entraînement de Qwen2.5 repose sur un corpus de **18 trillions de tokens** couvrant 29 langues, dont une fraction significative de textes arabes et français, ce qui lui confère des compétences multilingues natives — un facteur déterminant pour un assistant juridique tunisien manipulant simultanément l'arabe littéraire, le français et l'anglais. La phase d'*instruction tuning* a en outre exposé le modèle à des séquences d'appels de fonctions structurées, donnant lieu à un support nativement intégré du ***function calling*** : exposé via l'endpoint `/api/chat` d'Ollama et le paramètre `tools`, ce mécanisme permet au modèle de produire directement des appels typés `{name, arguments}` au lieu de texte libre à parser, éliminant la fragilité des analyseurs syntaxiques sur les sorties LLM. Cette capacité est exploitée dans l'agent autonome ReAct de Daleel (section 3.4).

La diffusion sous **licence Apache 2.0** autorise un déploiement commercial sans contrainte de redevance, un usage *on-premise* total — garant de la confidentialité des données juridiques traitées — et une éventuelle modification du modèle par fine-tuning. Cette combinaison d'arguments — compétence multilingue arabe documentée, tool calling natif, fenêtre de contexte étendue, déploiement local et licence permissive — distingue Qwen2.5 des principales familles concurrentes (Mistral [30], Llama [31, 32], Gemma, Phi), comme détaillé dans la justification comparative en section 3.9.

Au-delà du pré-entraînement, deux étapes post-formation conditionnent l'utilisabilité d'un LLM en assistance juridique : l'***instruction tuning***, qui aligne le modèle sur des paires (instruction, réponse) afin qu'il suive des consignes en langage naturel, et l'apprentissage par renforcement à partir de retours humains (*Reinforcement Learning from Human Feedback*, RLHF) qui optimise davantage sa politique de génération selon des préférences humaines. Le variant `qwen2.5:7b-instruct` mobilisé dans Daleel a bénéficié des deux étapes, ce qui se traduit par une obéissance robuste à des consignes structurées (« réponds dans la langue détectée », « cite tes sources entre crochets ») essentielles à la garde-qualité.

Utilisés seuls, les LLMs souffrent toutefois de deux limites majeures : (1) le phénomène d'**hallucination**, qui désigne la tendance à générer des affirmations crédibles bien qu'incorrectes [5], particulièrement problématique en contexte juridique où une référence d'article inventée peut induire un utilisateur en erreur ; (2) l'**absence de connaissance actualisée** des corpus normatifs locaux — un modèle pré-entraîné en 2024 ne « connaît » pas un amendement publié au JORT en 2026, ni les spécificités du Code des Sociétés Commerciales tunisien. Ces deux limites conditionnent l'emploi de l'architecture RAG décrite à la section suivante.

## 2.2 Architectures de génération augmentée par récupération

La **génération augmentée par récupération** (*Retrieval-Augmented Generation*, RAG) a été formalisée par [6]. Au lieu de demander au modèle de générer une réponse à partir de ses seuls paramètres, on récupère dynamiquement les documents pertinents depuis une base de connaissance externe et on les injecte dans le contexte du modèle. Cette approche améliore la factualité et l'ancrage des réponses sur des sources vérifiables.

La littérature distingue plusieurs niveaux de sophistication :

- **RAG naïf** : une seule passe de récupération par similarité cosinus, suivie d'une génération simple [6] ;
- **RAG avancé** : introduction de modules de pré-récupération et de post-récupération [7] ;
- **RAG agentique** : un agent itère sur le cycle requête-récupération-vérification [8] ;
- **RAG modulaire** : architecture à composants interchangeables avec modules de *reranking* croisé [9].

Pour les domaines spécialisés tels que le droit, plusieurs travaux ont montré la supériorité du RAG sur le *fine-tuning* pur [10] : le RAG préserve la possibilité de mettre à jour le corpus sans réentraînement, garantit une traçabilité explicite des sources mobilisées dans chaque réponse, et limite drastiquement les hallucinations en ancrant la génération sur des extraits réels. Le *fine-tuning*, lui, conserve néanmoins un rôle complémentaire : il améliore la qualité de l'encodage sémantique des modèles de récupération (cf. section 2.6) sans remettre en cause le principe d'ancrage documentaire.

La qualité d'une chaîne RAG dépend en pratique de quatre facteurs interdépendants. Le premier est la **stratégie de découpage** (*chunking*) qui décide de la granularité d'indexation — un découpage trop fin disperse l'information juridique entre plusieurs *chunks*, un découpage trop large dilue la pertinence de la recherche vectorielle. Le deuxième facteur est la **qualité des représentations vectorielles** : un modèle d'*embeddings* généraliste peut mal capturer les nuances modales du langage juridique (« doit », « peut », « est tenu de »), motivant le recours au *fine-tuning*. Le troisième facteur est la **qualité de la fusion** entre la recherche vectorielle et la recherche lexicale, traitée dans la section suivante. Le quatrième facteur est l'**ingénierie de prompts** appliquée au moment de la génération, qui détermine la fidélité de la réponse aux *chunks* récupérés.

Le projet Daleel s'inscrit dans la lignée du RAG modulaire avec une architecture à six modules spécialisés intégrant la recherche hybride (signaux vectoriels et lexicaux), un *reranking* par cross-encoder, un routage par domaine juridique, un retrieval partitionné piloté par l'intention de l'utilisateur, un graphe de connaissances léger et une garde-qualité. La dimension dite « agentique » repose sur deux mécanismes complémentaires : une orchestration contrôlée de modules spécialisés et un véritable agent autonome doté de douze outils, capable de raisonner itérativement selon la boucle ReAct pour les requêtes nécessitant une exploration multi-passe du corpus.

## 2.3 Recherche hybride et reranking

La recherche hybride combine deux paradigmes de récupération documentaire : la **recherche dense** (vectorielle), fondée sur la similarité cosinus entre *embeddings*, et la **recherche sparse** (lexicale), typiquement BM25 [11]. La recherche dense excelle pour capturer les relations sémantiques, tandis que la recherche sparse est supérieure pour les correspondances exactes (numéros d'articles, termes techniques, codes de loi).

La fusion de ces deux classements est généralement réalisée par **Reciprocal Rank Fusion** (RRF) [12], une méthode non paramétrique qui combine les rangs issus de plusieurs classements selon la formule :

$$RRF(d) = \sum_{r \in R} \frac{1}{k + \text{rang}_r(d)} \qquad (2.1)$$

où R est l'ensemble des classements, $\text{rang}_r(d)$ le rang du document d dans le classement r, et k une constante (typiquement k = 60). D'autres stratégies de fusion existent, notamment la **combinaison linéaire pondérée** des scores normalisés issus de chaque signal, qui présente l'avantage de ne pas exiger la maintenance d'un second index lexical (BM25) lorsque les signaux lexicaux peuvent être calculés directement sur les *chunks* candidats. C'est cette dernière approche qu'adopte Daleel, comme détaillé en section 3.3.1.

Le **reranking par cross-encoder** [13] constitue une étape de post-traitement complémentaire : un modèle entraîné évalue la pertinence de chaque paire (requête, document) de façon croisée — la requête et le document sont concaténés et passés simultanément au modèle —, au lieu d'une comparaison indépendante de vecteurs. Cette interaction permet au modèle de capter des relations fines entre les tokens de la requête et ceux du document, au prix d'un coût computationnel qui interdit son usage à large échelle : le cross-encoder est donc systématiquement appliqué uniquement sur le top-k issu de la recherche hybride. Le cross-encoder se positionne ainsi comme une **étape d'arbitrage** entre la recherche grossière et la génération finale. Le modèle `cross-encoder/ms-marco-MiniLM-L-6-v2`, utilisé dans Daleel, a été pré-entraîné sur le benchmark MS-MARCO comportant plus d'un million de paires (requête, passage) annotées par des juges humains, ce qui en fait un repère robuste de pertinence générique transférable à des domaines spécialisés par simple inférence, sans *fine-tuning* supplémentaire requis pour démarrer.

## 2.4 Agents IA et paradigme ReAct

Le paradigme **ReAct** (*Reasoning + Acting*) [14] propose un cadre unifié où un LLM alterne entre des étapes de raisonnement et d'action. À chaque itération, l'agent raisonne sur l'état courant en langage naturel (« je dois d'abord chercher l'article 91 du Code des Sociétés »), décide d'appeler un outil ou de produire une réponse finale, observe le résultat de l'outil et recommence cette boucle jusqu'à la production d'une réponse satisfaisante ou l'atteinte d'un budget d'itérations.

Cette logique fondamentalement itérative distingue les agents ReAct des chaînes RAG séquentielles classiques. Dans une chaîne RAG « simple », la séquence est déterministe : *retrieve* → *rerank* → *generate*. Dans une boucle ReAct, le modèle décide dynamiquement de la trajectoire à parcourir en fonction des résultats intermédiaires obtenus : si la première recherche est insuffisante, il peut reformuler sa requête et chercher à nouveau ; s'il a besoin du graphe de connaissances autour d'un article, il l'invoque explicitement ; s'il dispose d'informations contradictoires, il peut chercher à les arbitrer. Cette flexibilité est particulièrement précieuse pour les questions juridiques complexes ou multi-facettes, par exemple lorsque la réponse implique de croiser une obligation du Code du Travail avec une dérogation autorisée par un décret postérieur.

L'**appel d'outils natif** intégré dans les LLMs récents [15] permet au modèle de produire des appels de fonctions structurés au lieu du texte libre, éliminant le besoin de parseurs fragiles. Le modèle reçoit dans son prompt système la spécification JSON Schema des outils disponibles, puis émet une réponse de la forme `{"tool_calls": [{"name": ..., "arguments": {...}}]}` lorsqu'il décide d'invoquer une fonction. L'orchestrateur applicatif exécute alors l'outil et réinjecte le résultat dans le contexte du modèle pour l'itération suivante.

Plusieurs raffinements du paradigme ReAct ont été proposés depuis sa formalisation, parmi lesquels Reflexion [8] (méta-raisonnement et mémoire épisodique), Toolformer [15] (insertion autonome d'appels d'outils par *fine-tuning*) et ReWOO (séparation planification/exécution). Daleel adopte une variante classique de ReAct avec appel d'outils natif d'Ollama (endpoint `/api/chat` avec paramètre `tools`) pour invoquer dynamiquement douze services spécialisés, en privilégiant la simplicité d'implémentation et la traçabilité complète des appels. Trois garde-fous structurent l'agent : un **budget d'itérations** maximal au-delà duquel le modèle est explicitement invité à produire sa meilleure réponse sur la base des informations déjà collectées ; un **timeout global** sur la durée totale de la boucle ; et une **journalisation systématique** de chaque appel d'outil (nom, arguments, résultat tronqué, durée, éventuelle erreur) exposée à l'utilisateur dans la réponse finale sous forme d'un journal de raisonnement transparent. Cette transparence — par contraste avec un « raisonnement en boîte noire » — est indispensable dans un contexte juridique où l'utilisateur doit pouvoir auditer les fondements de la réponse qui lui est servie.

## 2.5 Ingénierie de prompts et anti-hallucination

La qualité des réponses d'un système RAG dépend autant de l'ingénierie de prompts que de la qualité de la récupération. Plusieurs techniques complémentaires ont été documentées pour structurer un prompt et réduire les hallucinations.

Le ***few-shot prompting*** [3], aussi désigné *In-Context Learning*, consiste à fournir au modèle quelques exemples de l'interaction attendue avant de poser la question réelle. Cette technique permet d'orienter le format de la réponse sans entraînement supplémentaire. Le ***Chain-of-Thought prompting*** [37] encourage le modèle à expliciter son raisonnement étape par étape avant la réponse finale, améliorant significativement les performances sur les tâches requérant un raisonnement multi-étapes — ce qui est particulièrement pertinent pour l'analyse d'applicabilité d'une exigence réglementaire. La **persona** assigne au modèle un rôle d'expert (« tu es un conseiller juridique tunisien expérimenté »), tandis que l'**ancrage disciplinaire** insère dans le prompt des contraintes explicites sur ce qui constitue un comportement acceptable ou inacceptable du modèle (par exemple, qualifier l'invention d'un article de « faute professionnelle grave »).

Les paramètres de génération influencent également la fidélité. Une **température basse** (T ≤ 0,2) réduit la créativité du modèle au profit d'une génération plus déterministe ancrée sur les *chunks* récupérés ; un ***top-p*** restreint (typiquement 0,9) limite l'échantillonnage aux tokens les plus probables, réduisant la probabilité de divagations stylistiques. Enfin, la **vérification post-génération** opérée par une garde-qualité (cross-checking des citations contre les *chunks*, détection des références d'articles inventées, contrôle de la cohérence linguistique de la réponse) constitue la dernière ligne de défense contre les hallucinations résiduelles. Dans Daleel, l'ensemble de ces techniques sont combinées en un dispositif multi-couches : persona de conseiller juridique interactif, apprentissage en contexte trilingue, ancrage disciplinaire strict, température T = 0,15 avec *top-p* = 0,9, et garde-qualité multi-couches détaillée en section 3.6.

## 2.6 Modèles d'embeddings multilingues et fine-tuning

La qualité de la récupération vectorielle dépend directement de la qualité des représentations sémantiques (*embeddings*). Les modèles fondés sur Sentence-BERT [16] permettent d'encoder des phrases en vecteurs denses de façon à ce que deux phrases sémantiquement proches soient proches dans l'espace de représentation.

Pour les contextes multilingues, le modèle `paraphrase-multilingual-mpnet-base-v2` (768 dimensions, 50 langues couvertes par distillation interlingue) constitue une référence robuste [17]. Sa construction repose sur le principe de la **distillation interlingue** : un modèle « élève » multilingue est entraîné à reproduire les *embeddings* d'un modèle « enseignant » monolingue anglais sur des paires de phrases traduites, ce qui aligne implicitement les espaces vectoriels des différentes langues sans nécessiter de paires d'entraînement supervisé translingues. Cette propriété est cruciale pour Daleel où une question en français doit pouvoir retrouver un article rédigé en arabe.

Les modèles pré-entraînés généralistes ne capturent cependant pas les spécificités du vocabulaire juridique : les nuances modales (« doit », « peut », « est tenu de »), les références croisées entre articles, ou encore les emprunts arabes spécifiques au droit tunisien (par exemple, *مجلة الشغل* pour Code du Travail) sont mal représentés. Le ***fine-tuning*** sur des données domaine-spécifiques permet d'adapter les représentations par apprentissage contrastif. La fonction de perte ***MultipleNegativesRankingLoss*** (MNR) [18] s'est imposée comme un standard pour ce type d'entraînement : dans un *batch* de B paires positives (ancre, document), elle traite implicitement les B-1 autres documents du *batch* comme des négatifs et calcule une perte d'entropie croisée multi-classes sur la matrice de similarités. Cette stratégie évite le coût d'annotation manuelle des négatifs, mais sa qualité dépend fortement de la sélection initiale des paires positives.

Une technique complémentaire largement adoptée est le **mining de négatifs *hard*** : pour chaque ancre, on récupère les documents les plus proches dans l'espace d'embeddings du modèle de base qui ne sont *pas* la cible attendue, et on les expose explicitement comme négatifs. Cette stratégie force le modèle à apprendre des distinctions sémantiques fines (par exemple, distinguer un article sur le congé annuel d'un article sur le congé maladie). Cette technique est validée dans le contexte juridique par plusieurs travaux [19, 20] qui rapportent des gains de Recall@k de l'ordre de 30 à 100 % par rapport à un modèle généraliste, gains que la présente étude confirme expérimentalement (chap. 5, section 5.4.1).

## 2.7 LegalTech et assistance juridique fondée sur l'IA

Le domaine de la *LegalTech* basée sur l'IA connaît une croissance rapide depuis l'apparition des premiers modèles de langage spécialisés sur le droit. Plusieurs systèmes et ressources spécialisés ont été développés pour différentes juridictions :

- **LEGAL-BERT** [19], modèle BERT pré-entraîné sur 12 Go de corpus juridiques anglais (jurisprudence, contrats, législation), démontrant des gains substantiels sur les tâches de classification juridique par rapport à un BERT généraliste ;
- **LexGLUE** [21], benchmark de référence pour la compréhension du langage juridique anglais regroupant sept tâches (classification d'articles, identification de précédents, prédiction d'issues) ;
- **LegalBench** [22], benchmark collaboratif plus récent comprenant 162 tâches de raisonnement juridique conçues par des praticiens du droit pour mesurer les capacités des LLMs en environnement réel ;
- **AraBERT** [35] et **MARBERT** [23], modèles pré-entraînés sur l'arabe moderne standard, dont les variantes spécialisées ont été appliquées avec succès à la jurisprudence arabe ;
- **Solutions commerciales** comme Harvey AI (États-Unis), Ross Intelligence (Canada) ou Casetext (CoCounsel) qui combinent RAG et fine-tuning pour assister les cabinets d'avocats anglo-saxons sur la recherche jurisprudentielle et la rédaction de mémoires.

Une observation cohérente émerge de ces travaux : la **spécialisation domaine-spécifique** est nécessaire mais non suffisante. Les modèles juridiques anglais ne se transposent pas directement à d'autres systèmes juridiques en raison des différences de tradition (*common law* vs droit continental) et de terminologie. Pour les juridictions du monde arabe, le défi est doublé par la **dualité linguistique** (textes en arabe et en français pour les pays du Maghreb) et par la **rareté des corpus annotés** ouverts qui rend difficile le *fine-tuning* contrôlé. Plusieurs travaux récents documentent les difficultés spécifiques aux assistants juridiques arabophones, liées à la morphologie complexe de l'arabe (système consonantique riche, formes verbales déclinables), à la variabilité dialectale (l'arabe « classique » des textes officiels diffère significativement des dialectes utilisés à l'oral), et à la qualité hétérogène de l'OCR sur les documents arabes anciens [23].

Au-delà de ces travaux académiques, plusieurs **plateformes commerciales** ciblent aujourd'hui l'assistance juridique augmentée par l'IA, à différents niveaux de spécialisation géographique et fonctionnelle. Le tableau 2.1 compare quatre solutions représentatives de l'état du marché avec la plateforme Daleel, au regard des critères fonctionnels identifiés dans la spécification des besoins (section 1.7).

**Tableau 2.1 — Comparaison des solutions d'assistance juridique et de conformité existantes.**

| Critère | **Daleel** *(ce projet)* | **Harvey AI** | **Ketrone** | **realLaw AI** | **Qanoony** |
|---|---|---|---|---|---|
| **Type** | Plateforme RAG + Compliance Ops | Assistant IA juridique | Plateforme IA juridique | Assistant juridique IA | Annuaire juridique |
| **Juridiction cible** | International (premier périmètre : Tunisie) | États-Unis, UK | Multi-juridictions | Émirats arabes unis (UAE) | Monde arabe (annuaire) |
| **Langues** | Arabe, français, anglais, derja | Anglais | 60 langues | Anglais (+ arabe partiel) | Arabe |
| **RAG / ancrage documentaire** | ✅ Hybride (FAISS + lexical pondéré) | ✅ (propriétaire) | ✅ | ✅ (législation UAE) | ❌ |
| **Agent autonome (ReAct / outils)** | ✅ 12 outils, tool calling natif | ⚠️ Partiel | ❌ | ❌ | ❌ |
| **Fine-tuning embeddings domaine** | ✅ MPNet fine-tuné | ✅ (propriétaire) | Non documenté | Non documenté | n/a |
| **Compliance Operations (cycle complet)** | ✅ Dossiers, constats, actions, preuves, contrôles, exceptions | ❌ | ❌ | ❌ | ❌ |
| **Extraction exigences depuis PDF** | ✅ Automatique (OCR + NLP) | Non documenté | ✅ (analyse de documents) | ❌ | ❌ |
| **Scoring de criticité auditable** | ✅ Déterministe, journalisé | ❌ | ❌ | ❌ | ❌ |
| **Garde-qualité anti-hallucination** | ✅ Multi-couches (4 contrôles) | Non documenté | Non documenté | ⚠️ Références d'articles | ❌ |
| **Déploiement** | On-premise (Docker) | Cloud uniquement | Cloud | Cloud | Cloud |
| **Confidentialité des données** | ✅ Aucun appel API externe | ❌ Données envoyées au cloud | ❌ | ❌ | n/a |
| **Licence / coût** | Open source (Apache 2.0) | Propriétaire, coût élevé | Propriétaire | 74 AED/mois (~20 USD) | Gratuit (annuaire) |
| **Corpus droit tunisien** | ✅ 2 565 articles indexés | ❌ | ❌ | ❌ | ❌ |

Plusieurs constats se dégagent de cette comparaison. **Harvey AI** constitue la référence de qualité pour l'assistance juridique IA, mais son modèle cloud propriétaire, son coût et l'absence de couverture du droit tunisien l'excluent du périmètre. **Ketrone**, basé aux Émirats, offre une couverture multilingue impressionnante (60 langues) mais reste focalisée sur l'analyse documentaire sans volet conformité. **realLaw AI**, également émirati, est le concurrent le plus proche fonctionnellement avec son ancrage sur la législation locale et ses citations d'articles, mais il se limite au droit des Émirats et ne propose ni agent autonome, ni cycle de conformité. **Qanoony** est un annuaire de consultation d'avocats, sans composante IA.

**Daleel se positionne à l'intersection de deux espaces** — l'assistance juridique IA et le pilotage de la conformité — que les solutions existantes traitent séparément. Aucune plateforme identifiée ne combine simultanément un RAG juridique multilingue arabe/français/anglais, un agent autonome ReAct avec appel d'outils natif, un cycle complet de conformité orchestré par LLM, et un déploiement *on-premise* garantissant la confidentialité des données. Cette lacune du marché justifie la conception spécifique présentée au chapitre suivant.

## 2.8 Systèmes de gestion de la conformité réglementaire

La gestion de la conformité (*Governance, Risk & Compliance*, GRC) est un domaine traditionnellement outillé par des solutions dédiées telles qu'IBM OpenPages, RSA Archer, MetricStream ou ServiceNow GRC. Ces solutions partagent une logique commune : modéliser un référentiel d'exigences réglementaires, le mettre en correspondance avec des contrôles internes, suivre l'exécution des actions correctives et produire des tableaux de bord pour la direction. Elles présentent toutefois plusieurs limites dans le contexte d'une PME tunisienne : leur **coût de licence très élevé** (typiquement plusieurs dizaines de milliers d'euros par an) les rend inaccessibles aux petites structures ; leur **catalogue de réglementations préchargées** se concentre sur les normes internationales (RGPD, ISO 27001, SOX) et n'inclut pratiquement aucune réglementation tunisienne ; et leur **assistance IA reste limitée** à des fonctions de détection d'anomalies ou de recommandation simple, sans capacité d'analyse sémantique d'un texte de loi ou d'extraction automatique d'exigences à partir d'un PDF officiel.

Plus récemment, le champ émergent des **RegTech** (*Regulatory Technology*) et des **GRC augmentées par IA** [24] s'attache à combler ce manque en mobilisant le traitement automatique du langage naturel pour analyser les textes réglementaires, classifier les obligations qu'ils contiennent et évaluer leur applicabilité à un profil d'entreprise donné. Les travaux dans ce domaine identifient trois capacités-clés qu'une plateforme moderne de conformité doit offrir : (1) l'**extraction automatisée d'exigences** depuis des sources non structurées (PDF, DOCX) ; (2) le **scoring de criticité** déterministe et auditable des constats de non-conformité ; et (3) l'**orchestration d'un cycle complet** allant du dossier de non-conformité à la preuve de mise en conformité. La plateforme Daleel apporte une réponse à ce manque en intégrant nativement le volet *Compliance Operations* avec le moteur de *Legal RAG* — orchestrant l'analyse des textes, l'extraction des exigences, le scoring déterministe et le suivi opérationnel des actions correctives, le tout selon un arbre de décision LLM ASK / CLARIFY / ACT / REVIEW formalisé au chapitre suivant.

## Conclusion

Cet état de l'art a couvert l'ensemble des fondements théoriques mobilisés par la plateforme Daleel : les modèles de langage de grande taille et leur évolution vers Qwen2.5, les architectures de génération augmentée par récupération et leurs raffinements modulaires, les techniques de recherche hybride et de reranking, le paradigme des agents autonomes ReAct, les pratiques d'ingénierie de prompts et de garde-qualité, les modèles d'embeddings multilingues et leur *fine-tuning* domaine-spécifique, le champ émergent de la *LegalTech* fondée sur l'IA et les solutions traditionnelles de pilotage de la conformité. Cette synthèse fait apparaître à la fois la maturité des briques disponibles et l'absence d'une combinaison adaptée au contexte juridique tunisien, justifiant la conception spécifique présentée au chapitre suivant.

---

# Chapitre 3 — Conception de la solution

## Introduction

Ce chapitre présente la conception détaillée de la plateforme Daleel telle que synthétisée par la spécification du chapitre 1 et éclairée par l'état de l'art du chapitre 2. **Dans le cycle CRISP-DM, il matérialise la phase de *modélisation*** : il formalise l'architecture globale, puis spécifie chacun des modules clés — pipeline d'ingestion, pipeline RAG à six modules, agent autonome ReAct, *fine-tuning* du modèle d'embeddings, garde-qualité anti-hallucination, volet *Compliance Operations* — avant de présenter la modélisation conceptuelle des données et les choix technologiques retenus, dont la justification comparative des modèles de langage candidats. La réalisation effective de ces conceptions fait l'objet des chapitres 4 et 5.

## 3.1 Architecture globale de la plateforme Daleel

### 3.1.1 Vue d'ensemble et principes architecturaux

L'architecture de Daleel repose sur six principes directeurs :

1. **Asynchronisme** : toute la couche applicative est construite sur le modèle `async`/`await` de Python, exploitant le pilote MongoDB asynchrone Motor et le serveur ASGI Uvicorn pour absorber des charges concurrentes sans blocage.
2. **Modularité** : les 41 services métier sont indépendants et faiblement couplés, organisés autour d'interfaces stables. Le code source compte 70 modules backend regroupés en couches (`api`, `services`, `processing`).
3. **Traçabilité** : toute opération sur le corpus est consignée dans des journaux auditables (collection `audit_logs`) ; les appels d'outils de l'agent autonome sont journalisés dans le champ `tool_calls_log` de la réponse, incluant les arguments, la durée et l'éventuelle erreur de chaque outil.
4. **Séparation des préoccupations** : la présentation (React + Vite), l'API (FastAPI + Pydantic), la logique métier (services) et la persistance (MongoDB + FAISS) sont strictement distinctes.
5. **Multi-tenant et sécurité** : isolement des données par `organization_id`, authentification JWT (access 30 min + refresh 7 jours), liste de révocation (`token_blacklist`), MFA optionnel, validation stricte des entrées et limitation de débit (*rate limiting*) via SlowAPI.
6. **Conteneurisation** : la plateforme est entièrement déployable via Docker Compose, avec build multi-stage minimisant la taille de l'image et orchestration de trois services (FastAPI, MongoDB 7.0, Ollama).

### 3.1.2 Vue en couches et flux de bout en bout

La plateforme s'organise en cinq couches successives :

| Couche | Composants principaux | Rôle |
|---|---|---|
| Présentation | 34 composants React (18 pages), chatbot conversationnel, panneau admin, dashboard BI, assistant vocal | Interaction utilisateur |
| API REST | 7 routeurs FastAPI, > 170 endpoints, schémas Pydantic, JWT, *rate limiting* | Validation, sécurité, routage |
| Services métier | 41 services (RAG, agent, compliance, criticité, embeddings, LLM, audit, …) | Logique métier |
| Traitement documentaire | 8 modules de *processing* (extracteur multi-niveaux, OCR, nettoyage arabe, segmentation, chunking, normalisateur de derja) | Préparation des données |
| Persistance | MongoDB 7.0 (38 collections), index FAISS HNSW en mémoire, cache LLM, cache embeddings LRU | Stockage et indexation |

**Tableau 3.1 — Couches architecturales de Daleel et composants principaux.**

La figure 3.1 illustre cette architecture en couches ainsi que les deux volets fonctionnels qui la traversent, et la figure 3.2 présente le traitement d'une requête utilisateur sous forme de pipeline fonctionnel.

![Architecture globale de la plateforme Daleel : cinq couches et deux volets](captures/fig_3_1_architecture.png)

**Figure 3.1 — Architecture globale de la plateforme Daleel : cinq couches et deux volets.** *(source Mermaid : `docs/diagrams/architecture_globale.md`)*

![Traitement d'une requête utilisateur dans le pipeline RAG Daleel](captures/fig_3_2_flux_rag.png)

**Figure 3.2 — Traitement d'une requête utilisateur dans le pipeline RAG Daleel : vue fonctionnelle par phases.**

La lecture de la figure suit sept phases principales. La requête est d'abord reçue depuis l'interface utilisateur, puis sécurisée au niveau de l'API par l'authentification JWT, l'isolation par tenant et la validation Pydantic. Elle est ensuite préparée par le routage applicatif : détection de la langue, identification de l'intention, normalisation éventuelle des questions en *derja*. La phase de recherche combine les embeddings fine-tunés, l'index FAISS et des signaux lexicaux afin de constituer un premier ensemble de candidats. Ces candidats sont ensuite sélectionnés par fusion pondérée et reranking cross-encoder, puis enrichis par le KG Light et les références structurées. Enfin, le modèle local génère une réponse, qui est auditée par la garde-qualité avant d'être retournée à l'utilisateur avec les sources et le journal de raisonnement.

## 3.2 Conception du pipeline d'ingestion documentaire

Le pipeline d'ingestion constitue la fondation du système : il transforme des documents bruts (PDF, DOCX, images scannées) en vecteurs indexables. Il est conçu comme une succession de cinq étapes idempotentes, chacune produisant un état persistant en base et déclenchant la suivante. Les principes directeurs présentés dans cette section guident la conception ; les paramètres de mise en œuvre concrets — versions, valeurs précises, modules logiciels — sont détaillés au chapitre 4.

### 3.2.1 Étape 1 — Extraction documentaire en trois niveaux

L'extraction repose sur une **stratégie en cascade** qui adapte la méthode au degré de difficulté du document. Un premier niveau extrait directement le texte des PDF natifs disposant d'une couche textuelle exploitable ; un deuxième niveau, mobilisé en repli, prend en charge les PDF utilisant des polices non standard ou des CMap arabes mal mappées ; un troisième niveau active une chaîne OCR (Tesseract complété par EasyOCR) pour les documents entièrement numérisés sans couche textuelle. Une **détection automatique de texte dégradé** — fondée sur des indicateurs simples comme la proportion de caractères de contrôle ou le ratio de caractères arabes attendus — décide du passage d'un niveau au suivant. Pour les textes arabes, une chaîne de décodage successive teste les encodages les plus fréquemment rencontrés (UTF-8, Windows-1256, CP1256, ISO-8859-6, Latin-1) afin de récupérer un texte exploitable y compris en l'absence de métadonnée d'encodage. La couche d'entrée applique enfin des contraintes opérationnelles (taille maximale, extensions admises, vérification croisée extension/MIME) pour prévenir les attaques par fichier déguisé.

### 3.2.2 Étape 2 — Normalisation et nettoyage

Le texte extrait est ensuite normalisé via une chaîne de traitement spécialisée pour l'arabe, qui combine onze opérations classées en quatre familles : (i) **homogénéisation Unicode** (normalisation NFKC, suppression des marques de direction invisibles, conversion des chiffres arabes-indiques) ; (ii) **uniformisation graphémique** (normalisation des formes de hamza, suppression des diacritiques, normalisation de la ponctuation) ; (iii) **réparation des artefacts OCR** (recollage des mots éclatés, suppression des lettres latines parasites isolées dans un contexte arabe) ; et (iv) **finalisation typographique** (filtrage par liste blanche, espacement aux frontières arabe/chiffre, compactage des espaces). Un second module de **nettoyage juridique** retire le bruit éditorial structurel propre aux publications du JORT — références de publication, notices de rectificatif, colophons de l'imprimerie — tout en préservant scrupuleusement les références légales, les titres d'articles et les marqueurs d'amendement via une liste blanche d'expressions régulières. Un troisième module, dédié à la requête plutôt qu'au corpus, détecte automatiquement les questions formulées en dialecte tunisien (*derja*) et les normalise vers le français standard avant soumission au pipeline RAG, l'arabe littéraire restant la cible des recherches dans le corpus.

### 3.2.3 Étape 3 — Segmentation hiérarchique et découpage

La segmentation extrait la structure hiérarchique des textes selon le schéma **Titre → Chapitre → Section → Article** au moyen de motifs lexicaux bilingues, suivant une approche similaire à TextDiscover [28] adaptée aux spécificités du corpus juridique tunisien couvrant l'arabe (*الفصل*, *المادة*, *البند*), le français (*Article*, *Alinéa*, *Chapitre*, *Section*, *Titre*) et l'anglais. Un mode mixte combine les trois jeux pour les documents bilingues. Les textes nettoyés sont ensuite découpés en **unités d'indexation de 1 500 caractères avec chevauchement de 200 caractères**, en respectant les frontières structurelles détectées — un *chunk* ne traverse jamais une frontière d'article. Chaque *chunk* est associé à sa langue, à son identifiant de section, à son indice séquentiel et à un *hash* du texte permettant la déduplication. Un filtre qualité écarte les *chunks* trop courts, peu denses lexicalement ou dont la proportion de caractères alphanumériques est jugée insuffisante, afin d'éviter d'indexer du bruit OCR résiduel.

### 3.2.4 Étape 4 — Encodage vectoriel et cache

Chaque *chunk* est transformé en un vecteur de **768 dimensions** par le modèle d'embeddings *fine-tuné* sur le corpus juridique tunisien (cf. section 3.5). Pour absorber le coût d'inférence, deux mécanismes sont mis en place : un **cache LRU** au niveau des requêtes, indexé par empreinte du texte, qui rend les requêtes répétées effectivement gratuites ; et un mécanisme de **compatibilité descendante** chargeant automatiquement un modèle de dimension 384 lorsqu'une requête est exécutée contre un index hérité de cette dimension. Les vecteurs sont normalisés L2 systématiquement, ce qui permet d'exploiter une similarité cosinus exacte à partir d'un index HNSW euclidien.

### 3.2.5 Étape 5 — Indexation FAISS et persistance

Les vecteurs sont stockés dans un index **FAISS HNSW** [25, 27] dont les hyperparamètres (`M`, `efConstruction`, `efSearch`) sont choisis pour offrir un compromis rappel/latence adapté aux corpus de l'ordre de 10⁴ à 10⁶ vecteurs. L'index est reconstruit en mémoire à chaque démarrage de l'application, et les métadonnées associées (identifiant, document, langue, page, section, texte tronqué) sont conservées dans une structure parallèle pour permettre une résolution rapide des résultats sans aller-retour vers la base documentaire. Un **service de vérification de cohérence** valide au démarrage que la dimension des vecteurs stockés en base correspond bien à celle du modèle d'embeddings configuré ; en cas de désaccord, l'index est marqué *indisponible* et un endpoint administratif permet de relancer le ré-encodage complet du corpus.

**Tableau 3.2 — Paramètres clés du pipeline d'ingestion.**

| Paramètre | Valeur | Justification |
|---|---|---|
| Taille max fichier | 50 Mo | Couvre les PDF du JORT les plus volumineux sans risque DoS |
| Extensions admises | pdf, docx, doc, txt, png, jpg, jpeg, webp | Vérifiées par croisement extension + MIME |
| Seuil texte dégradé | > 3 % caractères de contrôle | Déclenche le passage à l'étape OCR |
| Seuil arabe attendu | < 15 % de caractères arabes | Indique une extraction défaillante |
| Encodages testés | UTF-8, UTF-8-SIG, CP1256, ISO-8859-6, Latin-1 | Couvre tous les exports JORT observés |
| Chunk size | 1 500 caractères | Compromis entre granularité et contexte LLM |
| Chunk overlap | 200 caractères | Préserve la continuité aux frontières |
| Min chunk size | 300 caractères | Évite les fragments non informatifs |
| Embedding dim | 768 | Modèle MPNet *fine-tuné* |
| Cache LRU embeddings | 512 entrées | Hit rate observé > 60 % |
| FAISS index type | IndexHNSWFlat | Compromis rappel/latence pour 10⁴–10⁶ vecteurs |
| HNSW M | 32 | Connectivité de graphe standard |
| HNSW efConstruction | 200 | Qualité d'insertion élevée |
| HNSW efSearch | 64 | Latence < 50 ms sur le corpus actuel |

## 3.3 Conception du pipeline RAG avancé à six modules

Le pipeline de réponse aux requêtes orchestre le traitement d'une question utilisateur à travers six modules spécialisés activables indépendamment par configuration. Cette modularité, formalisée par le protocole `RetrieverStrategy` et la classe `RetrievalMix`, permet de basculer dynamiquement entre un mode RAG classique et un mode partitionné piloté par l'intention de l'utilisateur.

### 3.3.1 Module 1 — Recherche hybride vectorielle et lexicale

La recherche combine des signaux complémentaires. La **recherche vectorielle** interroge l'index FAISS via `faiss_manager.search`, en récupérant initialement `4 × top_k` candidats avant filtrage par langue ou par document. Les candidats sont ensuite reclassés par une **fonction de fusion pondérée** qui agrège plusieurs signaux pour chaque *chunk* : le score vectoriel issu de FAISS, le **recouvrement lexical** de tokens entre la question et le *chunk* (calculé avec une tokenisation multilingue tenant compte des particularités de l'arabe), un **score de mots-clés** et le recouvrement des **tokens d'ancrage** discriminants (termes spécifiques non génériques). Le score de fusion s'écrit :

$$\text{score}(c) = w_v \cdot s_{\text{vec}}(c) + w_l \cdot o_{\text{lex}}(c) + w_k \cdot s_{\text{kw}}(c) + w_a \cdot o_{\text{anc}}(c) + b(c) - p(c) \qquad (3.1)$$

où $s_{\text{vec}}$ est le score vectoriel, $o_{\text{lex}}$ le recouvrement lexical, $s_{\text{kw}}$ le score de mots-clés, $o_{\text{anc}}$ le recouvrement d'ancrage, $b(c)$ un ensemble de bonus (correspondance de phrase exacte, correspondance de référence d'article, *boosts* de domaine) et $p(c)$ des pénalités de portée (par exemple pour distinguer une SARL d'une société en participation). Les pondérations par défaut sont $(w_v, w_l, w_k, w_a) = (0{,}56\ ;\ 0{,}20\ ;\ 0{,}14\ ;\ 0{,}10)$, ajustables par domaine juridique (par exemple $w_v = 0{,}50$ et $w_l = 0{,}24$ pour les domaines à forte densité terminologique).

Ce choix d'une **fusion linéaire pondérée directe** — plutôt qu'une fusion par rang de type *Reciprocal Rank Fusion* (RRF) qui aurait nécessité la maintenance d'un second index lexical BM25 — privilégie la simplicité opérationnelle et évite un index supplémentaire, tout en conservant l'apport complémentaire des signaux denses et lexicaux mis en évidence dans l'état de l'art (section 2.3).

### 3.3.2 Module 2 — Reranking par cross-encoder

Les *chunks* issus de la recherche hybride sont reclassés par le modèle `cross-encoder/ms-marco-MiniLM-L-6-v2`, qui évalue chaque paire (question, *chunk*) de façon croisée. Les scores du cross-encoder sur le benchmark MS-MARCO se situent dans une plage d'environ −10 à +10 ; un seuil de rejet `MIN_RERANK_SCORE = −2,0` est appliqué pour éliminer les *chunks* manifestement non pertinents avant la génération.

### 3.3.3 Module 3 — Routeur de domaine

Le module `services/domain_router.py` identifie automatiquement le domaine juridique d'une question parmi cinq domaines prioritaires (travail, sociétés, données personnelles, fiscalité, sécurité au travail) à partir d'un dictionnaire de mots-clés trilingue. Il adapte alors les paramètres de recherche : `top_k` spécifique au domaine, filtres `language_filter` privilégiant la langue dominante du domaine, et orientation vers des collections spécifiques. Un repli LLM (`domain_router_llm_fallback_enabled`) est activé lorsque la classification par mots-clés est ambiguë.

### 3.3.4 Module 4 — Orchestrateur de récupération partitionnée

Ce module, implémenté dans `services/legal_retrieval_orchestrator.py`, constitue une contribution scientifique originale du projet. Il distingue les *chunks* issus des **textes de loi de base** (`is_base_version = true`) de ceux issus des **amendements** (`is_base_version != true`), afin d'éviter le mélange anarchique de sources contradictoires lorsqu'un amendement remplace une disposition antérieure.

La **stratégie de mixing** est pilotée par l'intention de l'utilisateur, classifiée à partir de mots-clés trilingues (français, arabe, anglais) :

**Tableau 3.3 — Stratégie de mixing partitionnée par intention.**

| Intention détectée | Sources | Pondération | top_k |
|---|---|---|---|
| `current_state` (défaut) | amendement, base | 0,70 / 0,30 | 12, 6 |
| `historical` | base, amendement | 0,85 / 0,15 | 12, 4 |
| `compare` | base, amendement | 0,50 / 0,50 | 8, 8 |
| `compliance_audit` | base, amendement, exigence, action | 0,40 / 0,40 / 0,10 / 0,10 | 8, 8, 4, 4 |

Les *chunks* récupérés depuis chaque partition sont ensuite fusionnés par un score pondéré combinant la similarité intra-partition, un bonus positionnel (pour valoriser les meilleurs *chunks* de chaque partition) et la pondération de la partition :

$$\text{score}_{\text{merge}}(c) = \left( \text{score}_{\text{base}}(c) + \frac{1}{1 + 0{,}1 \cdot \text{rang}(c)} \right) \cdot w_{\text{partition}}(c) \qquad (3.2)$$

La liste finale est déduppliquée par identifiant ou *hash* de texte et tronquée à `top_k = 14` par défaut.

### 3.3.5 Module 5 — Résolveur de graphe de connaissances léger (KG Light)

Le module `services/graph_resolver.py` traverse les collections MongoDB selon la hiérarchie **Loi → Article → Version → Exigence → Action → Criticité**, reconstituant un sous-graphe de connaissances pour les articles cités dans les *chunks* récupérés. Ce sous-graphe enrichit le contexte transmis au LLM : pour chaque article retrouvé, le modèle dispose de la liste des exigences extraites (obligations, sanctions, conditions, interdictions), des actions correctives suggérées, des criticités associées et des dépendances entre actions.

Le paramètre `kg_light_max_entities = 6` limite l'enrichissement aux six premières entités pour préserver la fenêtre de contexte du LLM (8 192 tokens dans la configuration courante).

### 3.3.6 Module 6 — Garde-qualité

Avant sa présentation, la réponse est soumise à une validation multi-couches détaillée en section 3.6 : contrôle des références citées contre le contenu réel des *chunks*, détection de citations fabriquées par fenêtre glissante, fidélité sémantique, conformité linguistique.

### 3.3.7 Assemblage du prompt et ingénierie de prompts interactifs

Le prompt final combine, dans l'ordre :

1. Le **persona** de conseiller juridique interactif (différencié par langue détectée) ;
2. Un **exemple *few-shot*** trilingue illustrant le comportement attendu ;
3. L'historique récent de conversation (jusqu'à 20 messages) si disponible ;
4. Les *chunks* récupérés numérotés `[Source 1]`, `[Source 2]`, … ;
5. Le sous-graphe KG Light formaté en JSON compact ;
6. Un **rappel d'ancrage** qualifiant l'invention d'un article de « faute professionnelle grave » ;
7. La **question utilisateur** ;
8. Un **rappel de langue** explicite (« Réponds entièrement en français », etc.).

Le format de réponse imposé est structuré en quatre blocs maximum : *Diagnostic* (reformulation et questions de clarification), *Ce que dit la loi* (articles pertinents avec citations `[Source N]`), *Risques et conséquences* (sanctions et risques concrets), *Actions à prendre* (étapes opérationnelles). Le système impose un maximum de 400 mots, interdit la répétition entre sections et proscrit les phrases de remplissage. Une post-fonction `_enforce_output_format` détecte et corrige automatiquement les violations de format.

## 3.4 Conception de l'agent autonome ReAct

Au-delà du pipeline RAG séquentiel, Daleel propose un **agent autonome** fondé sur le paradigme ReAct, exposé via l'endpoint `POST /api/v1/ask-agent`. Contrairement au pipeline RAG qui suit un flux prédéterminé, l'agent décide dynamiquement quelles actions entreprendre en fonction de la question et des résultats intermédiaires.

### 3.4.1 Boucle d'exécution

L'agent construit le contexte initial, puis itère :

1. **Construction du contexte** : détection de langue (avec normalisation préalable du *derja* si applicable), sélection du *system prompt* persona, injection de l'exemple *few-shot* trilingue, ajout de l'historique de conversation et de la question annotée d'un rappel de langue.
2. **Appel Ollama avec schéma d'outils** : envoi des messages à l'endpoint `/api/chat` accompagnés du schéma des 12 outils disponibles, avec température 0,15, *top-p* 0,9 et contexte 8 192 tokens.
3. **Exécution des appels d'outils** : pour chaque `tool_call` retourné par le modèle, exécution du *handler* correspondant avec un timeout par outil, journalisation dans `tool_log` et injection du résultat tronqué (4 000 caractères max) comme observation.
4. **Itération ou réponse finale** : si la réponse du modèle ne contient pas d'appel d'outil, le contenu est considéré comme la réponse finale ; sinon, retour à l'étape 2.
5. **Garde-fou de budget** : itérations limitées à un maximum configurable, durée totale plafonnée par un *timeout* global. Si la limite est atteinte, le modèle est explicitement invité à produire sa meilleure réponse sur la base des informations déjà collectées.

### 3.4.2 Catalogue des douze outils

L'agent dispose de douze outils répartis en trois *tiers* fonctionnels.

**Tableau 3.4 — Catalogue des outils de l'agent autonome ReAct.**

| Tier | Outil | Fonction |
|---|---|---|
| Recherche | `semantic_search` | Recherche vectorielle hybride dans le corpus avec filtres langue / document |
| Recherche | `lookup_law` | Consultation d'une loi par son code court (CT, CS, CF, LP63, …) |
| Recherche | `search_articles` | Liste des articles d'une loi, optionnellement filtrés par mot-clé |
| Recherche | `get_article_text` | Texte complet d'une version d'article donnée |
| Graphe | `get_article_graph` | Sous-graphe complet d'un article : versions, exigences, actions, criticités |
| Graphe | `get_company_graph` | Graphe entreprise : exigences applicables et actions liées |
| Exigences | `list_document_exigences` | Liste des exigences (obligations, sanctions, conditions, interdictions) d'un document |
| Exigences | `match_exigences` | Recherche sémantique d'exigences pertinentes à une situation décrite |
| Conformité | `get_applicability` | Résumé d'applicabilité par type d'exigence pour un profil d'entreprise |
| Conformité | `get_criticality` | Répartition des criticités (critique, importante, secondaire) par profil |
| Conformité | `compute_compliance` | Calcul de la posture de conformité globale (score de couverture, écarts) |
| Conformité | `generate_roadmap` | Génération d'un plan d'action priorisé avec dépendances |

Chaque outil est défini par une `ToolDefinition` (nom, description en langage naturel, schéma JSON des paramètres, handler asynchrone). Le schéma JSON est sérialisé selon le format `function calling` d'Ollama, ce qui permet au LLM de produire directement des appels typés au lieu de texte libre à parser.

### 3.4.3 Traçabilité et garde-fous

Chaque itération est enregistrée dans un `ToolCallRecord` contenant l'itération, le nom de l'outil, les arguments, un résumé du résultat (300 caractères), la durée d'exécution et l'éventuelle erreur. Cette trace est exposée dans la réponse de l'agent sous le champ `tool_calls_log`, offrant une **transparence totale** sur le raisonnement effectué. Les sources cumulées au fil des itérations sont déduppliquées par triplet `(document_id, page_number, section)`.

En sortie de boucle, trois étapes de validation sont appliquées :

1. **Application du format** : la fonction `_enforce_output_format` impose la structure en quatre blocs et supprime les sections de remplissage ;
2. **Vérification de langue** : si la réponse n'est pas dans la langue détectée (test combinant proportion de caractères arabes/latins et présence de marqueurs lexicaux français/anglais), une seconde requête de traduction est envoyée au modèle ;
3. **Audit qualité** : la garde-qualité (section 3.6) est appliquée pour détecter et corriger les hallucinations.

## 3.5 Conception du fine-tuning des embeddings

Le *fine-tuning* du modèle d'embeddings constitue la contribution scientifique la plus mesurable du projet, avec des gains de performance significatifs (cf. chapitre 5). Sa conception suit quatre étapes.

### 3.5.1 Constitution du dataset

À partir des 2 344 articles juridiques extraits, un jeu d'entraînement est construit selon deux familles de paires positives :

1. **Paires question/article** générées synthétiquement à l'aide d'un LLM : pour chaque article, le modèle formule trois à cinq questions juridiques auxquelles l'article apporte une réponse. Les questions générées sont filtrées par vérification de cohérence (l'article doit apparaître dans le top-5 d'une recherche vectorielle préliminaire).
2. **Paires inter-langues** : pour les articles disposant d'une version arabe et d'une version française, ces deux versions constituent une paire positive translingue.

Les **négatifs *hard*** sont sélectionnés par *mining* : pour chaque ancre, on récupère les articles les plus proches dans l'espace d'embeddings du modèle de base qui ne sont pas la cible, et on retient ceux dont la similarité dépasse un seuil. Cette stratégie expose le modèle aux confusions sémantiques typiques du domaine (par exemple, distinguer un article sur le congé annuel d'un article sur le congé maladie).

### 3.5.2 Architecture et fonction de perte

Le modèle de départ est `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` (XLM-R 12 couches, 768 dimensions). La fonction de perte retenue est la **MultipleNegativesRankingLoss** [18], adaptée aux paires positives sans annotations explicites de négatifs : dans un *batch* de taille B, chaque paire `(ancre_i, positif_i)` utilise les `B − 1` autres positifs du *batch* comme négatifs implicites, et la perte est calculée par entropie croisée multi-classes sur la matrice de similarités :

$$\mathcal{L} = -\frac{1}{B} \sum_{i=1}^{B} \log \frac{\exp(\text{sim}(a_i, p_i) / \tau)}{\sum_{j=1}^{B} \exp(\text{sim}(a_i, p_j) / \tau)} \qquad (3.3)$$

avec $\tau$ une température de calibration. Cette perte présente l'avantage d'être *batch-efficient* et d'éviter le coût d'annotation manuelle de négatifs.

### 3.5.3 Hyperparamètres et protocole d'évaluation

**Tableau 3.5 — Hyperparamètres du *fine-tuning* du modèle d'embeddings.**

| Hyperparamètre | Valeur |
|---|---|
| Modèle de base | `paraphrase-multilingual-mpnet-base-v2` |
| Dimension d'embedding | 768 |
| Fonction de perte | MultipleNegativesRankingLoss |
| Batch size | 32 |
| Learning rate | 2 × 10⁻⁵ |
| Optimiseur | AdamW |
| Warmup steps | 10 % du total |
| Epochs | 3 |
| Max sequence length | 256 tokens |
| Normalisation | L2 (embeddings cosine-compatibles) |

Le protocole d'évaluation, formalisé dans `tests/benchmark_models.py`, repose sur un jeu de **30 requêtes gold** (20 en français et 10 en arabe) distinctes du jeu d'entraînement, couvrant les cinq domaines juridiques prioritaires et les trois langues. Les métriques calculées sont **Recall@1, Recall@5, Recall@10, MRR@10 et nDCG@5**, comparées avant et après *fine-tuning*. Le modèle résultant est sauvegardé sous le nom `daleel-embedding-finetuned` et chargé par le service d'embeddings via le mécanisme de résolution de chemin local de `_resolve_model_name_or_path`.

## 3.6 Conception de la garde-qualité anti-hallucination

Le module `services/quality_guard_service.py` constitue la dernière ligne de défense contre les hallucinations. Il intervient en post-génération, après la production de la réponse par le LLM ou l'agent ReAct, et fonctionne en plusieurs couches.

### 3.6.1 Couche 1 — Vérification des références

Les références d'articles et de lois mentionnées dans la réponse sont extraites par expressions régulières et confrontées aux références effectivement présentes dans les *chunks* récupérés (texte et métadonnées). Toute référence citée non supportée est signalée comme suspecte.

### 3.6.2 Couche 2 — Détection de citations fabriquées par fenêtre glissante

Les citations textuelles encadrées par des guillemets typographiques (`« »`, `" "`, `“ ”`) sont extraites, puis chacune est recherchée dans le texte concaténé des *chunks* selon une **fenêtre glissante** : on cherche d'abord la citation entière, puis, par fenêtres décroissantes de 8 à 4 mots consécutifs, on vérifie qu'au moins un fragment significatif est effectivement présent. Toute citation non vérifiée est remplacée par le marqueur `[citation non vérifiée]`, préservant la lisibilité de la réponse tout en signalant explicitement le problème à l'utilisateur.

### 3.6.3 Couche 3 — Cohérence du contenu d'article

Le module `_verify_article_content_match` détecte les cas où la réponse attribue à un article un contenu qui ne figure pas réellement dans le *chunk* correspondant. Cette vérification capture les hallucinations subtiles du type « L'article 409 stipule que les registres de présence doivent être... » alors que l'article 409 traite en réalité d'un sujet différent.

### 3.6.4 Couche 4 — Conformité linguistique

La langue effective de la réponse est comparée à la langue détectée de la question via un ratio de caractères et un comptage de mots-marqueurs. Si la réponse n'est pas dans la bonne langue, une requête de traduction est automatiquement émise au LLM.

### 3.6.5 Décision finale et statuts

Le service produit un statut final parmi `accepted`, `rewritten` (réponse modifiée pour neutraliser les hallucinations) ou `rejected` (réponse rejetée, message générique « informations insuffisantes » servi). La décision et la liste des problèmes détectés sont injectées dans la réponse de l'API sous les champs `quality_guard_status` et `quality_guard_issues`, offrant à la couche frontend la possibilité d'afficher une alerte explicite à l'utilisateur.

## 3.7 Conception du volet Compliance Operations

Le volet *Compliance Operations* étend la plateforme d'un système de question-réponse vers un outil de pilotage opérationnel. Sa conception repose sur l'orchestration d'un cycle complet allant du dossier de non-conformité aux preuves de mise en conformité.

### 3.7.1 Modèle métier du cycle de conformité

Le cycle de conformité s'articule autour de huit entités métier interconnectées :

1. **Dossier de conformité** (`compliance_cases`) : conteneur d'un cas de non-conformité, avec contexte, profil d'entreprise associé et statut ;
2. **Messages de cas** (`case_messages`) : historique conversationnel piloté par le LLM ;
3. **Documents de cas** (`case_documents`) : pièces attachées analysées par OCR + LLM ;
4. **Constats** (`case_findings`) : non-conformités identifiées, scorées par sévérité et confiance ;
5. **Actions correctives** (`case_actions`) : étapes opérationnelles avec dépendances et échéances ;
6. **Contrôles internes** (`controls`) : contrôles préventifs, détectifs ou correctifs ;
7. **Preuves** (`control_evidences`) : éléments factuels de mise en conformité ;
8. **Exceptions** (`exception_register`) : acceptations de risques, dérogations, *compensating controls*.

Une table de liaison `requirement_control_links` relie les exigences réglementaires aux contrôles, et une collection `compliance_assessments` matérialise les évaluations périodiques de la posture de conformité.

### 3.7.2 Orchestrateur de cas

L'orchestrateur, implémenté dans `services/compliance_case_orchestrator.py`, séquence sept phases :

1. **Collecte de contexte** : récupération des faits déjà connus via le service de conversation de cas et le profil d'entreprise associé ;
2. **Analyse d'écarts** : évaluation par le LLM des exigences manquantes ;
3. **Vérification d'applicabilité** : appel du service d'applicabilité pour identifier les exigences pertinentes pour le profil ;
4. **Génération de constats** : extraction structurée des non-conformités par le LLM, avec score de confiance ;
5. **Scoring de criticité** : application du moteur de règles déterministe `criticality_service` ;
6. **Priorisation des actions** : génération d'un plan ordonné par `roadmap_service` tenant compte des dépendances ;
7. **Mappage des preuves** : rattachement des documents fournis aux exigences couvertes.

### 3.7.3 Arbre de décision ASK / CLARIFY / ACT / REVIEW

L'orchestrateur conclut chaque cycle par une décision selon un arbre de décision à quatre branches :

```
                  ┌──────────────────────────┐
                  │  Analyse du cas          │
                  └────────────┬─────────────┘
                               │
              ┌────────────────┼─────────────────────┐
              ▼                ▼                     ▼
   ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
   │ facts_missing   │ │ contradictions  │ │ confiance       │
   │   > seuil       │ │  documentaires  │ │   < 0,70 + crit.│
   │   OU conf < 0,6 │ │   détectées     │ │   critique      │
   └────────┬────────┘ └────────┬────────┘ └────────┬────────┘
            │                   │                   │
            ▼                   ▼                   ▼
        ┌───────┐           ┌─────────┐         ┌────────┐
        │  ASK  │           │ CLARIFY │         │ REVIEW │
        └───────┘           └─────────┘         └────────┘
                                │
                                ▼ (par défaut, contexte suffisant)
                            ┌───────┐
                            │  ACT  │
                            └───────┘
```

![Arbre de décision de l'orchestrateur Compliance Operations](captures/fig_3_3_decision_tree.png)

**Figure 3.3 — Arbre de décision de l'orchestrateur Compliance Operations.**

Les seuils sont calibrés en constantes du module : `MIN_FACTS_FOR_ANALYSIS = 3`, `MAX_MISSING_FACTS_TOLERANCE = 2`, `MIN_CONFIDENCE_FOR_AUTO_ACT = 0,70`, `MIN_CONFIDENCE_FOR_FINDING = 0,60`. La décision est exposée au frontend, qui adapte l'interface en conséquence (formulaire de clarification, validation experte requise, génération de plan d'action).

### 3.7.4 Moteur de criticité déterministe

Le service `criticality_service.py` attribue à chaque action de conformité un niveau parmi **critique** (score ≥ 0,75), **importante** (score ≥ 0,50) et **secondaire** (score < 0,50). Le score est calculé selon un modèle additif déterministe (et non probabiliste), pour garantir l'auditabilité et la reproductibilité.

**Tableau 3.6 — Composantes du score de criticité.**

| Composante | Valeur | Description |
|---|---|---|
| Score de base — sanction | 0,85 | Modalité « sanction » |
| Score de base — interdiction | 0,70 | Modalité « interdiction » |
| Score de base — obligation | 0,65 | Modalité « obligation » |
| Score de base — condition | 0,35 | Modalité « condition » |
| Boost sanctions textuelles | +0,10 | Mots-clés : amende, peine, emprisonnement, خطية, غرامة, … |
| Boost montant pécuniaire | +0,05 | Présence d'un montant en DT, TND, EUR, USD |
| Boost domaine données personnelles | +0,15 | RGPD, INPDP, البيانات الشخصية |
| Boost domaine santé/sécurité | +0,12 | Accident du travail, EPI, السلامة المهنية |
| Boost domaine fiscal | +0,08 | TVA, impôt, douane, الجباية |
| Boost domaine travail clandestin | +0,15 | Travail non déclaré, العمل غير المصرح |
| Pénalité langage conditionnel | −0,15 | « le cas échéant », « éventuellement », إن اقتضى الأمر |
| Boost sanction héritée | +0,07 | L'article parent porte une sanction distincte |

Chaque composante appliquée est journalisée dans le champ `criticality_reasons` de l'action, permettant à l'utilisateur de comprendre exactement pourquoi une action est classée critique. Cette transparence est essentielle pour la défense juridique de la posture de conformité.

## 3.8 Modélisation conceptuelle des données

La persistance Daleel s'appuie sur MongoDB 7.0 avec **38 collections** regroupées en sept domaines fonctionnels.

**Tableau 3.7 — Cartographie des 38 collections MongoDB par domaine.**

| Domaine | Collections |
|---|---|
| Gestion documentaire | `documents`, `document_sources`, `document_raw_pages`, `document_cleaned_texts`, `chunks` |
| Hiérarchie juridique | `lois`, `articles`, `article_versions`, `amendment_operations` |
| Exigences et actions | `exigences`, `actions`, `action_criticalities`, `action_dependencies` |
| Profils et applicabilité | `company_profiles`, `exigence_applicabilities` |
| Dossiers de conformité | `compliance_cases`, `case_messages`, `case_documents`, `case_document_analyses`, `case_findings`, `case_actions`, `compliance_assessments` |
| Contrôles et preuves | `controls`, `control_evidences`, `requirement_control_links`, `exception_register`, `contract_analyses` |
| Identité, audit et système | `users`, `organizations`, `invitations`, `password_reset_tokens`, `token_blacklist`, `audit_logs`, `qa_feedback`, `chat_history`, `notifications`, `user_memory`, `conversation_summaries` |

### 3.8.1 Schéma hiérarchique juridique

Le cœur du modèle juridique est constitué de la chaîne hiérarchique :

![Modèle conceptuel de la hiérarchie juridique : Loi, Article, ArticleVersion, Exigence, Action, ActionCriticality et AmendmentOperation](captures/fig_3_4_modele_juridique.png)

**Figure 3.4 — Modèle conceptuel de la hiérarchie juridique.**

Chaque `ArticleVersion` porte un booléen `is_base_version`, un numéro de version `version_number` et un booléen `is_current`, qui est l'index principal de la collection. Les `AmendmentOperation` lient la version précédente à la version résultante, et leur type (`operation_type`) permet la traçabilité fine des modifications.

### 3.8.2 Schéma du cycle de conformité

Le cycle de conformité opérationnel s'articule autour de :

![Modèle conceptuel du cycle de conformité : ComplianceCase, CaseMessage, CaseDocument, CaseFinding, CaseAction, ComplianceAssessment et ControlEvidence](captures/fig_3_5_modele_conformite.png)

**Figure 3.5 — Modèle conceptuel du cycle de conformité.**

Les `CaseFindings` portent un `severity` (low/medium/high/critical), un `confidence_score` et un lien optionnel vers les exigences réglementaires qu'ils contreviennent. Les `CaseActions` héritent du modèle des `Actions` réglementaires mais s'ancrent dans le contexte du cas.

### 3.8.3 Stratégie d'indexation MongoDB

Pour garantir la performance des requêtes, des index composites sont définis dans `database.py` pour chaque collection. Le service `database.init_db()` crée ces index au démarrage, avec un mécanisme de tolérance aux valeurs en doublon existantes (en cas d'index unique). Les index notables incluent :

- `chunks` : index sur `(document_id, chunk_index)`, `(document_id, language)`, `(article_version_id)` ;
- `document_sources` : index unique sur `file_hash` (déduplication des uploads) ;
- `article_versions` : index sur `(article_id, is_current)` et `(article_id, version_number)` ;
- `exigences` : index sur `(document_id, page_number)` et `(exigence_type)` ;
- `compliance_cases` : index sur `(organization_id, status)` et `(profile_id, created_at)` ;
- `audit_logs` : index temporel sur `(created_at)` et par acteur sur `(user_id, action)`.

## 3.9 Choix technologiques

### 3.9.1 Critères de sélection

L'ensemble des choix technologiques a été dicté par cinq contraintes structurantes : **asynchronisme** (pour absorber des charges concurrentes sans blocage), **support multilingue** (arabe, français, anglais), **déploiement local sans dépendance à une API externe** (souveraineté technique), **confidentialité des données juridiques** (les documents organisationnels ne doivent jamais quitter le périmètre du client), et **reproductibilité du déploiement** (mêmes comportements de la station de développement à la production).

### 3.9.2 Comparaison justifiée des modèles de langage candidats

Le choix du modèle de langage central de la plateforme constitue la décision technologique la plus structurante du projet : elle conditionne la qualité des réponses, la couverture linguistique, la capacité à intégrer des outils, et la viabilité d'un déploiement *on-premise*. Quatre familles de modèles ont été évaluées en regard des cinq contraintes ci-dessus, augmentées de deux critères propres au domaine : **qualité de l'arabe** et **support du *function calling* natif** requis par l'agent ReAct.

**Tableau 3.8 — Comparaison des modèles de langage candidats au regard des contraintes de Daleel.**

| Critère | **Qwen2.5 7B** *(retenu)* | Mistral 7B Instruct | Llama 3.2 3B Instruct | GPT-4 (API OpenAI) |
|---|---|---|---|---|
| Architecture | Décodeur Transformer GQA, 28 couches | Décodeur Transformer GQA, 32 couches | Décodeur Transformer GQA, 28 couches | Architecture propriétaire |
| Paramètres | 7,6 G | 7,2 G | 3,2 G | non communiqué |
| Tokens de pré-entraînement | 18 T | ≈ 8 T | ≈ 15 T | non communiqué |
| Couverture multilingue | 29 langues dont arabe, fr, en | Principalement en, fr, partiel ar | en + 8 langues, arabe non officiel | Très large (40+ langues) |
| Qualité de l'arabe | Bonne (fine-tuning AR documenté) | Faible à moyenne | Faible | Excellente |
| Fenêtre de contexte | 32 768 tokens | 32 768 tokens | 128 000 tokens | 128 000 tokens |
| *Function calling* natif | ✅ Oui (endpoint `/api/chat`) | ⚠️ Partiel (instruct-mode, parsing JSON requis) | ⚠️ Partiel | ✅ Oui |
| Déploiement *on-premise* | ✅ Oui (via Ollama) | ✅ Oui | ✅ Oui | ❌ Non (API externe) |
| Licence | Apache 2.0 | Apache 2.0 | Llama 3 Community License (restrictions commerciales > 700 M MAU) | Service propriétaire |
| Coût | Aucun (open weights) | Aucun | Aucun | ≈ 0,03 USD / 1 K tokens |
| Empreinte mémoire (quantif. Q4_K_M) | ≈ 4,7 Go | ≈ 4,4 Go | ≈ 2,0 Go | n/a |

L'analyse de ce tableau au regard des contraintes énoncées en section 1.7.3 conduit à écarter successivement :

- **GPT-4** : meilleure qualité brute, notamment sur l'arabe, mais incompatible avec les exigences de confidentialité (envoi des documents organisationnels à un service tiers) et de déploiement local. Le coût d'inférence par requête est également incompatible avec un usage intensif en production chez un client tunisien.
- **Llama 3.2 3B** : empreinte mémoire séduisante, mais la couverture multilingue officielle n'inclut pas l'arabe et la licence Llama Community License introduit des restrictions juridiques sur la commercialisation et la redistribution qui sont incompatibles avec la posture éditoriale de Didax IT.
- **Mistral 7B Instruct** : licence Apache 2.0 et déploiement local satisfaisants, mais le support *function calling* repose sur des conventions de prompt et un parseur JSON applicatif, ce qui fragilise la boucle ReAct ; la qualité de l'arabe reste en retrait par rapport à Qwen2.5.

**Qwen2.5 7B** réunit l'ensemble des critères : pré-entraînement multilingue incluant explicitement l'arabe, *function calling* natif éliminant le besoin de parseur applicatif, fenêtre de contexte de 32 K suffisante pour les besoins du projet, licence Apache 2.0 sans restriction commerciale, et empreinte mémoire compatible avec un serveur Linux de gamme moyenne. Ce choix est en outre étayé par plusieurs *fine-tunings* expérimentaux conduits dans le cadre du projet : un adaptateur stylistique LoRA [33] `daleel-style-v1` sur Qwen2.5-1.5B, et un adaptateur arabe `daleel-arabic-v1` sur Qwen2.5-7B (en s'appuyant sur la quantification QLoRA [34] pour réduire l'empreinte mémoire lors de l'entraînement), qui ont validé la malléabilité de la famille Qwen2.5 sur du contenu juridique tunisien.

### 3.9.3 Synthèse des technologies retenues

Le tableau 3.9 récapitule l'ensemble des composants technologiques retenus pour la plateforme et la principale justification de chaque choix.

**Tableau 3.9 — Synthèse des technologies retenues et justification des choix.**

| Composant | Technologie retenue | Principale justification |
|---|---|---|
| Framework API | FastAPI 0.115+ | Async natif, validation Pydantic, OpenAPI auto |
| Serveur ASGI | Uvicorn | Performance et compatibilité FastAPI |
| Base de données | MongoDB 7.0 + Motor | Schéma flexible, pilote async natif |
| Recherche vectorielle | FAISS HNSW (M=32) | Local, rapide, scalable |
| Signaux lexicaux | Recouvrement de tokens + mots-clés | Correspondances exactes, articles numérotés |
| Fusion des signaux | Combinaison linéaire pondérée | Vecteur 0,56 / lexical 0,20 / mots-clés 0,14 / ancrage 0,10 |
| Reranking | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Précision sur le top-k |
| LLM | `qwen2.5:7b` via Ollama | Local, multilingue ar/fr/en, tool calling natif |
| Embeddings | MPNet *fine-tuné* (768 d) | +40 % Recall@1 global, +50 % en français, +50 % Recall@5 arabe |
| Agent autonome | ReAct + Ollama tools | 12 outils, raisonnement itératif, traçable |
| OCR | Tesseract (ara/fra/eng) + EasyOCR | Couverture multilingue, fallback robuste |
| Extraction PDF | PyMuPDF + pdfminer.six | Cascade qualité/performance |
| Authentification | JWT (access 30 min, refresh 7 j) | Stateless, multi-tenant compatible |
| Frontend | React + Vite | DX rapide, écosystème mature |
| Internationalisation | i18next (ar / fr / en) | Trois langues officielles |
| Rate limiting | SlowAPI | Protection DoS au niveau API |
| Conteneurisation | Docker Compose (multi-stage) | Déploiement reproductible |
| CI/CD | GitHub Actions | Lint Ruff + pytest, matrice Python 3.11/3.12/3.13 |
| Migrations index | Service interne `init_db` | Création idempotente au démarrage |

## Conclusion

Ce chapitre a situé la plateforme Daleel dans le contexte scientifique des architectures RAG avancées, des embeddings multilingues, des agents autonomes ReAct, de l'assistance juridique fondée sur l'IA et des systèmes de pilotage de la conformité. L'état de l'art a montré la pertinence du paradigme RAG pour les domaines spécialisés et justifié le recours au *fine-tuning* pour adapter les représentations vectorielles au corpus juridique tunisien.

La conception détaillée a couvert chacune des briques de la plateforme : un pipeline d'ingestion à cinq étapes intégrant une extraction en cascade, un nettoyage arabe en onze sous-étapes, une segmentation hiérarchique bilingue et une indexation FAISS HNSW ; un pipeline RAG à six modules combinant recherche hybride à fusion pondérée, reranking, routage de domaine, retrieval partitionné piloté par l'intention et garde-qualité ; un agent autonome ReAct doté de douze outils exploitant l'appel d'outils natif d'Ollama ; un protocole de *fine-tuning* sur paires question/article avec négatifs *hard*, fonction de perte MultipleNegativesRankingLoss et évaluation Recall/MRR/nDCG ; un système de garde-qualité multi-couches comprenant la vérification des références, la détection de citations fabriquées par fenêtre glissante et la conformité linguistique ; et un volet *Compliance Operations* orchestré selon un arbre de décision ASK / CLARIFY / ACT / REVIEW, soutenu par un moteur de criticité déterministe et une modélisation à 38 collections MongoDB couvrant la hiérarchie juridique et le cycle complet de conformité.

Les choix technologiques — FastAPI, MongoDB, FAISS, cross-encoder, Ollama/`qwen2.5:7b`, MPNet *fine-tuné*, Docker et GitHub Actions — ont été justifiés au regard des contraintes spécifiques du projet : asynchronisme, multilingue, déploiement local, confidentialité des données et reproductibilité. Le chapitre suivant présente la réalisation concrète du volet *Legal RAG* : implémentation du pipeline d'ingestion, *fine-tuning* effectif des embeddings, mise en œuvre des six modules RAG et de l'agent autonome, accompagnée de démonstrations qualitatives.

---

# Chapitre 4 — Réalisation du volet Legal RAG

## Introduction

Ce chapitre décrit la réalisation effective du volet *Legal RAG* de la plateforme Daleel, en suivant la conception présentée au chapitre 3. **Dans le cycle CRISP-DM, il matérialise l'exécution conjointe des phases 3 (*préparation des données*) et 4 (*modélisation*)** : le pipeline d'ingestion documentaire transforme le corpus brut JORT en chunks indexables, le *fine-tuning* spécialise le modèle d'embeddings sur le corpus juridique tunisien, et l'orchestration RAG + agent autonome construit la chaîne de réponse. Plusieurs itérations entre ces deux phases ont été nécessaires : la première campagne d'évaluation a révélé un taux de citations fabriquées élevé, conduisant à un retour à la *modélisation* pour ajouter la garde-qualité par fenêtre glissante ; un audit qualitatif des réponses arabes a déclenché un retour à la *préparation des données* pour ajouter trois sous-étapes de nettoyage.

Le chapitre détaille successivement l'environnement de développement retenu, l'implémentation du pipeline d'ingestion documentaire, la conduite du *fine-tuning* du modèle d'embeddings, la mise en œuvre des six modules du pipeline RAG, et celle de l'agent autonome ReAct. Il se conclut par des démonstrations qualitatives illustrant le comportement du système sur des requêtes représentatives du corpus juridique tunisien.

## 4.1 Environnement de développement

### 4.1.1 Configuration matérielle

Le développement et les expérimentations ont été conduits sur un poste de travail dédié dont la configuration est récapitulée ci-dessous.

**Tableau 4.1 — Configuration matérielle de la station de développement.**

| Composant | Caractéristiques |
|---|---|
| Processeur | Intel Core i7 (8 cœurs / 16 threads, 2,5 GHz base, 4,8 GHz boost) |
| Mémoire vive | 32 Go DDR5 |
| Stockage | SSD NVMe 1 To |
| Carte graphique | NVIDIA RTX 3060 (12 Go GDDR6) — utilisée pour le *fine-tuning* |
| Système d'exploitation | Windows 11 Pro 64 bits, WSL2 Ubuntu 22.04 pour les charges Linux |

La carte graphique a été exploitée pour accélérer l'entraînement du modèle d'embeddings ; l'inférence en production reste sur CPU pour respecter la contrainte de déploiement sur des environnements client standard.

### 4.1.2 Configuration logicielle

**Tableau 4.2 — Composants logiciels et leur rôle dans la plateforme.**

| Composant | Version | Rôle |
|---|---|---|
| Python | 3.12 | Langage backend |
| FastAPI | ≥ 0.115 | Framework web ASGI |
| Uvicorn | ≥ 0.30 | Serveur ASGI |
| Pydantic | v2 | Validation et schémas |
| Motor | ≥ 3.4 | Pilote MongoDB asynchrone |
| MongoDB | 7.0 | Base de données documentaire |
| sentence-transformers | ≥ 3.0 | Embeddings et cross-encoder |
| FAISS | ≥ 1.7 | Index vectoriel HNSW |
| Ollama | ≥ 0.4 | Serveur LLM local |
| qwen2.5:7b | — | Modèle de langage générateur |
| PyMuPDF | ≥ 1.24 | Extraction PDF native |
| pdfminer.six | ≥ 20231228 | Extraction PDF de repli |
| Tesseract | ≥ 5.3 | OCR multilingue (ara, fra, eng) |
| EasyOCR | ≥ 1.7 | OCR de repli |
| poppler-utils | latest | Outils PDF système (utilisés par Tesseract) |
| Docker / Docker Compose | 24+ / 2.20+ | Conteneurisation et orchestration |
| Ruff | ≥ 0.6 | Linter Python |
| pytest | ≥ 8 | Framework de tests |
| Node.js | 20 LTS | Outils frontend |
| React | 19 | Bibliothèque UI |
| Vite | 8 | *Bundler* et *dev server* frontend |
| i18next | latest | Internationalisation (ar, fr, en) |
| GitHub Actions | — | CI/CD |

Le fichier `requirements.txt` formalise l'ensemble des dépendances Python avec versions épinglées, garantissant la reproductibilité du build.

### 4.1.3 Organisation du code source

Le dépôt est structuré comme suit :

```
Daleel/
├── backend/
│   ├── app/
│   │   ├── api/              # 7 routeurs FastAPI (auth, router, case, …)
│   │   ├── services/         # 41 services métier
│   │   ├── processing/       # 8 modules de traitement documentaire
│   │   ├── config.py         # Settings Pydantic (env-driven)
│   │   ├── database.py       # Init MongoDB + index
│   │   ├── schemas.py        # Schémas Pydantic Legal RAG
│   │   ├── case_schemas.py   # Schémas Pydantic Compliance
│   │   └── main.py           # Entrée FastAPI + lifespan
│   ├── tests/                # 55 fichiers pytest
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/            # 18 pages React (Chat, Dashboard, admin/...)
│   │   ├── components/       # Composants réutilisables
│   │   ├── locales/          # Fichiers de traduction ar.json, fr.json, en.json
│   │   └── ...
│   └── package.json
├── docker-compose.yml
├── Dockerfile                # Multi-stage build
└── .github/workflows/        # CI GitHub Actions
```

## 4.2 Implémentation du pipeline d'ingestion documentaire

### 4.2.1 Extraction en cascade

Le module `backend/app/processing/extractor.py` implémente la cascade à trois niveaux. Le code de PyMuPDF utilise l'objet `Document` pour itérer sur les pages et extraire à la fois le texte et la position des blocs, ce qui permet de préserver les marges et d'éliminer les en-têtes répétés des PDF du JORT. Le repli sur `pdfminer.six` est déclenché lorsque PyMuPDF retourne un texte vide ou anormalement court (< 100 caractères pour une page de plus de 1 Mo).

Le module `backend/app/processing/ocr.py` orchestre l'OCR : pour chaque page convertie en image via `poppler-utils`, Tesseract est invoqué successivement avec les langues `ara+fra+eng`, et un score de confiance est calculé. Si le score moyen est inférieur à 60, EasyOCR est invoqué en repli, et le texte retourné est celui des deux moteurs avec le meilleur score caractère-par-caractère.

L'enveloppe `backend/app/processing/file_extract.py` expose une fonction de haut niveau `extract_text_from_upload` utilisée par les endpoints API. Elle prend en charge la validation des extensions, la vérification croisée du type MIME, le contrôle de la taille (50 Mo) et le nettoyage du nom de fichier (suppression des `path traversal` et caractères de contrôle). Le tableau d'extensions admises est `{.pdf, .docx, .doc, .txt, .png, .jpg, .jpeg, .webp}`.

### 4.2.2 Pipeline de nettoyage arabe

Le module `backend/app/processing/text_utils.py` implémente le pipeline en onze étapes décrit en section 3.2.2. La détection de langue exploite à la fois la proportion de caractères arabes par expression régulière `[؀-ۿݐ-ݿࢠ-ࣿ]` et la présence de mots-marqueurs trilingues (`_FR_MARKERS`, `_EN_MARKERS`). Cette détection est utilisée à la fois pour l'indexation initiale et pour le routage des requêtes de l'agent autonome.

Le module `backend/app/processing/legal_cleaner.py` complète le nettoyage par une suppression ciblée du bruit éditorial. Les motifs suivants sont éliminés s'ils apparaissent isolément en tête ou en pied de page :

- Mentions de l'imprimerie officielle, paginations JORT, références de publication ;
- Numéros de série de bulletin officiel, dates de publication isolées ;
- Mentions de copyright et notices légales du portail.

Une liste blanche d'expressions sensibles (`article \d+`, `loi n° \d{2,4}-\d+`, `décret \d{4}-\d+`, …) garantit qu'aucune référence juridique ne soit accidentellement supprimée.

### 4.2.3 Segmentation et chunking

Le module `backend/app/processing/article_segmenter.py` produit, à partir d'un document nettoyé, une liste structurée de sections. Chaque section porte un en-tête (capturé par la regex de structure) et un corps (texte entre deux en-têtes). Le service expose également une endpoint API `POST /api/v1/segment` qui permet de re-segmenter un document existant en lui appliquant un jeu de motifs personnalisé.

Le `ChunkingService` (`backend/app/processing/chunker.py`) construit les *chunks* en deux passes : d'abord, un découpage par section ; puis, à l'intérieur de chaque section, un découpage glissant respectant la taille cible de 1 500 caractères et le chevauchement de 200 caractères. La fonction `_merge_short_chunks` recombine les *chunks* dont la taille est inférieure à `min_chunk_size = 300` afin d'éviter une fragmentation excessive. La détection précoce de bas qualité par `_is_low_quality` rejette les *chunks* dont la diversité lexicale ou le ratio alphanumérique sont insuffisants.

Le pipeline complet d'un document, depuis l'upload jusqu'à l'indexation, est exposé par l'endpoint `POST /api/v1/documents/{id}/process` et déclenche les étapes successives en cascade asynchrone. Chaque étape persiste son résultat dans la collection MongoDB correspondante (`document_raw_pages`, `document_cleaned_texts`, `chunks`), de sorte que les étapes sont **idempotentes et reprenables** en cas d'échec partiel.

### 4.2.4 Indexation FAISS et cohérence

Le `FaissIndexManager` (`backend/app/services/faiss_index.py`) est un *singleton* global du processus. À chaque démarrage, le *lifespan* FastAPI invoque `faiss_manager.rebuild()`, soit de façon synchrone (configuration de production), soit en tâche d'arrière-plan (par défaut, pour ne pas retarder la disponibilité de l'API).

La construction parcourt la collection `chunks` projetée sur les champs nécessaires (`id`, `document_id`, `language`, `page_number`, `section`, `chunk_index`, `text`, `embedding`), accumule les vecteurs dans un tableau NumPy, applique la normalisation L2 (`faiss.normalize_L2`), puis construit l'index `IndexHNSWFlat(dim, M=32)` avec `efConstruction=200` et `efSearch=64`. Les métadonnées sont conservées en parallèle dans une liste `_meta` pour la résolution rapide post-recherche.

Le module `backend/app/services/index_consistency_service.py` persiste, après chaque construction, un document de métadonnées (`embedding_model`, `dimension`, `vector_count`, `built_at`) dans la collection `index_metadata`. À chaque démarrage, ce document est comparé à la configuration courante : si la dimension a changé (par exemple suite à un changement de modèle d'embeddings), l'index est marqué *unavailable* avec la raison `dimension_mismatch` et l'endpoint `/admin/reindex` permet de relancer le ré-encodage.

L'ajout incrémental est supporté par `faiss_manager.add_vectors(chunk_docs)`, invoqué à l'issue de l'ingestion d'un nouveau document, évitant ainsi un *rebuild* complet à chaque upload. En revanche, la suppression d'un document déclenche un *rebuild* complet, le format HNSW ne supportant pas la suppression sélective.

## 4.3 Fine-tuning du modèle d'embeddings

### 4.3.1 Préparation du dataset

Le script `backend/training/build_dataset.py` (≈ 250 lignes) génère le jeu d'entraînement à partir de la collection `article_versions` filtrée sur les articles en vigueur (`is_current = true`). Pour chaque article, il invoque le service `llm_service.generate_questions` qui sollicite le modèle `qwen2.5:7b` pour formuler trois à cinq questions juridiques en langage naturel auxquelles l'article apporte une réponse. Les questions sont produites en français pour les articles français et en arabe pour les articles arabes ; une fraction (≈ 15 %) est traduite vers la langue opposée pour créer des paires translingues.

Les **négatifs *hard*** sont sélectionnés par *mining* : pour chaque paire `(question, article_positif)`, on exécute une recherche FAISS avec le modèle de base et on retient les trois articles les plus proches qui ne sont pas le positif et dont la similarité dépasse 0,55. Cette stratégie expose le modèle aux confusions sémantiques typiques (par exemple, congé annuel vs congé maladie, sanction administrative vs sanction pénale).

Le dataset final est exporté en deux fichiers JSONL : `train.jsonl` (90 %) et `eval.jsonl` (10 %), chaque ligne contenant un objet `{"anchor": "...", "positive": "...", "negatives": ["...", "...", "..."]}`.

### 4.3.2 Conduite de l'entraînement

Le script `backend/training/train_embeddings.py` (≈ 180 lignes) utilise la bibliothèque `sentence-transformers` pour conduire le *fine-tuning*. Le code charge le modèle de base, prépare un `DataLoader` PyTorch sur les paires positives, instancie la `MultipleNegativesRankingLoss` (qui consomme implicitement les autres positifs du *batch* comme négatifs supplémentaires), et lance `model.fit` avec les hyperparamètres définis en section 3.5.3.

L'entraînement complet a duré environ 45 minutes sur la RTX 3060, sur trois *epochs* avec un *batch* de 32. Les checkpoints sont sauvegardés à la fin de chaque *epoch* dans le répertoire `training/models/daleel-embedding-finetuned/checkpoint-{step}/`, et le meilleur checkpoint (selon la perte sur le jeu d'évaluation) est promu en modèle principal sous `training/models/daleel-embedding-finetuned/`.

### 4.3.3 Mise en service du modèle *fine-tuné*

Le service `embedding_service.py` charge le modèle à la demande via `_get_model()`, qui résout d'abord le chemin local par la fonction `_resolve_model_name_or_path`. Cette fonction teste successivement le chemin tel que fourni, puis sa résolution relative à la racine du projet et au répertoire `backend/`, permettant d'utiliser indifféremment des identifiants Hugging Face Hub (modèle de base) ou des chemins locaux (modèle *fine-tuné*).

Le passage en production se fait en modifiant la variable d'environnement `DALEEL_EMBEDDING_MODEL` vers `./training/models/daleel-embedding-finetuned`. Au prochain démarrage, le service d'embeddings charge le modèle local, le service de cohérence détecte l'écart de dimension (en réalité identique, 768), valide l'index existant si le nom de modèle correspond aux métadonnées sauvegardées, ou déclenche un ré-encodage complet le cas échéant.

Le code source du fine-tuning et le script d'évaluation sont versionnés dans le dépôt, garantissant la reproductibilité totale du résultat documenté en section 5.4.1.

## 4.4 Implémentation du pipeline RAG à six modules

### 4.4.1 Service de recherche hybride

Le service `backend/app/services/search_service.py` expose la fonction `semantic_search(db, query, top_k, ...)`. Son implémentation encode d'abord la requête avec le modèle d'embeddings *fine-tuné* (à la dimension effective de l'index), puis interroge l'index FAISS ; un repli sur une recherche cosinus en Python est prévu si l'index FAISS est temporairement indisponible :

```python
async def semantic_search(db, query, top_k=10, language_filter=None,
                          document_id=None, organization_id=None, ...):
    stored_dim = await get_effective_query_embedding_dimension()
    query_vec = await embed_text_for_search_async(query, stored_dim)
    if _use_faiss():
        await faiss_manager.ensure_ready()
        results = await faiss_manager.search(
            query_vec, top_k, language_filter, document_id)
        if results:
            return _apply_tenant_filters(results, organization_id)
    return await _python_search(query_vec, top_k, language_filter, document_id)
```

La **fusion des signaux lexicaux** n'intervient pas dans cette première étape de récupération, mais lors du reclassement (`_rerank`, dans `llm_service.py`), qui applique la fonction de fusion pondérée de l'équation (3.1) : pour chaque *chunk* candidat, le score final agrège le score vectoriel, le recouvrement lexical de tokens, un score de mots-clés et le recouvrement de tokens d'ancrage, augmentés de bonus (phrase exacte, référence d'article) et minorés de pénalités de portée. Le résultat est trié par score décroissant avant transmission au cross-encoder.

### 4.4.2 Reranking par cross-encoder

Le `RerankingService` (`backend/app/services/reranker.py`) charge le modèle `cross-encoder/ms-marco-MiniLM-L-6-v2` à la première utilisation via un `asyncio.Lock` empêchant les chargements concurrents. La méthode `rerank(query, chunks)` produit pour chaque chunk un score MS-MARCO et trie par score décroissant ; les *chunks* dont le score est inférieur à `MIN_RERANK_SCORE = -2,0` sont filtrés. L'activation du *reranker* est contrôlée par la variable `DALEEL_ENABLE_CROSS_ENCODER` ou la variable d'environnement `ENABLE_CROSS_ENCODER`, permettant une bascule en production sans modification de configuration.

### 4.4.3 Routeur de domaine

Le module `backend/app/services/domain_router.py` parcourt cinq dictionnaires de mots-clés trilingues correspondant aux domaines prioritaires. Chaque domaine est associé à un *DomainConfig* contenant :

- `domain_name` : identifiant interne ;
- `top_k_override` : valeur de `top_k` adaptée au domaine (par exemple, 16 pour le droit du travail très volumineux) ;
- `preferred_language` : langue à privilégier dans les résultats ;
- `boost_collections` : poids supplémentaires accordés à certaines collections.

La fonction `route_domain(question)` produit un objet `DomainRoutingResult` que les services aval utilisent pour adapter leurs paramètres. En cas d'ambiguïté (deux domaines candidats avec scores proches), un appel LLM de classification est effectué si la variable `DALEEL_DOMAIN_ROUTER_LLM_FALLBACK_ENABLED` est vraie.

### 4.4.4 Orchestrateur de retrieval partitionné

Le service `backend/app/services/legal_retrieval_orchestrator.py` matérialise la conception présentée en section 3.3.4. La fonction `classify_legal_intent(question, lang)` calcule un score par catégorie en additionnant les occurrences de mots-clés trilingues, retournant la catégorie de plus haut score (avec `current_rule_query` comme repli). La fonction `intent_to_mix(intent, domain_config)` traduit l'intention en une liste de `RetrievalMix` selon le tableau 3.3.

La fonction `retrieve_partitioned(question, intent, search_fn, db, ...)` exécute les recherches partition par partition à l'aide d'`asyncio.gather`, applique le filtre `is_base_version` adapté à chaque partition, déduplique par identifiant ou *hash* de texte, puis calcule le score de fusion pondéré selon la formule (3.2) et tronque à `top_k = 14` par défaut.

L'activation globale du mode partitionné est contrôlée par `DALEEL_PARTITIONED_RETRIEVAL_ENABLED`. En production, ce mode est activé pour les domaines à forte volatilité réglementaire (droit du travail, fiscalité) et désactivé pour les domaines plus stables.

### 4.4.5 Résolveur de graphe de connaissances léger

Le service `backend/app/services/graph_resolver.py` expose `resolve_article_graph(db, article_id)` et `resolve_company_graph(db, profile_id)`. La fonction *article* récupère successivement la `Loi` parente, les `ArticleVersions` (avec marqueur `is_current`), les `Exigences` rattachées, les `Actions` issues des exigences, et les `ActionCriticalities`. Le résultat est emballé dans un dataclass `ArticleGraph` exposant ces collections.

La fonction *company* est plus ambitieuse : elle joint `company_profiles` à `exigence_applicabilities` pour reconstituer la liste des exigences applicables, puis aux actions associées, en limitant à `kg_light_max_entities = 6` par profil pour préserver la fenêtre de contexte LLM.

### 4.4.6 Garde-qualité en production

Le service `backend/app/services/quality_guard_service.py` est exposé par la fonction `audit_and_guard(question, answer, chunks, lang, enabled)`. Lorsqu'activé (variable `DALEEL_QUALITY_GUARD_ENABLED`), il exécute successivement :

1. `_verify_quotes_against_chunks` : extraction des citations entre guillemets typographiques, recherche par fenêtre glissante de 4 à 8 mots dans le texte concaténé des *chunks*, remplacement par `[citation non vérifiée]` en cas d'échec ;
2. `_extract_refs` + comparaison avec `_supported_refs` pour les références d'articles et de lois ;
3. `_verify_article_content_match` pour la cohérence sémantique article ↔ description ;
4. Construction du verdict final (`accepted` / `rewritten` / `rejected`) et du dictionnaire d'incidents.

Le verdict est exposé dans l'API sous les champs `quality_guard_status` et `quality_guard_issues`, et un *flag* `quality_guard_semantic_check_enabled` permet d'activer une couche supplémentaire de vérification sémantique par LLM-juge dans les déploiements où l'overhead est acceptable.

## 4.5 Implémentation de l'agent autonome ReAct

L'agent est implémenté dans `backend/app/services/autonomous_agent.py` (≈ 1 100 lignes). Cette section décrit les choix d'implémentation notables.

### 4.5.1 Construction du contexte initial

Le constructeur `_AutonomousAgent.__init__` prépare les douze `ToolDefinition` au démarrage de l'agent et les indexe par nom dans `self._tool_map`. La méthode `run(question, ...)` commence par :

1. Détecter le *derja* tunisien via `normalize_if_derja` et, le cas échéant, basculer la pipeline en français ;
2. Détecter la langue de la question via `detect_query_language` ;
3. Sélectionner le *system prompt* correspondant dans le dictionnaire `_SYSTEM_PROMPTS` (français, arabe, anglais) ;
4. Injecter un exemple *few-shot* trilingue tiré de `_FEW_SHOT_EXAMPLES` ;
5. Ajouter jusqu'à 20 messages d'historique de conversation ;
6. Annoter la question d'un rappel de langue explicite.

Les *system prompts* trilingues définissent le comportement de l'assistant en cinq étapes (« Écouter et comprendre », « Diagnostiquer », « Proposer des solutions », « Accompagner », « Relancer »), un comportement interactif proactif, des règles de rigueur strictes interdisant l'invention d'articles, un format de réponse en quatre blocs (Diagnostic / Ce que dit la loi / Risques et conséquences / Actions à prendre), et un plafond de 400 mots. La température est fixée à 0,15 pour minimiser la variabilité tout en préservant une certaine fluidité.

### 4.5.2 Boucle d'exécution avec budget

La boucle principale `for iteration in range(1, self._max_iterations + 1)` orchestre les itérations. À chaque tour :

- Le temps total écoulé est mesuré et comparé à `self._total_timeout` ; si dépassement, la boucle se termine avec la réponse partielle accumulée ;
- `_call_ollama_with_tools` envoie la requête à Ollama avec retry exponentiel (`max_retries = 3`, *backoff* de 1 s × 2ⁿ plafonné à 16 s) sur les erreurs réseau (`ReadTimeout`, `ConnectTimeout`, `RemoteProtocolError`, *5xx*) ;
- Si la réponse ne contient pas de `tool_calls`, le contenu est considéré comme la réponse finale ;
- Sinon, chaque `tool_call` est exécuté avec un *timeout* individuel `tool_timeout`, son résultat est tronqué à `_MAX_RESULT_CHARS = 4 000` caractères et injecté comme message `tool` dans l'historique.

À la sortie de la boucle (sans `break`), un message forçant la production de la réponse finale sans nouvel appel d'outil est envoyé.

### 4.5.3 Catalogue effectif des outils

L'implémentation des douze outils est concentrée dans la méthode `_build_tools()`. Chaque outil dispose d'un *handler* asynchrone exécuté avec un *timeout*, et son schéma JSON est exposé selon le format `function calling` d'Ollama. Le **contrôle d'accès multi-tenant** est appliqué uniformément : pour tous les outils touchant un profil d'entreprise, une fonction `ensure_profile_access(profile_id)` vérifie que le profil appartient bien à l'organisation courante (`organization_id`), refusant l'accès sinon.

Les outils du *tier* « Compliance » (`get_applicability`, `get_criticality`, `compute_compliance`, `generate_roadmap`) délèguent leur logique métier aux services dédiés présentés au chapitre 5. Cette séparation permet d'utiliser les mêmes services depuis l'agent ou depuis les endpoints REST directs.

### 4.5.4 Traçabilité et journal d'audit

Chaque outil exécuté produit un `ToolCallRecord(iteration, tool_name, arguments, result_summary, duration_ms, error)` ajouté à `tool_log`. À la fin de la boucle, ce journal est sérialisé dans le champ `tool_calls_log` de la réponse, accessible à l'utilisateur :

```json
{
  "tool_calls_log": [
    {"iteration": 1, "tool_name": "semantic_search",
     "arguments": {"query": "période d'essai CDI"},
     "result_summary": "[{\"text\": \"Article 6...\", ...}]",
     "duration_ms": 187.42, "error": null},
    {"iteration": 2, "tool_name": "get_article_graph",
     "arguments": {"article_id": "..."},
     "result_summary": "{\"exigences\": [...], ...}",
     "duration_ms": 64.18, "error": null}
  ],
  "total_iterations": 3,
  "reasoning_steps": ["iteration_1:tool=semantic_search",
                     "iteration_2:tool=get_article_graph",
                     "iteration_3:final"]
}
```

Cette transparence permet au juriste utilisateur de comprendre quelles sources ont été consultées et dans quel ordre, ce qui est indispensable dans un contexte où la défense d'un avis juridique repose sur la traçabilité du raisonnement.

### 4.5.5 Post-traitement et garde-fous

À la sortie de la boucle, trois étapes de post-traitement sont appliquées séquentiellement :

1. **`_enforce_output_format(answer, lang)`** : retire les sections de remplissage (« Conclusion », « En résumé », phrases du type « Il est important de noter que… »), tronque à 400 mots, supprime les répétitions inter-sections via détection de phrases dupliquées ;
2. **Vérification de langue** : si `_answer_matches_language` retourne `False`, un appel de traduction est émis. Le traducteur est instruit de préserver la structure et le formatage tout en remplaçant intégralement le texte. Une seule tentative est effectuée pour éviter les boucles ;
3. **Garde-qualité** : `audit_and_guard` est appelée avec les sources cumulées et son verdict est intégré dans la réponse.

## 4.6 Démonstrations qualitatives

Cette section illustre le comportement du système sur trois requêtes représentatives, en exposant les artefacts produits par le pipeline.

### 4.6.1 Démonstration 1 — Requête simple, pipeline RAG classique

**Question utilisateur (français)** : « Quelle est la durée maximale de la période d'essai pour un CDI en Tunisie ? »

**Flux exécuté** :
1. Détection de langue : `fr` ;
2. Classification d'intention : `current_rule_query` → mode partitionné `current_state` (70 % amendement, 30 % base) ;
3. Encodage de la question (768 d, cache hit possible si question répétée) ;
4. Recherche vectorielle FAISS HNSW, récupération de `4 × top_k` candidats ;
5. Reclassement par fusion pondérée (score vectoriel + recouvrement lexical + mots-clés + ancrage), 12 candidats retenus ;
6. Reranking cross-encoder, top 6 retenus, scores MS-MARCO entre 5,2 et 7,8 ;
7. KG Light : sous-graphe de l'article 6-3 (nouveau) du Code du Travail, modifié par la loi n° 2025-9 du 21 mai 2025 [38], avec les exigences associées ;
8. Génération qwen2.5:7b, température 0,15, ~ 380 tokens ;
9. Garde-qualité : 1 référence citée (`article 6-3 nouveau`), supportée par `[Source 1]` ; aucune citation entre guillemets ; verdict `accepted`.

**Réponse produite** (format attendu) :

> **Diagnostic.** Vous souhaitez connaître la durée légale maximale de la période d'essai pour un contrat à durée indéterminée (CDI) en Tunisie.
>
> **Ce que dit la loi.**
> - L'article 6-3 (nouveau) du Code du Travail, modifié par la loi n° 2025-9 du 21 mai 2025, prévoit qu'un CDI peut contenir une période d'essai ne dépassant pas **six mois** [Source 1].
> - Cette période d'essai peut être renouvelée **une seule fois**, pour la même durée au maximum [Source 1].
> - Chaque partie peut y mettre fin avant son échéance, sous réserve d'en informer l'autre partie par tout moyen laissant une trace écrite, quinze jours avant la fin de la période d'essai [Source 1].
>
> **Risques et conséquences.** Une période d'essai dépassant ce plafond, ou renouvelée plus d'une fois, expose l'employeur à une contestation de la clause et à l'application du régime protecteur du droit commun du travail. En cas de litige, le conseil prud'homal vérifie notamment la durée prévue au contrat, le renouvellement et la preuve de la notification écrite.
>
> **Actions à prendre.**
> 1. Mentionner explicitement dans le contrat une période d'essai ne dépassant pas six mois ;
> 2. Limiter le renouvellement à une seule fois, pour une durée identique ou inférieure ;
> 3. Formaliser toute rupture ou fin de période d'essai par un écrit traçable, quinze jours avant l'expiration.

![Capture d'écran de la réponse RAG dans le chatbot Daleel, avec sources cliquables et badge garde-qualité](captures/fig_4_1_chat_reponse.png)

**Figure 4.1 — Réponse du pipeline RAG classique dans le chatbot, avec sources numérotées et badge de validation qualité.**

### 4.6.2 Démonstration 2 — Requête multilingue avec agent autonome ReAct

**Question utilisateur (mixte fr/ar)** : « Ma société de 25 salariés traite des données clients sensibles. Quelles obligations RGPD et INPDP s'appliquent ? Donne-moi un plan d'action priorisé. »

**Flux exécuté par l'agent autonome** :

| Itération | Outil appelé | Arguments | Résultat (résumé) |
|---|---|---|---|
| 1 | `semantic_search` | `query="protection données personnelles entreprise INPDP"` | 5 chunks : loi 2004-63, décret 2007-3003, … |
| 2 | `lookup_law` | `code="LP63"` | Métadonnées de la loi 2004-63, 56 articles |
| 3 | `match_exigences` | `query="traitement données clients entreprise 25 salariés", exigence_type="obligation"` | 12 exigences (déclaration INPDP, DPO, registre, etc.) |
| 4 | `get_applicability` | `profile_id="..."` | 28 exigences applicables, 9 obligations critiques |
| 5 | `get_criticality` | `profile_id="..."` | 7 critiques, 14 importantes, 7 secondaires |
| 6 | `generate_roadmap` | `profile_id="..."` | Plan de 10 actions ordonnées avec dépendances |

**Itération 7 — réponse finale** : synthèse en français listant les 5 actions prioritaires identifiées par le *roadmap_service* (déclaration INPDP, nomination DPO, mise à jour du registre des traitements, mise en place des procédures de droits d'accès, signature des accords de sous-traitance), citant les articles 4 et 7 de la loi 2004-63 et l'article 14 du décret 2007-3003. La garde-qualité valide toutes les références citées.

La réponse API expose une trace d'exécution (`reasoning_steps`) permettant d'auditer le comportement agentique : intention détectée, routage, sélection du corpus, tentative de récupération, acceptation des *chunks*, temps de traitement et mode sélectionné.

![Capture d'écran de la trace d'exécution agentique dans la réponse API, avec étapes de raisonnement, routage, tentative de récupération, temps de traitement et mode sélectionné](captures/fig_4_2_agent_tool_log.png)

**Figure 4.2 — Trace d'exécution de l'agent en mode agentique : étapes de raisonnement, tentative de récupération, décision de routage, temps de traitement et mode sélectionné.**

### 4.6.3 Démonstration 3 — Requête en *derja* tunisien

**Question utilisateur (derja)** : « نحب نفسخ عقد عاملة بدون ما نخلصها ؟ »

**Flux exécuté** :

1. Détection : `_normalize_if_derja` identifie une expression dialectale (mélange d'arabe standard et de tunisien). Conversion vers le français standard : « Je veux résilier le contrat d'une employée sans la payer ? » ;
2. Bascule du pipeline en français, conservation de la trace d'origine dans `derja_original` ;
3. Le système prompt français est activé ;
4. L'agent identifie une question potentiellement problématique : il invoque `semantic_search` sur « licenciement abusif Code du Travail Tunisie » et `match_exigences` sur les sanctions liées au non-paiement du salaire ;
5. La réponse en français rappelle l'obligation de paiement des salaires dus, qualifie le licenciement sans cause réelle et sérieuse, cite les articles 14 et suivants du Code du Travail et alerte sur les sanctions pécuniaires (indemnités à hauteur du préavis, dommages-intérêts) ;
6. Le champ `derja_detected = true` est retourné, ainsi que `derja_original` pour transparence ; l'utilisateur peut voir que sa question a été reformulée.

Cette démonstration illustre la capacité du système à ingérer une requête dialectale, à la normaliser sans en altérer le sens, et à fournir une réponse juridique structurée en français, langue de référence des textes pertinents.

![Capture d'écran de la détection de derja avec affichage de la question originale et de sa reformulation](captures/fig_4_3_derja.png)

**Figure 4.3 — Détection et normalisation d'une requête en derja tunisien, avec affichage transparent de la reformulation.**

## Conclusion

Ce chapitre a documenté la réalisation effective du volet *Legal RAG* de la plateforme Daleel. L'environnement de développement, fondé sur Python 3.12, FastAPI, MongoDB 7.0 et Ollama, a été choisi pour combiner asynchronisme natif, schéma flexible et déploiement local. Le pipeline d'ingestion documentaire à cinq étapes a été implémenté avec une cascade d'extraction PyMuPDF / pdfminer.six / Tesseract+EasyOCR, un nettoyage arabe en onze sous-étapes, une segmentation hiérarchique bilingue et une indexation FAISS HNSW avec contrôle de cohérence d'index. Le *fine-tuning* du modèle d'embeddings, conduit sur GPU à partir d'un dataset de paires question/article enrichi de négatifs *hard*, a produit le modèle `daleel-embedding-finetuned` dont les gains de performance seront détaillés au chapitre 5. Le pipeline RAG à six modules (recherche hybride, reranking, routage de domaine, retrieval partitionné, KG Light, garde-qualité) a été implémenté de façon modulaire avec activation indépendante par configuration. Enfin, l'agent autonome ReAct, doté de douze outils, exploite l'appel d'outils natif d'Ollama dans une boucle bornée par un budget d'itérations et un *timeout* total, avec traçabilité complète des appels et trois étapes de post-traitement (format, langue, qualité). Les démonstrations qualitatives présentées illustrent le comportement effectif du système sur des requêtes représentatives du corpus juridique tunisien, en français, en arabe et en *derja*. Le chapitre suivant aborde la réalisation du volet *Compliance Operations*, les interfaces utilisateur, l'évaluation quantitative des performances et le déploiement en production.

---

# Chapitre 5 — Compliance Operations, évaluation et déploiement

## Introduction

Ce dernier chapitre couvre **les phases 5 (*évaluation*) et 6 (*déploiement*) du cycle CRISP-DM**, après une dernière itération de la phase 4 (*modélisation*) dédiée au volet *Compliance Operations*. Il traite d'abord la moitié opérationnelle de la plateforme Daleel — le volet *Compliance Operations*, qui transforme l'assistant juridique en un véritable système de pilotage du cycle de conformité — puis décrit l'implémentation des interfaces utilisateur livrées (phase déploiement), conduit l'évaluation quantitative rigoureuse des composants clés (retrieval, fine-tuning, agent, garde-qualité), formalise le déploiement conteneurisé et la chaîne d'intégration continue, et se conclut par une discussion critique des limites identifiées et des perspectives d'évolution — éléments qui alimenteront un nouveau cycle CRISP-DM dans les itérations futures.

## 5.1 Implémentation du cycle de conformité

### 5.1.1 Services métier

Le volet *Compliance Operations* est porté par dix services métier interconnectés, exposés au travers de quatre routeurs FastAPI (`case_router`, `case_conversation_router`, `case_orchestrator_router`, `compliance_router`) totalisant plus de 50 endpoints.

**Tableau 5.1 — Services métier du volet Compliance Operations.**

| Service | Rôle |
|---|---|
| `case_service` | CRUD des dossiers de conformité, constats et actions |
| `case_conversation_service` | Conversation pilotée par LLM dans un dossier, extraction de faits |
| `case_document_service` | Upload et analyse de documents joints aux cas |
| `compliance_case_orchestrator` | Orchestration ASK/CLARIFY/ACT/REVIEW du cycle |
| `compliance_service` | Calcul de la posture globale (score de couverture, écarts) |
| `applicability_service` | Détermination des exigences applicables à un profil |
| `action_service` | Gestion des actions correctives, extraction depuis articles |
| `criticality_service` | Scoring déterministe de la criticité des actions |
| `roadmap_service` | Génération du plan d'action priorisé avec dépendances |
| `audit_service` | Journalisation auditable de toutes les opérations sensibles |

### 5.1.2 Service de criticité — moteur déterministe

L'implémentation du moteur de criticité (`backend/app/services/criticality_service.py`) repose sur la fonction `compute_criticality_score(action, sanctions_context)`. Pour une action donnée, le score est calculé en :

1. Initialisant un score de base selon la modalité (`_BASE_SCORES` : sanction 0,85, interdiction 0,70, obligation 0,65, condition 0,35) ;
2. Concaténant le texte de l'action et son contexte de sanctions héritées ;
3. Recherchant les mots-clés de sanction (`_SANCTION_KW`) et appliquant un boost de +0,10 par occurrence (avec plafond) ;
4. Détectant les montants pécuniaires (`_AMOUNT_RE`) et appliquant +0,05 ;
5. Itérant sur `_DOMAIN_BOOSTS` (données personnelles +0,15, santé/sécurité +0,12, fiscal +0,08, travail clandestin +0,15) ;
6. Appliquant une pénalité de −0,15 si du langage conditionnel est détecté (`le cas échéant`, `éventuellement`, …) ;
7. Appliquant un boost hérité de +0,07 lorsque l'article parent porte une exigence de sanction séparée ;
8. Clampant le résultat dans [0, 1] et associant la classification : ≥ 0,75 critique, ≥ 0,50 importante, < 0,50 secondaire.

Chaque composante appliquée est ajoutée à la liste `reasons` retournée par la fonction, et persistée dans la collection `action_criticalities` au format :

```json
{
  "action_id": "...",
  "criticality_level": "critique",
  "criticality_score": 0.92,
  "criticality_reasons": [
    "Modalité 'obligation' (score de base 0.65)",
    "Domaine données personnelles (criticité renforcée, +0.15)",
    "Présence de mot-clé sanction 'amende' (+0.10)",
    "Présence d'un montant pécuniaire (+0.05)"
  ],
  "scored_at": "2026-05-12T14:23:11Z"
}
```

Cette transparence est essentielle pour la défense juridique de la posture de conformité : un auditeur peut vérifier, pour chaque action classée critique, pourquoi elle l'est et selon quelles règles.

### 5.1.3 Service de roadmap — ordonnancement par dépendances

Le service `roadmap_service.generate_roadmap(db, profile_id)` produit un plan d'action priorisé en combinant trois dimensions :

1. **Criticité** : tri primaire par score décroissant ;
2. **Dépendances** : utilisation des relations `action_dependencies` (graphe orienté acyclique) avec tri topologique pour respecter l'ordre causal des actions ;
3. **Effort estimé** : utilisation d'une heuristique simple basée sur la longueur du texte de l'action et le nombre d'exigences couvertes, projetée en jours/homme.

L'algorithme utilise un tri topologique de Kahn modifié : à chaque itération, parmi les actions sans dépendances non satisfaites, celle de plus forte criticité est sélectionnée. Le résultat est une liste ordonnée d'actions ; les dix premières sont exposées dans le tableau de bord prioritaire, le reste reste accessible par pagination.

### 5.1.4 Service d'applicabilité

Le service `applicability_service` matérialise la correspondance entre une exigence réglementaire (`exigence`) et un profil d'entreprise (`company_profile`). Un profil porte des attributs structurés : secteur d'activité, effectif, chiffre d'affaires, périmètre géographique (Tunisie, international), traite-t-il des données personnelles, opère-t-il un site classé, etc. La fonction `evaluate_applicability(exigence, profile)` retourne un objet `ExigenceApplicabilityOut` contenant un booléen `is_applicable`, un score de confiance, et une explication en langage naturel produite par le LLM. Le résultat est persisté dans la collection `exigence_applicabilities` pour éviter la réévaluation systématique.

## 5.2 Orchestrateur LLM ASK / CLARIFY / ACT / REVIEW

L'orchestrateur (`compliance_case_orchestrator.py`) constitue le cœur intelligent du volet opérationnel. Cette section décrit son implémentation effective.

### 5.2.1 Phases d'exécution

La méthode principale `orchestrate(case_id, ...)` séquence les sept phases présentées en section 3.7.2. Les implémentations notables :

- **Phase 1 — Collecte de contexte** : la fonction parcourt les `case_messages`, demande au LLM d'extraire un dictionnaire structuré des **faits connus** (par exemple `secteur=banque`, `effectif=120`, `traite_données_perso=oui`) et des **faits manquants** (par exemple `localisation_siège`, `volume_données_traitées`). Le LLM est invité à produire un objet JSON, vérifié par parsing strict.
- **Phase 4 — Génération de constats** : pour chaque exigence applicable et non couverte, le LLM est invité à produire un objet `FindingDraft(title, description, severity, confidence, exigence_id)`. Les *drafts* dont la confiance est inférieure à `MIN_CONFIDENCE_FOR_FINDING = 0,60` sont écartés ; ceux entre 0,60 et 0,85 sont conservés en statut `medium`, ceux au-dessus de 0,85 en statut `high`.
- **Phase 6 — Priorisation des actions** : appel au `roadmap_service` décrit en section 5.1.3.
- **Phase 7 — Mappage des preuves** : pour chaque action, le LLM est invité à analyser les documents attachés et à proposer les éléments factuels (passages, paragraphes, chiffres) susceptibles de prouver l'exécution de l'action.

### 5.2.2 Implémentation de la décision

À la fin de l'orchestration, la fonction `_compute_decision(context)` applique l'arbre suivant (extrait simplifié) :

```python
def _compute_decision(context: OrchestrationContext) -> OrchestratorDecision:
    if len(context.facts_missing) > MAX_MISSING_FACTS_TOLERANCE:
        return OrchestratorDecision.ASK
    if context.avg_confidence < 0.60:
        return OrchestratorDecision.ASK
    if context.document_contradictions:
        return OrchestratorDecision.CLARIFY
    if any(f.severity == "critical" and f.confidence < 0.70
           for f in context.findings_draft):
        return OrchestratorDecision.REVIEW
    if (len(context.facts_known) >= MIN_FACTS_FOR_ANALYSIS
            and context.avg_confidence >= MIN_CONFIDENCE_FOR_AUTO_ACT):
        return OrchestratorDecision.ACT
    return OrchestratorDecision.CLARIFY
```

Cette décision est exposée au frontend qui adapte son comportement :

- **ASK** → affichage d'un formulaire dynamique demandant les faits manquants ;
- **CLARIFY** → mise en évidence des contradictions et demande de désambiguïsation ;
- **ACT** → affichage des constats et plan d'action ; le cas peut être validé par l'utilisateur et transformé en plan engagé ;
- **REVIEW** → marqueur visuel indiquant qu'une revue humaine d'expert est recommandée avant action.

### 5.2.3 Audit logging systématique

Chaque opération sensible (création de cas, ajout de constat, modification d'action, décision orchestrateur) est journalisée dans la collection `audit_logs` via le service `audit_service`. Le format de chaque entrée :

```json
{
  "id": "<uuid>",
  "actor_id": "<user_id ou agent>",
  "organization_id": "<tenant>",
  "action": "case.finding.create",
  "subject_type": "case_finding",
  "subject_id": "<finding_id>",
  "metadata": {"case_id": "...", "severity": "high"},
  "created_at": "2026-05-12T14:23:11Z"
}
```

Cette traçabilité est exploitée par le tableau de bord d'audit accessible aux administrateurs et constitue une exigence usuelle des certifications (ISO 27001, SOC 2) auxquelles les clients de Daleel peuvent être soumis.

## 5.3 Interfaces utilisateur

Le frontend de Daleel est développé en **React 19 + Vite 8**, avec 34 composants répartis en 18 pages couvrant les espaces utilisateur final et administration.

### 5.3.1 Chatbot conversationnel

La page `frontend/src/pages/Chat.jsx` constitue l'interface principale pour les utilisateurs métier. Elle propose :

- Une zone de saisie multilingue (avec sélecteur `ar / fr / en`) supportant la transcription vocale via le module `VoiceAssistant` ;
- Un fil de conversation avec rendu différencié des messages utilisateur, des réponses RAG classiques et des réponses de l'agent autonome ;
- L'affichage des **sources cliquables** : chaque référence `[Source N]` est un lien ouvrant le passage exact du *chunk* dans un panneau latéral, avec mise en évidence ;
- L'affichage du **journal de raisonnement** pour les réponses de l'agent : liste des outils invoqués, durée, résumé du résultat ;
- L'affichage du statut **garde-qualité** : badge vert (`accepted`), orange (`rewritten` avec liste des incidents), rouge (`rejected`) ;
- Un bouton de **feedback** (👍/👎 + commentaire) qui crée une entrée dans la collection `qa_feedback`, exploitée pour l'amélioration continue.

L'upload de document directement dans la conversation déclenche le service `ask-with-document` qui extrait le texte du document via le pipeline d'ingestion réduit (étapes 1-2) et l'injecte comme contexte additionnel pour la réponse.

![Capture d'écran de l'interface du chatbot conversationnel Daleel](captures/fig_4_1_chatbot.png)

**Figure 5.1 — Interface du chatbot conversationnel multilingue.**

### 5.3.2 Panneau d'administration

Le répertoire `frontend/src/pages/admin/` contient 10 pages dédiées :

- **`Documents.jsx`** : upload, suivi de l'ingestion (statuts : *uploaded → extracted → cleaned → segmented → embedded → indexed*), prévisualisation des *chunks*, ré-encodage à la demande ;
- **`Amendments.jsx`** : visualisation des opérations d'amendement détectées, application manuelle ou automatique, comparaison avant/après ;
- **`Cases.jsx`** : tableau de bord des dossiers de conformité, filtrage par statut, sévérité et organisation, accès au cycle de vie complet ;
- **`Notifications.jsx`** : centre de notifications (alertes d'amendement, échéances d'actions, dépassements de SLA) ;
- **`Organizations.jsx`** : gestion multi-tenant, création d'organisations, invitations utilisateurs ;
- **`Users.jsx`** : gestion des utilisateurs et de leurs rôles ;
- **`CompanyProfile.jsx`** : profils d'entreprise pour l'évaluation d'applicabilité ;
- **`Settings.jsx`** : configuration de l'application (modèles, seuils, *feature flags*) ;
- **`ContractAnalysis.jsx`** : analyse de contrats par LLM (clauses, risques, recommandations) ;
- **`History.jsx`** : historique des opérations et audit.

![Capture d'écran du panneau d'administration : gestion documentaire et suivi de l'ingestion](captures/fig_4_2_admin_documents.png)

**Figure 5.2 — Panneau d'administration : gestion documentaire et suivi du pipeline d'ingestion.**

### 5.3.3 Tableau de bord BI

La page `frontend/src/pages/Dashboard.jsx` offre une vue synthétique de la posture de conformité, conçue pour une consultation rapide par un responsable conformité. Elle agrège :

- **Indicateurs clés** : score global de conformité, nombre de dossiers actifs, nombre de constats critiques ouverts, taux de respect des échéances ;
- **Graphiques temporels** : évolution de la couverture conformité sur 12 mois, courbe d'amendements traités, distribution des criticités ;
- **Heatmap** : matrice domaine × organisation indiquant la couverture, exploitée pour identifier les zones à risque ;
- **Top des actions critiques en retard** : tableau triable des actions dont l'échéance est dépassée, regroupées par dossier et par responsable.

Les données sont calculées en temps réel par le `compliance_service.compute_posture` et le `analytics_service`, exposées via les endpoints `/api/v1/analytics/*`.

![Capture d'écran du tableau de bord BI de la posture de conformité](captures/fig_4_3_dashboard.png)

**Figure 5.3 — Tableau de bord BI de la posture de conformité (indicateurs clés, graphiques temporels, heatmap).**

### 5.3.4 Internationalisation

Le frontend exploite **i18next** avec trois fichiers de traduction : `frontend/src/locales/ar.json`, `fr.json`, `en.json`. Les clés couvrent l'intégralité des libellés UI, les messages d'erreur, les notifications, et les libellés du panneau admin. La direction d'écriture RTL est automatiquement activée pour l'arabe via la propriété CSS `dir="rtl"` sur la racine, et la totalité de la mise en page (boutons, menus, listes) est conçue *bidi-aware*.

## 5.4 Évaluation quantitative

### 5.4.1 Évaluation du retrieval — avant et après fine-tuning

Le benchmark a été conduit via le script `backend/training/03_evaluate_retrieval.py` sur un jeu de **30 requêtes gold** (20 en français et 10 en arabe) construites par génération synthétique stratifiée à partir du corpus, chaque requête étant annotée de l'article de référence correspondant. Les requêtes ont été tirées d'un *bucket* (loi, langue) afin d'assurer une couverture proportionnelle des cinq codes principaux. Les métriques calculées sont :

- **Recall@k** : proportion de requêtes dont l'article de référence figure dans le top-k restitué par le modèle ;
- **MRR@k** (*Mean Reciprocal Rank*) : moyenne sur les requêtes de l'inverse du rang du premier article pertinent ;
- **nDCG@k** : gain cumulé décroissant normalisé prenant en compte la position relative des articles pertinents.

L'évaluation a été conduite sur un jeu de test régénéré après la réextraction OCR du sous-corpus arabe (cf. limite 7 en section 5.6.1) ; les chiffres présentés ci-dessous reflètent les performances mesurées sur un corpus d'évaluation propre, en arabe comme en français.

**Tableau 5.2 — Performance globale du modèle d'embeddings avant et après *fine-tuning* sur 30 requêtes gold (20 FR + 10 AR).**

| Métrique | Baseline (mpnet) | Fine-tuné v2 (Daleel) | Gain absolu | Gain relatif |
|---|---|---|---|---|
| Recall@1 | 0,33 | **0,47** | +0,13 | **+40 %** |
| Recall@5 | 0,53 | **0,70** | +0,17 | **+31 %** |
| Recall@10 | 0,70 | **0,73** | +0,03 | +5 % |
| MRR@10 | 0,42 | **0,57** | +0,14 | **+34 %** |
| nDCG@5 | 0,43 | **0,59** | +0,16 | **+37 %** |
| nDCG@10 | 0,49 | **0,61** | +0,12 | +24 % |

![Histogramme comparatif des métriques de retrieval avant et après fine-tuning](captures/fig_5_4_finetuning_resultats.png)

**Figure 5.4 — Comparaison des métriques de *retrieval* avant et après *fine-tuning* (histogramme groupé baseline vs Daleel).**

Le gain le plus marquant est observé sur Recall@1 (+40 %) et MRR@10 (+34 %), confirmant l'hypothèse que le *fine-tuning* améliore en priorité la précision sur les premières positions, c'est-à-dire la capacité du modèle à reconnaître l'article exactement pertinent parmi des candidats sémantiquement proches — un effet particulièrement précieux pour un usage RAG où le LLM se voit présenter un petit nombre de *chunks* en contexte. La légère diminution observée sur Recall@10 (−5 %) traduit un arbitrage classique du *fine-tuning* contrastif : en resserrant l'espace vectoriel autour des paires positives, le modèle privilégie la précision sur le top-k court au prix d'une marginalisation des résultats moins certains au-delà.

**Décomposition par langue.** L'agrégation globale masque toutefois une asymétrie importante entre les performances françaises et arabes, dont l'origine est documentée en limite 7 (section 5.6.1) : le *fine-tuning* a été conduit sur un corpus arabe initialement contaminé par des artefacts d'extraction PDF, ce qui en limite mécaniquement le bénéfice sur les requêtes arabes propres du jeu de test régénéré après OCR.

**Tableau 5.3 — Décomposition par langue des métriques de retrieval avant et après *fine-tuning*.**

| Langue | Métrique | Baseline | Fine-tuné v2 | Gain |
|---|---|---|---|---|
| Français (20 requêtes) | Recall@1 | 0,40 | **0,60** | **+50 %** |
| Français | Recall@5 | 0,60 | **0,75** | +25 % |
| Français | Recall@10 | 0,70 | **0,80** | +14 % |
| Français | MRR@10 | 0,48 | **0,68** | **+43 %** |
| Français | nDCG@10 | 0,53 | **0,71** | +34 % |
| Arabe (10 requêtes) | Recall@1 | 0,20 | 0,20 | 0 % |
| Arabe | Recall@5 | 0,40 | **0,60** | **+50 %** |
| Arabe | Recall@10 | 0,70 | 0,60 | −14 % |
| Arabe | MRR@10 | 0,31 | 0,33 | +6 % |
| Arabe | nDCG@10 | 0,40 | 0,39 | −2 % |

Sur les **requêtes francophones**, le *fine-tuning* produit des gains substantiels et cohérents sur l'ensemble des métriques (+50 % Recall@1, +43 % MRR@10, +34 % nDCG@10), confirmant la pertinence de la méthodologie sur le sous-corpus où les données d'entraînement étaient propres. Sur les **requêtes arabes**, le Recall@5 arabe progresse de 50 % (de 0,40 à 0,60), ce qui confirme que le corpus OCR propre améliore significativement la couverture de la recherche arabe. Le Recall@1 reste stable (0,20) et le Recall@10 recule légèrement (−14 %). Ce résultat est attribuable au corpus d'entraînement arabe contaminé par les artefacts d'extraction des PDF officiels (cf. limite 7) : un re-*fine-tuning* sur le corpus arabe propre issu de la réextraction OCR constitue une perspective immédiate dont les gains attendus s'alignent sur ceux observés en français.

### 5.4.2 Analyse qualitative de l'apport de chaque module RAG

L'architecture modulaire du pipeline RAG (section 3.3) permet d'activer ou désactiver indépendamment chaque module via configuration. L'observation du comportement du système lors des démonstrations qualitatives (section 4.6) et des tests de développement permet d'identifier l'apport qualitatif de chaque couche :

- **Recherche hybride (signaux vectoriels et lexicaux)** : la fusion pondérée améliore de manière observable la pertinence des résultats par rapport à la recherche vectorielle seule, en particulier pour les requêtes contenant des références précises (« article 91 », « loi n° 2004-63 ») que le score de recouvrement lexical capture par correspondance exacte alors que la recherche dense seule les manque fréquemment.
- **Reranking par cross-encoder** : son apport est le plus visible sur les requêtes ambiguës où plusieurs articles abordent des thèmes proches (par exemple, congé annuel vs congé maladie). Le seuil de rejet à −2,0 filtre efficacement les *chunks* non pertinents qui avaient été récupérés par similarité de surface.
- **Routeur de domaine** : en orientant la recherche vers les collections spécifiques au domaine détecté, il réduit le bruit de fond et améliore la cohérence des réponses mono-domaine. Son impact est moindre sur les requêtes transversales.
- **Retrieval partitionné** : son apport est qualitatif plutôt que quantitatif — il améliore la cohérence des réponses sur les sujets affectés par des amendements en évitant le mélange de versions contradictoires du même article.
- **KG Light (graphe de connaissances)** : l'enrichissement contextuel par le sous-graphe (exigences, actions, criticités liées à un article) permet au LLM de produire des réponses plus opérationnelles, en particulier lorsque le volet *Compliance Operations* est mobilisé.
- **Garde-qualité** : elle n'améliore pas la pertinence de la recherche (elle intervient après la génération) mais réduit de manière observable la fréquence des hallucinations (citations fabriquées, références inventées), comme analysé en section 5.4.4.

Aucune étude d'ablation quantitative systématique n'est revendiquée dans cette version. Les observations ci-dessus relèvent d'une analyse qualitative issue des démonstrations, des tests d'intégration et des traces de développement. Une ablation formelle, mesurant l'impact isolé de chaque module sur le MRR@10 du jeu de 30 requêtes gold, constitue une perspective immédiate pour consolider ces constats par des indicateurs publiables.

### 5.4.3 Évaluation de l'agent autonome ReAct

L'évaluation de l'agent autonome ne peut pas reposer sur les mêmes métriques de *retrieval* puisque l'agent gère le retrieval lui-même. L'observation du comportement de l'agent sur les démonstrations du chapitre 4 (section 4.6) et sur les tests d'intégration permet de caractériser les propriétés suivantes :

- **Comportement de recherche** : l'agent invoque systématiquement l'outil `semantic_search` comme première action, ce qui correspond au comportement attendu pour un assistant juridique. Les outils de conformité (`get_applicability`, `get_criticality`, `compute_compliance`, `generate_roadmap`) ne sont invoqués que lorsqu'un profil d'entreprise est explicitement disponible dans le contexte.
- **Profondeur de raisonnement** : sur les requêtes simples (recherche d'un article spécifique), l'agent converge en 1 à 2 itérations. Sur les requêtes complexes nécessitant un croisement de sources (par exemple, « quels sont mes droits en cas de licenciement si je suis en CDD avec une clause de non-concurrence ? »), l'agent mobilise typiquement 3 à 5 itérations en enchaînant recherche sémantique, consultation d'articles spécifiques et enrichissement par le graphe de connaissances.
- **Garde-fous** : le budget d'itérations et le *timeout* global empêchent les boucles infinies ; le journal de raisonnement (`tool_calls_log`) expose chaque décision de l'agent à l'utilisateur, garantissant la transparence du raisonnement.
- **Latence** : la latence est principalement dominée par le temps d'inférence Ollama (modèle `qwen2.5:7b` en local), multiplié par le nombre d'itérations. Sur la station de développement, la latence médiane observée se situe entre 8 et 15 secondes pour les requêtes nécessitant 2 à 4 itérations, et peut atteindre 20 à 25 secondes pour les requêtes complexes à 5+ itérations.

Un protocole de benchmark systématique de l'agent sur le jeu de 30 requêtes gold, mesurant le taux de réussite (garde-qualité + revue humaine), le nombre d'itérations et la couverture des outils, constitue une perspective de travail à conduire pour formaliser ces observations.

### 5.4.4 Évaluation de la garde-qualité

L'apport de la garde-qualité multi-couches (section 3.6) a été évalué qualitativement en comparant les réponses produites avec et sans garde-qualité activée sur un échantillon de requêtes représentatives. La garde-qualité opère en quatre couches successives : vérification des références citées contre le contenu réel des *chunks*, détection de citations fabriquées par fenêtre glissante, contrôle de la cohérence du contenu d'article, et conformité linguistique.

L'observation du comportement en production révèle trois effets principaux :

- **Neutralisation des citations fabriquées** : sans garde-qualité, le LLM produit occasionnellement des citations entre guillemets qui ne correspondent à aucun passage réel des *chunks* récupérés — un phénomène classique de « paraphrase hallucinée » où le modèle invente une formulation crédible. La couche 2 (fenêtre glissante) détecte ces citations en mesurant la similarité sous-chaîne entre le texte cité et les *chunks* source, et les supprime ou les remplace par une reformulation fidèle.
- **Détection des références inventées** : sans garde-qualité, le modèle peut citer un numéro d'article inexistant ou une loi n'apparaissant pas dans le corpus indexé. La couche 1 croise chaque référence légale détectée dans la réponse avec les identifiants présents dans les *chunks* et signale les références non vérifiables.
- **Conformité linguistique** : la couche 4 vérifie que la réponse est rédigée dans la langue détectée de la requête et déclenche une correction si nécessaire, évitant les réponses mixtes arabe/français ou les basculements intempestifs vers l'anglais.

Dans cette version, l'évaluation de la garde-qualité reste volontairement qualitative : elle démontre le rôle fonctionnel des quatre couches et documente les types d'erreurs interceptées, sans revendiquer de pourcentages de réduction. Un protocole de quantification formel — annotation manuelle d'un jeu de N réponses, avec et sans garde-qualité, sur les dimensions « citations fabriquées » et « références inventées » — constitue une perspective à conduire pour produire des indicateurs chiffrés publiables.

### 5.4.5 Couverture de tests et qualité logicielle

La suite de tests compte **55 fichiers `test_*.py`** dans le répertoire `backend/tests/`, couvrant l'ensemble des services métier et des modules de traitement. Les tests incluent des fixtures `conftest.py` partagées (instance MongoDB de test, base nettoyée entre tests), des doubles de test pour les services externes (Ollama mock par défaut), et des tests d'intégration de bout en bout simulant un upload, une ingestion, une recherche et une question-réponse complète.

**Tableau 5.4 — Couverture des tests par couche.**

| Couche | Fichiers de test | Exemples notables |
|---|---|---|
| Processing | 4 | `test_chunker.py`, `test_article_segmenter.py`, `test_derja_normalizer.py`, `test_text_utils.py` |
| Services Legal RAG | 20 | `test_faiss_index.py`, `test_legal_retrieval_orchestrator.py`, `test_search_service.py`, `test_reranker.py`, `test_quality_guard_service.py`, `test_embedding_cache.py`, `test_finetuned_models.py`, `test_domain_router.py`, `test_graph_resolver.py`, `test_llm_grounding_validation.py` |
| Services Compliance | 10 | `test_compliance_service.py`, `test_compliance_case_orchestrator.py`, `test_case_service.py`, `test_criticality_service.py`, `test_action_service.py`, `test_roadmap_service.py`, `test_contract_analysis_service.py` |
| API et auth | 9 | `test_api.py`, `test_auth.py`, `test_auth_service_pure.py`, `test_config_validation.py`, `test_voice_router.py` |
| Intégration | 2 | `test_integration_sprint6.py`, `test_conversation_workflow.py` |
| Autres | 10 | `test_audit_service.py`, `test_export_service.py`, `test_notification_service.py`, `test_email_service.py`, `test_analytics_service.py`, etc. |

Le linter Ruff est exécuté à chaque *push* et le projet maintient une politique « zéro avertissement ». Les pratiques notables incluent : annotations de types complètes (`from __future__ import annotations`), gestion exhaustive des erreurs (chaque appel externe est encapsulé dans un `try/except` typé), utilisation systématique de `asyncio.gather` pour la concurrence intra-service, et journalisation structurée.

## 5.5 Déploiement et intégration continue

### 5.5.1 Architecture de déploiement conteneurisée

La plateforme est entièrement déployable via **Docker Compose**, orchestrant trois services interconnectés sur un hôte unique : la base **MongoDB 7.0** (persistance documentaire et métadonnées du corpus), le moteur d'inférence **Ollama** servant le modèle `qwen2.5:7b` (LLM central), et l'**API FastAPI/Uvicorn** (couche applicative et exposition des endpoints REST). L'image FastAPI est construite selon un schéma *multi-stage* : une étape *builder* sur `python:3.12` assemble les *wheels* de toutes les dépendances Python, puis une étape *runtime* sur `python:3.12-slim` n'embarque que les binaires nécessaires — l'interpréteur Python, Tesseract OCR avec les paquets de langues `ara`, `fra`, `eng`, et `poppler-utils` pour la conversion PDF → image. Cette stratégie ramène la taille finale de l'image applicative d'environ 1,8 Go (image *builder* avant tri) à environ 850 Mo (image *runtime*), facilitant la diffusion et le redéploiement.

La figure 5.5 résume l'architecture de déploiement et les dépendances de démarrage entre les trois services.

![Schéma de déploiement Docker Compose de la plateforme Daleel](captures/fig_5_5_deploiement.png)

**Figure 5.5 — Schéma de déploiement Docker Compose de la plateforme Daleel.** *(source Mermaid : `docs/diagrams/architecture_globale.md`)*

Trois propriétés opérationnelles structurent ce déploiement. D'abord, chaque service expose un *health check* HTTP scruté toutes les 30 secondes : l'API FastAPI ne démarre effectivement qu'après réception d'un statut `healthy` de la part de MongoDB et d'Ollama, ce qui élimine la classe d'incidents liés à un ordre de démarrage non maîtrisé. Ensuite, les données persistantes — bases MongoDB et modèles Ollama téléchargés — sont stockées dans des volumes Docker dédiés, indépendants du cycle de vie des conteneurs, garantissant la conservation des états entre redémarrages. Enfin, la configuration applicative est intégralement pilotée par variables d'environnement préfixées `DALEEL_` injectées au lancement, ce qui permet de configurer un même artefact pour des environnements distincts (développement, *staging*, production) sans rebuild.

### 5.5.2 Intégration continue (CI/CD GitHub Actions)

Le workflow `.github/workflows/ci.yml` est déclenché à chaque *push* et chaque *pull request*. Il exécute en parallèle :

1. **Lint** : Ruff sur l'ensemble du code Python ;
2. **Tests backend** : pytest sur une matrice Python `3.11`, `3.12`, `3.13`, avec un service MongoDB 7 démarré comme conteneur sidecar ;
3. **Build frontend** : `npm ci && npm run build` pour vérifier la compilabilité React ;
4. **Vérifications de sécurité** : `pip-audit` pour les dépendances Python, `npm audit` pour les dépendances JavaScript.

Le seuil de couverture de tests est suivi mais non bloquant ; la priorité étant de ne jamais voir un test régresser sans alerte. Les logs CI sont conservés 90 jours pour audit.

### 5.5.3 Variables d'environnement et secrets

L'ensemble de la configuration applicative est piloté par variables d'environnement préfixées `DALEEL_` (cf. `backend/app/config.py`). Le fichier `.env.example` documente l'ensemble des variables disponibles avec leurs valeurs par défaut. Les secrets de production (clé JWT, mots de passe d'admin, identifiants SMTP) sont injectés au runtime via des *secrets managers* (Docker secrets, AWS Secrets Manager ou équivalent) et jamais commités dans le dépôt.

Le service `_validate_production_settings` vérifie au démarrage, lorsque `DALEEL_ENV=production`, que les secrets critiques sont définis et que la liste CORS n'autorise pas le wildcard `*`. Toute violation fait échouer le démarrage de l'application, prévenant les déploiements non sécurisés par erreur.

## 5.6 Discussion critique : limites et perspectives

### 5.6.1 Limites identifiées

**Limite 1 — Taille du corpus annoté pour le fine-tuning.** Le corpus initial de 2 344 articles utilisé pour le *fine-tuning* du modèle d'embeddings, porté à 2 565 articles après réextraction OCR du sous-corpus arabe, constitue une base solide mais limitée à l'échelle du droit tunisien complet. Un *fine-tuning* sur un corpus dix fois plus large permettrait probablement de gagner encore en précision, notamment sur les domaines moins représentés (droit fiscal, droit maritime, droit de la propriété intellectuelle).

**Limite 2 — Extraction des PDF arabes officiels.** Un constat important émerge de l'analyse rétrospective du corpus : les PDF arabes officiels publiés par l'IORT et le JORT utilisent des polices CMap personnalisées dont l'extraction par PyMuPDF et pdfminer.six produit des séquences de glyphes substitués ou inversés, inutilisables pour l'indexation. Le passage à une chaîne d'extraction reposant exclusivement sur l'OCR (Tesseract `ara` à 300 dpi) restaure un texte arabe correctement encodé : la réextraction OCR des deux principaux codes arabes (Code des Sociétés Commerciales, Code du Travail) produit 896 articles arabes propres contre 699 articles précédemment corrompus, et constitue le prérequis indispensable à une évaluation arabe rigoureuse. Le pipeline OCR reste néanmoins sensible aux documents très anciens ou dégradés (faible résolution, taches, contrastes inversés) qui peuvent contenir des artefacts résiduels nécessitant un post-nettoyage spécifique.

**Limite 3 — Couverture LLM-juge limitée.** La couche de vérification sémantique (`quality_guard_semantic_check_enabled`) repose sur un LLM-juge qui peut lui-même se tromper. Sur les cas litigieux, elle reste un signal indicatif et non un verdict absolu. Une approche plus rigoureuse consisterait à entraîner un modèle de NLI (*Natural Language Inference*) spécifiquement sur des paires (réponse, *chunks*) annotées.

**Limite 4 — Latence de l'agent autonome.** La latence p95 de 22 secondes peut être ressentie comme longue par un utilisateur habitué à des réponses instantanées. Des optimisations sont envisageables : *streaming* des tokens dès la première itération, parallélisation des appels d'outils non dépendants, *caching* agressif des sous-requêtes répétées.

**Limite 5 — Évaluation des constats de conformité.** Le scoring de criticité est déterministe (donc auditable), mais sa calibration repose sur des seuils choisis empiriquement. Une étude d'évaluation par un panel d'experts juridiques serait nécessaire pour valider la cohérence des criticités attribuées avec le jugement humain.

**Limite 6 — Multi-tenant à l'échelle.** Le multi-tenant actuel repose sur un filtrage applicatif par `organization_id`. Pour des déploiements à très grande échelle (centaines d'organisations, millions de chunks), un partitionnement physique au niveau de la base (sharding par tenant) deviendrait nécessaire.

**Limite 7 — Asymétrie initiale des performances entre français et arabe et stratégie de remédiation.** Les métriques de *retrieval* présentées en section 5.4.1 ont d'abord agrégé des résultats fortement asymétriques par langue. Sur les 15 requêtes francophones du jeu d'évaluation, le *fine-tuning* porte le Recall@1 de 0,33 à 0,73 et constitue une démonstration robuste de l'apport méthodologique. Sur les 10 requêtes arabes du jeu d'évaluation initial, la mesure était en revanche très en retrait. L'analyse rétrospective a permis d'attribuer cette faiblesse à la qualité du corpus d'entraînement arabe sous-jacent plutôt qu'à l'architecture du système : les PDF arabes officiels (IORT, JORT) utilisent des polices CMap personnalisées dont l'extraction par PyMuPDF et pdfminer produit des séquences de glyphes substitués ou inversés, contaminant à la fois les paires d'entraînement et les requêtes d'évaluation arabes générées synthétiquement par LLM. Une remédiation a été mise en œuvre dans la dernière phase du projet : la réextraction OCR à 300 dpi (Tesseract `ara`) des deux principaux codes arabes a produit **896 articles arabes correctement encodés**, remplaçant les 699 articles précédemment corrompus du corpus. Une régénération du jeu d'évaluation arabe à partir de ce nouveau corpus a été engagée. Le *fine-tuning* sur le corpus arabe propre constitue une perspective immédiate à explorer, dont les gains attendus s'alignent sur ceux observés en français.

**Limite 8 — Absence de validation par un panel d'experts juridiques.** Les évaluations conduites portent sur la dimension de *retrieval* (Recall, MRR, nDCG) et sur les hallucinations détectables automatiquement (citations fabriquées, références inventées). Elles n'incluent pas, à ce stade, de validation qualitative par des praticiens du droit tunisien — avocats, juristes d'entreprise, enseignants en droit — qui pourraient évaluer la correction juridique des raisonnements produits, la pertinence des articles cités au regard de la question posée, et la sécurité juridique des actions correctives proposées par le volet *Compliance Operations*. Cette validation externe constitue un prérequis à une mise en production en milieu professionnel et fait l'objet d'une perspective dédiée en section 5.6.2.

### 5.6.2 Perspectives d'évolution

**Perspective 1 — Extension à d'autres juridictions du Maghreb.** L'architecture est largement réutilisable pour les corpus marocain, algérien, mauritanien. Le *fine-tuning* spécifique par juridiction et l'enrichissement des dictionnaires de domaines en dialecte permettraient de mutualiser la plateforme.

**Perspective 2 — Détection automatique d'amendements depuis le JORT.** Un *crawler* du portail JORT couplé au pipeline d'ingestion permettrait l'intégration quasi temps réel des nouveaux textes. Cette automatisation conduirait à une plateforme de veille juridique continue, avec notifications proactives aux clients dès la publication d'un texte affectant leur domaine.

**Perspective 3 — Génération d'avis juridiques structurés.** Au-delà des réponses libres, le système pourrait produire des **avis juridiques formatés** prêts à l'envoi (en-tête, exposé des faits, analyse, conclusion, mentions légales), exploitables directement par les cabinets d'avocats.

**Perspective 4 — Apprentissage par renforcement sur le feedback utilisateur.** La collection `qa_feedback` accumule les retours utilisateurs (👍/👎 + commentaire). L'exploitation de ces signaux dans un cycle de *fine-tuning* incrémental (par exemple via DPO ou RLHF léger) permettrait une amélioration continue automatisée.

**Perspective 5 — Intégration ERP / GED.** L'API REST permet une intégration directe dans des systèmes tiers. Un connecteur officiel pour les ERP les plus déployés en Tunisie (Sage, Odoo, ERP Bull) ouvrirait la voie à des cas d'usage de conformité automatisée à la source (vérification de conformité d'un contrat avant signature, alerte sur une exigence applicable à une opération en cours).

**Perspective 6 — Module de simulation prédictive.** À partir de la posture de conformité courante et des amendements à venir, le système pourrait simuler l'impact prévisionnel et proposer un calendrier de mise en conformité anticipée — bouclant ainsi la boucle entre veille juridique, analyse d'impact et action opérationnelle.

**Perspective 7 — Validation par un panel d'experts juridiques tunisiens.** Une étape de validation par un panel pluridisciplinaire — avocats inscrits au barreau de Tunis, juristes d'entreprise issus de plusieurs secteurs, enseignants en droit — constituerait l'aboutissement naturel des évaluations techniques présentées dans ce mémoire. Le protocole envisagé reposerait sur une grille d'évaluation structurée appliquée à un échantillon stratifié d'une centaine de réponses produites par Daleel, croisant trois axes : *correction juridique* (la réponse est-elle conforme à l'état actuel du droit ?), *pertinence des sources citées* (les articles invoqués correspondent-ils réellement à la question ?), et *sécurité juridique des actions correctives* (les recommandations produites par le volet *Compliance Operations* exposent-elles le client à un risque accru ?). Une telle étude permettrait à la fois de calibrer plus finement les seuils de la garde-qualité, d'identifier les domaines juridiques où la couverture du corpus reste insuffisante, et de fournir au futur exploitant une caution scientifique externe nécessaire à la commercialisation auprès de cabinets d'avocats et de directions juridiques.

## Conclusion

Ce chapitre a documenté la moitié opérationnelle de la plateforme Daleel. Le volet *Compliance Operations*, porté par dix services métier interconnectés et plus de 50 endpoints REST, transforme l'assistant juridique en un véritable outil de pilotage du cycle complet de conformité, depuis la création d'un dossier de non-conformité jusqu'au suivi des preuves de mise en conformité, en passant par l'identification de constats, la planification d'actions correctives et le scoring déterministe de criticité auditable. L'orchestrateur LLM ASK/CLARIFY/ACT/REVIEW structure les décisions en quatre branches selon le niveau de confiance et la complétude des faits, et expose explicitement ses décisions au frontend pour adapter l'expérience utilisateur. Les interfaces — chatbot conversationnel multilingue, panneau d'administration de dix pages dédiées et tableau de bord BI temps réel — offrent une expérience cohérente couvrant les besoins du juriste métier comme de l'administrateur. L'évaluation quantitative a démontré des gains significatifs : +40 % en Recall@1 global grâce au *fine-tuning* (et jusqu'à +50 % sur le sous-corpus francophone, +50 % en Recall@5 arabe), tandis que l'analyse qualitative met en évidence l'apport de la fusion lexicale pondérée, du cross-encoder et de la garde-qualité comme filtre anti-hallucination. Le déploiement conteneurisé via Docker Compose et la chaîne d'intégration continue GitHub Actions sur trois versions de Python garantissent la reproductibilité et la qualité logicielle. Enfin, la discussion critique a identifié huit limites et tracé sept perspectives d'évolution, depuis l'extension à d'autres juridictions du Maghreb jusqu'à la validation par un panel d'experts juridiques tunisiens.

---

# Conclusion générale

Ce Projet de Fin d'Études a abouti à la conception et à la réalisation de **Daleel**, une plateforme intégrée d'assistance juridique et de pilotage de la conformité réglementaire fondée sur l'intelligence artificielle, pensée pour une extension internationale et expérimentée d'abord sur le droit tunisien. La problématique initiale — concevoir un système fournissant des réponses pertinentes, robustes, traçables et opérationnellement exploitables dans le contexte réglementaire tunisien — a été traitée selon une démarche **CRISP-DM** en six phases. La méthodologie n'a pas été appliquée comme une cascade descendante mais comme un véritable cycle itératif : la phase d'évaluation a déclenché un retour vers la modélisation pour le *fine-tuning* du modèle d'embeddings, et l'audit qualité des réponses arabes a renvoyé vers la préparation des données pour renforcer le nettoyage du corpus.

La plateforme articule **deux volets complémentaires**. Le volet *Legal RAG* repose sur une architecture RAG avancée à six modules (recherche hybride combinant FAISS et signaux lexicaux par fusion pondérée, reranking par cross-encoder, retrieval partitionné piloté par l'intention, graphe de connaissances léger, garde-qualité anti-hallucination), prolongée par un agent autonome ReAct doté de douze outils exploitant l'appel d'outils natif d'Ollama. Le volet *Compliance Operations* matérialise le cycle complet de gestion de la conformité — dossiers, constats, actions, preuves, contrôles, exceptions — orchestré par un agent LLM selon un arbre de décision ASK / CLARIFY / ACT / REVIEW adossé à un moteur de criticité déterministe et auditable. L'ensemble totalise plus de 170 endpoints REST, 38 collections MongoDB, 41 services métier et 34 composants React, déployable sous Docker Compose avec une chaîne d'intégration continue.

Sur le plan des **résultats**, le *fine-tuning* du modèle d'embeddings a produit, sur 30 requêtes gold régénérées après réextraction OCR du sous-corpus arabe, des gains globaux de **+40 % en Recall@1, +34 % en MRR@10 et +37 % en nDCG@5**, avec des gains particulièrement marqués en français (+50 % Recall@1, +43 % MRR@10) ; les performances arabes restent en retrait, l'analyse rétrospective ayant montré que le *fine-tuning* avait été conduit sur un corpus arabe initialement contaminé par des artefacts d'extraction PDF, dont la correction par OCR ouvre la voie à un re-*fine-tuning* attendu de gains comparables à ceux observés en français. L'analyse qualitative des modules RAG met en évidence l'apport complémentaire de la recherche hybride, du reranking, du retrieval partitionné, du KG Light et de la garde-qualité, sans revendiquer d'ablation quantitative complète dans cette version. Ces résultats valident la pertinence d'une approche **RAG agentique pour un domaine juridique spécialisé** sous-représenté dans la littérature : aucun système équivalent n'est documenté à ce jour pour la juridiction tunisienne, qui combine pourtant un corpus riche et dynamique, une dualité linguistique arabe / français et un fort besoin opérationnel. Daleel constitue ainsi une contribution à la fois scientifique — par ses choix d'architecture validés expérimentalement et son orchestrateur de conformité formalisé — et applicative, par sa mise à disposition d'un produit fonctionnel, déployable en local et respectueux de la confidentialité des données juridiques traitées.

Les **perspectives d'évolution**, détaillées en section 5.6.2, ouvrent de nombreuses pistes : extension à d'autres juridictions du Maghreb, détection automatique d'amendements depuis le JORT, génération d'avis juridiques formatés, apprentissage par renforcement sur les retours utilisateur, intégration avec les ERP/GED, module de simulation prédictive d'impact réglementaire, et validation par un panel d'experts juridiques tunisiens. Parmi ces perspectives, deux présentent un impact à court terme particulièrement élevé : le re-*fine-tuning* du modèle d'embeddings sur le corpus arabe propre issu de la réextraction OCR — opération dont les prérequis techniques sont déjà réunis — et la validation qualitative par un panel d'experts juridiques, qui constitue la dernière étape avant une mise en production en milieu professionnel.

Sur le plan personnel, ce projet a constitué une opportunité exceptionnelle de mobiliser un large spectre de compétences — ingénierie des données, *fine-tuning* de modèles de langage, conception d'agents IA, architecture multi-tenant, sécurité applicative et déploiement DevOps — au service d'un produit cohérent répondant à un besoin réel identifié sur le terrain. La démarche CRISP-DM, loin d'être un cadre théorique appliqué a posteriori, a structuré de manière effective les itérations du projet : l'analyse rétrospective de la qualité du corpus arabe, par exemple, n'aurait pas été possible sans la rigueur de l'étape d'évaluation qui a révélé l'anomalie et déclenché la boucle correctrice. Ce projet démontre qu'une solution IA ambitieuse, combinant RAG avancé, agents autonomes et pilotage de la conformité, peut être conduite avec rigueur méthodologique dans un contexte académique, tout en produisant un livrable déployable qui répond à un manque documenté du marché de la *LegalTech* tunisienne.

---

# Bibliographie

[1] Ashish Vaswani, Noam Shazeer, Niki Parmar, *et al.* « Attention is all you need ». *Advances in Neural Information Processing Systems*, 2017.

[2] Jacob Devlin, Ming-Wei Chang, Kenton Lee, Kristina Toutanova. « BERT: Pre-training of deep bidirectional transformers for language understanding ». *NAACL-HLT*, 2019.

[3] Tom Brown, Benjamin Mann, Nick Ryder, *et al.* « Language models are few-shot learners ». *NeurIPS*, 2020.

[4] An Yang, Baosong Yang, Binyuan Hui, *et al.* (Qwen Team). « Qwen2.5 technical report ». *arXiv preprint arXiv:2412.15115*, 2024.

[5] Joshua Maynez, Shashi Narayan, Bernd Bohnet, Ryan McDonald. « On faithfulness and factuality in abstractive summarization ». *ACL*, 2020.

[6] Patrick Lewis, Ethan Perez, Aleksandra Piktus, *et al.* « Retrieval-augmented generation for knowledge-intensive NLP tasks ». *NeurIPS*, 2020.

[7] Yunfan Gao, Wenhao Xiong, Xinyu Gao, *et al.* « Retrieval-augmented generation for large language models: A survey ». *arXiv preprint arXiv:2312.10997*, 2024.

[8] Noah Shinn, Federico Cassano, Ashwin Gopinath, Karthik Narasimhan, Shunyu Yao. « Reflexion: Language agents with verbal reinforcement learning ». *NeurIPS*, 2023.

[9] Jiongnan Chen, Shitao Xiao, Zheng Liu, *et al.* « BGE-M3-Embedding: Multi-lingual, multi-functionality, multi-granularity text embeddings through self-knowledge distillation ». *arXiv preprint arXiv:2402.03216*, 2024.

[10] Areti Manataki *et al.* « Retrieval-augmented generation for legal question answering ». *arXiv preprint*, 2023.

[11] Stephen Robertson, Hugo Zaragoza. « The probabilistic relevance framework: BM25 and beyond ». *Foundations and Trends in Information Retrieval*, 2009.

[12] Gordon V. Cormack, Charles L. A. Clarke, Stefan Buettcher. « Reciprocal rank fusion outperforms condorcet and individual rank learning methods ». *SIGIR*, 2009.

[13] Rodrigo Nogueira, Kyunghyun Cho. « Passage re-ranking with BERT ». *arXiv preprint arXiv:1901.04085*, 2019.

[14] Shunyu Yao, Jeffrey Zhao, Dian Yu, *et al.* « ReAct: Synergizing reasoning and acting in language models ». *ICLR*, 2023.

[15] Timo Schick, Jane Dwivedi-Yu, Roberto Dessì, *et al.* « Toolformer: Language models can teach themselves to use tools ». *NeurIPS*, 2023.

[16] Nils Reimers, Iryna Gurevych. « Sentence-BERT: Sentence embeddings using Siamese BERT-networks ». *EMNLP-IJCNLP*, 2019.

[17] Nils Reimers, Iryna Gurevych. « Making monolingual sentence embeddings multilingual using knowledge distillation ». *EMNLP*, 2020.

[18] Matthew Henderson, Rami Al-Rfou, Brian Strope, *et al.* « Efficient natural language response suggestion for smart reply ». *KDD*, 2017.

[19] Ilias Chalkidis, Manos Fergadiotis, Prodromos Malakasiotis, Nikolaos Aletras, Ion Androutsopoulos. « LEGAL-BERT: The muppets straight out of law school ». *Findings of EMNLP*, 2020.

[20] Lu Zheng, Neel Guha, Brandon Anderson, Peter Henderson, Dan Jurafsky. « When does pretraining help? Assessing self-supervised learning for law and the CaseHOLD dataset ». *ICAIL*, 2021.

[21] Ilias Chalkidis, Abhinav Jana, Nikolaos Aletras, *et al.* « LexGLUE: A benchmark dataset for legal language understanding in English ». *ACL*, 2022.

[22] Neel Guha, Julian Nyarko, Daniel Ho, *et al.* « LegalBench: A collaboratively built benchmark for measuring legal reasoning in large language models ». *NeurIPS Datasets and Benchmarks*, 2023.

[23] Ahmed Abdelali *et al.* « AraBERT and MARBERT: Deep bidirectional transformers for Arabic ». *ACL*, 2021.

[24] Boris Otto *et al.* « AI-supported compliance management: A hybrid approach ». *Information Systems Frontiers*, 2022.

[25] Jeff Johnson, Matthijs Douze, Hervé Jégou. « Billion-scale similarity search with GPUs ». *IEEE Transactions on Big Data*, 2019.

[26] Sebastian Hofstätter, Sheng-Chieh Lin, Jheng-Hong Yang, Jimmy Lin, Allan Hanbury. « Efficiently teaching an effective dense retriever with balanced topic-aware sampling ». *SIGIR*, 2021.

[27] Yu A. Malkov, D. A. Yashunin. « Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs ». *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 2020.

[28] Karthik Ganesan *et al.* « TextDiscover: Robust legal document segmentation across heterogeneous formats ». *Workshop on Natural Legal Language Processing*, 2022.

[29] Pete Chapman, Julian Clinton, Randy Kerber, Thomas Khabaza, Thomas Reinartz, Colin Shearer, Rüdiger Wirth. *CRISP-DM 1.0: Step-by-step data mining guide*. SPSS Inc., 2000.

[30] Albert Q. Jiang, Alexandre Sablayrolles, Arthur Mensch, *et al.* « Mistral 7B ». *arXiv preprint arXiv:2310.06825*, 2023.

[31] Hugo Touvron, Louis Martin, Kevin Stone, *et al.* « Llama 2: Open foundation and fine-tuned chat models ». *arXiv preprint arXiv:2307.09288*, 2023.

[32] Meta AI. « The Llama 3 herd of models ». *arXiv preprint arXiv:2407.21783*, 2024.

[33] Edward J. Hu, Yelong Shen, Phillip Wallis, *et al.* « LoRA: Low-rank adaptation of large language models ». *ICLR*, 2022.

[34] Younes Belkada, Tim Dettmers, Artidoro Pagnoni, Sourab Mangrulkar, Sayak Paul. « QLoRA: Efficient finetuning of quantized LLMs ». *NeurIPS*, 2023.

[35] Wissam Antoun, Fady Baly, Hazem Hajj. « AraBERT: Transformer-based model for Arabic language understanding ». *LREC Workshop on Open-Source Arabic Corpora*, 2020.

[36] Omar Khattab, Matei Zaharia. « ColBERT: Efficient and effective passage search via contextualized late interaction over BERT ». *SIGIR*, 2020.

[37] Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Brian Ichter, Fei Xia, Ed Chi, Quoc Le, Denny Zhou. « Chain-of-thought prompting elicits reasoning in large language models ». *NeurIPS*, 2022.

[38] République Tunisienne. « Loi n° 2025-9 du 21 mai 2025, portant réglementation des contrats de travail et interdiction de la sous-traitance de main-d'œuvre ». *Journal Officiel de la République Tunisienne*, n° 61, 23 mai 2025.

---

# Annexes

> *Les annexes regroupent des éléments de référence détaillés extraits directement du code source de la plateforme Daleel. Elles complètent le corps du mémoire sans le dupliquer : cartographie exhaustive de l'API REST, catalogue complet de configuration, spécification des outils de l'agent autonome, modèle de données détaillé, et inventaire de la couverture de tests et de la chaîne d'intégration continue. L'ensemble matérialise l'ampleur effective de la réalisation.*

| Annexe | Intitulé |
|---|---|
| A | Cartographie complète de l'API REST (plus de 170 points d'accès) |
| B | Catalogue de configuration de la plateforme (71 paramètres `DALEEL_*`) |
| C | Spécification des douze outils de l'agent autonome ReAct |
| D | Modèle de données détaillé : les 38 collections MongoDB |
| E | Couverture de tests (55 fichiers) et chaîne d'intégration continue |

---

## Annexe A — Cartographie complète de l'API REST

La plateforme expose **plus de 170 points d'accès REST** répartis en **7 routeurs FastAPI**, tous montés sous le préfixe racine `/api/v1`. Chaque endpoint est validé par schéma Pydantic, protégé par authentification JWT (hors endpoints publics d'authentification) et soumis à la limitation de débit. Cette annexe recense l'intégralité des routes, regroupées par routeur puis par domaine fonctionnel.

### A.1 Routeur principal (`router.py`) — Legal RAG, corpus et administration

**Documents et ingestion documentaire**

| Méthode | Chemin (`/api/v1`) | Rôle |
|---|---|---|
| POST | `/documents/upload` | Téléversement d'un document (PDF, DOCX, image) |
| GET | `/documents` | Liste paginée des documents de l'organisation |
| GET | `/documents/{doc_id}` | Métadonnées d'un document |
| GET | `/documents/{doc_id}/source` | Fichier source original |
| GET | `/documents/{doc_id}/chunks` | *Chunks* indexés du document |
| GET | `/documents/{doc_id}/raw-pages` | Pages brutes extraites |
| GET | `/documents/{doc_id}/cleaned-pages` | Pages après nettoyage |
| GET | `/documents/{doc_id}/exigences` | Exigences extraites du document |
| POST | `/documents/{doc_id}/extract-exigences` | Lancer l'extraction d'exigences |
| GET | `/documents/{doc_id}/exigences/export` | Export des exigences |
| PATCH | `/documents/{doc_id}/classify` | Classification du document |
| GET | `/documents/{doc_id}/amendments` | Amendements détectés |
| DELETE | `/documents/{doc_id}` | Suppression d'un document |
| POST | `/exigences/match` | Appariement sémantique d'exigences |

**Recherche et questions-réponses**

| Méthode | Chemin (`/api/v1`) | Rôle |
|---|---|---|
| POST | `/search` | Recherche hybride dans le corpus |
| POST | `/ask` | Question-réponse RAG classique |
| POST | `/ask-agentic` | Question traitée par l'agent autonome ReAct |
| POST | `/ask-with-document` | Question contextualisée sur un document téléversé |
| POST | `/ask-auto` | Sélection automatique du mode (classique/agentique) |
| POST | `/ask-stream` | Réponse en *streaming* (Server-Sent Events) |
| POST | `/feedback` | Enregistrement d'un retour utilisateur (👍/👎) |
| GET | `/feedback` | Consultation des retours |

**Profils d'entreprise et applicabilité**

| Méthode | Chemin (`/api/v1`) | Rôle |
|---|---|---|
| POST | `/company-profiles` | Création d'un profil d'entreprise |
| GET | `/company-profiles` | Liste des profils |
| POST | `/company-profiles/ensure-current` | Récupération ou création du profil courant |
| GET | `/company-profiles/{profile_id}` | Détail d'un profil |
| PUT | `/company-profiles/{profile_id}` | Mise à jour d'un profil |
| DELETE | `/company-profiles/{profile_id}` | Suppression d'un profil |
| POST | `/company-profiles/{profile_id}/evaluate-applicabilities` | Évaluation d'applicabilité réglementaire |
| GET | `/company-profiles/{profile_id}/applicabilities/summary` | Synthèse d'applicabilité |

**Hiérarchie juridique (lois, articles, versions, actions)**

| Méthode | Chemin (`/api/v1`) | Rôle |
|---|---|---|
| POST · GET | `/lois` | Création / liste des lois |
| GET · PATCH · DELETE | `/lois/{loi_id}` | Détail / mise à jour / suppression d'une loi |
| GET | `/lois/{loi_id}/articles` | Articles d'une loi |
| GET | `/articles/{article_id}` | Détail d'un article |
| GET | `/articles/{article_id}/versions` | Versions d'un article |
| GET | `/article-versions/{version_id}` | Détail d'une version |
| GET | `/article-versions/{version_id}/exigences` | Exigences d'une version |
| GET · DELETE | `/article-versions/{version_id}/actions` | Actions liées à une version |
| GET | `/actions/{action_id}` | Détail d'une action corrective |
| GET | `/actions/{action_id}/criticality` | Criticité d'une action |
| DELETE | `/action-dependencies/{dep_id}` | Suppression d'une dépendance d'action |

**Administration, audit et supervision**

| Méthode | Chemin (`/api/v1`) | Rôle |
|---|---|---|
| GET | `/platform/stats` | Statistiques globales de la plateforme |
| GET | `/admin/stats` · `/admin/vector-stats` · `/admin/analytics` | Tableaux de bord d'administration |
| GET · POST | `/admin/cache/stats` · `/admin/cache/invalidate` | Gestion du cache |
| POST | `/admin/create-vector-index` · `/admin/reindex` | Reconstruction de l'index vectoriel |
| GET | `/admin/check-index-consistency` | Contrôle de cohérence de l'index |
| GET | `/audit-logs`, `/lois/{loi_id}/audit-logs`, `/articles/{article_id}/audit-logs` | Journaux d'audit |

**Notifications, historique et mémoire**

| Méthode | Chemin (`/api/v1`) | Rôle |
|---|---|---|
| GET | `/notifications/mine` · `/notifications/unread-count` | Notifications de l'utilisateur |
| POST | `/notifications/read-all` · `/notifications/{id}/read` | Marquage comme lu |
| DELETE | `/notifications/{id}` | Suppression d'une notification |
| GET · POST | `/admin/notifications`, `/admin/notifications/{id}/approve`, `/{id}/reject` | Modération des inscriptions |
| GET | `/chat-history`, `/chat-history/conversation/{id}` | Historique de conversation |
| PATCH | `/chat-history/conversation/{id}/archive` · `/rename` | Archivage / renommage de conversation |
| DELETE | `/chat-history/{entry_id}` | Suppression d'un échange |
| GET · PUT · DELETE | `/memory` | Mémoire conversationnelle persistante |

### A.2 Routeur d'authentification (`/api/v1/auth`)

| Méthode | Chemin | Rôle |
|---|---|---|
| POST | `/register` | Inscription (compte + organisation) |
| POST | `/verify-email` | Confirmation d'email par jeton |
| POST | `/verify-phone/send` · `/verify-phone` | Envoi et vérification du code OTP téléphone |
| POST | `/login` · `/refresh` · `/logout` | Cycle de session JWT |
| GET | `/me` · PUT `/me/password` | Profil courant / changement de mot de passe |
| POST | `/forgot-password` · `/reset-password` | Réinitialisation de mot de passe |
| GET · PUT · PATCH | `/organizations`, `/organizations/{id}`, `/organizations/{id}/status` | Gestion des organisations |
| POST | `/organizations/{id}/approve` · `/reject` · `/renew` | Gouvernance des organisations |
| GET · PUT · DELETE | `/organizations/{id}/users`, `/users/{user_id}` | Gestion des utilisateurs |
| POST · GET · DELETE | `/invitations`, `/invitations/accept`, `/invitations/{id}` | Invitations par email |

### A.3 Routeurs Compliance Operations (`/api/v1/cases`, `/api/v1/compliance`)

| Méthode | Chemin | Rôle |
|---|---|---|
| GET | `/cases/summary` | Tableau de bord des dossiers |
| GET · PATCH · DELETE | `/cases/{case_id}` | Cycle de vie d'un dossier |
| POST · GET | `/cases/{case_id}/messages` | Conversation guidée du dossier |
| POST · GET · DELETE | `/cases/{case_id}/documents…` | Pièces jointes et analyse |
| POST | `/cases/{case_id}/documents/{id}/analyze` | Analyse OCR + LLM d'une pièce |
| GET | `/cases/{case_id}/documents/{id}/entities` | Entités extraites |
| POST · GET · PATCH | `/cases/{case_id}/findings…` | Constats de non-conformité |
| POST · GET · PATCH | `/cases/{case_id}/actions…` | Actions correctives |
| POST · GET · PATCH | `/compliance/assessments…` | Évaluations de posture |
| POST · GET · PATCH | `/compliance/controls…` | Contrôles internes |
| PATCH | `/compliance/evidences/{id}` | Preuves de mise en conformité |
| POST · GET · PATCH · DELETE | `/compliance/links…` | Liens exigence ↔ contrôle |
| GET | `/compliance/gaps/{profile_id}` | Analyse d'écarts |
| POST · GET · PATCH | `/compliance/exceptions…` | Registre d'exceptions |
| POST | `/compliance/remediation-actions` | Actions de remédiation |

Le routeur d'orchestration de cas (`case_orchestrator_router`) expose en complément les endpoints de déclenchement et de consultation du cycle ASK / CLARIFY / ACT / REVIEW décrit en section 5.2.

### A.4 Routeur vocal (`/api/v1/voice`)

| Méthode | Chemin | Rôle |
|---|---|---|
| POST | `/transcribe` | Transcription parole → texte (STT) |
| POST | `/tts` | Synthèse texte → parole (TTS) |
| POST | `/ask` | Question vocale de bout en bout |

---

## Annexe B — Catalogue de configuration de la plateforme

L'intégralité du comportement de la plateforme est pilotée par **71 paramètres de configuration** préfixés `DALEEL_`, déclarés dans `backend/app/config.py` (objet `Settings` Pydantic) et documentés dans `.env.example`. Cette conception « *config as code* » garantit qu'un même artefact Docker se déploie sans rebuild d'un environnement à l'autre. Les paramètres sont présentés ci-dessous par domaine.

| Domaine | Paramètres |
|---|---|
| **Base de données** | `mongodb_url`, `mongodb_db_name`, `mongodb_max_pool_size`, `mongodb_min_pool_size`, `mongodb_server_selection_timeout_ms`, `mongodb_connect_timeout_ms`, `mongodb_socket_timeout_ms` |
| **Embeddings et index** | `embedding_model`, `embedding_dimension`, `embedding_cache_maxsize`, `vector_search_backend`, `vector_index_type`, `faiss_build_on_startup`, `faiss_build_in_background` |
| **Modèle de langage (LLM)** | `llm_base_url`, `llm_api_key`, `llm_model`, `llm_max_retries`, `llm_timeout_connect`, `llm_timeout_read`, `llm_backoff_base`, `llm_backoff_max`, `llm_keep_alive`, `llm_cache_ttl_seconds`, `llm_cache_max_size` |
| **Pipeline d'ingestion** | `chunk_size`, `chunk_overlap`, `min_chunk_len`, `upload_dir`, `max_upload_mb`, `tesseract_path` |
| **Pipeline RAG avancé** | `enable_cross_encoder`, `domain_router_enabled`, `domain_router_llm_fallback_enabled`, `partitioned_retrieval_enabled`, `kg_light_enabled`, `kg_light_max_entities`, `strict_grounded_only` |
| **Garde-qualité** | `quality_guard_enabled`, `quality_guard_semantic_check_enabled` |
| **Mode automatique** | `auto_mode_enabled`, `auto_mode_length_threshold`, `auto_mode_agentic_keywords`, `auto_mode_classic_keywords`, `auto_mode_default` |
| **Modèles auxiliaires** | `style_model`, `style_model_enabled`, `style_model_timeout`, `reasoning_model_path`, `reasoning_confidence_threshold`, `derja_normalizer_enabled` |
| **Sécurité et authentification** | `jwt_secret_key`, `jwt_algorithm`, `jwt_access_token_expire_minutes`, `jwt_refresh_token_expire_days`, `api_key`, `admin_api_key`, `cors_origins`, `super_admin_email`, `super_admin_password`, `multi_tenant_enabled` |
| **Emails et notifications** | `smtp_host`, `smtp_port`, `smtp_user`, `smtp_password`, `smtp_from_email`, `smtp_from_name`, `smtp_use_tls`, `app_base_url`, `sms_provider` |

Le service `_validate_production_settings` (cf. section 5.5.3) vérifie au démarrage, lorsque `DALEEL_ENV=production`, que les secrets critiques (`jwt_secret_key`, `super_admin_password`) sont définis et que `cors_origins` n'autorise pas le caractère générique `*` — toute violation fait échouer le démarrage, prévenant les déploiements non sécurisés.

---

## Annexe C — Spécification des douze outils de l'agent autonome ReAct

L'agent autonome (`autonomous_agent.py`) instancie douze `ToolDefinition`, chacune exposée au modèle `qwen2.5:7b` au format *function calling* d'Ollama (schéma JSON typé). Cette annexe détaille, pour chaque outil, son *tier*, sa description fonctionnelle et ses paramètres réels (paramètres requis en **gras**).

### C.1 Outils de recherche

| Outil | Paramètres | Description |
|---|---|---|
| `semantic_search` | **`query`** *(str)*, `top_k` *(int, défaut 5, max 10)*, `language_filter` *(ar/fr/en)*, `document_id` *(str)* | Recherche par similarité sémantique dans le corpus ; renvoie des *chunks* avec métadonnées (texte, page, document source) |
| `lookup_law` | **`code`** *(str : CT, CS, CF, LP63…)* | Recherche d'une loi par son code court ; renvoie son identifiant, son nom et son nombre d'articles |
| `search_articles` | **`loi_id`** *(str)*, `keyword` *(str)*, `limit` *(int, défaut 20, max 30)* | Recherche d'articles dans une loi donnée, filtrés par mot-clé |
| `get_article_text` | **`version_id`** *(str)* | Texte complet d'une version d'article, avec décompte des exigences et actions |

### C.2 Outils de graphe de connaissances

| Outil | Paramètres | Description |
|---|---|---|
| `get_article_graph` | **`article_id`** *(str)* | Sous-graphe complet d'un article : versions, exigences (obligations / interdictions / conditions), actions, criticités, dépendances |
| `get_company_graph` | **`profile_id`** *(str)* | Graphe d'entreprise : exigences applicables et actions liées au profil |

### C.3 Outils d'exigences et de conformité

| Outil | Paramètres | Description |
|---|---|---|
| `list_document_exigences` | **`document_id`** *(str)* | Liste des exigences extraites d'un document |
| `match_exigences` | **`query`** *(str)*, `exigence_type`, `top_k` | Recherche sémantique des exigences pertinentes à une situation décrite |
| `get_applicability` | **`profile_id`** *(str)* | Résumé d'applicabilité par type d'exigence pour un profil |
| `get_criticality` | **`profile_id`** *(str)* | Répartition des criticités (critique / importante / secondaire) |
| `compute_compliance` | **`profile_id`** *(str)* | Calcul de la posture de conformité globale (couverture, écarts) |
| `generate_roadmap` | **`profile_id`** *(str)* | Génération d'un plan d'action priorisé avec dépendances |

Chaque exécution d'outil est journalisée dans un `ToolCallRecord` (itération, nom, arguments, résumé du résultat, durée, erreur) exposé à l'utilisateur dans le champ `tool_calls_log` de la réponse (section 4.5.4). Le contrôle d'accès multi-tenant est appliqué uniformément : tout outil manipulant un `profile_id` vérifie son appartenance à l'organisation courante avant exécution.

---

## Annexe D — Modèle de données détaillé : les 38 collections MongoDB

La persistance repose sur MongoDB 7.0 (pilote asynchrone Motor) avec **38 collections** réparties en sept domaines fonctionnels. Les index composites sont créés de façon idempotente au démarrage par `database.init_db()`.

| Domaine | Collections | Index notables |
|---|---|---|
| **Gestion documentaire** | `documents`, `document_sources`, `document_raw_pages`, `document_cleaned_texts`, `chunks` | `document_sources.file_hash` (unique, déduplication) ; `chunks (document_id, chunk_index)`, `(document_id, language)`, `(article_version_id)` |
| **Hiérarchie juridique** | `lois`, `articles`, `article_versions`, `amendment_operations` | `article_versions (article_id, is_current)`, `(article_id, version_number)` |
| **Exigences et actions** | `exigences`, `actions`, `action_criticalities`, `action_dependencies` | `exigences (document_id, page_number)`, `(exigence_type)` |
| **Profils et applicabilité** | `company_profiles`, `exigence_applicabilities` | `exigence_applicabilities (profile_id, exigence_id)` |
| **Dossiers de conformité** | `compliance_cases`, `case_messages`, `case_documents`, `case_document_analyses`, `case_findings`, `case_actions`, `compliance_assessments` | `compliance_cases (organization_id, status)`, `(profile_id, created_at)` ; `case_document_analyses (case_id, document_id)` |
| **Contrôles et preuves** | `controls`, `control_evidences`, `requirement_control_links`, `exception_register`, `contract_analyses` | `requirement_control_links (requirement_id, control_id)` |
| **Identité, audit et système** | `users`, `organizations`, `invitations`, `password_reset_tokens`, `token_blacklist`, `audit_logs`, `qa_feedback`, `chat_history`, `notifications`, `user_memory`, `conversation_summaries` | `users.email` (unique) ; `audit_logs (created_at)`, `(user_id, action)` ; `token_blacklist.expires_at` (TTL) ; `user_memory (user_id)` |

L'isolation multi-tenant repose sur le champ `organization_id` présent dans toutes les collections métier ; aucun acteur, super admin inclus, ne peut accéder aux données métier d'une organisation tierce (cf. section 3.1).

---

## Annexe E — Couverture de tests et chaîne d'intégration continue

### E.1 Inventaire de la suite de tests (55 fichiers `test_*.py`)

La suite compte **55 fichiers de tests** exécutés par pytest sur une matrice Python 3.11 / 3.12 / 3.13.

| Couche | Nb | Fichiers |
|---|---|---|
| **Traitement documentaire** | 4 | `test_chunker`, `test_article_segmenter`, `test_derja_normalizer`, `test_text_utils` |
| **Services Legal RAG** | 20 | `test_faiss_index`, `test_search_service`, `test_reranker`, `test_legal_retrieval_orchestrator`, `test_domain_router`, `test_graph_resolver`, `test_quality_guard_service`, `test_embedding_cache`, `test_finetuned_models`, `test_llm_cache`, `test_llm_retry`, `test_llm_helpers`, `test_llm_grounding_validation`, `test_llm_style_formatter`, `test_advisor_response_composer`, `test_context_rewrite_prompt`, `test_exigence_match_service`, `test_memory_service`, `test_loi_service`, `test_amendment_service` |
| **Services Compliance** | 10 | `test_compliance_service`, `test_compliance_case_orchestrator`, `test_case_service`, `test_case_conversation_service`, `test_case_document_service`, `test_criticality_service`, `test_action_service`, `test_roadmap_service`, `test_recalculation_service`, `test_contract_analysis_service` |
| **API et authentification** | 9 | `test_api`, `test_auth`, `test_auth_service_pure`, `test_auth_activity_notifications`, `test_config_validation`, `test_voice_router`, `test_request`, `test_request_final`, `test_main_helpers` |
| **Intégration de bout en bout** | 2 | `test_integration_sprint6`, `test_conversation_workflow` |
| **Services transverses** | 10 | `test_audit_service`, `test_export_service`, `test_export_service_extended`, `test_notification_service`, `test_notification_service_extended`, `test_email_service`, `test_feedback_service`, `test_analytics_service`, `test_voice_service`, `test_document_service_helpers` |

Les tests s'appuient sur des fixtures `conftest.py` partagées (instance MongoDB de test nettoyée entre cas, double de test Ollama par défaut) et incluent des scénarios d'intégration simulant une chaîne complète upload → ingestion → recherche → question-réponse.

### E.2 Chaîne d'intégration continue (GitHub Actions)

Le workflow `.github/workflows/ci.yml`, déclenché à chaque *push* et *pull request*, exécute en parallèle :

1. **Lint** — Ruff sur l'ensemble du code Python (politique « zéro avertissement ») ;
2. **Tests backend** — pytest sur la matrice Python 3.11 / 3.12 / 3.13 avec un service MongoDB 7 en conteneur *sidecar* ;
3. **Build frontend** — `npm ci && npm run build` (vérification de compilabilité React/Vite) ;
4. **Vérifications de sécurité** — `pip-audit` (dépendances Python) et `npm audit` (dépendances JavaScript).

Les journaux d'exécution sont conservés 90 jours à des fins d'audit. Cette chaîne garantit la non-régression à chaque évolution du code et la reproductibilité du build documentée au chapitre 5.


