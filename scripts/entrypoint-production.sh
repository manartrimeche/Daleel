#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Daleel — Entrypoint de production (all-in-one)
#
# Lance Ollama puis l'API FastAPI dans un seul conteneur.
# Gere l'arret propre (SIGTERM) des deux processus.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

OLLAMA_HOST="${OLLAMA_HOST:-0.0.0.0:11434}"
OLLAMA_MODEL="${DALEEL_LLM_MODEL:-qwen2.5:7b}"
ALLOW_RUNTIME_MODEL_PULL="${DALEEL_ALLOW_RUNTIME_MODEL_PULL:-false}"
API_PORT="${API_PORT:-8000}"
API_WORKERS="${API_WORKERS:-1}"

# PIDs pour le cleanup
OLLAMA_PID=""
API_PID=""

cleanup() {
    echo "[entrypoint] Arret en cours..."
    [ -n "$API_PID" ]    && kill "$API_PID"    2>/dev/null || true
    [ -n "$OLLAMA_PID" ] && kill "$OLLAMA_PID" 2>/dev/null || true
    wait 2>/dev/null || true
    echo "[entrypoint] Termine."
    exit 0
}
trap cleanup SIGTERM SIGINT

# ── 1. Demarrer Ollama ──────────────────────────────────────────────────────
echo "[entrypoint] Demarrage Ollama (host=$OLLAMA_HOST)..."
export OLLAMA_HOST
ollama serve &
OLLAMA_PID=$!

# Attendre qu'Ollama soit pret (max 30s)
echo "[entrypoint] Attente Ollama..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "[entrypoint] Ollama pret (${i}s)"
        break
    fi
    if ! kill -0 "$OLLAMA_PID" 2>/dev/null; then
        echo "[entrypoint] ERREUR: Ollama s'est arrete pendant le demarrage"
        wait "$OLLAMA_PID" 2>/dev/null || true
        exit 1
    fi
    if [ "$i" -eq 30 ]; then
        echo "[entrypoint] ERREUR: Ollama n'a pas demarre en 30s"
        exit 1
    fi
    sleep 1
done

# ── 2. Verifier que le modele est disponible ─────────────────────────────────
echo "[entrypoint] Verification modele '$OLLAMA_MODEL'..."
if ollama list | awk 'NR > 1 {print $1}' | grep -Fxq "$OLLAMA_MODEL"; then
    echo "[entrypoint] Modele '$OLLAMA_MODEL' present."
elif [ "$ALLOW_RUNTIME_MODEL_PULL" = "true" ]; then
    echo "[entrypoint] Modele absent; telechargement autorise..."
    ollama pull "$OLLAMA_MODEL"
    echo "[entrypoint] Modele '$OLLAMA_MODEL' telecharge."
else
    echo "[entrypoint] ERREUR: modele '$OLLAMA_MODEL' absent de l'image."
    echo "[entrypoint] Runtime pull desactive (DALEEL_ALLOW_RUNTIME_MODEL_PULL=false)."
    exit 1
fi

# ── 3. Demarrer l'API FastAPI ────────────────────────────────────────────────
echo "[entrypoint] Demarrage API Daleel (port=$API_PORT, workers=$API_WORKERS)..."
cd /app
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "$API_PORT" \
    --workers "$API_WORKERS" \
    --log-level info &
API_PID=$!

echo ""
echo "========================================"
echo "  Daleel est pret !"
echo "  API     : http://localhost:${API_PORT}"
echo "  Ollama  : http://localhost:11434"
echo "  Health  : http://localhost:${API_PORT}/api/v1/health"
echo "========================================"
echo ""

# Attendre que l'un des deux processus se termine
wait -n "$OLLAMA_PID" "$API_PID" 2>/dev/null || true
cleanup
