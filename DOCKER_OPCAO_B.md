# 🐳 Opção B Docker — 1 Comando — SEM Rust, SEM Python, SEM Node

**Escolheste Opção B — a mais fácil no Windows!** Não precisa Python, Rust, venv, pip — apenas Docker Desktop.

## ✅ Pré-requisitos

1. **Docker Desktop** instalado e rodando:
   - Download: https://www.docker.com/products/docker-desktop/
   - Instala, reinicia PC, abre Docker Desktop, espera ficar verde "Running"
   - Testa: abre CMD e digita `docker --version` → deve mostrar versão

## 🚀 Setup — 1 Comando

### Windows — Duplo clique ou CMD:

**Opção B1 — Script automático (recomendado):**
```cmd
cd AI_R
docker-start.bat
```
- Faz git pull, build, start, abre browser http://localhost:3000

**Opção B2 — Comando manual:**
```cmd
cd AI_R
docker compose up --build
```
- Primeira vez demora 2-5 min (baixa python:3.11-slim + node:20-alpine + pip install)
- Depois fica rápido (cache)

**Opção B3 — Com logs visíveis:**
```cmd
cd AI_R
docker compose up --build
```
- Vê logs backend + frontend ao vivo
- Ctrl+C para parar

## 🌐 Acessar

Depois de `docker compose up --build`:

- **Frontend:** http://localhost:3000 — CHAT AI | Settings — 13 templates
- **Backend:** http://localhost:8000
- **Docs Swagger:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health → `{"status":"healthy","providers":200,...}`
- **Rigor:** http://localhost:8000/api/benchmark/rigor
- **Stats:** http://localhost:8000/api/dashboard/stats

**Sem keys funciona!** ovhcloud 100% free sem key (2 RPM 500M/5M por dia) + 13 templates:
- landing-page, dashboard-saas, ecommerce, blog-md, chat-app, portfolio, api-gateway + 6

## 🔑 Com Keys — 200 Providers

Para usar 200 providers, cria `.env` na raiz `AI_R/.env`:
```
GROQ_API_KEY=gsk_...
CEREBRAS_API_KEY=csk_...
MISTRAL_API_KEY=...
OPENROUTER_API_KEY=sk-or-...
HF_TOKEN=hf_...
GEMINI_API_KEY=...
NVIDIA_API_KEY=nvapi-...
```

Depois:
```cmd
docker compose down
docker compose up --build
```

Docker lê `.env` automaticamente via `${GROQ_API_KEY:-}` no docker-compose.yml

## 🛠️ Comandos Úteis

```cmd
# Ver logs
docker compose logs -f
docker compose logs -f backend
docker compose logs -f frontend

# Ver containers rodando
docker ps

# Parar tudo
docker compose down

# Reset total (apaga DB e rebuild)
docker compose down -v
docker compose up --build

# Health check
curl http://localhost:8000/health
# ou no browser: http://localhost:8000/health

# Testar chat sem key (ovhcloud free)
curl http://localhost:8000/v1/chat/completions -H "Content-Type: application/json" -d "{\"model\":\"llama-3.3-70b-versatile\",\"messages\":[{\"role\":\"user\",\"content\":\"Hi in 3 words\"}],\"max_tokens\":10}"
```

## 🆘 Troubleshooting Windows

**1. Docker não encontrado:**
```
docker: command not found
```
- Instala Docker Desktop https://www.docker.com/products/docker-desktop/
- Reinicia PC
- Abre Docker Desktop e espera "Running"

**2. Porta 8000 ou 3000 ocupada:**
```cmd
# Parar containers antigos
docker compose down
# Ver quem usa porta
netstat -ano | findstr :8000
netstat -ano | findstr :3000
# Mata processo ou muda porta no docker-compose.yml
```

**3. Build falha no Windows:**
```cmd
# Limpa cache Docker
docker system prune -a
docker compose up --build --no-cache
```

**4. Frontend não abre:**
- Aguarda 30s — backend tem healthcheck 30s start_period
- Vê logs: `docker compose logs -f backend`
- Testa backend primeiro: http://localhost:8000/health deve dar 200 OK
- Depois frontend: http://localhost:3000

**5. WSL2 no Windows:**
- Docker Desktop usa WSL2 — se der erro WSL, abre PowerShell admin:
```powershell
wsl --update
wsl --shutdown
```
- Abre Docker Desktop novamente

## 📊 O que Docker faz (sem Rust!)

- **Backend Dockerfile:** `FROM python:3.11-slim`
  - Python 3.11 tem wheels binários para `pydantic-core` (não precisa Rust/maturin)
  - `pip install -r requirements.txt` com versões flexíveis `>=` encontra wheels
  - Evita erro `Failed building wheel for pydantic-core` que tiveste no Windows Python 3.13

- **Frontend Dockerfile:** `FROM node:20-alpine`
  - Build Next.js 16.3.5 Turbopack
  - 0 vulns, 1.0s build

- **docker-compose.yml:** 2 serviços + 2 volumes
  - backend:8000 + frontend:3000
  - Volumes `backend_db` + `backend_storage` persistem DB
  - Healthcheck curl backend, frontend depende de backend healthy

## ✅ Vantagens Opção B Docker

| Opção A Local | Opção B Docker ⭐ |
|---------------|-------------------|
| Precisa Python 3.11/3.12, Node, Rust opcional | Apenas Docker Desktop |
| venv, pip install, npm install manual | 1 comando `docker compose up --build` |
| Erro pydantic-core sem Rust no Windows 3.13 | Sem Rust — python:3.11-slim tem wheels |
| Portas podem conflitar | Isolado em containers |
| Precisa .env manual | Lê .env automático |

**Opção B é a mais fácil no Windows!** 🎉

## 🎯 Próximos Passos

1. `docker-start.bat` ou `docker compose up --build`
2. Abre http://localhost:3000 — CHAT AI | Settings
3. Testa: digita "Cria uma landing page moderna" no CHAT AI
4. Vê 13 templates em Workplace
5. Adiciona keys no `.env` para 200 providers se quiseres

---

**Pronto! 1 comando Docker — sem Rust — 200 providers — 13 templates**
