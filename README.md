# Daleel

Daleel is a Tunisian legal intelligence platform for document ingestion, semantic legal search, compliance workflows, and contract analysis. It combines a FastAPI backend, MongoDB, FAISS-based retrieval, local LLM integration through Ollama, and a React/Vite frontend.

## Highlights

- Legal document upload, extraction, chunking, and semantic search.
- Retrieval-augmented legal answers with grounding and quality checks.
- Authentication, roles, organizations, invitations, and notifications.
- Compliance case management, roadmap generation, exports, and audit support.
- Contract analysis with risk findings, missing clauses, scoring, and recommendations.
- Multilingual UI foundations for French, English, and Arabic.

## Stack

- Backend: Python, FastAPI, Motor/MongoDB, FAISS, sentence-transformers, pytest.
- Frontend: React, Vite, React Router, i18next, ESLint.
- AI runtime: Ollama-compatible local LLM endpoint.
- Delivery: Docker, Docker Compose, GitHub Actions CI.

## Project Layout

```text
backend/          FastAPI app, services, processing pipeline, tests
frontend/         React/Vite application
interface-daleel/ Legacy/static interface files served by the backend
docs/             Presentation and project documentation
data/             Example legal data
.github/          CI workflows
```

## Local Setup

Create a `.env` file from `.env.example`, then adjust MongoDB, LLM, authentication, and SMTP settings for your environment.

Backend:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests --cov=backend/app --cov-report=term --cov-fail-under=50
```

Frontend:

```powershell
cd frontend
npm ci
npm run lint
npm run build
```

Full local stack:

```powershell
docker compose up --build
```

After Ollama starts, pull the configured model if it is not already available:

```powershell
docker compose exec ollama ollama pull qwen2.5:7b
```

## Quality Gates

The current verified baseline is:

- `865` backend tests passing.
- `50.12%` backend coverage with a CI threshold of `50%`.
- Backend Ruff linting.
- Backend Bandit security scan.
- Frontend ESLint.
- Frontend production build.

## Demo Flow

A strong demo can follow this sequence:

1. Authenticate and show role-aware navigation.
2. Upload or select legal documents.
3. Ask a grounded legal question and inspect cited context.
4. Open compliance or contract analysis results.
5. Export or review an actionable roadmap.

## Notes

This project is designed as an engineering and legal-tech prototype. Legal outputs should be treated as decision support and reviewed by a qualified professional before operational use.
