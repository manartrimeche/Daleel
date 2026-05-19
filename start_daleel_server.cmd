@echo off
cd /d "%~dp0"
set PATH=%~dp0.venv\Scripts;%PATH%
set DALEEL_VECTOR_SEARCH_BACKEND=python-cosine
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > "uvicorn.live.out.log" 2> "uvicorn.live.err.log"
