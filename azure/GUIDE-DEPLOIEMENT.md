# Daleel — Guide de Deploiement Azure

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure Resource Group                      │
│                       rg-daleel                              │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Container Apps Environment                    │   │
│  │                                                       │   │
│  │  ┌─────────────────┐    ┌──────────────────────┐     │   │
│  │  │  daleel-api      │    │  daleel-ollama       │     │   │
│  │  │  (FastAPI +      │───>│  (qwen2.5:7b)        │     │   │
│  │  │   React frontend)│    │  ingress: internal    │     │   │
│  │  │  ingress: externe│    │  4 CPU / 8 Go RAM     │     │   │
│  │  │  2 CPU / 4 Go RAM│    └──────────────────────┘     │   │
│  │  │  1-3 replicas    │                                  │   │
│  │  └────────┬─────────┘                                  │   │
│  └───────────┼────────────────────────────────────────────┘   │
│              │                                                │
│  ┌───────────▼──────────┐   ┌──────────────────────┐        │
│  │  Cosmos DB            │   │  Blob Storage         │        │
│  │  (API MongoDB 7.0)    │   │  (uploads)            │        │
│  │  Base: manar           │   │  stdaleeluploads      │        │
│  └───────────────────────┘   └──────────────────────┘        │
│                                                              │
│  ┌───────────────────────┐                                   │
│  │  Container Registry    │                                   │
│  │  acrdaleel.azurecr.io  │                                   │
│  └───────────────────────┘                                   │
└─────────────────────────────────────────────────────────────┘
```

## Pre-requis

1. **Compte Azure** avec un abonnement actif
2. **Azure CLI** installe :
   ```powershell
   # Windows
   winget install Microsoft.AzureCLI

   # Linux / WSL
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   ```
3. **Extensions Azure CLI** :
   ```bash
   az extension add --name containerapp --upgrade
   az extension add --name cosmosdb-preview --upgrade
   ```

## Deploiement rapide (script automatise)

### 1. Configurer les variables

```powershell
cd azure
Copy-Item .env.azure.template .env.azure
# Editez .env.azure avec vos valeurs
```

Variables obligatoires a remplir :
- `AZURE_SUBSCRIPTION_ID` — votre ID d'abonnement Azure
- `DALEEL_JWT_SECRET_KEY` — generer avec : `openssl rand -base64 64`
- `DALEEL_API_KEY` — cle API pour l'acces a l'application
- `DALEEL_ADMIN_API_KEY` — cle API admin

### 2. Lancer le deploiement

```powershell
# PowerShell (Windows)
.\deploy.ps1

# Bash (Linux / WSL / macOS)
chmod +x deploy.sh
./deploy.sh
```

### 3. Telecharger le modele LLM

```bash
az containerapp exec \
  -g rg-daleel \
  -n daleel-ollama \
  --command "ollama pull qwen2.5:7b"
```

### 4. Verifier

```bash
curl https://<votre-url>.azurecontainerapps.io/api/v1/health
```

## Deploiement manuel pas-a-pas

### Etape 1 : Connexion et configuration

```bash
# Se connecter
az login

# Selectionner l'abonnement
az account set --subscription "<votre-subscription-id>"

# Creer le groupe de ressources
az group create --name rg-daleel --location francecentral
```

### Etape 2 : Container Registry

```bash
# Creer le registry
az acr create \
  --resource-group rg-daleel \
  --name acrdaleel \
  --sku Basic \
  --admin-enabled true

# Build et push l'image (via ACR Tasks — pas besoin de Docker local)
az acr build \
  --registry acrdaleel \
  --image daleel-api:latest \
  --file Dockerfile .
```

### Etape 3 : Cosmos DB (MongoDB)

```bash
# Creer le compte
az cosmosdb create \
  --resource-group rg-daleel \
  --name daleel-cosmos \
  --kind MongoDB \
  --server-version "7.0" \
  --default-consistency-level Session \
  --locations regionName=francecentral failoverPriority=0

# Creer la base
az cosmosdb mongodb database create \
  --resource-group rg-daleel \
  --account-name daleel-cosmos \
  --name manar

# Recuperer la connection string
az cosmosdb keys list \
  --resource-group rg-daleel \
  --name daleel-cosmos \
  --type connection-strings \
  --query "connectionStrings[0].connectionString" -o tsv
```

### Etape 4 : Container Apps Environment

```bash
az containerapp env create \
  --resource-group rg-daleel \
  --name daleel-env \
  --location francecentral
```

### Etape 5 : Deployer Ollama

```bash
az containerapp create \
  --resource-group rg-daleel \
  --name daleel-ollama \
  --environment daleel-env \
  --image ollama/ollama:latest \
  --cpu 4 --memory 8Gi \
  --min-replicas 1 --max-replicas 1 \
  --target-port 11434 \
  --ingress internal
```

### Etape 6 : Deployer Daleel API

```bash
# Recuperer les credentials ACR
ACR_PASSWORD=$(az acr credential show --name acrdaleel --query "passwords[0].value" -o tsv)

# Recuperer l'URL Ollama interne
OLLAMA_URL="https://$(az containerapp show -g rg-daleel -n daleel-ollama --query 'properties.configuration.ingress.fqdn' -o tsv)"

# Recuperer la connection string Cosmos
COSMOS_CONN=$(az cosmosdb keys list -g rg-daleel -n daleel-cosmos --type connection-strings --query "connectionStrings[0].connectionString" -o tsv)

# Deployer
az containerapp create \
  --resource-group rg-daleel \
  --name daleel-api \
  --environment daleel-env \
  --image acrdaleel.azurecr.io/daleel-api:latest \
  --registry-server acrdaleel.azurecr.io \
  --registry-username acrdaleel \
  --registry-password "$ACR_PASSWORD" \
  --cpu 2 --memory 4Gi \
  --min-replicas 1 --max-replicas 3 \
  --target-port 8000 \
  --ingress external \
  --env-vars \
    "DALEEL_ENV=production" \
    "DALEEL_MONGODB_URL=$COSMOS_CONN" \
    "DALEEL_MONGODB_DB_NAME=manar" \
    "DALEEL_LLM_BASE_URL=$OLLAMA_URL" \
    "DALEEL_LLM_MODEL=qwen2.5:7b" \
    "DALEEL_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-mpnet-base-v2" \
    "DALEEL_EMBEDDING_DIMENSION=768" \
    "DALEEL_VECTOR_SEARCH_BACKEND=faiss" \
    "DALEEL_DOMAIN_ROUTER_ENABLED=true" \
    "DALEEL_QUALITY_GUARD_ENABLED=true" \
    "DALEEL_KG_LIGHT_ENABLED=true"
```

### Etape 7 : Telecharger le modele et verifier

```bash
# Telecharger qwen2.5:7b dans Ollama
az containerapp exec -g rg-daleel -n daleel-ollama --command "ollama pull qwen2.5:7b"

# Tester le health check
API_URL="https://$(az containerapp show -g rg-daleel -n daleel-api --query 'properties.configuration.ingress.fqdn' -o tsv)"
curl "$API_URL/api/v1/health"
```

## Estimation des couts

| Ressource | SKU | Cout estime/mois |
|---|---|---|
| Container Apps (API) | 2 vCPU / 4 Go | ~50 EUR |
| Container Apps (Ollama) | 4 vCPU / 8 Go | ~100 EUR |
| Cosmos DB | Serverless | ~10-30 EUR |
| Container Registry | Basic | ~5 EUR |
| Blob Storage | Standard LRS | ~1 EUR |
| **Total estime** | | **~170-190 EUR/mois** |

> Pour un PFE / demo : reduisez Ollama a 2 vCPU / 4 Go (~85 EUR) ou utilisez
> `--min-replicas 0` sur l'API pour ne payer que lors de l'utilisation.

## Operations courantes

### Mise a jour de l'application

```bash
# Rebuild + redeploy
az acr build --registry acrdaleel --image daleel-api:latest --file Dockerfile .

# Forcer le redemarrage
az containerapp revision restart -g rg-daleel -n daleel-api
```

### Voir les logs

```bash
az containerapp logs show -g rg-daleel -n daleel-api --follow
az containerapp logs show -g rg-daleel -n daleel-ollama --follow
```

### Scaler

```bash
# Scaler l'API (ex: 2-5 replicas)
az containerapp update -g rg-daleel -n daleel-api --min-replicas 2 --max-replicas 5
```

### Domaine personnalise

```bash
az containerapp hostname add \
  -g rg-daleel \
  -n daleel-api \
  --hostname daleel.votre-domaine.tn

# Puis configurer le certificat TLS
az containerapp hostname bind \
  -g rg-daleel \
  -n daleel-api \
  --hostname daleel.votre-domaine.tn \
  --environment daleel-env
```

### Supprimer toutes les ressources

```powershell
# PowerShell
.\teardown.ps1

# Bash
az group delete --name rg-daleel --yes
```

## Depannage

| Probleme | Solution |
|---|---|
| Image trop grosse pour ACR Tasks | Augmenter le timeout : `--timeout 3600` |
| Ollama OOM (Out of Memory) | Augmenter la memoire : `--memory 16Gi` |
| CORS bloque | Verifier `DALEEL_CORS_ORIGINS` contient l'URL HTTPS complete |
| Cosmos DB lent | Augmenter les RU/s ou passer en throughput provisionne |
| FAISS index vide apres redeploy | Normal : re-uploader les documents via l'interface |
