# Intégration du modèle fine-tuné dans Daleel

Une fois `04_finetune_embeddings.py` terminé avec succès, le modèle se trouve dans
`training/models/daleel-embedding-finetuned/`.

## Changement de config : ZÉRO modification de code

`app/services/embedding_service.py` (ligne 87) fait déjà :

```python
_model = SentenceTransformer(settings.embedding_model)
```

Et `SentenceTransformer` accepte indifféremment un HF id OU un chemin local.
Il suffit donc de changer `DALEEL_EMBEDDING_MODEL` dans `.env` :

```env
# Avant
DALEEL_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-mpnet-base-v2

# Après
DALEEL_EMBEDDING_MODEL=./training/models/daleel-embedding-finetuned
DALEEL_EMBEDDING_DIMENSION=768
```

> Garde `embedding_dimension=768` — le fine-tuning ne change PAS la dimension.

## Pipeline de mise en prod (CRITIQUE)

**Les embeddings stockés dans MongoDB ont été produits avec l'ancien modèle.**
Tu ne peux pas simplement changer le modèle : il faut ré-encoder tous les `chunks`.

### Étape 1 — Backup des embeddings actuels

```powershell
# Dump collection chunks (sécurité rollback)
mongodump --uri "mongodb://localhost:27017" --db daleel --collection chunks --out backup/before_finetuning/
```

### Étape 2 — Ré-embedding avec le nouveau modèle

Script recommandé (à écrire au besoin, ~30 lignes) : itérer sur `chunks`,
`embed_texts(batch)` avec le nouveau modèle, `update_one({"id": id}, {"$set": {"embedding": vec, "embedding_model_version": "daleel-v1-finetuned"}})`.

Idée : ajouter le champ `embedding_model_version` pour identifier quel modèle a
produit chaque vecteur — utile pour un rollback partiel ou un A/B test.

### Étape 3 — Redémarrage de l'API

Au boot, `app/services/faiss_index.py` reconstruit l'index FAISS depuis Mongo.
Donc : redémarrer `uvicorn` = index rebuild automatique avec les nouveaux
vecteurs. Aucune action manuelle.

## Rollback

Si les métriques terrain se dégradent (feedback utilisateur, benchmark en prod) :

1. Restaurer la collection depuis le backup :
   ```powershell
   mongorestore --uri "mongodb://localhost:27017" --db daleel --collection chunks backup/before_finetuning/daleel/chunks.bson --drop
   ```
2. Remettre `DALEEL_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-mpnet-base-v2` dans `.env`.
3. Redémarrer l'API → FAISS rebuild avec les anciens vecteurs.

**Durée de rollback : ~2 minutes.** Bien inférieure au temps de ré-embedding initial.

## Précautions

| Aspect | À vérifier |
|--------|-----------|
| Dimension | 768 (inchangée). Vérifier avec `GET /admin/vector-stats` |
| Cache embeddings | Le LRU cache dans `embedding_service.py` est lié au *process*, donc redémarrer l'API suffit. Pas de cache Redis à invalider |
| Queries vs chunks | `search_service.py` auto-détecte la dimension dominante des chunks. Tant que tous les chunks sont à jour, pas de mismatch |
| Index FAISS | Rebuildé automatiquement au boot. Pas d'index fichier à supprimer |
| Admin UI | Le modèle apparaît dans `GET /admin/stats` sous `embedding_model` — utile pour confirmer la bascule |

## A/B Test progressif (optionnel, avancé)

Pour tester sans migrer toute la base :

1. Ajouter le champ `embedding_model_version` à `chunks` (défaut "mpnet-v1").
2. Ré-encoder seulement un sous-ensemble (ex: une loi spécifique) vers "daleel-v1-finetuned".
3. Dans `search_service.py`, router les queries selon un flag de config vers
   l'une ou l'autre version.
4. Comparer les métriques terrain (feedback, Recall apparent via `sources`).

C'est de l'over-engineering pour un PFE ; le rollback backup/restore suffit largement.
