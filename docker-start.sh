#!/bin/bash
# AI Provider OS — Opção B Docker — 1 comando Linux/Mac — SEM Rust, SEM Python

set -e

echo "🚀 AI Provider OS — Opção B Docker — 1 comando"
echo "==============================================="
echo ""

echo "Verificando Docker..."
docker --version || { echo "❌ Docker não encontrado — instale https://www.docker.com/products/docker-desktop/"; exit 1; }
docker compose version || docker-compose --version || { echo "❌ Docker Compose não encontrado"; exit 1; }

echo ""
echo "✅ Docker OK"
echo ""

echo "[1/3] Git pull..."
git pull origin main 2>/dev/null || echo "  Git pull falhou — continua com arquivos locais"

echo ""
echo "[2/3] Build e Start — docker compose up --build — 2-5 min primeira vez..."
docker compose up --build -d

echo ""
echo "[3/3] Aguardando backend healthy (30s)..."
sleep 10
docker ps

echo ""
echo "Health check..."
curl -s http://localhost:8000/health | head -c 200 || echo "  Aguardando backend — tente curl http://localhost:8000/health em 10s"
echo ""

echo ""
echo "=========================================="
echo "✅ Opção B Docker Concluído!"
echo "=========================================="
echo ""
echo "  Frontend: http://localhost:3000 — CHAT AI | Settings"
echo "  Backend:  http://localhost:8000"
echo "  Docs:     http://localhost:8000/docs"
echo "  Health:   http://localhost:8000/health"
echo ""
echo "  Logs: docker compose logs -f"
echo "  Parar: docker compose down"
echo "  Reset: docker compose down -v && docker compose up --build"
echo ""
echo "  Sem keys funciona! ovhcloud free sem key + 13 templates"
echo ""
