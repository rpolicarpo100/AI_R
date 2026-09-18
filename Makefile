# AI Provider OS — Makefile Setup Fácil
# Uso: make setup — depois make dev ou make docker

.PHONY: setup dev docker stop clean test health

# Setup fácil 1 comando — venv, deps, .env auto
setup:
	@echo "🚀 Setup Fácil 1 Comando..."
	@bash setup.sh

# Dev local — 2 processos (requer setup)
dev:
	@echo "🚀 Dev Local — backend :8000 + frontend :3000"
	@bash start.sh

# Docker — 1 comando mais fácil
docker:
	@echo "🐳 Docker — 1 comando..."
	docker compose up --build

docker-down:
	docker compose down

# Parar tudo
stop:
	@echo "🛑 Parando..."
	@lsof -ti:8000,3000 | xargs kill -9 2>/dev/null || true
	@pkill -f uvicorn 2>/dev/null || true
	@pkill -f "next dev" 2>/dev/null || true
	@echo "✅ Parado"

# Limpeza
clean:
	rm -rf backend/.venv backend/__pycache__ backend/app/__pycache__ backend/ai_provider_os.db backend/.fernet_key
	rm -rf frontend/node_modules frontend/.next
	rm -f backend.log frontend.log
	@echo "✅ Limpo"

# Teste rápido
test:
	cd backend && source .venv/bin/activate && pytest tests/test_p8_context_compiler.py tests/test_p6_speed_capacity.py tests/test_e2e_workplace_p7.py tests/test_multi_agent_p8.py -v

# Health check
health:
	@curl -s http://localhost:8000/health | python3 -m json.tool
	@echo ""
	@curl -s http://localhost:8000/api/dashboard/stats | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"Providers: {d.get('ai_network',{}).get('total_providers',0)} Models: {d.get('ai_network',{}).get('total_models',0)}\")" 2>/dev/null || echo "Stats não disponível"

# Logs
logs:
	tail -f backend.log frontend.log

# Ajuda
help:
	@echo "AI Provider OS — Comandos Fáceis:"
	@echo ""
	@echo "  make setup   — Setup fácil 1 comando (venv, deps, .env auto)"
	@echo "  make dev     — Start backend :8000 + frontend :3000"
	@echo "  make docker  — Docker 1 comando (mais fácil)"
	@echo "  make stop    — Parar tudo"
	@echo "  make clean   — Limpeza"
	@echo "  make test    — Testes rápidos"
	@echo "  make health  — Health check"
	@echo "  make logs    — Ver logs"
	@echo ""
	@echo "Fluxo mais fácil:"
	@echo "  1. make setup"
	@echo "  2. make dev  — ou make docker"
	@echo "  3. Abrir http://localhost:3000"
