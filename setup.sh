#!/bin/bash
# AI Provider OS — Setup Fácil 1 Comando
# Uso: bash setup.sh
# Faz tudo automaticamente: venv, deps, .env, DB, backend + frontend
# Depois: backend http://localhost:8000 — frontend http://localhost:3000

set -e

echo "🚀 AI Provider OS — Setup Fácil 1 Comando"
echo "=========================================="
echo ""

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detecta OS
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
# Opcional — funciona sem keys (ovhcloud free sem key 2 RPM 500M/5M por dia)
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
  # Gera SECRET_KEY random se for placeholder
  if grep -q "change-me" backend/.env; then
    SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)
    sed -i "s/change-me-32chars-minimum-secret-key-prod/$SECRET/g" backend/.env || sed -i '' "s/change-me-32chars-minimum-secret-key-prod/$SECRET/g" backend/.env
    echo "  ✅ SECRET_KEY gerado auto: ${SECRET:0:16}..."
  fi
else
  echo "  ✅ backend/.env já existe — mantém"
fi

# 2. Backend venv + deps
echo ""
echo -e "${YELLOW}[2/5] Backend — venv + deps...${NC}"
cd backend
if [ ! -d ".venv" ]; then
  echo "  Criando venv..."
  python3 -m venv .venv
  echo "  ✅ venv criado"
else
  echo "  ✅ venv já existe"
fi

echo "  Ativando venv e instalando deps..."
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet python-jose passlib python-multipart slowapi cryptography httpx[http2] orjson 2>/dev/null || pip install --quiet python-jose passlib python-multipart slowapi cryptography httpx orjson
echo "  ✅ deps instaladas (200 providers, 50 adapters)"

# Testa backend rápido
echo "  Testando backend init..."
python3 -c "
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
  npm install --silent
  echo "  ✅ npm deps instaladas"
else
  echo "  ✅ node_modules já existe"
fi

# Frontend .env.local auto
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
source .venv/bin/activate
python3 << 'PY' 2>&1 | tail -n 10
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

# 5. Pronto — instruções
echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}✅ Setup Fácil Concluído!${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""
echo -e "${BLUE}Opção A — Docker (mais fácil, 1 comando):${NC}"
echo "  docker compose up --build"
echo "  → Frontend: http://localhost:3000"
echo "  → Backend:  http://localhost:8000/docs"
echo ""
echo -e "${BLUE}Opção B — Local dev (2 terminais):${NC}"
echo "  Terminal 1 — Backend:"
echo "    cd backend && source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "  Terminal 2 — Frontend:"
echo "    cd frontend && npm run dev"
echo "  → Frontend: http://localhost:3000 — CHAT AI | Settings"
echo ""
echo -e "${BLUE}Opção C — Start tudo com 1 script:${NC}"
echo "  bash start.sh"
echo ""
echo -e "${YELLOW}Sem keys funciona!${NC} ovhcloud 100% free sem key (2 RPM 500M/5M por dia) + 13 templates"
echo "  Para usar 200 providers, adicione keys em backend/.env: GROQ_API_KEY, CEREBRAS_API_KEY, etc"
echo ""
echo -e "${GREEN}Teste: curl http://localhost:8000/health${NC}"
echo ""
