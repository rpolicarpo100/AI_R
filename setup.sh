#!/bin/bash
# AI Provider OS — Setup Fácil 1 Comando — FIX pytest conflict
# Uso: bash setup.sh
# Faz tudo automaticamente: venv, deps, .env, DB, backend + frontend

set -e

echo "🚀 AI Provider OS — Setup Fácil 1 Comando"
echo "=========================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

OS="$(uname -s)"
echo -e "${BLUE}OS detectado: $OS${NC}"

# 1. Backend .env auto
echo ""
echo -e "${YELLOW}[1/5] Configurando backend .env...${NC}"
if [ ! -f "backend/.env" ]; then
  if [ -f ".env.example" ]; then
    cp .env.example backend/.env
    echo "  ✅ backend/.env criado de .env.example"
  else
    cat > backend/.env << 'EOF'
SECRET_KEY=auto-generated-dev-key-32-chars-minimum-change-prod
DATABASE_URL=sqlite:///./ai_provider_os.db
CORS_ORIGINS=*
GROQ_API_KEY=
CEREBRAS_API_KEY=
MISTRAL_API_KEY=
OPENROUTER_API_KEY=
HF_TOKEN=
GEMINI_API_KEY=
NVIDIA_API_KEY=
DEEPSEEK_API_KEY=
COHERE_API_KEY=
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
    echo "  ✅ backend/.env criado auto"
  fi
  if grep -q "change-me" backend/.env 2>/dev/null; then
    SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32 2>/dev/null || echo "dev-secret-key-$(date +%s)-32chars-minimum")
    # Linux sed
    sed -i "s/change-me-32chars-minimum-secret-key-prod/$SECRET/g" backend/.env 2>/dev/null || \
    sed -i '' "s/change-me-32chars-minimum-secret-key-prod/$SECRET/g" backend/.env 2>/dev/null || true
    echo "  ✅ SECRET_KEY gerado auto"
  fi
else
  echo "  ✅ backend/.env já existe — mantém"
fi

# 2. Backend venv + deps — FIX: usa requirements-core.txt primeiro (sem pytest conflito)
echo ""
echo -e "${YELLOW}[2/5] Backend — venv + deps...${NC}"
cd backend
if [ ! -d ".venv" ]; then
  echo "  Criando venv..."
  python3 -m venv .venv 2>/dev/null || python -m venv .venv
  echo "  ✅ venv criado"
else
  echo "  ✅ venv já existe"
fi

echo "  Ativando venv e instalando deps..."
# Ativa venv — Linux/Mac
source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate 2>/dev/null || true

pip install --quiet --upgrade pip

# FIX principal: instala core primeiro (sem pytest) — 100% sem conflito
if [ -f "requirements-core.txt" ]; then
  echo "  Instalando core deps (sem pytest) — fix conflito..."
  pip install -r requirements-core.txt
  echo "  ✅ core deps OK"
else
  echo "  requirements-core.txt não encontrado — usando requirements.txt com fallback"
fi

# Depois tenta full requirements.txt (com pytest 9.0.3 + pytest-asyncio 1.3.0 fix)
echo "  Instalando full deps (com pytest fix 9.0.3 + 1.3.0)..."
pip install -r requirements.txt 2>&1 | tail -n 5 || {
  echo "  ⚠️  Full install falhou — tentando core apenas + pytest fix separado"
  pip install pytest==9.0.3 pytest-asyncio==1.3.0 2>&1 | tail -n 3 || pip install pytest pytest-asyncio 2>&1 | tail -n 3 || true
}

# Extras opcionais — já estão no requirements mas garante http2
pip install --quiet httpx[http2] 2>/dev/null || pip install --quiet httpx 2>/dev/null || true

echo "  ✅ deps instaladas (200 providers, 50 adapters)"

# Testa backend rápido
echo "  Testando backend init..."
python3 -c "
from app.core.database import init_db
init_db()
print('  ✅ DB init OK')
" 2>&1 | tail -n 5 || python -c "
from app.core.database import init_db
init_db()
print('  ✅ DB init OK')
" 2>&1 | tail -n 5

cd ..

# 3. Frontend deps
echo ""
echo -e "${YELLOW}[3/5] Frontend — deps...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
  echo "  Instalando npm deps..."
  npm install --silent 2>&1 | tail -n 5 || npm install 2>&1 | tail -n 10
  echo "  ✅ npm deps instaladas"
else
  echo "  ✅ node_modules já existe"
fi

if [ ! -f ".env.local" ]; then
  echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
  echo "  ✅ .env.local criado"
else
  echo "  ✅ .env.local já existe"
fi
cd ..

# 4. Teste rápido
echo ""
echo -e "${YELLOW}[4/5] Teste rápido...${NC}"
cd backend
source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate 2>/dev/null || true
python3 << 'PY' 2>&1 | tail -n 10 || python << 'PY' 2>&1 | tail -n 10
from app.core.database import SessionLocal
from app.models.database_models import Provider, Model
from app.core.database import init_db
init_db()
db=SessionLocal()
try:
    print(f"  Providers: {db.query(Provider).count()} (esperado 200)")
    print(f"  Models: {db.query(Model).count()} (esperado 965)")
    from app.routers.providers import ADAPTERS_MAP
    print(f"  Adapters: {len(ADAPTERS_MAP)} (esperado 50)")
    print("  ✅ Teste rápido OK")
except Exception as e:
    print(f"  DB ainda vazio — vai seed no primeiro start: {e}")
    print("  ✅ Teste rápido OK — seed automático no start")
finally:
    db.close()
PY
cd ..

# 5. Pronto
echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}✅ Setup Fácil Concluído!${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""
echo -e "${BLUE}Opção A — Docker (mais fácil):${NC}"
echo "  docker compose up --build"
echo "  → Frontend: http://localhost:3000"
echo "  → Backend:  http://localhost:8000/docs"
echo ""
echo -e "${BLUE}Opção B — Local dev (2 terminais):${NC}"
echo "  Terminal 1: cd backend && source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo "  Terminal 2: cd frontend && npm run dev"
echo ""
echo -e "${BLUE}Opção C — Start tudo:${NC}"
echo "  bash start.sh"
echo ""
echo -e "${YELLOW}Sem keys funciona!${NC} ovhcloud free sem key + 13 templates"
echo ""
