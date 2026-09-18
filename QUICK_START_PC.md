# QUICK START PC — AI Provider OS — 200 Providers — Teste Rápido

## 🚀 1. Clone Repo

```bash
git clone https://github.com/rpolicarpo100/AI_R.git
cd AI_R
```

Ou se já tens 1-PROJECT:
```bash
cd /home/user/1-PROJECT
```

## 📦 2. Backend — FastAPI — 200 Providers

```bash
cd backend

# Criar venv
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Instalar deps
pip install -r requirements.txt
pip install python-jose passlib python-multipart slowapi cryptography httpx[http2] orjson

# Configurar .env (opcional — sem keys funciona com ovhcloud 100% free sem key)
cp .env.example .env
# Editar .env se tiveres keys: GROQ_API_KEY, CEREBRAS_API_KEY, etc

# Rodar backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Backend estará em:
# http://localhost:8000
# http://localhost:8000/docs (Swagger)
# http://localhost:8000/health
# http://localhost:8000/metrics
```

**Primeira vez**: Vai seed 200 providers automaticamente (P7-P15 200) — demora ~5s:
- P7 32→... 
- P9-P14 100 providers
- P15 200 100→200 providers (libertai, berget_ai, llmwise, opper 700+ models, eurouter 100+ models 10K req/mo free GDPR, etc)
- Total 200 providers, 181 free_no_card, 14 free_no_key, 965 models

**Testar backend**:
```bash
# Health
curl http://localhost:8000/health

# Stats
curl http://localhost:8000/api/dashboard/stats | jq .ai_network

# List providers com paginação P27 (400KB→50KB)
curl "http://localhost:8000/api/dashboard/network?page=0&per_page=50" | jq .pagination

# Rigor
curl http://localhost:8000/api/benchmark/rigor | jq

# Test provider ovhcloud sem key (real free 2 RPM 500M/5M per day)
curl http://localhost:8000/api/providers/ovhcloud/test -X POST

# Chat completion OpenAI-compatible
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.3-70b-versatile",
    "messages": [{"role": "user", "content": "Hello, say hi in 3 words"}],
    "max_tokens": 10
  }'
```

## 💻 3. Frontend — Next.js 16.3.5 — CHAT AI | Settings

```bash
cd frontend

# Instalar deps
npm install

# Rodar frontend
npm run dev

# Frontend estará em:
# http://localhost:3000
# CHAT AI | Settings dashboard
```

**Frontend tabs**:
- **CHAT AI**: Chat com 200 providers, /testa /audita /contesta /melhora /explica comandos que leem arquivos reais
- **Settings**: Dashboard network (200 providers paginação 50 per page P27), benchmarks, rigor, agents, audit, observability

## 🧪 4. Testes — 54 PASS

```bash
cd backend
source .venv/bin/activate

# Core tests P6-P8 + e2e
pytest tests/test_p8_context_compiler.py tests/test_p8_rigor_optimizer.py tests/test_p7_rigor_powerful.py tests/test_p6_speed_capacity.py tests/test_e2e_workplace_p7.py tests/test_multi_agent_p8.py -v

# Todos tests (191 funcs)
pytest tests/ -k "not test_e2e" -v  # sem server
pytest tests/ -v  # com server (alguns 59 fail expected precisa server rodando)

# Resultado esperado: 54 PASS (45 core + 9 e2e workplace multi_agent)
```

## 🔍 5. Auditoria Rápida — 200 Providers

```bash
cd backend
python3 << 'PY'
from app.core.database import SessionLocal
from app.models.database_models import Provider, Model
from app.routers.providers import ADAPTERS_MAP

db=SessionLocal()
print(f"Providers: {db.query(Provider).count()} (esperado 200)")
print(f"Models: {db.query(Model).count()} (esperado 963)")
print(f"Free_no_card: {len([p for p in db.query(Provider).all() if (p.capabilities or {}).get('free_no_card')])} (esperado 181)")
print(f"Free_no_key: {len([p for p in db.query(Provider).all() if (p.capabilities or {}).get('free_no_key')])} (esperado 14)")
print(f"Adapters dedicados: {len(ADAPTERS_MAP)} (esperado 50)")

from app.services.rigor_optimizer_p8 import rigor_optimizer_p8
rigor=rigor_optimizer_p8.get_current_rigor()
print(f"Rigor: total {rigor['total']} med {rigor['measured']} {rigor['measured_pct']}% (esperado 80.5% com 99 novos unmeasured)")

# Check fixes
zero_ctx=db.query(Model).filter(Model.context_window==0).all()
is_chat_true=len([m for m in zero_ctx if (m.capabilities or {}).get('is_chat')])
print(f"Context 0 com is_chat True: {is_chat_true} (esperado 0)")

placeholder=[p for p in db.query(Provider).all() if '{' in p.base_url or 'localhost' in p.base_url]
with_note=len([p for p in placeholder if (p.capabilities or {}).get('needs_account_id') or (p.capabilities or {}).get('local_setup_required')])
print(f"Placeholders com nota: {with_note}/{len(placeholder)} (esperado 11/11)")

db.close()
PY
```

**Esperado**:
- Providers: 200
- Models: 963
- Free_no_card: 181
- Free_no_key: 14
- Adapters: 50
- Rigor: 80.5% (416/517) — 99 novos unmeasured
- Context 0 is_chat True: 0
- Placeholders com nota: 11/11

## 🔑 6. Deploy Key — Já Configurada

Deploy key ed25519 já adicionada em https://github.com/rpolicarpo100/AI_R/settings/keys com write access:
- Public: `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPHdOMkig60awtMFNiDCHId3aX6L2qz6jQHALNYdkJfU ai_r-deploy@arena.ai`
- Fingerprint: SHA256:bL7tTlKRYe7vJzwu4xFxbltW8qBJegO2JXDCsRTjyzo
- Push OK: 5 commits main -> main via SSH `git@github-ai-r:rpolicarpo100/AI_R.git`

**Para push futuro no PC**:
```bash
# Copiar private key para ~/.ssh/
mkdir -p ~/.ssh
# Colar private key em ~/.ssh/ai_r_deploy_key (chmod 600)
# Criar ~/.ssh/config:
# Host github-ai-r
#   HostName github.com
#   User git
#   IdentityFile ~/.ssh/ai_r_deploy_key
#   IdentitiesOnly yes
#   StrictHostKeyChecking no

git remote set-url origin git@github-ai-r:rpolicarpo100/AI_R.git
git push origin main
```

## 📊 7. Métricas para Verificar

**Performance P24-P30**:
- HTTP Pool: keepalive 50 max 200 (antes 20/100) — `app/core/policy.py`
- DB Pool: size 20 overflow 40 (antes 10/20) — `app/core/policy.py`
- Cache TTL: L1 30→60 L1_MAX 100→200 provider 60→120 — `app/core/policy.py`
- Dashboard paginação: /network?page=0&per_page=50 400KB→50KB — `app/routers/dashboard.py`
- DB query: 51.1ms sem cache → 0-1ms com cache hit — `app/services/http_client.py`
- HTTP pool fallback: hardcoded 10/50/20 → policy 50/200 — `app/services/http_client.py`

**Melhorias implementadas**:
- ✅ P19 context 0 16→0 is_chat False
- ✅ P20 placeholders 11→0 com notas
- ✅ P24 pool 20→50 max 100→200
- ✅ P26 cache TTL L1 30→60 provider 60→120
- ✅ P27 dashboard paginação 400KB→50KB
- ✅ P30 DB pool 10→20 20→40
- ✅ Provider sem models 1→0
- ✅ Adapters 30→50 dedicados (opper 700+ models, eurouter 100+ models 10K req/mo free GDPR, codingplanx 600+ models, deepinfra $0.10/1M, novita $0.135/1M, siliconflow China 200+ models, zhipu GLM free China, qwen 70M, cloudflare 10K neurons, huggingface 300+ models)

**Pendentes P16-P40 6-11 dias**:
- P16 Medição real 99 novos rigor 80.5%→100%
- P21 Health check real 200 providers 187 low rating
- P23 Free_no_key test 181
- P40 Frontend virtualização 200

## 🎯 8. Teste Rápido Completo (1 comando)

```bash
# Backend + Frontend + Tests + Auditoria em 1 comando
cd backend && source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
sleep 5 && curl http://localhost:8000/health && curl http://localhost:8000/api/dashboard/stats | jq .ai_network && pytest tests/test_p8_context_compiler.py tests/test_p6_speed_capacity.py -v | tail -n 5
```

## 📂 9. Estrutura Pastas

```
1-PROJECT/ (4.6M)
  backend/ (FastAPI 200 providers 50 adapters)
    app/
      adapters/ (6 files: base, openai_compat, gemini, ollama, aihorde, dedicated_p15, dedicated_p15_200)
      core/ (policy.py P0+P5 50/200 pool, database.py WAL 64MB mmap 256MB, errors.py, config.py, token_calculator.py)
      models/ (database_models.py, agent_models.py, project_models.py)
      routers/ (14 routers: providers, models_registry, chat, chat_fast, dashboard com paginação P27, benchmark, agents, projects, auth, task_queue, audit, commands, multi_agent, observability, p17_lean, rigor, context)
      services/ (36 services 2.2M)
    tests/ (23 files 191 funcs 54 PASS)
    Dockerfile
    requirements.txt
    ai_provider_os.db (2.80 MB 200 providers 965 models — gitignored)
  frontend/ (Next.js 16.3.5 Turbopack CHAT AI | Settings 509K 7 deps 0 vulns)
  docs/ (6 files core + P15 200)
  README.md
  QUICK_START_PC.md (este)

2-ADDITIONAL/ (828K 39 ficheiros)
  auditorias/ (AUDITORIA_EXTENSIVA_100_PROVIDERS, AUDITORIA_IMPLEMENTACAO_P15-P24, AUDITORIA_200_PROVIDERS_MELHORIAS, AUDITORIA_COMPLETA_RAPIDEZ_PROCESSAMENTO)
  reports/ (P15_200_PROVIDERS_DOBRO, P14_100_PROVIDERS_DEEP_SEARCH, etc)
  roadmaps/, verificacao/, p23/, configs/, scripts/, imagens/, mocks/, uploads/
```

## 🔗 10. Links Úteis

- **Repo**: https://github.com/rpolicarpo100/AI_R
- **Backend**: http://localhost:8000
- **Docs Swagger**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics
- **Frontend**: http://localhost:3000
- **Deploy Keys**: https://github.com/rpolicarpo100/AI_R/settings/keys
- **Free LLM List**: https://github.com/nejib1/Free-LLM (40 base URLs)
- **Infrabase Groq Alternatives 98**: https://infrabase.ai/alternatives/groq

---

**Pronto para testar no PC!** 200 providers, 181 free_no_card, 14 free_no_key, 965 models, 50 adapters dedicados, 54 PASS, melhorias rapidez P26-P30 implementadas.
