$ErrorActionPreference = "Continue"
Set-Location -LiteralPath $PSScriptRoot
$env:PATH = "$PSScriptRoot\.venv\Scripts;$env:PATH"
$env:DALEEL_VECTOR_SEARCH_BACKEND = "python-cosine"
& "$PSScriptRoot\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 1>> "$PSScriptRoot\uvicorn.live.out.log" 2>> "$PSScriptRoot\uvicorn.live.err.log"
