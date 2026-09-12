@echo off
chcp 65001 >nul
cd /d "%~dp0"
docker info >nul 2>&1
if errorlevel 1 (
    echo 请先安装并启动 Docker Desktop，使用 Linux containers。
    pause
    exit /b 1
)
echo 首次构建需要联网下载依赖和 MiniLM 模型，请等待容器就绪。
docker compose -p rag-portfolio -f compose.run.yml up -d --build --wait --wait-timeout 300
if errorlevel 1 (
    echo 启动失败，请查看上方日志。
    pause
    exit /b 1
)
start "" "http://localhost:8000/docs"
echo 已打开接口页面。先使用 POST /documents 添加文档，再使用 POST /query 提问。
