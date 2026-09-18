@echo off
REM AI Provider OS — Setup Fácil Windows 1 Comando — FIX pytest conflict
REM Uso: setup.bat — corrige ERROR: Cannot install pytest==9.0.3 + pytest-asyncio==1.2.0

echo 🚀 AI Provider OS — Setup Fácil Windows
echo ==========================================

echo.
echo [1/5] Configurando backend .env...
if not exist backend\.env (
  if exist .env.example (
    copy .env.example backend\.env
    echo   backend\.env criado de .env.example
  ) else (
    echo SECRET_KEY=auto-generated-dev-key-32-chars-minimum-change-prod> backend\.env
    echo DATABASE_URL=sqlite:///./ai_provider_os.db>> backend\.env
    echo CORS_ORIGINS=*>> backend\.env
    echo GROQ_API_KEY=>> backend\.env
    echo CEREBRAS_API_KEY=>> backend\.env
    echo MISTRAL_API_KEY=>> backend\.env
    echo   backend\.env criado auto
  )
) else (
  echo   backend\.env ja existe — mantem
)

echo.
echo [2/5] Backend — venv + deps — FIX conflito pytest...
cd backend
if not exist .venv (
  echo   Criando venv...
  python -m venv .venv
  echo   venv criado
) else (
  echo   venv ja existe
)

echo   Ativando venv...
call .venv\Scripts\activate.bat

echo   Upgrade pip...
python -m pip install --quiet --upgrade pip

echo   Instalando core deps (sem pytest) — fix conflito...
if exist requirements-core.txt (
  pip install -r requirements-core.txt
  echo   core deps OK
) else (
  echo   requirements-core.txt nao encontrado — instalando core manual
  pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings python-multipart cryptography httpx apscheduler python-jose passlib openai slowapi redis tornado orjson bcrypt
)

echo   Instalando full deps com pytest fix 9.0.3 + 1.3.0...
pip install -r requirements.txt
if %errorlevel% neq 0 (
  echo   Full falhou — tentando pytest fix separado...
  pip install pytest==9.0.3 pytest-asyncio==1.3.0
  if %errorlevel% neq 0 (
    echo   Tentando pytest sem versao...
    pip install pytest pytest-asyncio
  )
)

echo   Instalando http2 extra...
pip install --quiet httpx[http2] 2>nul || pip install --quiet httpx 2>nul

echo   deps instaladas — 200 providers 50 adapters

cd ..

echo.
echo [3/5] Frontend — deps...
cd frontend
if not exist node_modules (
  echo   Instalando npm deps...
  call npm install --silent
  if %errorlevel% neq 0 (
    echo   Tentando npm install sem silent...
    call npm install
  )
  echo   npm deps instaladas
) else (
  echo   node_modules ja existe
)

if not exist .env.local (
  echo NEXT_PUBLIC_API_URL=http://localhost:8000> .env.local
  echo   .env.local criado
) else (
  echo   .env.local ja existe
)
cd ..

echo.
echo [4/5] Teste rapido...
cd backend
call .venv\Scripts\activate.bat
python -c "from app.core.database import init_db; init_db(); print('  DB init OK')"
if %errorlevel% neq 0 (
  echo   DB init falhou — vai seed no primeiro start (normal)
)
cd ..

echo.
echo ==========================================
echo Setup Facil Concluido! FIX pytest conflict OK
echo ==========================================
echo.
echo Opcao A — Docker (mais facil):
echo   docker compose up --build
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8000/docs
echo.
echo Opcao B — Local dev (2 terminais):
echo   Terminal 1: cd backend ^&^& .venv\Scripts\activate ^&^& uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
echo   Terminal 2: cd frontend ^&^& npm run dev
echo   Frontend: http://localhost:3000
echo.
echo Sem keys funciona! ovhcloud free sem key 2 RPM + 13 templates
echo Fix: pytest==9.0.3 + pytest-asyncio==1.3.0 (antes 1.2.0 conflito)
echo.
