# Présentation de pré-soutenance - Projet Daleel

## Slide 1 - Titre

**Daleel : Plateforme intelligente de recherche juridique et de conformité**

Projet de Fin d'Études  
Pré-soutenance  

**Idée principale à dire :**  
Daleel est une plateforme qui aide à exploiter les textes juridiques tunisiens grâce à l'intelligence artificielle. Elle permet de rechercher, comprendre, questionner et suivre la conformité à partir de documents juridiques.

---

## Slide 2 - Contexte général

- Les textes juridiques sont nombreux, longs et souvent complexes.
- Les documents peuvent être en français, en arabe ou en anglais.
- Une partie des sources existe sous forme de PDF ou de documents scannés.
- Les entreprises ont besoin de comprendre rapidement quelles obligations s'appliquent à leur activité.
- Les équipes conformité doivent suivre les exigences, les preuves, les exceptions et les changements réglementaires.

**À l'oral :**  
Le projet part d'un besoin réel : rendre l'accès à l'information juridique plus rapide, plus structuré et plus fiable, surtout dans un contexte où les textes sont volumineux et parfois difficiles à exploiter automatiquement.

---

## Slide 3 - Problématique

**Comment aider un utilisateur à trouver une information juridique fiable, contextualisée et traçable dans un grand volume de documents ?**

Principales difficultés :

- recherche classique par mots-clés insuffisante ;
- textes longs, multilingues et parfois scannés ;
- besoin de réponses avec sources, pas seulement des réponses générées ;
- suivi des amendements et des versions d'articles ;
- transformation de l'information juridique en actions de conformité.

**À l'oral :**  
La problématique n'est pas uniquement de poser une question à un modèle IA. Le vrai enjeu est de connecter la réponse aux documents sources, de limiter les hallucinations, et de garder une traçabilité exploitable.

---

## Slide 4 - Objectifs du projet

- Centraliser les documents juridiques.
- Extraire automatiquement le contenu, y compris depuis des PDF scannés.
- Découper et indexer les textes pour la recherche sémantique.
- Permettre un Q&A juridique multilingue avec références.
- Structurer les lois en articles, versions, exigences et actions.
- Gérer les cas de conformité, les contrôles, les preuves et les exceptions.

**À l'oral :**  
L'objectif est de passer d'une simple base documentaire à une plateforme d'assistance juridique et de pilotage de conformité.

---

## Slide 5 - Solution proposée

**Daleel combine deux volets :**

1. **RAG juridique**  
   Recherche augmentée par génération : le système récupère les passages pertinents puis génère une réponse fondée sur ces sources.

2. **Compliance Ops**  
   Gestion opérationnelle de la conformité : cas, exigences, contrôles, preuves, exceptions, actions et audit.

Fonctionnalités clés :

- upload de documents PDF/DOCX/TXT/images ;
- extraction texte et OCR ;
- recherche vectorielle avec FAISS ;
- génération de réponses via LLM local ;
- contrôle qualité des réponses ;
- suivi des cas et des actions de conformité.

**À l'oral :**  
La solution ne remplace pas l'expert juridique. Elle l'assiste en accélérant la recherche, en organisant les preuves et en proposant des pistes d'analyse à vérifier.

---

## Slide 6 - Architecture générale

Architecture en couches :

- **Interface utilisateur** : chatbot et panneau admin.
- **API FastAPI** : endpoints, authentification, validation.
- **Services métier** : RAG, documents, recherche, conformité, orchestration.
- **Traitement documentaire** : extraction, OCR, nettoyage, découpage.
- **Stockage** : MongoDB pour les données structurées.
- **Recherche IA** : embeddings multilingues + FAISS.
- **Génération** : LLM local via Ollama.

**À l'oral :**  
J'ai choisi une architecture modulaire pour séparer l'API, la logique métier, le traitement documentaire et la persistance. Cela rend le projet plus maintenable et plus facile à faire évoluer.

---

## Slide 7 - Pipeline de traitement

Exemple de parcours d'un document :

1. Upload du document juridique.
2. Extraction du texte avec PyMuPDF, pdfminer ou OCR.
3. Nettoyage et normalisation du contenu.
4. Découpage en segments exploitables.
5. Génération des embeddings.
6. Indexation dans FAISS et stockage dans MongoDB.
7. Recherche sémantique et génération d'une réponse sourcée.

**À l'oral :**  
Ce pipeline permet de transformer un document brut en une base de connaissance interrogeable. Le système ne répond pas seulement à partir du modèle, il s'appuie d'abord sur les passages retrouvés dans les documents.

---

## Slide 8 - Modules réalisés

- Documents et RAG : upload, extraction, recherche, Q&A.
- Profils d'entreprise et applicabilité des exigences.
- Lois, articles, versions et actions réglementaires.
- Criticité et feuille de route de conformité.
- Amendements, versioning et journal d'audit.
- RAG avancé : routage par domaine, qualité, enrichissement contexte.
- Case management : dossiers, documents, constats et actions.
- Compliance steering : assessments, contrôles, preuves, exceptions.
- Conversation autour d'un cas.
- Orchestration et réponse structurée pour l'aide à la décision.

**À l'oral :**  
Le projet a été développé progressivement en 10 sprints. Chaque sprint ajoute une brique fonctionnelle qui rapproche la plateforme d'un outil complet d'assistance juridique et de conformité.

---

## Slide 9 - Taux d'avancement

**Avancement global estimé : 85 % à 90 %.**

Éléments réalisés :

- 10 sprints fonctionnels.
- Backend FastAPI opérationnel.
- Base MongoDB structurée en 27 collections.
- Recherche sémantique et pipeline RAG implémentés.
- Modules conformité et gestion de cas implémentés.
- Interface chatbot et panneau admin disponibles.
- 33 fichiers de tests.
- Documentation projet, audit et changelog disponibles.
- Docker et CI/CD préparés.

Reste à finaliser :

- durcissement sécurité : CSP, sanitization, configuration production ;
- tests end-to-end complets ;
- amélioration de l'interface frontend ;
- optimisation de la recherche vectorielle pour de très grands volumes ;
- stabilisation finale avant déploiement.

**À l'oral :**  
Le cœur fonctionnel du projet est réalisé. Les travaux restants concernent surtout l'industrialisation, la sécurité, les tests bout-en-bout et l'amélioration de l'expérience utilisateur.

---

## Slide 10 - Conclusion

**Daleel apporte :**

- un accès plus rapide aux textes juridiques ;
- des réponses contextualisées et sourcées ;
- une meilleure traçabilité des obligations ;
- un passage de la recherche documentaire vers le pilotage de conformité ;
- une base extensible pour intégrer d'autres domaines juridiques.

**Message final :**  
Ce projet montre comment une architecture RAG peut être adaptée à un contexte juridique tunisien, tout en gardant une logique de contrôle, de traçabilité et d'aide à la décision.

**À l'oral :**  
Pour la suite, l'objectif est de consolider la solution afin de la rendre plus robuste, plus sécurisée et plus prête pour une utilisation réelle.
