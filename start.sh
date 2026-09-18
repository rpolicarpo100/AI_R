#!/bin/bash
# AI Provider OS — Start Fácil 1 Comando
# Uso: bash start.sh
# Inicia backend + frontend em background
# Requer: bash setup.sh já executado 1x

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 AI Provider OS — Start Fácil${NC}"
echo "=============================="

# Verifica se setup foi feito
if [ ! -d "backend/.venv" ]; then
  echo -e "${YELLOW}⚠️  Setup não feito — executando setup.sh primeiro...${NC}"
  bash setup.sh
fi

# Mata processos antigos nas portas 8000 e 3000
echo ""
echo "Limpando portas 8000 e 3000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
sleep 1

# Backend
echo ""
echo -e "${YELLOW}[1/2] Iniciando backend :8000...${NC}"
cd backend
source .venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..
echo "  Backend PID $BACKEND_PID — log: backend.log"
sleep 3
curl -s http://localhost:8000/health | head -c 200
echo ""
echo -e "${GREEN}  ✅ Backend http://localhost:8000 — Docs http://localhost:8000/docs${NC}"

# Frontend
echo ""
echo -e "${YELLOW}[2/2] Iniciando frontend :3000...${NC}"
cd frontend
nohup npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "  Frontend PID $FRONTEND_PID — log: frontend.log"
sleep 3
echo -e "${GREEN}  ✅ Frontend http://localhost:3000 — CHAT AI | Settings${NC}"

echo ""
echo -e "${GREEN}==============================${NC}"
echo -e "${GREEN}✅ Tudo iniciado!${NC}"
echo -e "${GREEN}==============================${NC}"
echo ""
echo "  Frontend: http://localhost:3000 — CHAT AI | Settings"
echo "  Backend:  http://localhost:8000"
echo "  Docs:     http://localhost:8000/docs"
echo "  Health:   http://localhost:8000/health"
echo "  Rigor:    http://localhost:8000/api/benchmark/rigor"
echo ""
echo "  Logs: tail -f backend.log frontend.log"
echo "  Parar: lsof -ti:8000,3000 | xargs kill -9"
echo "         ou: pkill -f uvicorn; pkill -f 'next dev'"
echo ""
