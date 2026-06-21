#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Daleel — Script de deploiement Azure (Bash / Linux / macOS / WSL)
#
# Pre-requis :
#   1. Azure CLI installe  : curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
#   2. Docker installe
#   3. Copier .env.azure.template → .env.azure et remplir les valeurs
#
# Usage :
#   chmod +x deploy.sh
#   ./deploy.sh              # Deploiement complet
#   ./deploy.sh infra        # Infrastructure seulement
#   ./deploy.sh build        # Build + push images
#   ./deploy.sh deploy       # Deployer les containers
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
STEP="${1:-all}"

# ── Charger la configuration ────────────────────────────────────────────────
ENV_FILE="$SCRIPT_DIR/.env.azure"
if [ ! -f "$ENV_FILE" ]; then
    echo "ERREUR: Fichier .env.azure introuvable."
    echo "Copiez .env.azure.template vers .env.azure et remplissez les valeurs :"
    echo "  cp .env.azure.template .env.azure"
    exit 1
fi

set -a
source "$ENV_FILE"
set +a

# Valeurs par defaut
AZURE_RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-rg-daleel}"
AZURE_LOCATION="${AZURE_LOCATION:-francecentral}"
ACR_NAME="${ACR_NAME:-acrdaleel}"
CONTAINER_APP_ENV="${CONTAINER_APP_ENV:-daleel-env}"
CONTAINER_APP_API="${CONTAINER_APP_API:-daleel-api}"
CONTAINER_APP_OLLAMA="${CONTAINER_APP_OLLAMA:-daleel-ollama}"
COSMOS_ACCOUNT_NAME="${COSMOS_ACCOUNT_NAME:-daleel-cosmos}"
COSMOS_DB_NAME="${COSMOS_DB_NAME:-manar}"
STORAGE_ACCOUNT_NAME="${STORAGE_ACCOUNT_NAME:-stdaleeluploads}"

ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"
API_IMAGE="${ACR_LOGIN_SERVER}/daleel-api:latest"

step() { echo -e "\n\033[36m=== $1 ===\033[0m"; }
ok()   { echo -e "\033[32m  OK: $1\033[0m"; }

# ═══════════════════════════════════════════════════════════════════════════════
# ETAPE 1 : Infrastructure Azure
# ═══════════════════════════════════════════════════════════════════════════════
deploy_infrastructure() {
    step "1/6 — Connexion Azure"
    if ! az account show &>/dev/null; then
        echo "Connexion requise..."
        az login
    fi
    [ -n "${AZURE_SUBSCRIPTION_ID:-}" ] && az account set --subscription "$AZURE_SUBSCRIPTION_ID"
    echo "Subscription : $(az account show --query name -o tsv)"

    step "2/6 — Groupe de ressources"
    az group create \
        --name "$AZURE_RESOURCE_GROUP" \
        --location "$AZURE_LOCATION" \
        --output none
    ok "$AZURE_RESOURCE_GROUP ($AZURE_LOCATION)"

    step "3/6 — Azure Container Registry"
    az acr create \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$ACR_NAME" \
        --sku Basic \
        --admin-enabled true \
        --output none
    ok "$ACR_NAME.azurecr.io"

    step "4/6 — Azure Cosmos DB (API MongoDB)"
    az cosmosdb create \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$COSMOS_ACCOUNT_NAME" \
        --kind MongoDB \
        --server-version "7.0" \
        --default-consistency-level Session \
        --locations regionName="$AZURE_LOCATION" failoverPriority=0 \
        --output none
    ok "$COSMOS_ACCOUNT_NAME (MongoDB 7.0)"

    az cosmosdb mongodb database create \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --account-name "$COSMOS_ACCOUNT_NAME" \
        --name "$COSMOS_DB_NAME" \
        --output none
    ok "base '$COSMOS_DB_NAME' creee"

    step "5/6 — Azure Blob Storage"
    az storage account create \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$STORAGE_ACCOUNT_NAME" \
        --sku Standard_LRS \
        --kind StorageV2 \
        --output none
    az storage container create \
        --account-name "$STORAGE_ACCOUNT_NAME" \
        --name uploads \
        --output none
    ok "$STORAGE_ACCOUNT_NAME / uploads"

    step "6/6 — Container Apps Environment"
    az containerapp env create \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$CONTAINER_APP_ENV" \
        --location "$AZURE_LOCATION" \
        --output none
    ok "environnement '$CONTAINER_APP_ENV'"
}

# ═══════════════════════════════════════════════════════════════════════════════
# ETAPE 2 : Build & Push Docker
# ═══════════════════════════════════════════════════════════════════════════════
build_and_push() {
    step "Build — Image Docker Daleel"

    az acr login --name "$ACR_NAME"

    echo "Build dans Azure Cloud (ACR Tasks)..."
    az acr build \
        --registry "$ACR_NAME" \
        --image daleel-api:latest \
        --file Dockerfile \
        "$PROJECT_ROOT"

    ok "image $API_IMAGE prete"
}

# ═══════════════════════════════════════════════════════════════════════════════
# ETAPE 3 : Deploiement des Container Apps
# ═══════════════════════════════════════════════════════════════════════════════
deploy_containers() {
    step "Secrets — Recuperation des credentials"

    COSMOS_CONN_STR=$(az cosmosdb keys list \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$COSMOS_ACCOUNT_NAME" \
        --type connection-strings \
        --query "connectionStrings[0].connectionString" \
        -o tsv)

    ACR_PASSWORD=$(az acr credential show \
        --name "$ACR_NAME" \
        --query "passwords[0].value" \
        -o tsv)

    # ── Deployer Ollama ──
    step "Deploy — Ollama (LLM)"
    az containerapp create \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$CONTAINER_APP_OLLAMA" \
        --environment "$CONTAINER_APP_ENV" \
        --image "ollama/ollama:latest" \
        --cpu 4 --memory 8Gi \
        --min-replicas 1 --max-replicas 1 \
        --target-port 11434 \
        --ingress internal \
        --output none

    OLLAMA_FQDN=$(az containerapp show \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$CONTAINER_APP_OLLAMA" \
        --query "properties.configuration.ingress.fqdn" \
        -o tsv)
    OLLAMA_URL="https://${OLLAMA_FQDN}"
    ok "Ollama accessible a $OLLAMA_URL"

    # ── Generer JWT secret si necessaire ──
    if [ -z "${DALEEL_JWT_SECRET_KEY:-}" ] || [[ "${DALEEL_JWT_SECRET_KEY}" == "<"* ]]; then
        DALEEL_JWT_SECRET_KEY=$(openssl rand -base64 48)
        echo "JWT secret auto-genere."
    fi

    # ── Deployer Daleel API ──
    step "Deploy — Daleel API"
    az containerapp create \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$CONTAINER_APP_API" \
        --environment "$CONTAINER_APP_ENV" \
        --image "$API_IMAGE" \
        --registry-server "$ACR_LOGIN_SERVER" \
        --registry-username "$ACR_NAME" \
        --registry-password "$ACR_PASSWORD" \
        --cpu 2 --memory 4Gi \
        --min-replicas 1 --max-replicas 3 \
        --target-port 8000 \
        --ingress external \
        --env-vars \
            "DALEEL_ENV=production" \
            "DALEEL_MONGODB_URL=$COSMOS_CONN_STR" \
            "DALEEL_MONGODB_DB_NAME=$COSMOS_DB_NAME" \
            "DALEEL_LLM_BASE_URL=$OLLAMA_URL" \
            "DALEEL_LLM_MODEL=qwen2.5:7b" \
            "DALEEL_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-mpnet-base-v2" \
            "DALEEL_EMBEDDING_DIMENSION=768" \
            "DALEEL_VECTOR_SEARCH_BACKEND=faiss" \
            "DALEEL_CHUNK_SIZE=1500" \
            "DALEEL_CHUNK_OVERLAP=200" \
            "DALEEL_MAX_UPLOAD_MB=100" \
            "DALEEL_DOMAIN_ROUTER_ENABLED=true" \
            "DALEEL_QUALITY_GUARD_ENABLED=true" \
            "DALEEL_KG_LIGHT_ENABLED=true" \
            "DALEEL_AUTO_MODE_ENABLED=true" \
            "DALEEL_JWT_SECRET_KEY=secretref:jwt-secret" \
            "DALEEL_API_KEY=secretref:api-key" \
            "DALEEL_ADMIN_API_KEY=secretref:admin-api-key" \
        --secrets \
            "jwt-secret=$DALEEL_JWT_SECRET_KEY" \
            "api-key=${DALEEL_API_KEY:-changeme}" \
            "admin-api-key=${DALEEL_ADMIN_API_KEY:-changeme}" \
        --output none

    # Recuperer l'URL finale
    API_FQDN=$(az containerapp show \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$CONTAINER_APP_API" \
        --query "properties.configuration.ingress.fqdn" \
        -o tsv)

    # Mettre a jour CORS
    az containerapp update \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$CONTAINER_APP_API" \
        --set-env-vars "DALEEL_CORS_ORIGINS=https://${API_FQDN}" \
        --output none

    echo ""
    echo -e "\033[32m================================================\033[0m"
    echo -e "\033[32m  Daleel deploye avec succes !\033[0m"
    echo -e "\033[32m================================================\033[0m"
    echo ""
    echo -e "\033[33m  URL : https://$API_FQDN\033[0m"
    echo -e "\033[33m  API : https://$API_FQDN/api/v1\033[0m"
    echo -e "\033[33m  Docs: https://$API_FQDN/docs\033[0m"
    echo ""
    echo -e "\033[36mETAPE SUIVANTE :\033[0m"
    echo "  1. Telecharger le modele Ollama :"
    echo "     az containerapp exec -g $AZURE_RESOURCE_GROUP -n $CONTAINER_APP_OLLAMA --command 'ollama pull qwen2.5:7b'"
    echo "  2. Verifier le health check :"
    echo "     curl https://$API_FQDN/api/v1/health"
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════════
# Execution
# ═══════════════════════════════════════════════════════════════════════════════
cat << 'BANNER'

  ____        _           _
 |  _ \  __ _| | ___  ___| |
 | | | |/ _` | |/ _ \/ _ \ |
 | |_| | (_| | |  __/  __/ |
 |____/ \__,_|_|\___|\___|_|  Azure Deploy

BANNER

case "$STEP" in
    infra)  deploy_infrastructure ;;
    build)  build_and_push ;;
    deploy) deploy_containers ;;
    all)
        deploy_infrastructure
        build_and_push
        deploy_containers
        ;;
    *)
        echo "Usage: $0 [all|infra|build|deploy]"
        exit 1
        ;;
esac
