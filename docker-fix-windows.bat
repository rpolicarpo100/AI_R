@echo off
REM AI Provider OS — FIX Docker daemon não rodando Windows
REM Uso: docker-fix-windows.bat — roda como ADMIN se possível
REM Fix para: failed to connect to docker API at npipe:////./pipe/dockerDesktopLinuxEngine

echo 🔧 FIX Docker daemon não rodando — Windows
echo ==========================================
echo Erro: failed to connect to docker API at npipe:////./pipe/dockerDesktopLinuxEngine
echo       O sistema não conseguiu localizar o ficheiro especificado.
echo.

echo [1/5] Verificando Docker instalado...
docker --version
if %errorlevel% neq 0 (
  echo ❌ Docker não instalado — instala https://www.docker.com/products/docker-desktop/
  pause
  exit /b 1
)
echo ✅ Docker CLI instalado

echo.
echo [2/5] Verificando WSL...
wsl --version
if %errorlevel% neq 0 (
  echo ⚠️  WSL não encontrado — Docker Desktop precisa WSL2
  echo Instala WSL: wsl --install no PowerShell ADMIN
) else (
  echo ✅ WSL OK
)

echo.
echo [3/5] Atualizando WSL...
echo   Executando: wsl --update
wsl --update
if %errorlevel% neq 0 (
  echo ⚠️  wsl --update falhou — tenta rodar este bat como ADMIN (botão direito Run as administrator)
) else (
  echo ✅ WSL atualizado
)

echo.
echo [4/5] Reiniciando WSL...
echo   Executando: wsl --shutdown
wsl --shutdown
echo ✅ WSL shutdown OK — vai reiniciar com Docker Desktop

echo.
echo [5/5] Iniciando Docker Desktop...
echo   Tentando abrir Docker Desktop...
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe" 2>nul
timeout /t 2 /nobreak >nul
start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" 2>nul
timeout /t 2 /nobreak >nul

echo.
echo   Aguardando Docker Desktop iniciar (30s)...
echo   Abre Docker Desktop manualmente se não abrir sozinho
echo   Espera ficar VERDE Running no canto inferior esquerdo
echo.
timeout /t 30 /nobreak

echo.
echo Verificando se daemon agora está rodando...
docker ps
if %errorlevel% equ 0 (
  echo.
  echo ✅ Docker daemon AGORA está rodando!
  echo   Podes executar: docker-start.bat
  echo   Ou: docker compose up --build
) else (
  echo.
  echo ❌ Ainda não rodando — faz manualmente:
  echo   1. Abre Docker Desktop no menu Iniciar
  echo   2. Espera ficar VERDE Running (pode demorar 1-2 min primeira vez)
  echo   3. Se der erro WSL, abre PowerShell ADMIN e faz:
  echo      wsl --update
  echo      wsl --shutdown
  echo   4. Abre Docker Desktop novamente
  echo   5. Depois: docker-start.bat
)

echo.
pause
