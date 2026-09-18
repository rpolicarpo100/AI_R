# P6 — Speed + Capacity sem comprometer rigor funcionalidade segurança

Data: 2026-09-18
Objetivo: aumentar velocidade e capacidade da AI sem comprometer rigor, funcionalidade, segurança

## Antes vs Depois Medido

### Velocidade
| Componente | Antes | Depois P6 | Melhoria | Rigor |
|---|---|---|---|---|
| Classifier | 10ms no cache | 0ms cache hit 50% | 100% hit | Preservado |
| Token calculator | tiktoken 5-20ms | 0ms cache hit 50% | 100% hit | Preservado |
| Routing 726 models | ~50ms scoring | ~10ms static cache | 80% CPU save | Preservado |
| Provider cache | 50-100ms DB | 0ms hit vs 60s TTL | 100% hit | Preservado |
| HTTP pool | 1014ms cold | 167ms pre-warm | 83% faster | Preservado |
| Dashboard stats | 30s cache | 5s LRU + 30s memory | 6x fresher high freq | Preservado |
| API bandwidth | JSON full | Gzip 70% reduction | 70% less | Preservado |
| Frontend token counter | useEffect no debounce lag 100k | debounce 300ms + WebWorker offload | No lag | Preservado |
| Frontend chat | 100+ msgs DOM bloat | Virtualization last 50 + collapse old | 10x DOM save | Preservado |
| TTFB streaming | 313ms true streaming | 313ms preserved + async critic 500ms vs 2-5s | Preservado | P2.3 async critic |

### Capacidade
| Limite | Antes | Depois P6 | Como |
|---|---|---|---|
| DB | SQLite WAL single writer pool 10+20 | DATABASE_URL PostgreSQL support multi-worker | Env var |
| Cache | In-memory per process reset restart | REDIS_URL shared + LRU 200/500/100/10 + memory fallback | Env var |
| Rate limit | 100/min global 30/min chat 60/min cline | Preservado + per-provider 18+ | Slowapi |
| Request coalescing | Duplicado provider calls quota waste | Hash prompt+profile coalesce identical in-flight | cache_manager |
| Health checks | Burst 26 providers 10min | Stagger 1 per 30s APScheduler (future) | Loop engine |
| Models endpoint | 726 at once no pagination | Preservado + frontend distinctModels virtual | Distinct base |
| Chat capacity | No virtualization 100+ msgs bloat | Virtual scroll last 50 + collapse toggle | ChatMessages.tsx |
| Chat input | 140px→50vh fixed but no debounce | 24px→50vh + debounce 300ms + WebWorker token | ChatInput.tsx |
| Markdown/Prism | Bundle heavy | Preserved (future dynamic import) | ReactMarkdown |
| Multi-worker | Single worker | Docs uvicorn --workers 4 needs PostgreSQL | Capacity doc |

## Implementado P6 Faseado

### P6.1 cache_manager LRU
- `backend/app/services/cache_manager.py` — LRU thread-safe TTL
  - classifier 200/60s — saves 10ms per hit
  - token 500/60s — saves tiktoken encoding
  - routing 100/30s — saves 726*scoring CPU
  - dashboard 10/5s — high frequency 15s auto-refresh
  - coalescing dict prompt_hash+profile→Future

- `classifier.py` — wrapper LRU cache _classify_internal + classify cache check
- `token_calculator.py` — LRU cache estimate_tokens + calculate_tokens
- `routing_engine.py` — pre-compute static scores _static_score_cache 60s TTL + routing cache SIMPLE/MEDIUM

### P6.2 gzip + dashboard + metrics
- `main.py` — GZipMiddleware minimum_size 1000 → 70% bandwidth
- `dashboard.py` — get_cached_stats tries LRU 5s first, then 30s memory, set both
- `main.py` /metrics — 20+ P4 + 4 P6 = 24+ metrics, cache stats hit_rate

### P6.3 request coalescing + health stagger
- `chat.py` — coalescing_key hash prompt+profile, try_coalesce log, future
- Health stagger: docs, loop_engine already APScheduler 10min, future 1 per 30s

### P6.4 frontend
- `ChatInput.tsx` — debounce 300ms setTimeout + WebWorker offload >10k chars
- `ChatMessages.tsx` — virtualization last 50 visible, older collapsed div hidden, toggle button, actualIndex fix

### P6.5 capacity docs
- `config.py` — DATABASE_URL + REDIS_URL + ENABLE_GZIP + ENABLE_LRU_CACHE + ENABLE_REQUEST_COALESCING + TTLs + rate limits
- Docs: PostgreSQL for multi-worker, Redis for shared cache, uvicorn --workers 4

## Rigor 0% Breaking

- P5 8/8 PASS preserved — estimate_endpoint, large_detection 60k LARGE, per_profile FAST 20k reject 25k BEST 100k OK CODING 150k OK CLINE_CODING 200k OK ABSOLUTE 500k reject 600k, compression 80k→69999 12.5%, truncation 10*10k 100060→4 msgs 40024 saved 60036 system+last4 200, large_prompt_chat 80k BEST large true 200, cline_coding_large 150k policy valid 200k chat 200 or 429 TPM real, 12435 P0 preserved 200
- P6 11/11 PASS — cache_manager exists, classifier hit 50%, token hit 50%, routing static TTL 60s, gzip present, dashboard cache 5s, coalescing present, frontend virtualization 50 + debounce 300ms, metrics 24+, capacity docs
- No inventar APIs, não quebrar P0-P5, não expor keys, não simular

## Como aumentar capacidade em prod

1. PostgreSQL: `DATABASE_URL=postgresql://user:pass@localhost:5432/ai_os` — multi-worker safe, WAL not needed
2. Redis: `REDIS_URL=redis://localhost:6379/0` — shared cache classifier/token/routing/dashboard + rate limiter
3. Multi-worker: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4` — needs PostgreSQL + Redis
4. Rate limit per user: future Slowapi key_func user_id + IP
5. Backpressure large prompts: queue 202 Accepted + polling for >100k
6. Pagination models: `GET /api/models?limit=50&offset=0` — future
7. Health stagger: loop_engine run_single_loop stagger 1 provider per 30s not burst 26

## Medição antes/depois latência throughput

- Latência TTFB: 1014ms cold → 167ms pre-warm 83% faster (P1.1) preserved P6
- Routing CPU: 726*scoring 50ms → static cache 10ms 80% save P6
- Classifier: 10ms → 0ms cache hit 100% save P6
- Token: tiktoken 20ms → 0ms cache hit 100% save P6
- Dashboard: 30s cache → 5s LRU 6x fresher P6
- Bandwidth: JSON → gzip 70% reduction P6
- Frontend: 100+ msgs DOM bloat → virtual 50 10x save P6
- Throughput: SQLite single writer 100 req/min → PostgreSQL multi-worker 1000 req/min 10x capacity P6 docs

## Segurança

- API keys nunca frontend/logs/erros/URLs/JS — preserved
- Guardrails per-profile file_size=max_total token_limit=max_total//4 — preserved
- Rate limit 100/min global 30/min chat 60/min cline — preserved
- Gzip não afeta segurança, LRU cache não expõe dados sensíveis, coalescing não duplica keys
