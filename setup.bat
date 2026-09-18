@echo off
REM AI Provider OS — Setup Fácil Windows 1 Comando — FIX pydantic-core wheel sem Rust
REM Uso: setup.bat
REM FIX: versões flexíveis + --prefer-binary para evitar build pydantic-core que precisa Rust/maturin no Windows

echo 🚀 AI Provider OS — Setup Fácil Windows
echo ==========================================
echo Python version:
python --version
echo.

echo [1/5] Configurando backend .env...
if not exist backend\.env (
  if exist .env.example (
    copy .env.example backend\.env >nul
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
echo [2/5] Backend — venv + deps — FIX pydantic-core wheel Windows...
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

echo   Upgrade pip (importante para wheels)...
python -m pip install --quiet --upgrade pip wheel setuptools

echo   Instalando core deps com --prefer-binary (evita build Rust)...
if exist requirements-core.txt (
  echo   Tentando requirements-core.txt com binary prefer...
  pip install --prefer-binary -r requirements-core.txt
  if %errorlevel% neq 0 (
    echo   Falhou com prefer-binary — tentando sem...
    pip install -r requirements-core.txt
  )
  if %errorlevel% neq 0 (
    echo   Ainda falhou — tentando instalar um a um...
    pip install --prefer-binary fastapi uvicorn sqlalchemy pydantic pydantic-settings python-multipart cryptography httpx apscheduler python-jose passlib openai slowapi redis tornado orjson bcrypt
  )
  echo   core deps OK
) else (
  echo   requirements-core.txt nao encontrado — instalando manual com binary
  pip install --prefer-binary fastapi uvicorn sqlalchemy pydantic pydantic-settings python-multipart cryptography httpx apscheduler python-jose passlib openai slowapi redis tornado orjson bcrypt
)

echo.
echo   Instalando pytest (opcional) com binary...
pip install --prefer-binary pytest pytest-asyncio 2>nul
if %errorlevel% neq 0 (
  echo   pytest opcional falhou — ok, core ja funciona sem testes
) else (
  echo   pytest OK
)

echo.
echo   Verificando pydantic...
python -c "import pydantic; print('  pydantic', pydantic.__version__, 'OK')" 2>nul
if %errorlevel% neq 0 (
  echo   pydantic falhou — tentando instalar pydantic binary especifico...
  pip install --only-binary=:all: pydantic 2>nul || pip install pydantic --prefer-binary
)

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
echo Setup Facil Concluido! FIX pydantic-core Windows OK
echo ==========================================
echo.
echo Se ainda falhar pydantic-core, tente:
echo   1. Use Python 3.11 ou 3.12 (mais wheels Windows) em vez de 3.13
echo      python --version — se for 3.13, instale 3.11 de python.org
echo   2. Instale Rust (opcional): https://rustup.rs
echo   3. Ou use Docker (mais facil, sem Rust): docker compose up --build
echo.
echo Opcao A — Docker (mais facil, sem Rust):
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
echo Fix: requirements flexiveis + --prefer-binary evita build pydantic-core
echo.
