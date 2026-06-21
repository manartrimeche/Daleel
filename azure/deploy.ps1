# ─────────────────────────────────────────────────────────────────────────────
# Daleel — Script de deploiement Azure (PowerShell)
#
# Pre-requis :
#   1. Azure CLI installe  : winget install Microsoft.AzureCLI
#   2. Docker Desktop       : en cours d'execution
#   3. Copier .env.azure.template → .env.azure et remplir les valeurs
#
# Usage :
#   .\deploy.ps1                  # Deploiement complet
#   .\deploy.ps1 -Step infra      # Creer uniquement l'infrastructure
#   .\deploy.ps1 -Step build      # Build + push images seulement
#   .\deploy.ps1 -Step deploy     # Deployer les containers seulement
#   .\deploy.ps1 -Step all        # Tout (defaut)
# ─────────────────────────────────────────────────────────────────────────────

param(
    [ValidateSet("all", "infra", "build", "deploy")]
    [string]$Step = "all"
)

$ErrorActionPreference = "Stop"

# ── Charger la configuration ────────────────────────────────────────────────
$envFile = Join-Path $PSScriptRoot ".env.azure"
if (-not (Test-Path $envFile)) {
    Write-Error @"
Fichier .env.azure introuvable.
Copiez .env.azure.template vers .env.azure et remplissez les valeurs :
  Copy-Item .env.azure.template .env.azure
"@
    exit 1
}

Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        $key = $Matches[1].Trim()
        $val = $Matches[2].Trim()
        if ($val -and $val -ne '' -and -not $val.StartsWith('<')) {
            Set-Variable -Name $key -Value $val -Scope Script
        }
    }
}

# Valeurs par defaut
if (-not $AZURE_RESOURCE_GROUP)   { $AZURE_RESOURCE_GROUP   = "rg-daleel" }
if (-not $AZURE_LOCATION)         { $AZURE_LOCATION         = "francecentral" }
if (-not $ACR_NAME)               { $ACR_NAME               = "acrdaleel" }
if (-not $CONTAINER_APP_ENV)      { $CONTAINER_APP_ENV      = "daleel-env" }
if (-not $CONTAINER_APP_API)      { $CONTAINER_APP_API      = "daleel-api" }
if (-not $CONTAINER_APP_OLLAMA)   { $CONTAINER_APP_OLLAMA   = "daleel-ollama" }
if (-not $COSMOS_ACCOUNT_NAME)    { $COSMOS_ACCOUNT_NAME    = "daleel-cosmos" }
if (-not $COSMOS_DB_NAME)         { $COSMOS_DB_NAME         = "manar" }
if (-not $STORAGE_ACCOUNT_NAME)   { $STORAGE_ACCOUNT_NAME   = "stdaleeluploads" }

$PROJECT_ROOT = Split-Path $PSScriptRoot -Parent
$ACR_LOGIN_SERVER = "${ACR_NAME}.azurecr.io"
$API_IMAGE = "${ACR_LOGIN_SERVER}/daleel-api:latest"
$OLLAMA_IMAGE = "ollama/ollama:latest"

function Write-Step { param([string]$msg) Write-Host "`n=== $msg ===" -ForegroundColor Cyan }

# ═══════════════════════════════════════════════════════════════════════════════
# ETAPE 1 : Infrastructure Azure
# ═══════════════════════════════════════════════════════════════════════════════
function Deploy-Infrastructure {
    Write-Step "1/6 — Connexion Azure"
    $account = az account show 2>$null | ConvertFrom-Json
    if (-not $account) {
        Write-Host "Connexion requise..."
        az login
    }
    if ($AZURE_SUBSCRIPTION_ID) {
        az account set --subscription $AZURE_SUBSCRIPTION_ID
    }
    Write-Host "Subscription : $(az account show --query name -o tsv)"

    Write-Step "2/6 — Groupe de ressources"
    az group create `
        --name $AZURE_RESOURCE_GROUP `
        --location $AZURE_LOCATION `
        --output none
    Write-Host "OK : $AZURE_RESOURCE_GROUP ($AZURE_LOCATION)"

    Write-Step "3/6 — Azure Container Registry"
    az acr create `
        --resource-group $AZURE_RESOURCE_GROUP `
        --name $ACR_NAME `
        --sku Basic `
        --admin-enabled true `
        --output none
    Write-Host "OK : $ACR_NAME.azurecr.io"

    Write-Step "4/6 — Azure Cosmos DB (API MongoDB)"
    # Creer le compte Cosmos DB avec API MongoDB
    az cosmosdb create `
        --resource-group $AZURE_RESOURCE_GROUP `
        --name $COSMOS_ACCOUNT_NAME `
        --kind MongoDB `
        --server-version "7.0" `
        --default-consistency-level Session `
        --locations regionName=$AZURE_LOCATION failoverPriority=0 `
        --output none
    Write-Host "OK : $COSMOS_ACCOUNT_NAME (MongoDB 7.0)"

    # Creer la base de donnees
    az cosmosdb mongodb database create `
        --resource-group $AZURE_RESOURCE_GROUP `
        --account-name $COSMOS_ACCOUNT_NAME `
        --name $COSMOS_DB_NAME `
        --output none
    Write-Host "OK : base '$COSMOS_DB_NAME' creee"

    Write-Step "5/6 — Azure Blob Storage"
    az storage account create `
        --resource-group $AZURE_RESOURCE_GROUP `
        --name $STORAGE_ACCOUNT_NAME `
        --sku Standard_LRS `
        --kind StorageV2 `
        --output none
    az storage container create `
        --account-name $STORAGE_ACCOUNT_NAME `
        --name uploads `
        --output none
    Write-Host "OK : $STORAGE_ACCOUNT_NAME / uploads"

    Write-Step "6/6 — Container Apps Environment"
    az containerapp env create `
        --resource-group $AZURE_RESOURCE_GROUP `
        --name $CONTAINER_APP_ENV `
        --location $AZURE_LOCATION `
        --output none
    Write-Host "OK : environnement '$CONTAINER_APP_ENV'"
}

# ═══════════════════════════════════════════════════════════════════════════════
# ETAPE 2 : Build & Push Docker
# ═══════════════════════════════════════════════════════════════════════════════
function Build-AndPush {
    Write-Step "Build — Image Docker Daleel"

    # Login au registry
    az acr login --name $ACR_NAME

    # Build et push via ACR Tasks (build dans le cloud, pas besoin de Docker local)
    Write-Host "Build dans Azure Cloud (ACR Tasks)..."
    az acr build `
        --registry $ACR_NAME `
        --image daleel-api:latest `
        --file Dockerfile `
        $PROJECT_ROOT

    Write-Host "OK : image $API_IMAGE prete"
}

# ═══════════════════════════════════════════════════════════════════════════════
# ETAPE 3 : Deploiement des Container Apps
# ═══════════════════════════════════════════════════════════════════════════════
function Deploy-Containers {
    # ── Recuperer les secrets ──
    Write-Step "Secrets — Recuperation des credentials"

    $COSMOS_CONN_STR = az cosmosdb keys list `
        --resource-group $AZURE_RESOURCE_GROUP `
        --name $COSMOS_ACCOUNT_NAME `
        --type connection-strings `
        --query "connectionStrings[0].connectionString" `
        -o tsv

    $ACR_PASSWORD = az acr credential show `
        --name $ACR_NAME `
        --query "passwords[0].value" `
        -o tsv

    $STORAGE_KEY = az storage account keys list `
        --resource-group $AZURE_RESOURCE_GROUP `
        --account-name $STORAGE_ACCOUNT_NAME `
        --query "[0].value" `
        -o tsv

    # ── Deployer Ollama ──
    Write-Step "Deploy — Ollama (LLM)"
    az containerapp create `
        --resource-group $AZURE_RESOURCE_GROUP `
        --name $CONTAINER_APP_OLLAMA `
        --environment $CONTAINER_APP_ENV `
        --image $OLLAMA_IMAGE `
        --cpu 4 --memory 8Gi `
        --min-replicas 1 --max-replicas 1 `
        --target-port 11434 `
        --ingress internal `
        --output none

    $OLLAMA_FQDN = az containerapp show `
        --resource-group $AZURE_RESOURCE_GROUP `
        --name $CONTAINER_APP_OLLAMA `
        --query "properties.configuration.ingress.fqdn" `
        -o tsv
    $OLLAMA_URL = "https://${OLLAMA_FQDN}"
    Write-Host "OK : Ollama accessible a $OLLAMA_URL"

    # ── Telecharger le modele dans Ollama ──
    Write-Host "Telechargement du modele qwen2.5:7b (cela peut prendre quelques minutes)..."
    # Note : cette commande sera executee apres le deploiement via exec
    # az containerapp exec ne supporte pas directement, on utilise un job
    Write-Host "IMPORTANT: Apres le deploiement, executez manuellement :"
    Write-Host "  az containerapp exec -g $AZURE_RESOURCE_GROUP -n $CONTAINER_APP_OLLAMA --command 'ollama pull qwen2.5:7b'"

    # ── Deployer Daleel API ──
    Write-Step "Deploy — Daleel API"

    # Generer un JWT secret si non fourni
    if (-not $DALEEL_JWT_SECRET_KEY -or $DALEEL_JWT_SECRET_KEY.StartsWith('<')) {
        $bytes = New-Object byte[] 48
        [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
        $DALEEL_JWT_SECRET_KEY = [Convert]::ToBase64String($bytes)
        Write-Host "JWT secret auto-genere."
    }

    $API_FQDN_PLACEHOLDER = "daleel-api.placeholder.azurecontainerapps.io"

    az containerapp create `
        --resource-group $AZURE_RESOURCE_GROUP `
        --name $CONTAINER_APP_API `
        --environment $CONTAINER_APP_ENV `
        --image $API_IMAGE `
        --registry-server $ACR_LOGIN_SERVER `
        --registry-username $ACR_NAME `
        --registry-password $ACR_PASSWORD `
        --cpu 2 --memory 4Gi `
        --min-replicas 1 --max-replicas 3 `
        --target-port 8000 `
        --ingress external `
        --env-vars `
            "DALEEL_ENV=production" `
            "DALEEL_MONGODB_URL=$COSMOS_CONN_STR" `
            "DALEEL_MONGODB_DB_NAME=$COSMOS_DB_NAME" `
            "DALEEL_LLM_BASE_URL=$OLLAMA_URL" `
            "DALEEL_LLM_MODEL=qwen2.5:7b" `
            "DALEEL_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-mpnet-base-v2" `
            "DALEEL_EMBEDDING_DIMENSION=768" `
            "DALEEL_VECTOR_SEARCH_BACKEND=faiss" `
            "DALEEL_CHUNK_SIZE=1500" `
            "DALEEL_CHUNK_OVERLAP=200" `
            "DALEEL_MAX_UPLOAD_MB=100" `
            "DALEEL_DOMAIN_ROUTER_ENABLED=true" `
            "DALEEL_QUALITY_GUARD_ENABLED=true" `
            "DALEEL_KG_LIGHT_ENABLED=true" `
            "DALEEL_AUTO_MODE_ENABLED=true" `
            "DALEEL_JWT_SECRET_KEY=secretref:jwt-secret" `
            "DALEEL_API_KEY=secretref:api-key" `
            "DALEEL_ADMIN_API_KEY=secretref:admin-api-key" `
        --secrets `
            "jwt-secret=$DALEEL_JWT_SECRET_KEY" `
            "api-key=$DALEEL_API_KEY" `
            "admin-api-key=$DALEEL_ADMIN_API_KEY" `
        --output none

    # Recuperer l'URL finale
    $API_FQDN = az containerapp show `
        --resource-group $AZURE_RESOURCE_GROUP `
        --name $CONTAINER_APP_API `
        --query "properties.configuration.ingress.fqdn" `
        -o tsv

    # Mettre a jour CORS avec la vraie URL
    az containerapp update `
        --resource-group $AZURE_RESOURCE_GROUP `
        --name $CONTAINER_APP_API `
        --set-env-vars "DALEEL_CORS_ORIGINS=https://${API_FQDN}" `
        --output none

    Write-Host ""
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "  Daleel deploye avec succes !" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  URL : https://$API_FQDN" -ForegroundColor Yellow
    Write-Host "  API : https://$API_FQDN/api/v1" -ForegroundColor Yellow
    Write-Host "  Docs: https://$API_FQDN/docs" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "ETAPE SUIVANTE :" -ForegroundColor Cyan
    Write-Host "  1. Telecharger le modele Ollama :"
    Write-Host "     az containerapp exec -g $AZURE_RESOURCE_GROUP -n $CONTAINER_APP_OLLAMA --command 'ollama pull qwen2.5:7b'"
    Write-Host "  2. Verifier le health check :"
    Write-Host "     curl https://$API_FQDN/api/v1/health"
    Write-Host ""
}

# ═══════════════════════════════════════════════════════════════════════════════
# Execution
# ═══════════════════════════════════════════════════════════════════════════════

Write-Host @"

  ____        _           _
 |  _ \  __ _| | ___  ___| |
 | | | |/ _` | |/ _ \/ _ \ |
 | |_| | (_| | |  __/  __/ |
 |____/ \__,_|_|\___|\___|_|  Azure Deploy

"@ -ForegroundColor Cyan

switch ($Step) {
    "infra"  { Deploy-Infrastructure }
    "build"  { Build-AndPush }
    "deploy" { Deploy-Containers }
    "all"    {
        Deploy-Infrastructure
        Build-AndPush
        Deploy-Containers
    }
}
