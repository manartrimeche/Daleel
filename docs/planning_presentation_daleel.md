# Planning de présentation - Pré-soutenance Daleel

## 1. Lecture synthétique du projet

Après lecture de la structure, des rapports, du backend, des services principaux, des tests, du frontend et de la configuration, le projet peut être présenté comme une plateforme complète en deux grands axes :

1. **Recherche juridique intelligente**
   - ingestion de documents juridiques ;
   - extraction texte et OCR ;
   - nettoyage et découpage des textes ;
   - embeddings multilingues ;
   - recherche sémantique avec FAISS ;
   - réponse RAG avec sources.

2. **Pilotage de conformité**
   - profils d'entreprise ;
   - exigences applicables ;
   - lois, articles, versions et amendements ;
   - actions, criticité et roadmap ;
   - case management ;
   - contrôles, preuves, exceptions et audit.

### Points importants à valoriser devant le jury

- Le projet ne se limite pas à un chatbot : il transforme des documents juridiques en base de connaissance exploitable.
- Le système utilise une architecture RAG pour réduire les hallucinations.
- Le projet est adapté au contexte tunisien : droit tunisien, multilingue, documents scannés, français/arabe/anglais.
- La solution couvre aussi la conformité opérationnelle : cas, contrôles, preuves, exceptions et actions.
- L'architecture est structurée en couches : API, services métier, traitement documentaire, base de données, IA.
- L'avancement est élevé : backend fonctionnel, nombreux modules réalisés, tests, documentation, Docker et CI.

### Chiffres à citer

- **10 sprints fonctionnels**.
- **57 fichiers Python** dans l'application.
- **122 routes API** côté backend.
- **27 collections MongoDB**.
- **33 fichiers de tests**.
- **2 interfaces frontend** : chatbot et panneau admin.
- **Pipeline IA complet** : extraction, OCR, embeddings, FAISS, LLM, quality guard.
- **Avancement global estimé : 85 % à 90 %**.

---

## 2. Planning recommandé pour une présentation de 15 minutes

| Partie | Durée | Contenu | Message principal |
|---|---:|---|---|
| 1. Introduction | 45 s | Nom du projet, objectif général | Daleel est une plateforme d'assistance juridique et de conformité. |
| 2. Contexte général | 1 min | Complexité des textes juridiques, multilinguisme, documents scannés | L'accès à l'information juridique est lent et difficile. |
| 3. Problématique | 1 min 15 | Recherche fiable, sources, traçabilité, conformité | Il faut répondre avec des sources, pas seulement générer du texte. |
| 4. Objectifs | 1 min | Centraliser, extraire, rechercher, répondre, suivre la conformité | Le projet transforme les textes en outil d'aide à la décision. |
| 5. Solution proposée | 1 min 30 | RAG juridique + Compliance Ops | Daleel combine recherche IA et gestion opérationnelle de conformité. |
| 6. Architecture globale | 1 min 45 | Frontend, FastAPI, services, MongoDB, FAISS, Ollama | L'architecture est modulaire et extensible. |
| 7. Pipeline documentaire et RAG | 2 min | Upload, OCR, nettoyage, chunking, embeddings, recherche, réponse | Le système répond à partir des documents retrouvés. |
| 8. Modules métier réalisés | 2 min | Lois, articles, exigences, amendements, criticité, roadmap, cases | Le projet couvre toute la chaîne juridique vers conformité. |
| 9. Qualité, sécurité et tests | 1 min | Auth, rate limiting, CORS, tests, CI, Docker | Le projet est préparé pour être stabilisé et industrialisé. |
| 10. Taux d'avancement | 1 min | Réalisé, en cours, restant | Le cœur fonctionnel est prêt ; il reste la consolidation finale. |
| 11. Limites et perspectives | 1 min | Frontend, E2E, sécurité navigateur, scalabilité vectorielle | Les limites sont identifiées et transformées en feuille de route. |
| 12. Conclusion | 45 s | Apport du projet et suite | Daleel adapte le RAG au contexte juridique tunisien avec traçabilité. |

---

## 3. Ordre des slides conseillé

### Slide 1 - Titre

**Daleel : Plateforme intelligente de recherche juridique et de conformité**

À dire :
> Mon projet s'appelle Daleel. C'est une plateforme qui aide à exploiter les textes juridiques tunisiens grâce à l'intelligence artificielle, tout en gardant une logique de sources, de traçabilité et de conformité.

### Slide 2 - Contexte général

Points :
- volume important de textes juridiques ;
- documents longs et complexes ;
- multilinguisme français/arabe/anglais ;
- documents parfois scannés ;
- besoin de conformité pour les entreprises.

Transition :
> À partir de ce contexte, la difficulté principale est de fournir une réponse fiable et exploitable, pas seulement une recherche de mots-clés.

### Slide 3 - Problématique

Question centrale :
> Comment aider un utilisateur à trouver rapidement une information juridique fiable, contextualisée et traçable dans un grand volume de documents ?

À insister :
- fiabilité ;
- sources ;
- anti-hallucination ;
- suivi des versions et amendements ;
- transformation en actions de conformité.

### Slide 4 - Objectifs

Objectifs :
- centraliser les documents ;
- extraire automatiquement le contenu ;
- indexer les textes ;
- répondre aux questions ;
- structurer les exigences ;
- piloter la conformité.

Transition :
> Pour répondre à ces objectifs, j'ai conçu Daleel autour de deux volets complémentaires.

### Slide 5 - Solution proposée

Deux blocs :

1. **RAG juridique**
   - recherche sémantique ;
   - récupération des passages pertinents ;
   - génération d'une réponse fondée sur les sources.

2. **Compliance Ops**
   - gestion de cas ;
   - exigences applicables ;
   - contrôles ;
   - preuves ;
   - exceptions ;
   - actions.

Phrase clé :
> Le but n'est pas de remplacer l'expert juridique, mais de lui donner un outil qui accélère la recherche et organise la conformité.

### Slide 6 - Architecture générale

Présenter simplement :
- interface chatbot/admin ;
- API FastAPI ;
- services métier ;
- traitement documentaire ;
- MongoDB ;
- FAISS ;
- Ollama ;
- OCR.

À éviter :
- ne pas détailler toutes les classes ;
- ne pas lister tous les endpoints.

### Slide 7 - Pipeline documentaire

Parcours :
1. upload ;
2. extraction ;
3. OCR si nécessaire ;
4. nettoyage ;
5. découpage ;
6. embeddings ;
7. indexation ;
8. recherche et réponse.

Phrase clé :
> Cette étape transforme un document brut en connaissance interrogeable.

### Slide 8 - Pipeline de réponse RAG

Étapes :
- question utilisateur ;
- détection de langue ;
- détection du domaine juridique ;
- recherche sémantique ;
- reranking ;
- construction du contexte ;
- génération LLM ;
- contrôle qualité ;
- réponse avec sources.

À valoriser :
- domain router ;
- retrieval partitionné base/amendements ;
- quality guard ;
- réponse multilingue.

### Slide 9 - Modules conformité

Présenter comme une chaîne :

**Texte juridique → exigence → applicabilité → action → criticité → roadmap → contrôle → preuve → exception**

Modules :
- profils d'entreprise ;
- exigences applicables ;
- actions réglementaires ;
- scoring de criticité ;
- amendements et audit ;
- cases ;
- controls/evidences/exceptions.

### Slide 10 - Réalisation technique et qualité

À citer :
- backend FastAPI ;
- MongoDB avec 27 collections ;
- 122 routes API ;
- tests automatisés ;
- CI GitHub Actions ;
- Docker ;
- authentification API key ;
- rate limiting sur endpoints sensibles ;
- CORS configurable ;
- FAISS avec fallback.

### Slide 11 - Taux d'avancement

Formulation conseillée :

> Le projet est avancé à environ 85 % à 90 %. Le cœur fonctionnel est réalisé : ingestion documentaire, RAG, recherche, modules juridiques, gestion de conformité, interfaces, tests et documentation. Les travaux restants concernent surtout la stabilisation finale.

Réalisé :
- backend ;
- RAG ;
- conformité ;
- case management ;
- tests ;
- documentation ;
- Docker/CI.

Reste :
- tests end-to-end ;
- amélioration UX frontend ;
- sécurité navigateur : CSP et sanitization ;
- scalabilité vectorielle sur très grands volumes ;
- préparation déploiement.

### Slide 12 - Conclusion

Message final :
> Daleel montre comment une architecture RAG peut être adaptée au contexte juridique tunisien, avec une attention particulière aux sources, aux versions, aux obligations et à la traçabilité.

---

## 4. Version courte si le jury donne seulement 8 à 10 minutes

| Partie | Durée | À garder |
|---|---:|---|
| Introduction + contexte | 1 min 30 | Besoin, complexité juridique, documents multilingues |
| Problématique | 1 min | Réponse fiable, sourcée, traçable |
| Solution | 1 min 30 | RAG juridique + Compliance Ops |
| Architecture | 1 min 30 | FastAPI, MongoDB, FAISS, Ollama, OCR |
| Pipeline | 1 min 30 | Document vers réponse sourcée |
| Modules réalisés | 1 min | Lois, exigences, actions, cases, contrôles |
| Avancement + suite | 1 min | 85-90 %, reste stabilisation |
| Conclusion | 30 s | Apport du projet |

Dans cette version courte, il faut éviter les détails de chaque sprint et regrouper les modules.

---

## 5. Démonstration recommandée

Si une démonstration est possible, choisir un scénario simple :

1. Ouvrir le chatbot.
2. Poser une question juridique.
3. Montrer que la réponse cite ou s'appuie sur des sources.
4. Ouvrir le panneau admin.
5. Montrer les documents, les statistiques ou les modules de conformité.

Scénario oral :
> Je pars d'un document juridique importé. Le système l'a découpé et indexé. Quand je pose une question, Daleel cherche les passages pertinents, construit un contexte, puis génère une réponse contrôlée.

Ne pas faire une démonstration trop longue : 2 minutes maximum.

---

## 6. Questions probables du jury et réponses courtes

### Pourquoi utiliser RAG au lieu d'un simple LLM ?

Parce qu'un LLM seul peut inventer des réponses. Avec RAG, la réponse est construite à partir de passages récupérés dans les documents, ce qui améliore la traçabilité.

### Pourquoi MongoDB ?

Les données sont hétérogènes : documents, pages, chunks, lois, articles, versions, exigences, actions, cas, preuves et exceptions. MongoDB permet de stocker ces objets flexibles efficacement.

### Pourquoi FAISS ?

FAISS permet une recherche vectorielle rapide sur les embeddings, donc une recherche par sens et non uniquement par mots-clés.

### Comment limiter les hallucinations ?

Le projet utilise des sources récupérées, un contrôle des références, un contrôle de fidélité et une réécriture conservative quand la réponse n'est pas assez fiable.

### Quel est l'apport principal ?

L'apport principal est l'adaptation d'une architecture RAG au domaine juridique tunisien, avec une extension vers le pilotage de conformité.

### Qu'est-ce qui reste à faire ?

Finaliser les tests end-to-end, améliorer l'interface, renforcer la sécurité navigateur et préparer le déploiement.

---

## 7. Conseil de présentation

Il faut présenter Daleel comme une progression logique :

**Problème documentaire → Recherche intelligente → Réponse sourcée → Structuration juridique → Pilotage conformité**

Le jury doit comprendre que le projet n'est pas seulement une application IA, mais un système complet qui relie documents, règles juridiques, décisions et actions.

