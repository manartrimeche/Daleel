# Notes Q&A — Soutenance Daleel (détails techniques retirés des annexes)

Document de préparation pour les questions du jury. Ces détails ont été retirés des slides (annexes 25-27 de la version prof) mais restent disponibles ici pour répondre précisément si le jury approfondit.

---

## 1. Fine-tuning des embeddings

| Paramètre | Valeur |
|---|---|
| Modèle de base | `paraphrase-multilingual-mpnet-base-v2` (768 dimensions) |
| Fonction de perte | `MultipleNegativesRankingLoss` (apprentissage contrastif) |
| Données d'entraînement | 973 paires question–article, issues de 487 articles "propres" (sur 2 565 du corpus) |
| Batch size | 32 |
| Learning rate | 2 × 10⁻⁵ — optimiseur AdamW |
| Epochs | 3 |
| Normalisation | L2 (similarité cosinus) |

### Protocole d'évaluation
- 50 requêtes gold : 30 en français, 20 en arabe
- **Zéro fuite** : articles jamais vus pendant l'entraînement
- Requêtes générées par LLM, **relues et validées par le juriste de Didax IT**
- Métriques : Recall@k, MRR@10, nDCG
- Comparaison équitable : même corpus, mêmes 50 questions, seul le modèle d'embedding change

### Résultats (rappel slide 15)
- Recall@1 : 0,40 → 0,60 (**+50 %**)
- Recall@5 : 0,60 → 0,84 (**+40 %**)
- Recall@5 arabe : 0,40 → 0,75 (**+87 %**)

---

## 2. Recherche & pipeline RAG

| Composant | Détail |
|---|---|
| Recherche dense | Index **FAISS (HNSW)** sur embeddings fine-tunés |
| Recherche lexicale | Signaux mots-clés (correspondance exacte de termes) |
| Fusion hybride | Pondération **0,56 dense / 0,20 lexical / 0,14 / 0,10** (4 signaux combinés) |
| Reranking | Cross-encoder **ms-marco MiniLM-L6**, avec seuil de rejet |
| Segmentation (chunking) | Chunks de **1 500 caractères**, chevauchement de **200** |
| Routeur de domaine | **5 domaines juridiques**, repli (fallback) LLM si ambigu |
| Garde-qualité | Vérification des références + citations + cohérence de langue |

### Points d'attention pour le jury
- La fusion hybride à 4 poids permet d'équilibrer pertinence sémantique (dense) et précision terminologique (lexical) — important pour le vocabulaire juridique tunisien où certains termes techniques n'ont pas de bon équivalent sémantique.
- Le retrieval partitionné (slide 11) évite de mélanger loi en vigueur et amendements lors de la recherche.
- Le routeur de domaine réduit le bruit en limitant la recherche au(x) domaine(s) juridique(s) pertinent(s) avant le retrieval.

---

## 3. Génération, agent & industrialisation

### LLM de génération
| Paramètre | Valeur |
|---|---|
| Modèle | **qwen2.5:7b** via **Ollama** (licence Apache 2.0, 100 % on-premise) |
| Température | 0,15 |
| Top-p | 0,9 |
| Fenêtre de contexte | 8 192 tokens |
| Function calling | Natif Ollama — appels d'outils typés (pas de parsing fragile de texte) |

### Agent ReAct
- **12 outils** organisés en **3 tiers** : recherche · graphe de connaissances · conformité
- Garde-fous : budget d'itérations + timeout global (évite les boucles infinies)
- Temps de réponse observé : 8 à 15 secondes (raisonnement complet de bout en bout)
- Traçabilité 100 % : chaque étape journalisée et auditable

### Tests & CI/CD
- **951 tests** collectés, **~50 % de couverture** (seuil CI)
- CI : **GitHub Actions**, Python **3.11 → 3.13**
- LLM mocké en environnement de test (pas d'appel réel à Ollama en CI)

### Déploiement
- **Docker Compose** : 3 services — MongoDB · Ollama · FastAPI
- Architecture **multi-tenant** : isolation par organisation, vue Super Admin agrégée
- Mode SaaS ou on-premise (souveraineté des données juridiques)

---

## 4. Cohérence des chiffres clés (vérifié sur les 24 slides)

| Chiffre | Signification | Cohérence |
|---|---|---|
| 2 565 | Articles indexés dans le corpus (ar/fr) | ✓ cohérent (slides 7, 8, 13) |
| 487 | Articles "propres" sélectionnés pour le fine-tuning | ✓ (slide 13) |
| 973 | Paires question–article générées pour l'entraînement | ✓ (slide 13) |
| 50 | Requêtes gold d'évaluation (30 fr / 20 ar) | ✓ (slides 13, 15) |
| +50 % / +40 % / +87 % | Gains Recall@1, Recall@5, Recall@5 arabe | ✓ cohérent (slides 15, 24) |
| 951 | Tests collectés | ✓ (slides 22, 24) |
| ~50 % | Couverture de tests | ✓ (slides 22, 24) |
| 8-15 s | Temps de réponse de l'agent | ✓ (slides 12, 18) |
| 12 outils / 3 tiers | Outils de l'agent ReAct | ✓ (slides 12, 24) |
| 6 modules | Pipeline RAG | ✓ (slides 11, 24) |
