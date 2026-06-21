# ─────────────────────────────────────────────────────────────────────────────
# Daleel — Suppression des ressources Azure
#
# ATTENTION : Supprime TOUTES les ressources du groupe rg-daleel.
# Usage : .\teardown.ps1
# ─────────────────────────────────────────────────────────────────────────────

$ErrorActionPreference = "Stop"

$envFile = Join-Path $PSScriptRoot ".env.azure"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $key = $Matches[1].Trim()
            $val = $Matches[2].Trim()
            if ($val -and -not $val.StartsWith('<')) {
                Set-Variable -Name $key -Value $val -Scope Script
            }
        }
    }
}

$AZURE_RESOURCE_GROUP = if ($AZURE_RESOURCE_GROUP) { $AZURE_RESOURCE_GROUP } else { "rg-daleel" }

Write-Host ""
Write-Host "ATTENTION : Ceci va supprimer le groupe '$AZURE_RESOURCE_GROUP'" -ForegroundColor Red
Write-Host "et TOUTES ses ressources (Cosmos DB, Container Apps, ACR, Storage)." -ForegroundColor Red
Write-Host ""
$confirm = Read-Host "Tapez le nom du groupe pour confirmer"

if ($confirm -ne $AZURE_RESOURCE_GROUP) {
    Write-Host "Annule." -ForegroundColor Yellow
    exit 0
}

Write-Host "Suppression en cours..." -ForegroundColor Yellow
az group delete --name $AZURE_RESOURCE_GROUP --yes --no-wait
Write-Host "Suppression lancee (async). Verifiez dans le portail Azure." -ForegroundColor Green
