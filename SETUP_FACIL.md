# 🚀 Setup Fácil — 1 Comando — AI Provider OS

**200 providers, 181 free, 14 free sem key, 965 models, 50 adapters, 13 templates — 1 comando**

## Opção 1 — Docker (MAIS FÁCIL — 1 comando) ⭐ Recomendado

```bash
git clone https://github.com/rpolicarpo100/AI_R.git
cd AI_R
docker compose up --build
```

- Frontend: http://localhost:3000 — CHAT AI | Settings
- Backend: http://localhost:8000 — Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

**Sem keys funciona!** ovhcloud 100% free sem key (2 RPM 500M/5M por dia) + 13 templates

Para usar 200 providers, adicione keys no `.env` ou `backend/.env`:
```
GROQ_API_KEY=gsk_...
CEREBRAS_API_KEY=csk_...
MISTRAL_API_KEY=...
```

---

## Opção 2 — Script Automático (FÁCIL — 1 comando local)

**Linux/Mac:**
```bash
git clone https://github.com/rpolicarpo100/AI_R.git
cd AI_R
bash setup.sh
bash start.sh
```

**Windows:**
```cmd
git clone https://github.com/rpolicarpo100/AI_R.git
cd AI_R
setup.bat
:: Depois 2 terminais:
:: Terminal 1: cd backend && .venv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
:: Terminal 2: cd frontend && npm run dev
```

`setup.sh` faz tudo automaticamente:
1. ✅ Cria `backend/.env` auto com SECRET_KEY random
2. ✅ Cria venv `backend/.venv` + instala deps `requirements.txt` + extras
3. ✅ Instala `frontend/node_modules`
4. ✅ Cria `frontend/.env.local` com `NEXT_PUBLIC_API_URL`
5. ✅ Testa DB init + seed 200 providers auto

`start.sh` inicia tudo:
- Backend :8000 — Docs :8000/docs — Health :8000/health
- Frontend :3000 — CHAT AI | Settings
- Logs: `backend.log` + `frontend.log`
- Parar: `lsof -ti:8000,3000 | xargs kill -9`

---

## Opção 3 — Makefile (FÁCIL)

```bash
make setup   # Setup 1 comando
make dev     # Start backend :8000 + frontend :3000
make docker  # Docker 1 comando
make health  # Health check
make test    # Testes rápidos
make stop    # Parar tudo
make help    # Ajuda
```

Fluxo:
```bash
make setup
make dev
# Abrir http://localhost:3000
```

---

## Opção 4 — Manual (antes, 10 passos — agora simplificado para 2)

**Backend:**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install python-jose passlib python-multipart slowapi cryptography httpx[http2] orjson
cp ../.env.example .env  # opcional — funciona sem .env (auto SECRET_KEY)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

---

## ✅ Verificação — 1 comando

```bash
curl http://localhost:8000/health
# {"status":"healthy","providers":200,"models":965,...}

curl http://localhost:8000/api/dashboard/stats | jq .ai_network
# {"total_providers":200,"free_no_card":181,"free_no_key":14,"total_models":965}

curl http://localhost:8000/api/benchmark/rigor | jq
# {"total":517,"measured":517,"measured_pct":100.0} — P16 100% rigor

# Chat test sem key (ovhcloud free)
curl http://localhost:8000/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"llama-3.3-70b-versatile","messages":[{"role":"user","content":"Hi in 3 words"}],"max_tokens":10}'
```

---

## 📦 O que setup.sh faz automaticamente (antes manual)

| Antes (manual 10 passos) | Agora (setup.sh 1 comando) |
|---------------------------|----------------------------|
| Criar .env manual + SECRET_KEY manual | ✅ Auto gera .env + SECRET_KEY random |
| python3 -m venv .venv manual | ✅ Auto cria venv se não existe |
| pip install -r requirements.txt + extras manual | ✅ Auto instala tudo quiet |
| npm install manual | ✅ Auto instala se node_modules não existe |
| Criar frontend .env.local manual | ✅ Auto cria |
| init_db manual | ✅ Auto testa DB init |
| Seed 200 providers manual | ✅ Auto seed no primeiro start backend |
| 2 terminais manual | ✅ start.sh inicia tudo background |

**Antes: 10 comandos, 5 minutos, erro fácil**
**Agora: 1 comando, 2 minutos, auto**

---

## 🔑 Keys — Opcional — Funciona sem

**Sem keys:**
- ovhcloud — 100% free sem key — 2 RPM — 500M input / 5M output por dia — EU DE/FI — experimental
- pollinations — free sem key — image + text
- 13 templates — landing-page, dashboard-saas, ecommerce, blog-md, chat-app, portfolio, api-gateway + 6

**Com keys (200 providers):**
Adicione em `backend/.env` ou `.env` na raiz:
```
GROQ_API_KEY=gsk_...
CEREBRAS_API_KEY=csk_...
MISTRAL_API_KEY=...
OPENROUTER_API_KEY=sk-or-...
HF_TOKEN=hf_...
GEMINI_API_KEY=...
NVIDIA_API_KEY=nvapi-...
DEEPSEEK_API_KEY=...
COHERE_API_KEY=...
```

Free providers com free tier (181 free_no_card):
- Groq — free 14k req/dia
- Cerebras — free 1M tokens/dia
- Mistral — $10/mês free credits
- OpenRouter — free models
- HuggingFace — 300+ models $0.10/mês
- Cohere — 1k/mês free
- etc — 181 free_no_card

---

## 🧪 Testes — 1 comando

```bash
cd backend
source .venv/bin/activate
pytest tests/test_p8_context_compiler.py tests/test_p6_speed_capacity.py tests/test_e2e_workplace_p7.py tests/test_multi_agent_p8.py -v
# 20 PASS — workplace templates 13, create project 200 OK, multi-agent REAL groq 1372ms
```

---

## 📂 Estrutura

```
AI_R/
  docker-compose.yml — 1 comando docker compose up --build
  setup.sh — 1 comando local Linux/Mac
  setup.bat — 1 comando Windows
  start.sh — start backend + frontend 1 comando
  Makefile — make setup, make dev, make docker
  SETUP_FACIL.md — este ficheiro
  backend/
    .venv/ — auto criado por setup.sh
    .env — auto criado com SECRET_KEY random
    ai_provider_os.db — 2.80 MB 200 providers 965 models auto seed
    app/ — FastAPI 200 providers 50 adapters
    requirements.txt
  frontend/
    node_modules/ — auto criado por setup.sh
    .env.local — auto criado
    app/ — Next.js 16.3.5 CHAT AI | Settings 13 templates
```

---

## 🆘 Troubleshooting Fácil

**Porta 8000 ou 3000 ocupada:**
```bash
lsof -ti:8000,3000 | xargs kill -9
# ou
make stop
```

**Reset total:**
```bash
make clean
make setup
make dev
```

**Docker reset:**
```bash
docker compose down -v
docker compose up --build
```

**Logs:**
```bash
tail -f backend.log frontend.log
# ou
make logs
```

**Health:**
```bash
make health
# ou
curl http://localhost:8000/health
```

---

**Pronto! 1 comando — 200 providers — 13 templates — CHAT AI | Settings**
