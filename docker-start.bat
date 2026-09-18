@echo off
REM AI Provider OS — Opção B Docker — 1 comando Windows — SEM Rust, SEM Python
REM Uso: docker-start.bat
REM Requer: Docker Desktop instalado e rodando

echo 🚀 AI Provider OS — Opção B Docker — 1 comando
echo ===============================================
echo.

echo Verificando Docker...
docker --version
if %errorlevel% neq 0 (
  echo ❌ Docker não encontrado!
  echo Instale Docker Desktop: https://www.docker.com/products/docker-desktop/
  echo Depois reinicie e execute este bat novamente.
  pause
  exit /b 1
)

echo.
echo Verificando Docker Compose...
docker compose version
if %errorlevel% neq 0 (
  echo Tentando docker-compose...
  docker-compose --version
  if %errorlevel% neq 0 (
    echo ❌ Docker Compose não encontrado!
    pause
    exit /b 1
  )
)

echo.
echo ✅ Docker OK
echo.

echo [1/3] Git pull (atualizando)...
git pull origin main 2>nul || echo   Git pull falhou ou não é repo git — ok, continua com arquivos locais

echo.
echo [2/3] Build e Start — docker compose up --build — pode demorar 2-5 min primeira vez...
echo   Backend: python:3.11-slim + requirements flexiveis (sem Rust)
echo   Frontend: node:20-alpine
echo.

docker compose up --build -d

if %errorlevel% neq 0 (
  echo ❌ docker compose up falhou — tentando sem -d para ver logs...
  docker compose up --build
  pause
  exit /b 1
)

echo.
echo [3/3] Aguardando backend ficar healthy (30s)...
timeout /t 10 /nobreak >nul
docker ps

echo.
echo Verificando health...
timeout /t 5 /nobreak >nul
curl -s http://localhost:8000/health 2>nul || echo   Aguardando backend iniciar — tente curl http://localhost:8000/health em 10s

echo.
echo ==========================================
echo ✅ Opção B Docker Concluído!
echo ==========================================
echo.
echo   Frontend: http://localhost:3000 — CHAT AI ^| Settings
echo   Backend:  http://localhost:8000
echo   Docs:     http://localhost:8000/docs
echo   Health:   http://localhost:8000/health
echo   Rigor:    http://localhost:8000/api/benchmark/rigor
echo.
echo   Logs: docker compose logs -f
echo   Parar: docker compose down
echo   Reset: docker compose down -v ^&^& docker compose up --build
echo.
echo   Sem keys funciona! ovhcloud free sem key 2 RPM 500M/5M por dia + 13 templates
echo   Para usar 200 providers, adicione keys no .env na raiz:
echo     GROQ_API_KEY=gsk_...
echo     CEREBRAS_API_KEY=csk_...
echo.
echo Abrindo browser...
start http://localhost:3000 2>nul
start http://localhost:8000/docs 2>nul

echo.
pause
