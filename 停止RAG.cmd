@echo off
chcp 65001 >nul
cd /d "%~dp0"
docker compose -p rag-portfolio -f compose.run.yml stop
if errorlevel 1 pause
