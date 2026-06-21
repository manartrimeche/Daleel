# Captures d'écran à intégrer dans le rapport

> Lance l'app (`docker-compose up` puis ouvrir `http://localhost:3000`), reproduis le scénario décrit, prends la capture, sauvegarde sous `figures/screen_<n>.png`, puis insère dans le rapport à l'endroit indiqué.
>
> Conseil format : PNG, largeur 1200-1600 px, masquer les données sensibles (emails réels, noms d'entreprise réels) → utiliser un compte de démo.

---

## Section 3.6 — Démonstrations qualitatives Legal RAG

### Capture 1 — Réponse RAG classique (Démo 1)

**Section rapport** : 3.6.1
**Scénario** :
1. Connecte-toi au chatbot en mode utilisateur
2. Pose la question : « Quelle est la durée maximale de la période d'essai pour un CDI en Tunisie ? »
3. Attends la réponse complète (~ 3-5 s)
4. Capture l'écran : question + réponse en 4 blocs + sources `[Source N]` cliquables

**Fichier** : `figures/screen_1_rag_classique_periode_essai.png`
**Légende** : *Figure 3.1 — Réponse du pipeline RAG classique à une requête simple sur la période d'essai d'un CDI. La réponse suit le format en quatre blocs et cite chaque article par un lien `[Source N]` ouvrant le passage exact.*

---

### Capture 2 — Réponse agent autonome avec journal d'outils (Démo 2)

**Section rapport** : 3.6.2
**Scénario** :
1. Active le mode « Agent autonome » (toggle en haut du chat)
2. Charge un profil entreprise de démo (25 salariés, traitement données)
3. Pose : « Ma société de 25 salariés traite des données clients sensibles. Quelles obligations RGPD et INPDP s'appliquent ? Donne-moi un plan d'action priorisé. »
4. Attends la fin (~ 10-20 s, plusieurs itérations)
5. Capture l'écran : réponse finale + **panneau latéral / accordéon avec le journal des appels d'outils** (`semantic_search`, `match_exigences`, `generate_roadmap`, …)

**Fichier** : `figures/screen_2_agent_autonome_compliance_log.png`
**Légende** : *Figure 3.2 — Réponse de l'agent autonome ReAct sur une requête de conformité multilingue. Le panneau latéral expose le journal des six outils invoqués au fil des itérations avec leur durée d'exécution.*

---

### Capture 3 — Reformulation derja (Démo 3)

**Section rapport** : 3.6.3
**Scénario** :
1. Mode chatbot classique
2. Pose en derja : « نحب نفسخ عقد عاملة بدون ما نخلصها ؟ »
3. Capture l'écran après réponse : on doit voir l'**indicateur derja_detected** et la **reformulation française** affichée (en italique ou dans une bulle informative), puis la réponse juridique structurée

**Fichier** : `figures/screen_3_derja_normalisation.png`
**Légende** : *Figure 3.3 — Traitement d'une question en dialecte tunisien (derja). Le système affiche la reformulation française produite par le normalisateur avant d'exécuter le pipeline RAG.*

---

### Capture 4 — Statut garde-qualité (optionnelle mais valorisante)

**Section rapport** : 3.6 (à insérer en fin de section comme illustration de la sécurité)
**Scénario** :
1. Pose volontairement une question ambiguë ou hors corpus pour déclencher un rewrite
2. Ou prends une réponse réelle avec badge garde-qualité visible
3. Capture l'écran avec **badge vert (`accepted`) OU orange (`rewritten` avec tooltip listant les incidents)**

**Fichier** : `figures/screen_4_quality_guard_badge.png`
**Légende** : *Figure 3.4 — Affichage du statut de la garde-qualité dans le chatbot. Le badge coloré informe l'utilisateur du verdict (accepté, réécrit, rejeté) et expose la liste des incidents en survol.*

---

## Section 4.3 — Interfaces utilisateur

### Capture 5 — Chatbot multilingue (vue d'ensemble)

**Section rapport** : 4.3.1
**Scénario** :
1. Capture d'écran de la page Chat.jsx avec une conversation existante visible (français)
2. Bien montrer : sélecteur de langue (ar/fr/en) en haut, sources cliquables, bouton feedback 👍/👎, zone de saisie avec icône micro (vocal)

**Fichier** : `figures/screen_5_chatbot_overview.png`
**Légende** : *Figure 4.1 — Interface du chatbot conversationnel Daleel. La barre supérieure offre le sélecteur trilingue, et chaque réponse expose ses sources cliquables et un bouton de feedback utilisateur.*

---

### Capture 6 — Vue RTL en arabe

**Section rapport** : 4.3.4 (internationalisation)
**Scénario** :
1. Bascule la langue UI en arabe
2. Reproduis la même conversation qu'en capture 5 mais en arabe
3. La mise en page doit être en **RTL** (boutons, menu, fil de conversation inversés)

**Fichier** : `figures/screen_6_chatbot_rtl_arabic.png`
**Légende** : *Figure 4.2 — Adaptation automatique de l'interface en mode RTL pour la langue arabe. L'ensemble de la mise en page est inversé sans dégradation visuelle.*

---

### Capture 7 — Panneau admin / Documents

**Section rapport** : 4.3.2
**Scénario** :
1. Connecte-toi en admin
2. Va sur `Admin → Documents`
3. Capture la liste de documents avec **statuts d'ingestion visibles** (uploaded → extracted → cleaned → segmented → embedded → indexed)
4. Idéalement avoir un document avec barre de progression en cours d'ingestion

**Fichier** : `figures/screen_7_admin_documents.png`
**Légende** : *Figure 4.3 — Vue d'administration des documents. Chaque document est suivi à travers les six étapes du pipeline d'ingestion, avec ré-encodage à la demande possible.*

---

### Capture 8 — Panneau admin / Cases (cycle conformité)

**Section rapport** : 4.3.2
**Scénario** :
1. Va sur `Admin → Cases`
2. Capture la vue : liste filtrable par statut + sévérité + organisation
3. Idéalement ouvrir un cas et capturer aussi le détail : timeline des messages, constats, actions, preuves

**Fichier** : `figures/screen_8_admin_cases_list.png` et `figures/screen_8b_admin_case_detail.png`
**Légende capture liste** : *Figure 4.4 — Tableau de bord des dossiers de conformité. Filtrage par statut, sévérité et organisation permettent au responsable de prioriser les revues.*
**Légende capture détail** : *Figure 4.5 — Vue détaillée d'un dossier de conformité : timeline de la conversation orchestrateur, constats identifiés, actions correctives et preuves rattachées.*

---

### Capture 9 — Dashboard BI

**Section rapport** : 4.3.3
**Scénario** :
1. Connecte-toi sur le tableau de bord (`Dashboard.jsx`)
2. Capture une vue avec **données réelles** (ou démo avec données seedées) :
   - Score global de conformité
   - Évolution sur 12 mois (graphique courbe)
   - Heatmap domaine × organisation
   - Top actions critiques en retard

**Fichier** : `figures/screen_9_dashboard_bi.png`
**Légende** : *Figure 4.6 — Tableau de bord de la posture de conformité. Les indicateurs clés, la courbe d'évolution et la heatmap domaine × organisation permettent une lecture synthétique en quelques secondes.*

---

### Capture 10 — Décision ASK / CLARIFY dans le frontend

**Section rapport** : 4.2.2
**Scénario** :
1. Crée un cas de conformité avec des informations volontairement incomplètes (peu de faits)
2. Lance l'orchestrateur
3. Le frontend doit afficher le **formulaire ASK dynamique** demandant les faits manquants

**Fichier** : `figures/screen_10_orchestrator_ask.png`
**Légende** : *Figure 4.7 — Frontend dynamique en réponse à la décision ASK de l'orchestrateur. Le formulaire est généré automatiquement à partir de la liste des faits manquants identifiés par le LLM.*

---

### Capture 11 — Détails d'une action avec criticité expliquée (optionnelle)

**Section rapport** : 4.1.2 (illustrer la transparence du moteur de criticité)
**Scénario** :
1. Ouvre une action classée « critique »
2. Capture le panneau qui montre le **score, le niveau et la liste des `criticality_reasons`**
3. Exemple visé : « Modalité 'obligation' (score de base 0.65) / Domaine données personnelles (+0.15) / Sanction (+0.10) / Montant pécuniaire (+0.05) → score 0.95 critique »

**Fichier** : `figures/screen_11_criticality_explained.png`
**Légende** : *Figure 4.8 — Affichage de l'explication d'une criticité dans l'interface. Chaque composante du score est exposée, permettant à l'auditeur de comprendre pourquoi une action est classée critique.*

---

## Récapitulatif — total de figures à produire

| # | Fichier suggéré | Section rapport | Importance |
|---|---|---|---|
| 1 | screen_1_rag_classique_periode_essai.png | 3.6.1 | Indispensable |
| 2 | screen_2_agent_autonome_compliance_log.png | 3.6.2 | Indispensable |
| 3 | screen_3_derja_normalisation.png | 3.6.3 | Très valorisant |
| 4 | screen_4_quality_guard_badge.png | 3.6 fin | Optionnelle |
| 5 | screen_5_chatbot_overview.png | 4.3.1 | Indispensable |
| 6 | screen_6_chatbot_rtl_arabic.png | 4.3.4 | Très valorisant |
| 7 | screen_7_admin_documents.png | 4.3.2 | Indispensable |
| 8 | screen_8_admin_cases_list.png + 8b detail | 4.3.2 | Indispensable |
| 9 | screen_9_dashboard_bi.png | 4.3.3 | Indispensable |
| 10 | screen_10_orchestrator_ask.png | 4.2.2 | Très valorisant |
| 11 | screen_11_criticality_explained.png | 4.1.2 | Optionnelle |

**Minimum vital pour soutenance** : 1, 2, 5, 7, 8, 9 (six captures).
**Recommandé** : ajouter 3 et 6 pour valoriser le multilingue + derja, et 10 pour illustrer ASK/CLARIFY.
**Bonus** : 4 et 11 pour valoriser la transparence garde-qualité et criticité.

---

## Comment insérer dans le rapport

À l'endroit indiqué dans le rapport, après le paragraphe pertinent, ajouter :

```markdown
![Légende courte alt](figures/screen_X_nom.png)

**Figure X.Y — Légende complète telle que définie ci-dessus.**
```

Pour un export PDF via Pandoc, ajouter dans le YAML en tête du rapport (à créer si besoin) :

```yaml
---
title: "Daleel — Rapport de PFE"
author: "Manar Trimeche"
date: "2026"
documentclass: report
geometry: margin=2.5cm
fontsize: 11pt
header-includes:
  - \usepackage{float}
  - \floatplacement{figure}{H}
---
```
