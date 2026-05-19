# reset_and_rebuild.ps1
# Script complet pour réinitialiser la base et régénérer les embeddings avec les nouveaux paramètres
# Usage: .\reset_and_rebuild.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DALEEL RAG RESET & REBUILD SCRIPT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Chemins
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$DataDir = Join-Path $ProjectRoot "data"

Write-Host "📁 Project root: $ProjectRoot"
Write-Host "📂 Data directory: $DataDir"
Write-Host ""

# ============================================
# ÉTAPE 1 : Arrêter le serveur uvicorn
# ============================================
Write-Host "🛑 Étape 1 — Arrêt du serveur FastAPI (uvicorn)..." -ForegroundColor Yellow
try {
    # Trouver les processus uvicorn et les arrêter
    $uvicornProcesses = Get-Process | Where-Object { $_.ProcessName -like "*uvicorn*" -or $_.MainWindowTitle -like "*uvicorn*" }
    if ($uvicornProcesses) {
        $uvicornProcesses | Stop-Process -Force
        Write-Host "   ✅ Serveur uvicorn arrêté" -ForegroundColor Green
    } else {
        Write-Host "   ℹ️ Aucun processus uvicorn trouvé (peut-être déjà arrêté)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ⚠️ Impossible d'arrêter uvicorn automatiquement: $_" -ForegroundColor Yellow
    Write-Host "   → Veuillez fermer manuellement la fenêtre PowerShell où uvicorn tourne (Ctrl+C)" -ForegroundColor Yellow
    pause
}

Start-Sleep -Seconds 2

# ============================================
# ÉTAPE 2 : Nettoyage complet de MongoDB
# ============================================
Write-Host ""
Write-Host "🧹 Étape 2 — Nettoyage complet de la base MongoDB..." -ForegroundColor Yellow

Write-Host "   Tentative avec 'mongo'..." -ForegroundColor Gray
try {
    mongo daleel --eval "db.documents.deleteMany({}); db.chunks.deleteMany({}); db.document_raw_pages.deleteMany({}); db.document_cleaned_texts.deleteMany({}); db.exigences.deleteMany({}); db.document_sources.deleteMany({}); db.lois.deleteMany({}); db.articles.deleteMany({}); db.article_versions.deleteMany({}); print('✅ Base nettoyée')" 2>$null
    Write-Host "   ✅ Nettoyage MongoDB réussi avec 'mongo'" -ForegroundColor Green
} catch {
    Write-Host "   'mongo' non trouvé, essai avec 'mongosh'..." -ForegroundColor Gray
    try {
        mongosh daleel --eval "db.documents.deleteMany({}); db.chunks.deleteMany({}); db.document_raw_pages.deleteMany({}); db.document_cleaned_texts.deleteMany({}); db.exigences.deleteMany({}); db.document_sources.deleteMany({}); db.lois.deleteMany({}); db.articles.deleteMany({}); db.article_versions.deleteMany({}); print('✅ Base nettoyée')" --quiet
        Write-Host "   ✅ Nettoyage MongoDB réussi avec 'mongosh'" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ ERREUR : Impossible de se connecter à MongoDB." -ForegroundColor Red
        Write-Host "   → Vérifiez que MongoDB est démarré (mongod) et que la base 'daleel' existe." -ForegroundColor Yellow
        Read-Host "Appuyez sur Entrée pour quitter"
        exit 1
    }
}

# ============================================
# ÉTAPE 3 : Redémarrer le serveur
# ============================================
Write-Host ""
Write-Host "🚀 Étape 3 — Démarrage du serveur FastAPI..." -ForegroundColor Yellow

# Vérifier que l'env virtuel existe
$venvPath = Join-Path $ProjectRoot ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "   ❌ Environnement virtuel non trouvé à $venvPath" -ForegroundColor Red
    Write-Host "   → Créez-le avec : python -m venv .venv" -ForegroundColor Yellow
    Read-Host "Appuyez sur Entrée pour quitter"
    exit 1
}

# Activer l'env virtuel et démarrer uvicorn en arrière-plan
Write-Host "   Activation de l'environnement virtuel..." -ForegroundColor Gray
$ActivateScript = Join-Path $venvPath "Scripts\Activate.ps1"
. $ActivateScript

Write-Host "   Démarrage d'uvicorn (log visible dans cette fenêtre)..." -ForegroundColor Gray

# Lancer uvicorn dans un job en arrière-plan
$Job = Start-Job -ScriptBlock {
    cd $using:ProjectRoot
    python -m uvicorn app.main:app --reload
} -Name "UvicornServer"

# Attendre un peu que le serveur démarre
Write-Host "   Attente du démarrage du serveur (10s)..." -ForegroundColor Gray
Start-Sleep -Seconds 10

# Vérifier si le port 8000 est en écoute
try {
    $listening = Test-NetConnection -ComputerName "localhost" -Port 8000 -InformationLevel Quiet
    if ($listening) {
        Write-Host "   ✅ Serveur démarré sur http://localhost:8000" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️ Le serveur ne semble pas écouter sur le port 8000." -ForegroundColor Yellow
        Write-Host "   → Vérifiez les logs du job uvicorn ci-dessous." -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ⚠️ Impossible de vérifier le port 8000: $_" -ForegroundColor Yellow
}

# ============================================
# ÉTAPE 4 : Bulk upload avec paramètres optimisés
# ============================================
Write-Host ""
Write-Host "📥 Étape 4 — Upload des documents et génération des embeddings..." -ForegroundColor Yellow
Write-Host "   (Cela peut prendre 2-5 minutes selon le nombre de documents)" -ForegroundColor Gray

# Vérifier que le dossier data existe et contient des fichiers
if (-not (Test-Path $DataDir)) {
    Write-Host "   ❌ Dossier 'data' non trouvé: $DataDir" -ForegroundColor Red
    Read-Host "Appuyez sur Entrée pour quitter"
    exit 1
}

$files = Get-ChildItem $DataDir -File | Where-Object { $_.Extension -in ".pdf", ".txt", ".docx" }
if ($files.Count -eq 0) {
    Write-Host "   ⚠️ Aucun fichier supporté (.pdf, .txt, .docx) dans $DataDir" -ForegroundColor Yellow
    Read-Host "Appuyez sur Entrée pour quitter"
    exit 1
}

Write-Host "   Fichiers trouvés: $($files.Count)" -ForegroundColor Gray

# Appeler l'API bulk-upload
$Url = "http://localhost:8000/api/v1/documents/bulk-upload"
$Body = @{
    data_dir = "data"
    chunk_size = 1500
    chunk_overlap = 200
} | ConvertTo-Json

Write-Host "   Envoi de la requête bulk-upload..." -ForegroundColor Gray

try {
    $response = Invoke-RestMethod -Uri $Url -Method Post -ContentType "application/json" -Body $Body
    if ($response.succeeded -ne $null) {
        Write-Host "   ✅ Upload réussi !" -ForegroundColor Green
        Write-Host "      • Fichiers traités : $($response.total_files)" -ForegroundColor Green
        Write-Host "      • Succès          : $($response.succeeded)" -ForegroundColor Green
        Write-Host "      • Échecs          : $($response.failed)" -ForegroundColor Yellow
        Write-Host "      • Total chunks    : $($response.total_chunks)" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️ reponse inattendue: $($response | ConvertTo-Json -Depth 3)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Erreur lors de l'upload: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $errorBody = $reader.ReadToEnd()
        Write-Host "      Détails : $errorBody" -ForegroundColor Yellow
    }
    Read-Host "Appuyez sur Entrée pour quitter"
    exit 1
}

# ============================================
# ÉTAPE 5 : Vérification
# ============================================
Write-Host ""
Write-Host "🔍 Étape 5 — Vérification des documents en base..." -ForegroundColor Yellow

try {
    $docsResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/documents" -Method Get
    if ($docsResponse.total -gt 0) {
        Write-Host "   ✅ $($docsResponse.total) document(s) chargé(s) avec succès" -ForegroundColor Green
        Write-Host "   Documents :" -ForegroundColor Gray
        foreach ($doc in $docsResponse.documents) {
            Write-Host "      • $($doc.filename) — $($doc.total_chunks) chunks, status=$($doc.status)" -ForegroundColor Gray
        }
    } else {
        Write-Host "   ⚠️ Aucun document trouvé en base." -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Erreur lors de la vérification: $_" -ForegroundColor Red
}

# ============================================
# ÉTAPE 6 : Test de recherche
# ============================================
Write-Host ""
Write-Host "🧪 Étape 6 — Test de recherche sémantique..." -ForegroundColor Yellow

$searchBody = @{
    query = "obligations du gérant SARL"
    top_k = 5
} | ConvertTo-Json

try {
    $searchResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/search" -Method Post -ContentType "application/json" -Body $searchBody
    Write-Host "   ✅ Recherche retourne $($searchResponse.total) résultats" -ForegroundColor Green
    if ($searchResponse.results.Count -gt 0) {
        Write-Host "   Meilleur score : $($searchResponse.results[0].score.ToString('P2'))" -ForegroundColor Gray
        Write-Host "   Document       : $($searchResponse.results[0].filename)" -ForegroundColor Gray
        Write-Host "   Section        : $($searchResponse.results[0].section)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ❌ Erreur recherche: $_" -ForegroundColor Red
}

# ============================================
# RÉSUMÉ
# ============================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ✅ REBUILD TERMINÉ" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Prochaines étapes :" -ForegroundColor White
Write-Host "1. Le serveur tourne sur http://localhost:8000" -ForegroundColor Gray
Write-Host "2. Testez une question :" -ForegroundColor Gray
Write-Host "   curl.exe -X POST 'http://localhost:8000/api/v1/ask' -H 'Content-Type: application/json' -d '{\"question\":\"Quelles sont les obligations du gérant?\",\"top_k\":5,\"temperature\":0.2}'" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Vérifiez que le champ 'model' dans la reponse est 'qwen2.5:7b' (sans '+grounded')" -ForegroundColor Gray
Write-Host ""
Write-Host "Pour arrêter le serveur : Fermez la fenêtre ou exécutez Stop-Job -Name 'UvicornServer'" -ForegroundColor Gray
Write-Host ""
Write-Host "Logs du serveur disponibles dans la fenêtre où uvicorn a été démarré." -ForegroundColor Gray

# Garder le script ouvert pour inspection
Read-Host "Appuyez sur Entrée pour fermer ce script (le serveur continue en arrière-plan)"
