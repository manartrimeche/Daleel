@echo off
cd /d "%~dp0frontend"
"C:\Program Files\nodejs\node.exe" node_modules\vite\bin\vite.js --host 127.0.0.1 --port 3000 >> "%~dp0vite-3000.log" 2>&1
