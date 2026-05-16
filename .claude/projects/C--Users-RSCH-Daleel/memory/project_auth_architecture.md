---
name: Architecture auth multi-tenant validée
description: Flux auth complet validé - auth globale, sélection tenant, permissions scoped, admin plateforme vs admin entreprise
type: project
---

Flux d'accès validé (2026-05-10) :
1. Login (auth globale) → identifie l'utilisateur
2. Sélection entreprise/secteur → définit le contexte tenant
3. Chargement profil entreprise → config métier + permissions
4. Permissions tenant-scoped → actions autorisées selon rôle dans l'entreprise

Deux niveaux d'admin :
- **Super admin (plateforme)** : voit tout, gère les entreprises, config générale, supervision
- **Admin entreprise** : scopé à son entreprise, gère ses membres et ses rôles

Profil entreprise doit contenir :
- Nom, secteur, identifiant tenant, logo/branding
- Type de plan/abonnement, statut actif/inactif
- Règles d'accès, liste admins, liste membres

Écrans à implémenter :
- Login
- Sélection entreprise/secteur
- Dashboard utilisateur
- Dashboard admin entreprise
- Profil entreprise
- Gestion users
- Gestion rôles
- Paramètres plateforme (super admin)

**Why:** Architecture multi-tenant SaaS standard, recommandée pour cloisonner les accès entre tenants.
**How to apply:** Toujours séparer auth (qui es-tu) / tenant selection (quel contexte) / authorization (que peux-tu faire). Ne jamais donner d'accès cross-tenant sauf au super admin.
