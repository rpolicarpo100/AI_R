@echo off
REM AI Provider OS — Setup Fácil Windows 1 Comando
REM Uso: setup.bat
REM Faz tudo: venv, deps, .env, DB, instruções

echo 🚀 AI Provider OS — Setup Fácil Windows
echo ==========================================

echo.
echo [1/5] Configurando backend .env...
if not exist backend\.env (
  if exist .env.example (
    copy .env.example backend\.env
    echo   ✅ backend\.env criado
  ) else (
    echo SECRET_KEY=auto-generated-dev-key-32-chars-minimum-change-prod> backend\.env
    echo DATABASE_URL=sqlite:///./ai_provider_os.db>> backend\.env
    echo CORS_ORIGINS=*>> backend\.env
    echo GROQ_API_KEY=>> backend\.env
    echo CEREBRAS_API_KEY=>> backend\.env
    echo MISTRAL_API_KEY=>> backend\.env
    echo   ✅ backend\.env criado auto
  )
) else (
  echo   ✅ backend\.env já existe
)

echo.
echo [2/5] Backend — venv + deps...
cd backend
if not exist .venv (
  echo   Criando venv...
  python -m venv .venv
  echo   ✅ venv criado
) else (
  echo   ✅ venv já existe
)

echo   Instalando deps...
call .venv\Scripts\activate.bat
python -m pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet python-jose passlib python-multipart slowapi cryptography httpx orjson
echo   ✅ deps instaladas

cd ..

echo.
echo [3/5] Frontend — deps...
cd frontend
if not exist node_modules (
  echo   Instalando npm deps...
  call npm install --silent
  echo   ✅ npm deps instaladas
) else (
  echo   ✅ node_modules já existe
)

if not exist .env.local (
  echo NEXT_PUBLIC_API_URL=http://localhost:8000> .env.local
  echo   ✅ .env.local criado
)
cd ..

echo.
echo [4/5] Teste rápido...
cd backend
call .venv\Scripts\activate.bat
python -c "from app.core.database import init_db; init_db(); print('  ✅ DB init OK')"
cd ..

echo.
echo ==========================================
echo ✅ Setup Fácil Concluído!
echo ==========================================
echo.
echo Opção A — Docker (mais fácil):
echo   docker compose up --build
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8000/docs
echo.
echo Opção B — Local dev (2 terminais):
echo   Terminal 1: cd backend ^&^& .venv\Scripts\activate ^&^& uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
echo   Terminal 2: cd frontend ^&^& npm run dev
echo   Frontend: http://localhost:3000
echo.
echo Sem keys funciona! ovhcloud free sem key + 13 templates
echo.
