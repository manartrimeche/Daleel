---
name: Architecture modules validée
description: Les 7 modules fonctionnels validés pour Daleel avec système admin multi-entreprise et gestion des rôles
type: project
---

7 modules validés (2026-05-10) :
1. Dashboard — vue d'ensemble
2. Chat — RAG conversationnel (coeur de l'app)
3. Documents — upload, OCR, gestion
4. Conformité — Posture + Évaluations + Contrôles + Exceptions (fusionné)
5. Dossiers — cases de conformité + findings + actions
6. Corpus Législatif — Lois + Articles + Amendements (fusionné)
7. Administration — Users, Profil Entreprise, Audit Log, Config système

**Why:** Simplification de 14 sections éclatées vers 7 modules cohérents. L'ancien admin.html avait tout à plat.
**How to apply:** Toute implémentation UI doit suivre cette structure de 7 modules. Les rôles sont : owner, admin, member, viewer.

Système auth à implémenter :
- Login/signup avec choix secteur obligatoire
- JWT tokens
- Invitations par admin
- Profil entreprise lié au moteur d'applicabilité
- Modèle LLM adapté au secteur de l'entreprise
