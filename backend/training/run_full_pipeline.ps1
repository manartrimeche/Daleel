# =============================================================================
# Pipeline reproductible de fine-tuning + evaluation — projet Daleel
# =============================================================================
# Produit, en une commande, des artefacts coherents avec le rapport :
#   1. Entraine le modele d'embeddings sur train_set.jsonl (487 articles / 973 paires)
#      avec des hyperparametres DOCUMENTES (3 epochs, batch 32, lr 2e-5).
#   2. Evalue le baseline ET le modele fine-tune sur eval_set_clean.jsonl
#      (50 requetes gold, sans fuite par construction).
#   3. Regenere la figure fig_5_4_finetuning_resultats.png.
#
# Usage :  cd backend ; ./training/run_full_pipeline.ps1
# =============================================================================

# Ne PAS utiliser "Stop" : les scripts Python ecrivent des warnings sur stderr
# (ex. HuggingFace Hub) que PowerShell prendrait pour des erreurs fatales.
$ErrorActionPreference = "Continue"
$env:PYTHONIOENCODING = "utf-8"
$env:HF_HUB_DISABLE_PROGRESS_BARS = "1"

function Assert-LastExit($etape) {
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ECHEC reel a l'etape : $etape (code $LASTEXITCODE)" -ForegroundColor Red
        exit 1
    }
}

# --- Hyperparametres documentes (a reporter dans le tableau 3.4) -------------
$EPOCHS = 3
$BATCH  = 32
$LR     = "2e-5"

$DATA    = "training/data"
$MODEL   = "training/models/daleel-embedding-finetuned-final"
$BASE    = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

Write-Host "==== ETAPE 1/4 : Fine-tuning ($EPOCHS epochs, batch $BATCH, lr $LR) ====" -ForegroundColor Cyan
python training/04_finetune_embeddings.py `
  --train "$DATA/train_set.jsonl" `
  --eval "$DATA/eval_set_clean.jsonl" `
  --articles "$DATA/articles.jsonl" `
  --output-dir $MODEL `
  --epochs $EPOCHS --batch-size $BATCH --learning-rate $LR `
  --skip-baseline
Assert-LastExit "1 - fine-tuning"

Write-Host "==== ETAPE 2/4 : Evaluation BASELINE (MPNet generique) ====" -ForegroundColor Cyan
python training/03_evaluate_retrieval.py `
  --model $BASE `
  --articles "$DATA/articles.jsonl" `
  --eval "$DATA/eval_set_clean.jsonl" `
  --output "$DATA/baseline_clean_metrics.json"
Assert-LastExit "2 - eval baseline"

Write-Host "==== ETAPE 3/4 : Evaluation MODELE FINE-TUNE ====" -ForegroundColor Cyan
python training/03_evaluate_retrieval.py `
  --model $MODEL `
  --articles "$DATA/articles.jsonl" `
  --eval "$DATA/eval_set_clean.jsonl" `
  --output "$DATA/finetuned_clean_metrics.json"
Assert-LastExit "3 - eval fine-tune"

Write-Host "==== ETAPE 4/4 : Generation de la figure ====" -ForegroundColor Cyan
python training/plot_finetuning_results.py
Assert-LastExit "4 - figure"

Write-Host ""
Write-Host "==== PIPELINE TERMINE ====" -ForegroundColor Green
Write-Host "Modele     : $MODEL"
Write-Host "Metriques  : $DATA/baseline_clean_metrics.json + finetuned_clean_metrics.json"
Write-Host "Figure     : captures/fig_5_4_finetuning_resultats.png"
Write-Host "Config doc : epochs=$EPOCHS, batch=$BATCH, lr=$LR, dataset=train_set.jsonl (487 art / 973 paires)"
