---
name: Règles métier clés validées par l'utilisateur
description: Isolation des données par tenant, upload PDF only avec processing auto, super admin n'accède pas aux données métier des entreprises
type: feedback
---

1. **Isolation totale des données métier par entreprise** : historique chat, dossiers, conformité sont privés à l'entreprise. Le super admin ne peut PAS y accéder — il gère uniquement la plateforme (entreprises, config, supervision).
**Why:** Cloisonnement strict des données entre tenants, même vis-à-vis du super admin.
**How to apply:** Toujours filtrer par organization_id sur les collections métier. Le super admin voit les stats agrégées mais jamais le contenu.

2. **Upload PDF uniquement** : les documents doivent être uploadés en format PDF.
**Why:** Standardisation du format d'entrée.
**How to apply:** Valider le MIME type à l'upload, rejeter tout ce qui n'est pas application/pdf.

3. **Data processing automatique à l'upload** : quand un PDF est uploadé, le pipeline complet se lance automatiquement (extraction → nettoyage → chunking → embedding → indexation FAISS).
**Why:** L'utilisateur ne doit pas avoir à déclencher manuellement les étapes de traitement.
**How to apply:** L'endpoint d'upload doit enchaîner tout le pipeline en background task après réception du fichier.
