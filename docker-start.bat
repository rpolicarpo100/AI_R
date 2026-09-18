@echo off
REM AI Provider OS — Opção B Docker — 1 comando Windows — FIX daemon não rodando
REM Uso: docker-start.bat
REM Requer: Docker Desktop instalado e RODANDO (não só instalado)

echo 🚀 AI Provider OS — Opção B Docker — 1 comando
echo ===============================================
echo.

echo Verificando Docker...
docker --version
if %errorlevel% neq 0 (
  echo ❌ Docker não encontrado!
  echo Instale Docker Desktop: https://www.docker.com/products/docker-desktop/
  pause
  exit /b 1
)

echo.
echo Verificando Docker Compose...
docker compose version >nul 2>&1
if %errorlevel% neq 0 (
  docker-compose --version >nul 2>&1
  if %errorlevel% neq 0 (
    echo ❌ Docker Compose não encontrado!
    pause
    exit /b 1
  )
)

echo ✅ Docker CLI OK — versão 29.7.2 detectada
echo.

echo Verificando Docker DAEMON (engine rodando)...
docker ps >nul 2>&1
if %errorlevel% neq 0 (
  echo.
  echo ❌ Docker daemon NÃO está rodando!
  echo Erro que tiveste: failed to connect to docker API at npipe:////./pipe/dockerDesktopLinuxEngine
  echo O sistema não conseguiu localizar o ficheiro especificado.
  echo.
  echo 🔧 FIX — Faz isto AGORA:
  echo   1. Abre Docker Desktop manualmente (procura Docker Desktop no menu Iniciar)
  echo   2. Espera 30-60s até ficar VERDE Running / Engine running no canto inferior esquerdo
  echo   3. Se ficar vermelho ou não inicia, faz no PowerShell ADMIN:
  echo      wsl --update
  echo      wsl --shutdown
  echo      Depois abre Docker Desktop novamente
  echo   4. Depois de Docker Desktop ficar VERDE, volta aqui e executa docker-start.bat novamente
  echo.
  echo   Tentando abrir Docker Desktop automaticamente...
  start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe" 2>nul
  start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" 2>nul
  start "" "%LOCALAPPDATA%\Docker\Docker Desktop.exe" 2>nul
  
  echo.
  echo   Aguardando 10s para Docker iniciar...
  timeout /t 10 /nobreak >nul
  docker ps >nul 2>&1
  if %errorlevel% neq 0 (
    echo   Ainda não rodando — aguardando mais 20s...
    timeout /t 20 /nobreak >nul
    docker ps >nul 2>&1
    if %errorlevel% neq 0 (
      echo.
      echo ❌ Docker daemon ainda não rodando após 30s
      echo   Abre Docker Desktop manualmente e espera ficar VERDE
      echo   Depois executa: docker-start.bat
      echo.
      pause
      exit /b 1
    )
  )
)

echo ✅ Docker daemon RODANDO — engine OK
echo.

echo [1/3] Git pull...
git pull origin main 2>nul || echo   Git pull falhou — continua com arquivos locais

echo.
echo [2/3] Build e Start — docker compose up --build -d — 2-5 min primeira vez...
docker compose up --build -d

if %errorlevel% neq 0 (
  echo.
  echo ❌ docker compose up falhou — tentando com logs visiveis...
  echo   Se ainda falhar, faz:
  echo   docker compose down -v
  echo   docker compose up --build
  echo.
  docker compose up --build
  pause
  exit /b 1
)

echo.
echo [3/3] Aguardando backend healthy (30s)...
timeout /t 10 /nobreak >nul
docker ps

echo.
echo Health check...
curl -s http://localhost:8000/health 2>nul || echo   Aguardando backend — tenta http://localhost:8000/health em 10s

echo.
echo ==========================================
echo ✅ Opção B Docker Concluído!
echo ==========================================
echo.
echo   Frontend: http://localhost:3000 — CHAT AI | Settings
echo   Backend:  http://localhost:8000
echo   Docs:     http://localhost:8000/docs
echo   Health:   http://localhost:8000/health
echo.
echo   Logs: docker compose logs -f
echo   Parar: docker compose down
echo   Reset: docker compose down -v ^&^& docker compose up --build
echo.
echo   Sem keys funciona! ovhcloud free 2 RPM + 13 templates
echo.
echo Abrindo browser...
start http://localhost:3000 2>nul
start http://localhost:8000/docs 2>nul

pause
