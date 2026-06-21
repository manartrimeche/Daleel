# Déploiement gratuit de Daleel

Ce guide déploie **tout Daleel en ligne, gratuitement**, sans modifier le cœur de
ton travail (pipeline RAG, embeddings, FAISS, domaine juridique). Seul le
**transport du LLM** change (Ollama local → API hébergée), via une simple variable.

## Architecture cible

| Composant | Hébergeur gratuit | Rôle |
|---|---|---|
| **Frontend** (React/Vite) | **Vercel** | Interface, sert le `dist/` |
| **Backend** (FastAPI) | **Hugging Face Spaces** (Docker, 16 Go RAM) | API + RAG + embeddings + FAISS |
| **Base de données** | **MongoDB Atlas** (M0, 512 Mo) | Documents + vecteurs |
| **LLM** | **OpenRouter** (modèle Qwen2.5) | Génération des réponses |

Le frontend appelle l'API en **chemins relatifs** (`/api/v1/...`). Sur Vercel, le
fichier [`frontend/vercel.json`](../frontend/vercel.json) **réécrit `/api/*` vers le
backend Hugging Face** → aucun code frontend à toucher, et pas de souci de CORS.

---

## 1. MongoDB Atlas (base de données)

1. Crée un compte sur https://www.mongodb.com/cloud/atlas → cluster **M0 (gratuit)**.
2. **Database Access** : crée un utilisateur + mot de passe.
3. **Network Access** : autorise `0.0.0.0/0` (toutes IP — nécessaire car l'IP de HF varie).
4. Récupère l'URI de connexion :
   `mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority`

---

## 2. OpenRouter (LLM gratuit, fidèle au PFE)

1. Crée un compte sur https://openrouter.ai → **Keys** → génère une clé `sk-or-...`.
2. Le modèle retenu est **`openai/gpt-oss-120b:free`** — modèle ouvert, testé en réel :
   répond bien en français juridique et **sans rate-limit (429)**, ce qui le rend fiable
   pour une démo en direct.
   > ⚠️ `qwen2.5:7b` (utilisé en local) **n'est plus disponible en gratuit** sur
   > OpenRouter, et les Qwen/Llama `:free` sont souvent throttlés (429). Le suffixe
   > **`:free`** reste obligatoire pour ne rien payer. Liste à jour des gratuits :
   > https://openrouter.ai/models?max_price=0.
   > Alternative également testée et fonctionnelle : `openai/gpt-oss-20b:free`.

> Alternatives compatibles (même mécanisme, `DALEEL_LLM_PROVIDER=openai`) :
> Groq `https://api.groq.com/openai/v1`, Together `https://api.together.xyz/v1`.

---

## 3. Backend → Hugging Face Spaces

1. Sur https://huggingface.co → **New Space** → **SDK : Docker** → **Blank**.
2. Pousse le code du projet dans le Space (ou connecte le dépôt GitHub).
   Le `Dockerfile` à la racine builde **frontend + backend** automatiquement.
3. À la racine du Space, le `README.md` doit commencer par ce bloc de métadonnées
   (c'est lui qui dit à HF d'exposer le port 8000) :

   ```yaml
   ---
   title: Daleel API
   emoji: ⚖️
   colorFrom: blue
   colorTo: indigo
   sdk: docker
   app_port: 8000
   ---
   ```

4. **Settings → Variables and secrets** : ajoute (en *Secrets* pour les clés) :

   | Variable | Valeur |
   |---|---|
   | `DALEEL_MONGODB_URL` | l'URI Atlas de l'étape 1 |
   | `DALEEL_MONGODB_DB_NAME` | `manar` |
   | `DALEEL_LLM_PROVIDER` | `openai` |
   | `DALEEL_LLM_BASE_URL` | `https://openrouter.ai/api/v1` |
   | `DALEEL_LLM_API_KEY` | ta clé `sk-or-...` |
   | `DALEEL_LLM_MODEL` | `openai/gpt-oss-120b:free` |
   | `DALEEL_JWT_SECRET_KEY` | une chaîne aléatoire ≥ 32 caractères |
   | `DALEEL_CORS_ORIGINS` | l'URL Vercel (ex. `https://daleel.vercel.app`) |
   | `DALEEL_SUPER_ADMIN_EMAIL` | ton email (crée le 1er compte admin) |
   | `DALEEL_SUPER_ADMIN_PASSWORD` | un mot de passe fort |
   | `DALEEL_APP_BASE_URL` | l'URL Vercel |

   > Génère le secret JWT : `python -c "import secrets;print(secrets.token_urlsafe(48))"`

5. Le Space build puis démarre. Au 1er lancement, le modèle d'embeddings (~1 Go)
   se télécharge — compte quelques minutes. URL finale : `https://<user>-<space>.hf.space`.
6. Teste : `https://<user>-<space>.hf.space/api/v1/health` doit répondre.

---

## 4. Frontend → Vercel

1. Dans [`frontend/vercel.json`](../frontend/vercel.json), remplace
   `REMPLACER-PAR-TON-SPACE.hf.space` par l'URL réelle de ton Space HF.
2. Sur https://vercel.com → **New Project** → importe le dépôt GitHub.
3. **Root Directory** : `frontend`. Vercel détecte Vite automatiquement
   (build `vite build`, output `dist`).
4. Déploie. Tu obtiens `https://<projet>.vercel.app`.
5. Reviens à l'étape 3 et mets `DALEEL_CORS_ORIGINS` / `DALEEL_APP_BASE_URL` à jour
   avec cette URL, puis redémarre le Space.

---

## Récapitulatif des limites du gratuit

- **Atlas M0** : 512 Mo de stockage (suffisant pour une démo / un PFE).
- **HF Spaces gratuit** : CPU only, se met en veille après inactivité (réveil au
  1er appel ≈ 30 s). Pas de stockage persistant → les fichiers uploadés et l'index
  FAISS sont reconstruits au redémarrage (normal pour une démo).
- **OpenRouter** : quotas journaliers selon le modèle gratuit choisi.

## Revenir en local (dev)

Aucun changement : laisse `DALEEL_LLM_PROVIDER=ollama` dans ton `.env` local et
tout fonctionne comme avant avec Ollama + `qwen2.5:7b`.
