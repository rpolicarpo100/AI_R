from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import time
import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager
# P9.2 orjson 10% faster JSON - Pydantic V2 uses orjson if installed
try:
    import orjson
    from fastapi.responses import ORJSONResponse
    DEFAULT_RESPONSE_CLASS = ORJSONResponse
    print("[P9.2] orjson available - using ORJSONResponse 10% faster")
except ImportError:
    from fastapi.responses import JSONResponse as ORJSONResponse
    DEFAULT_RESPONSE_CLASS = JSONResponse
    print("[P9.2] orjson not available - using JSONResponse fallback")
# Rate limiting - Dia 1 Segurança maior ROI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .core.database import get_db, init_db, SessionLocal
from .core.config import settings
from .models.database_models import Provider, Model, RequestLog, ProviderStatus, ModelStatus
from .models.agent_models import AgentDB, SkillDB
from .services.encryption import encrypt_api_key, mask_api_key, decrypt_api_key
from .services.classifier import classifier
from .services.routing_engine import routing_engine, Profile
from .services.circuit_breaker import circuit_breaker
from .services.orchestrator import orchestrator_service, SKILL_REGISTRY, AGENT_REGISTRY
from .services.agent_manager import agent_manager
from .services.loop_engine import loop_engine
from .routers import providers as providers_router
from .routers import models_registry as models_router
from .routers import chat as chat_router
from .routers import chat_fast as chat_fast_router  # P18 v1.2 — Fast-path SIMPLE vs COMPLEX
from .routers import dashboard as dashboard_router
from .routers import benchmark as benchmark_router
from .routers import agents as agents_router
from .routers import projects as projects_router
from .routers import auth as auth_router
from .routers import task_queue as task_queue_router
from .routers import audit as audit_router
from .routers import commands as commands_router
from .routers import multi_agent as multi_agent_router
from .routers import observability as observability_router
from .routers import p17_lean as p17_lean_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Import memory models so Base creates table
    try:
        from .models import memory_models
        print("[MEMORY] ApikeylessMemory model imported for table creation")
    except Exception as e:
        print(f"[MEMORY] Import failed: {e}")
    init_db()
    db = SessionLocal()
    try:
        if db.query(Provider).count() == 0:
            seed_providers(db)
        if db.query(Model).count() == 0:
            seed_models(db)
        if db.query(SkillDB).count() == 0 or db.query(AgentDB).count() == 0:
            print("[STARTUP] Seeding agents and skills with competencies...")
            from .services.agent_manager import AgentManager
            mgr = AgentManager(db)
            skills_created = mgr.seed_skills()
            agents_created = mgr.seed_agents()
            print(f"[STARTUP] Created {skills_created} skills, {agents_created} agents")
        
        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            scheduler = AsyncIOScheduler()
            scheduler.add_job(
                loop_engine.run_single_loop,
                'interval',
                minutes=10,
                id='loop_engine_cycle',
                replace_existing=True,
                max_instances=1,
            )
            scheduler.start()
            print("[STARTUP] APScheduler LOOP started: ciclo a cada 10 minutos (discovery, health, benchmark, rating, audit, evolution)")
            app.state.scheduler = scheduler
        except Exception as e:
            print(f"[STARTUP] Scheduler failed (optional): {e}")

        # P7 — Seed new free providers poderoso contínuo fluido
        try:
            from .services.new_providers_p7 import seed_p7_providers
            added = seed_p7_providers(db)
            if added > 0:
                print(f"[P7] Seeded {added} new free providers — total now {db.query(Provider).count()}")
            else:
                print(f"[P7] No new providers needed — total {db.query(Provider).count()} with {len([p for p in db.query(Provider).all() if (p.capabilities or {}).get('free_no_card')])} free_no_card")
        except Exception as e:
            print(f"[P7] Seed new providers failed: {e}")

        # P9 — Seed more free providers from web search 2026-09-18
        try:
            from .services.new_providers_p9 import seed_p9_providers
            added_p9 = seed_p9_providers(db)
            if added_p9 > 0:
                print(f"[P9] Seeded {added_p9} new free providers — total now {db.query(Provider).count()} with {len([p for p in db.query(Provider).all() if (p.capabilities or {}).get('free_no_card')])} free_no_card")
            else:
                print(f"[P9] No new P9 providers needed — total {db.query(Provider).count()} free_no_card {len([p for p in db.query(Provider).all() if (p.capabilities or {}).get('free_no_card')])}")
        except Exception as e:
            print(f"[P9] Seed P9 providers failed: {e}")

        # P10 DEEP — Seed even more free providers deep search 2026-09-18
        try:
            from .services.new_providers_p10_deep import seed_p10_deep_providers
            added_p10 = seed_p10_deep_providers(db)
            if added_p10 > 0:
                print(f"[P10 DEEP] Seeded {added_p10} new deep free providers — total now {db.query(Provider).count()} with {len([p for p in db.query(Provider).all() if (p.capabilities or {}).get('free_no_card')])} free_no_card")
            else:
                print(f"[P10 DEEP] No new P10 deep providers needed — total {db.query(Provider).count()} free_no_card {len([p for p in db.query(Provider).all() if (p.capabilities or {}).get('free_no_card')])}")
        except Exception as e:
            print(f"[P10 DEEP] Seed P10 deep providers failed: {e}")

        # P11 ULTRA DEEP — Seed ultra deep free providers 80+ models no card no daily limits
        try:
            from .services.new_providers_p11_ultra_deep import seed_p11_ultra_deep_providers
            added_p11 = seed_p11_ultra_deep_providers(db)
            if added_p11 > 0:
                print(f"[P11 ULTRA DEEP] Seeded {added_p11} new ultra deep free providers — total now {db.query(Provider).count()} with {len([p for p in db.query(Provider).all() if (p.capabilities or {}).get('free_no_card')])} free_no_card")
            else:
                print(f"[P11 ULTRA DEEP] No new P11 ultra deep providers needed — total {db.query(Provider).count()} free_no_card {len([p for p in db.query(Provider).all() if (p.capabilities or {}).get('free_no_card')])}")
        except Exception as e:
            print(f"[P11 ULTRA DEEP] Seed P11 ultra deep providers failed: {e}")

        # P12 ULTRA ULTRA DEEP — Seed ultra ultra deep free providers embeddings image video audio
        try:
            from .services.new_providers_p12_ultra_ultra_deep import seed_p12_ultra_ultra_deep_providers
            added_p12 = seed_p12_ultra_ultra_deep_providers(db)
            if added_p12 > 0:
                print(f"[P12 ULTRA ULTRA DEEP] Seeded {added_p12} new ultra ultra deep free providers — total now {db.query(Provider).count()} with {len([p for p in db.query(Provider).all() if (p.capabilities or {}).get('free_no_card')])} free_no_card")
            else:
                print(f"[P12 ULTRA ULTRA DEEP] No new P12 ultra ultra deep providers needed — total {db.query(Provider).count()} free_no_card {len([p for p in db.query(Provider).all() if (p.capabilities or {}).get('free_no_card')])}")
        except Exception as e:
            print(f"[P12 ULTRA ULTRA DEEP] Seed P12 ultra ultra deep providers failed: {e}")

        # P13 ULTRA ULTRA ULTRA DEEP — Seed ultra ultra ultra deep free providers local gateways 80+ models no daily limits
        try:
            from .services.new_providers_p13_ultra_ultra_ultra_deep import seed_p13_ultra_ultra_ultra_deep_providers
            added_p13 = seed_p13_ultra_ultra_ultra_deep_providers(db)
            if added_p13 > 0:
                print(f"[P13 ULTRA ULTRA ULTRA DEEP] Seeded {added_p13} new ultra ultra ultra deep free providers — total now {db.query(Provider).count()} with {len([p for p in db.query(Provider).all() if (p.capabilities or {}).get('free_no_card')])} free_no_card")
            else:
                print(f"[P13 ULTRA ULTRA ULTRA DEEP] No new P13 ultra ultra ultra deep providers needed — total {db.query(Provider).count()} free_no_card {len([p for p in db.query(Provider).all() if (p.capabilities or {}).get('free_no_card')])}")
        except Exception as e:
            print(f"[P13 ULTRA ULTRA ULTRA DEEP] Seed P13 ultra ultra ultra deep providers failed: {e}")

        # P14 100 — Seed 100 providers deep China MiniMax StepFun Baichuan Yi InternLM Moonshot Kimi
        try:
            from .services.new_providers_p14_100 import seed_p14_100_providers
            added_p14 = seed_p14_100_providers(db)
            if added_p14 > 0:
                print(f"[P14 100] Seeded {added_p14} new 100 providers — total now {db.query(Provider).count()} with {len([p for p in db.query(Provider).all() if (p.capabilities or {}).get('free_no_card')])} free_no_card")
            else:
                print(f"[P14 100] No new P14 100 providers needed — total {db.query(Provider).count()} free_no_card {len([p for p in db.query(Provider).all() if (p.capabilities or {}).get('free_no_card')])}")
        except Exception as e:
            print(f"[P14 100] Seed P14 100 providers failed: {e}")

        # P15 200 — Dobro 100→200 providers — EU gateways + China + novos 2026
        try:
            from .services.new_providers_p15_200 import seed_p15_200_providers
            added_p15 = seed_p15_200_providers(db)
            if added_p15 > 0:
                print(f"[P15 200] Seeded {added_p15} new 200 providers — total now {db.query(Provider).count()} with {len([p for p in db.query(Provider).all() if (p.capabilities or {}).get('free_no_card')])} free_no_card")
            else:
                print(f"[P15 200] No new P15 200 providers needed — total {db.query(Provider).count()} free_no_card {len([p for p in db.query(Provider).all() if (p.capabilities or {}).get('free_no_card')])}")
        except Exception as e:
            print(f"[P15 200] Seed P15 200 providers failed: {e}")

        # Memory — Apikeyless Archive — seed 15 sites reais verificados
        try:
            from .services.apikeyless_memory_service import apikeyless_memory_service
            mem_result = apikeyless_memory_service.seed_memory(db)
            print(f"[MEMORY] Seed result: {mem_result}")
        except Exception as e:
            print(f"[MEMORY] Seed failed (optional): {e}")

        # P20 — Database backup automático
        try:
            from .services.backup_service_p20 import backup_service_p20
            backup_result = backup_service_p20.backup()
            print(f"[P20] Backup result: {backup_result}")
            # Add backup job to scheduler — daily backup
            try:
                scheduler.add_job(
                    backup_service_p20.backup,
                    'interval',
                    hours=24,
                    id='backup_daily',
                    replace_existing=True,
                    max_instances=1,
                )
                print("[P20] Backup daily job added — every 24h")
            except:
                pass
        except Exception as e:
            print(f"[P20] Backup failed (optional): {e}")

        # P1.1 — HTTP pool pre-warm for fastest providers to reduce TTFB 50-100ms
        try:
            from .services.http_client import get_pooled_client
            fastest_providers = [
                ("cerebras", "https://api.cerebras.ai/v1"),
                ("groq", "https://api.groq.com/openai/v1"),
                ("openrouter", "https://openrouter.ai/api/v1"),
                ("github_models", "https://models.inference.ai.azure.com"),
                ("openai", "https://api.openai.com/v1"),
            ]
            # Pre-warm sync? We are in sync context, but get_pooled_client is async
            # Use asyncio to create clients
            import asyncio
            async def prewarm():
                for pid, base_url in fastest_providers:
                    try:
                        # Check if provider exists and has key or is fast
                        prov = db.query(Provider).filter(Provider.provider_id == pid).first()
                        if prov:
                            client = await get_pooled_client(pid, base_url, timeout=60.0, use_http2=True)
                            print(f"[P1.1 PRE-WARM] Pooled client ready for {pid} base={base_url}")
                    except Exception as e:
                        print(f"[P1.1 PRE-WARM] Failed for {pid}: {e}")
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(prewarm())
                else:
                    asyncio.run(prewarm())
            except RuntimeError:
                # No event loop, run new
                asyncio.run(prewarm())
            print(f"[P1.1 PRE-WARM] HTTP pool pre-warm attempted for {len(fastest_providers)} fastest providers")
        except Exception as e:
            print(f"[P1.1 PRE-WARM] Pre-warm failed (optional): {e}")

    finally:
        db.close()
    
    yield
    
    # Shutdown — P22 close pooled http clients
    try:
        if hasattr(app.state, 'scheduler'):
            app.state.scheduler.shutdown()
    except:
        pass
    try:
        from .services.http_client import close_all_clients
        import asyncio
        # Try to close clients
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(close_all_clients())
            else:
                asyncio.run(close_all_clients())
        except:
            # Fallback sync close attempt
            pass
        print("[SHUTDOWN] P22 HTTP pooled clients closed")
    except Exception as e:
        print(f"[SHUTDOWN] HTTP pool close failed: {e}")

# Rate limiter - 100 req/min por IP (Dia 1 Segurança)
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI Provider OS - Sistema operativo para providers e modelos de IA com LOOP de agentes com skills e competências + Chat Support Agents (intent, prompt optimizer, critic, code reviewer, rigor checker) - funcional, coerente, preciso, rigoroso, real, profissional, terceiro olho aberto + Rate Limiting 100/min + P9.2 orjson 10% faster + utcnow fix timezone-aware",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    default_response_class=DEFAULT_RESPONSE_CLASS
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

from fastapi.middleware.gzip import GZipMiddleware
# P6 — Gzip middleware — reduces bandwidth 70% for large prompts and dashboard stats
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def seed_providers(db: Session):
    # RIGOR: Sem simulações, sem auto-gerador. Quem cria app é o UTILIZADOR orientando a AI. Sem local-codegen.
    # Apenas providers reais, com status DISCOVERED até medição real
    initial = [
        {"provider_id": "groq", "name": "Groq", "base_url": "https://api.groq.com/openai/v1", "auth_type": "bearer", "status": ProviderStatus.DISCOVERED, "source": "official_docs", "source_confidence": "provider_claim", "capabilities": {"tool_calling": "UNKNOWN", "vision": False, "streaming": "UNKNOWN"}, "pricing_info": {"input_per_1m": "UNKNOWN - verify docs", "output_per_1m": "UNKNOWN", "source": "UNKNOWN"}},
        {"provider_id": "cerebras", "name": "Cerebras", "base_url": "https://api.cerebras.ai/v1", "auth_type": "bearer", "status": ProviderStatus.DISCOVERED, "source": "official_docs", "source_confidence": "provider_claim", "capabilities": {"tool_calling": "UNKNOWN", "vision": False}, "pricing_info": {"input_per_1m": "UNKNOWN", "output_per_1m": "UNKNOWN", "source": "UNKNOWN"}},
        {"provider_id": "gemini", "name": "Google Gemini", "base_url": "https://generativelanguage.googleapis.com/v1beta", "auth_type": "api_key", "status": ProviderStatus.DISCOVERED, "source": "official_docs", "source_confidence": "provider_claim", "capabilities": {"tool_calling": "UNKNOWN", "vision": "provider_claim"}, "pricing_info": {"input_per_1m": "UNKNOWN", "output_per_1m": "UNKNOWN", "source": "UNKNOWN"}},
        {"provider_id": "mistral", "name": "Mistral AI", "base_url": "https://api.mistral.ai/v1", "auth_type": "bearer", "status": ProviderStatus.DISCOVERED, "source": "official_docs", "source_confidence": "provider_claim", "capabilities": {"tool_calling": "UNKNOWN"}, "pricing_info": {"input_per_1m": "UNKNOWN", "output_per_1m": "UNKNOWN", "source": "UNKNOWN"}},
        {"provider_id": "openrouter", "name": "OpenRouter", "base_url": "https://openrouter.ai/api/v1", "auth_type": "bearer", "status": ProviderStatus.DISCOVERED, "source": "official_docs", "source_confidence": "verified", "capabilities": {"tool_calling": "UNKNOWN", "models": "provider_claim 200"}, "pricing_info": {"input_per_1m": "VARIES - UNKNOWN", "output_per_1m": "VARIES - UNKNOWN", "source": "UNKNOWN"}},
        {"provider_id": "github_models", "name": "GitHub Models", "base_url": "https://models.inference.ai.azure.com", "auth_type": "bearer", "status": ProviderStatus.DISCOVERED, "source": "official_docs", "source_confidence": "provider_claim", "capabilities": {"tool_calling": "UNKNOWN", "free": "provider_claim"}, "pricing_info": {"input_per_1m": "UNKNOWN", "output_per_1m": "UNKNOWN", "source": "UNKNOWN"}},
        {"provider_id": "ollama", "name": "Ollama (Local)", "base_url": "http://localhost:11434", "auth_type": "none", "status": ProviderStatus.DISCOVERED, "source": "official_docs", "source_confidence": "verified", "capabilities": {"local": "provider_claim", "privacy": "high"}, "pricing_info": {"input_per_1m": 0, "output_per_1m": 0, "local": True, "source": "provider_claim"}},
        {"provider_id": "openai", "name": "OpenAI", "base_url": "https://api.openai.com/v1", "auth_type": "bearer", "status": ProviderStatus.DISCOVERED, "source": "official_docs", "source_confidence": "provider_claim", "capabilities": {"tool_calling": "UNKNOWN"}, "pricing_info": {"input_per_1m": "UNKNOWN", "output_per_1m": "UNKNOWN", "source": "UNKNOWN"}},
        {"provider_id": "huggingface", "name": "Hugging Face", "base_url": "https://api-inference.huggingface.co/v1", "auth_type": "bearer", "status": ProviderStatus.DISCOVERED, "source": "official_docs", "source_confidence": "provider_claim", "capabilities": {"tool_calling": "UNKNOWN"}, "pricing_info": {"input_per_1m": "UNKNOWN", "source": "UNKNOWN"}},
    ]
    for p in initial:
        provider = Provider(**p)
        db.add(provider)
    db.commit()

def seed_models(db: Session):
    # RIGOR: Nenhum score inventado. Tudo 0, DISCOVERED, confidence 0, test_count 0, até benchmark medir.
    # Isso respeita "Não assumir que provider é bom porque fabricante afirma"
    models_data = [
        # Groq - scores UNKNOWN até medição
        {"model_id": "llama-3.3-70b-versatile", "provider_id": "groq", "display_name": "Llama 3.3 70B Versatile", "context_window": 0, "input_price": "UNKNOWN", "output_price": "UNKNOWN", "input_price_float": None, "output_price_float": None, "coding_score": 0, "reasoning_score": 0, "speed_score": 0, "reliability_score": 0, "tool_calling_score": 0, "json_score": 0, "overall_score": 0, "confidence_score": 0, "test_count": 0, "status": ModelStatus.DISCOVERED, "free_tier": False, "capabilities": {"tool_calling": "UNKNOWN", "source": "UNKNOWN - needs benchmark"}},
        {"model_id": "llama-3.1-8b-instant", "provider_id": "groq", "display_name": "Llama 3.1 8B Instant", "context_window": 0, "input_price": "UNKNOWN", "output_price": "UNKNOWN", "input_price_float": None, "output_price_float": None, "coding_score": 0, "reasoning_score": 0, "speed_score": 0, "reliability_score": 0, "tool_calling_score": 0, "json_score": 0, "overall_score": 0, "confidence_score": 0, "test_count": 0, "status": ModelStatus.DISCOVERED, "free_tier": False, "capabilities": {"source": "UNKNOWN"}},
        # Cerebras
        {"model_id": "llama-3.3-70b", "provider_id": "cerebras", "display_name": "Llama 3.3 70B (Cerebras)", "context_window": 0, "input_price": "UNKNOWN", "output_price": "UNKNOWN", "input_price_float": None, "output_price_float": None, "coding_score": 0, "reasoning_score": 0, "speed_score": 0, "reliability_score": 0, "tool_calling_score": 0, "json_score": 0, "overall_score": 0, "confidence_score": 0, "test_count": 0, "status": ModelStatus.DISCOVERED, "capabilities": {"source": "UNKNOWN"}},
        {"model_id": "llama3.1-8b", "provider_id": "cerebras", "display_name": "Llama 3.1 8B (Cerebras)", "context_window": 0, "input_price": "UNKNOWN", "output_price": "UNKNOWN", "input_price_float": None, "output_price_float": None, "coding_score": 0, "reasoning_score": 0, "speed_score": 0, "reliability_score": 0, "overall_score": 0, "confidence_score": 0, "test_count": 0, "status": ModelStatus.DISCOVERED},
        # Gemini
        {"model_id": "gemini-2.0-flash", "provider_id": "gemini", "display_name": "Gemini 2.0 Flash", "context_window": 0, "input_price": "UNKNOWN", "output_price": "UNKNOWN", "input_price_float": None, "output_price_float": None, "coding_score": 0, "reasoning_score": 0, "speed_score": 0, "reliability_score": 0, "tool_calling_score": 0, "json_score": 0, "overall_score": 0, "confidence_score": 0, "test_count": 0, "status": ModelStatus.DISCOVERED, "capabilities": {"vision": "UNKNOWN - provider_claim true, needs verification"}},
        {"model_id": "gemini-1.5-pro", "provider_id": "gemini", "display_name": "Gemini 1.5 Pro", "context_window": 0, "input_price": "UNKNOWN", "output_price": "UNKNOWN", "input_price_float": None, "output_price_float": None, "coding_score": 0, "reasoning_score": 0, "speed_score": 0, "reliability_score": 0, "tool_calling_score": 0, "json_score": 0, "overall_score": 0, "confidence_score": 0, "test_count": 0, "status": ModelStatus.DISCOVERED},
        # Mistral
        {"model_id": "mistral-large-latest", "provider_id": "mistral", "display_name": "Mistral Large", "context_window": 0, "input_price": "UNKNOWN", "output_price": "UNKNOWN", "input_price_float": None, "output_price_float": None, "coding_score": 0, "reasoning_score": 0, "speed_score": 0, "reliability_score": 0, "tool_calling_score": 0, "json_score": 0, "overall_score": 0, "confidence_score": 0, "test_count": 0, "status": ModelStatus.DISCOVERED},
        {"model_id": "codestral-latest", "provider_id": "mistral", "display_name": "Codestral", "context_window": 0, "input_price": "UNKNOWN", "output_price": "UNKNOWN", "input_price_float": None, "output_price_float": None, "coding_score": 0, "reasoning_score": 0, "speed_score": 0, "reliability_score": 0, "tool_calling_score": 0, "json_score": 0, "overall_score": 0, "confidence_score": 0, "test_count": 0, "status": ModelStatus.DISCOVERED},
        # OpenRouter
        {"model_id": "anthropic/claude-3.5-sonnet", "provider_id": "openrouter", "display_name": "Claude 3.5 Sonnet", "context_window": 0, "input_price": "UNKNOWN", "output_price": "UNKNOWN", "input_price_float": None, "output_price_float": None, "coding_score": 0, "reasoning_score": 0, "speed_score": 0, "reliability_score": 0, "tool_calling_score": 0, "json_score": 0, "overall_score": 0, "confidence_score": 0, "test_count": 0, "status": ModelStatus.DISCOVERED},
        {"model_id": "openai/gpt-4o-mini", "provider_id": "openrouter", "display_name": "GPT-4o Mini", "context_window": 0, "input_price": "UNKNOWN", "output_price": "UNKNOWN", "input_price_float": None, "output_price_float": None, "coding_score": 0, "reasoning_score": 0, "speed_score": 0, "reliability_score": 0, "tool_calling_score": 0, "json_score": 0, "overall_score": 0, "confidence_score": 0, "test_count": 0, "status": ModelStatus.DISCOVERED, "free_tier": False},
        # Ollama local - sem simulação, só se Ollama estiver rodando
        {"model_id": "llama3.2", "provider_id": "ollama", "display_name": "Llama 3.2 (Local)", "context_window": 0, "input_price": "0 / LOCAL", "output_price": "0 / LOCAL", "input_price_float": 0, "output_price_float": 0, "coding_score": 0, "reasoning_score": 0, "speed_score": 0, "reliability_score": 0, "tool_calling_score": 0, "json_score": 0, "overall_score": 0, "confidence_score": 0, "test_count": 0, "status": ModelStatus.DISCOVERED, "free_tier": True, "capabilities": {"local": True, "privacy": "high", "source": "provider_claim"}},
    ]
    for m in models_data:
        model = Model(**m)
        db.add(model)
    db.commit()

# Include routers P5 - Enterprise++ Rigoroso Profissional Crítico
app.include_router(providers_router.router, prefix=settings.API_PREFIX)
app.include_router(models_router.router, prefix=settings.API_PREFIX)
app.include_router(chat_router.router)  # /v1/chat/completions
app.include_router(chat_fast_router.router)  # P18 v1.2 — /v1/chat/completions/fast + /v1/chat/fast-path-stats — SIMPLE vs COMPLEX fast-path
app.include_router(dashboard_router.router, prefix=settings.API_PREFIX)
app.include_router(benchmark_router.router, prefix=settings.API_PREFIX)
app.include_router(agents_router.router, prefix=settings.API_PREFIX)  # /api/agents - LOOP com skills e competências
app.include_router(projects_router.router, prefix=settings.API_PREFIX)  # /api/projects - WORKPLACE projetos do chat + branches + export
app.include_router(auth_router.router, prefix=settings.API_PREFIX)  # /api/auth - JWT + roles + human override P4
app.include_router(task_queue_router.router, prefix=settings.API_PREFIX)  # /api/task-queue - Multi-agent P0→P4 pipeline P4
app.include_router(audit_router.router, prefix=settings.API_PREFIX)  # /api/audit - Audit Log Persistente P5
app.include_router(commands_router.router, prefix=settings.API_PREFIX)  # /api/commands - Chat Commands P6 /testa /audita /contesta
app.include_router(multi_agent_router.router, prefix=settings.API_PREFIX)  # /api/multi-agent - Multi-Agent REAL P8.3 intent→optimizer→router→critic→reviewer→rigor
app.include_router(observability_router.router, prefix=settings.API_PREFIX)  # /api/observability - Observability Enterprise P16 tracing sessions cost cache logs alerts guardrails 18+
app.include_router(p17_lean_router.router)  # /api/p17 - P17 Lean Provider Ranker + Prompt Engineer + Critic Heuristics + Fallback + Cache + Rigor
from .routers import rigor as rigor_router
app.include_router(rigor_router.router)  # /api/rigor - P7 Rigor Poderoso + P16 honesty + P21 health-check-200 + 100% confiança com realismo
from .routers import context as context_router
app.include_router(context_router.router)  # /api/context - P8 Context Compiler P0+P1+P2
from .routers import brainstorm as brainstorm_router
app.include_router(brainstorm_router.router, prefix=settings.API_PREFIX)  # /api/brainstorm - Brainstorming antes de construir/responder — mais perto do objetivo final
from .routers import memory as memory_router
app.include_router(memory_router.router, prefix=settings.API_PREFIX)  # /api/memory - Apikeyless Memory — arquiva sites apikeyless para acesso rápido e análises rápidas — continuamente aumentado, auditado, rating e categoria
from .routers import p16_5 as p16_5_router
app.include_router(p16_5_router.router, prefix=settings.API_PREFIX)  # /api/p16-5 - P16.5 Overall <10 de 717→300 — fix bug + cleanup + benchmark
from .routers import image_video as image_video_router
app.include_router(image_video_router.router, prefix=settings.API_PREFIX)  # /api/media - Image & Video Generation — UAI 938 models — uai_sk_live_ — image 163 video 221

@app.get("/")
@limiter.limit("100/minute")
async def root(request: Request):
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs": "/docs",
        "openai_compatible": "/v1/chat/completions",
        "dashboard": f"{settings.API_PREFIX}/dashboard/stats"
    }

@app.get("/metrics")
@limiter.limit("60/minute")
async def prometheus_metrics(request: Request, db: Session = Depends(lambda: SessionLocal())):
    """P4 - Observability - Prometheus metrics 15+ P4 - Grafana dashboard + task queue + branches"""
    try:
        from sqlalchemy import func
        from .models.database_models import RequestLog, BenchmarkResult
        from .models.agent_models import AgentDB, LoopTask
        from .models.project_models import ProjectBranch
        from .services.task_queue import task_queue
        
        providers = db.query(Provider).all()
        models = db.query(Model).all()
        logs = db.query(RequestLog).all()
        benchmarks = db.query(BenchmarkResult).all()
        
        online = len([p for p in providers if p.status.value in ["PRODUCTION","VERIFIED"]])
        degraded = len([p for p in providers if p.status.value == "DEGRADED"])
        offline = len([p for p in providers if p.status.value in ["OFFLINE","DISABLED","DEPRECATED"]])
        discovered = len([p for p in providers if p.status.value == "DISCOVERED"])
        
        measured = len([m for m in models if m.test_count>0])
        verified = len([m for m in models if m.status.value == "VERIFIED"])
        total_models = len(models)
        
        total_requests = len(logs)
        success_requests = len([r for r in logs if r.status == "success"])
        success_rate = (success_requests / total_requests * 100) if total_requests else 0
        avg_latency = sum(r.latency_ms for r in logs) / total_requests if total_requests else 0
        
        try:
            agents_count = db.query(AgentDB).count()
            agents_online = db.query(AgentDB).filter(AgentDB.status == "AVAILABLE").count()
            loop_tasks = db.query(LoopTask).count()
        except:
            agents_count = 0
            agents_online = 0
            loop_tasks = 0
        
        # P4 + P6 + P7 + P8 — Enhanced metrics with P0.5 P1 P2 P3 + P6 LRU + P7 rigor + P8 context compiler
        try:
            from .services.circuit_breaker import circuit_breaker
            from .services.http_client import get_provider_cache_stats, get_client_stats
            from .services.quota_tracker import quota_tracker
            from .services.cache_manager import get_all_stats as cache_manager_stats
            from .services.context_compiler import context_compiler
            from .services.continuous_benchmark_p7 import continuous_benchmark_p7
            deprecated_models = len([m for m in models if str(m.status) == "DEPRECATED" or getattr(m.status, 'value', str(m.status)) == "DEPRECATED"])
            circuits_open = len([p for p in providers if circuit_breaker.get_state(p.provider_id).get("state") and "OPEN" in str(circuit_breaker.get_state(p.provider_id).get("state"))])
            provider_cache_stats = get_provider_cache_stats()
            http_pool_stats = get_client_stats()
            quota_stats = quota_tracker.get_stats()
            cache_stats = cache_manager_stats()
            context_cache_stats = context_compiler.get_cache_stats()
            context_pattern_stats = context_compiler.get_pattern_stats()
            rigor_stats = continuous_benchmark_p7.get_rigor_stats()
        except Exception as e:
            print(f"[METRICS P4+P6+P7+P8] Enhanced metrics failed {e}")
            deprecated_models = 0
            circuits_open = 0
            provider_cache_stats = {"hit": False, "providers_count": 0, "models_count": 0}
            http_pool_stats = {"pooled_clients": 0}
            quota_stats = {"total_providers_tracked": 0, "total_429_hits_last_hour": 0}
            cache_stats = {"classifier": {"hit_rate": 0}, "token": {"hit_rate": 0}, "routing": {"hit_rate": 0}}
            context_cache_stats = {"hit_rate": 0}
            context_pattern_stats = {"compilations": 0, "avg_compression_ratio": 0}
            rigor_stats = {"chat_measured_pct": 0, "coding_nonzero_pct": 0}

        # Prometheus format — P4 enhanced with P0.5 P1 P2 P3
        metrics = f"""# HELP ai_provider_os_providers_total Total providers
# TYPE ai_provider_os_providers_total gauge
ai_provider_os_providers_total {len(providers)}

# HELP ai_provider_os_providers_online Online providers
# TYPE ai_provider_os_providers_online gauge
ai_provider_os_providers_online {online}

# HELP ai_provider_os_providers_degraded Degraded providers
# TYPE ai_provider_os_providers_degraded gauge
ai_provider_os_providers_degraded {degraded}

# HELP ai_provider_os_providers_offline Offline providers
# TYPE ai_provider_os_providers_offline gauge
ai_provider_os_providers_offline {offline}

# HELP ai_provider_os_providers_discovered Discovered providers
# TYPE ai_provider_os_providers_discovered gauge
ai_provider_os_providers_discovered {discovered}

# HELP ai_provider_os_models_total Total models
# TYPE ai_provider_os_models_total gauge
ai_provider_os_models_total {total_models}

# HELP ai_provider_os_models_measured Measured models
# TYPE ai_provider_os_models_measured gauge
ai_provider_os_models_measured {measured}

# HELP ai_provider_os_models_verified Verified models
# TYPE ai_provider_os_models_verified gauge
ai_provider_os_models_verified {verified}

# HELP ai_provider_os_models_deprecated Deprecated models P0.5
# TYPE ai_provider_os_models_deprecated gauge
ai_provider_os_models_deprecated {deprecated_models}

# HELP ai_provider_os_models_measured_percent Percent measured
# TYPE ai_provider_os_models_measured_percent gauge
ai_provider_os_models_measured_percent {round(measured/total_models*100,1) if total_models else 0}

# HELP ai_provider_os_requests_total Total requests
# TYPE ai_provider_os_requests_total counter
ai_provider_os_requests_total {total_requests}

# HELP ai_provider_os_requests_success_rate Success rate percent
# TYPE ai_provider_os_requests_success_rate gauge
ai_provider_os_requests_success_rate {round(success_rate,2)}

# HELP ai_provider_os_requests_avg_latency_ms Average latency ms
# TYPE ai_provider_os_requests_avg_latency_ms gauge
ai_provider_os_requests_avg_latency_ms {round(avg_latency,1)}

# HELP ai_provider_os_benchmark_results_total Total benchmark results
# TYPE ai_provider_os_benchmark_results_total counter
ai_provider_os_benchmark_results_total {len(benchmarks)}

# HELP ai_provider_os_agents_total Total agents
# TYPE ai_provider_os_agents_total gauge
ai_provider_os_agents_total {agents_count}

# HELP ai_provider_os_agents_online Online agents
# TYPE ai_provider_os_agents_online gauge
ai_provider_os_agents_online {agents_online}

# HELP ai_provider_os_loop_tasks Total loop tasks
# TYPE ai_provider_os_loop_tasks gauge
ai_provider_os_loop_tasks {loop_tasks}

# HELP ai_provider_os_rigor_percent Rigor percent measured
# TYPE ai_provider_os_rigor_percent gauge
ai_provider_os_rigor_percent {round(measured/total_models*100,1) if total_models else 0}

# HELP ai_provider_os_circuits_open Circuits OPEN P0.5
# TYPE ai_provider_os_circuits_open gauge
ai_provider_os_circuits_open {circuits_open}

# HELP ai_provider_os_provider_cache_hit Provider cache hit P1
# TYPE ai_provider_os_provider_cache_hit gauge
ai_provider_os_provider_cache_hit {1 if provider_cache_stats.get("hit") else 0}

# HELP ai_provider_os_provider_cache_age_seconds Provider cache age P1
# TYPE ai_provider_os_provider_cache_age_seconds gauge
ai_provider_os_provider_cache_age_seconds {provider_cache_stats.get("age_seconds",0)}

# HELP ai_provider_os_http_pool_clients HTTP pool clients P1
# TYPE ai_provider_os_http_pool_clients gauge
ai_provider_os_http_pool_clients {http_pool_stats.get("pooled_clients",0)}

# HELP ai_provider_os_quota_tracked_providers Quota tracked providers P2
# TYPE ai_provider_os_quota_tracked_providers gauge
ai_provider_os_quota_tracked_providers {quota_stats.get("total_providers_tracked",0)}

# HELP ai_provider_os_quota_429_hits_last_hour Quota 429 hits last hour P2
# TYPE ai_provider_os_quota_429_hits_last_hour counter
ai_provider_os_quota_429_hits_last_hour {quota_stats.get("total_429_hits_last_hour",0)}

# HELP ai_provider_os_info Info P4
# TYPE ai_provider_os_info gauge
ai_provider_os_info{{version="1.2.0-P23-P3",principle="rigor_medidos",p0="central_policy",p05="stability",p1="performance",p2="observability",p3="frontend_rating_taskqueue",p4="enterprise"}} 1

# HELP ai_provider_os_task_queue_total Total tasks in queue P4
# TYPE ai_provider_os_task_queue_total gauge
ai_provider_os_task_queue_total {len(task_queue.tasks) if 'task_queue' in globals() else 0}

# HELP ai_provider_os_workplace_branches_total Total branches P4
# TYPE ai_provider_os_workplace_branches_total gauge
ai_provider_os_workplace_branches_total {db.query(ProjectBranch).count() if 'ProjectBranch' in globals() else 0}

# HELP ai_provider_os_cache_classifier_hit_rate Classifier cache hit rate P6
# TYPE ai_provider_os_cache_classifier_hit_rate gauge
ai_provider_os_cache_classifier_hit_rate {cache_stats.get('classifier',{}).get('hit_rate',0)}

# HELP ai_provider_os_cache_token_hit_rate Token cache hit rate P6
# TYPE ai_provider_os_cache_token_hit_rate gauge
ai_provider_os_cache_token_hit_rate {cache_stats.get('token',{}).get('hit_rate',0)}

# HELP ai_provider_os_cache_routing_hit_rate Routing cache hit rate P6
# TYPE ai_provider_os_cache_routing_hit_rate gauge
ai_provider_os_cache_routing_hit_rate {cache_stats.get('routing',{}).get('hit_rate',0)}

# HELP ai_provider_os_cache_dashboard_hit_rate Dashboard cache hit rate P6
# TYPE ai_provider_os_cache_dashboard_hit_rate gauge
ai_provider_os_cache_dashboard_hit_rate {cache_stats.get('dashboard',{}).get('hit_rate',0)}

# HELP ai_provider_os_info_v6 Info P6 speed capacity
# TYPE ai_provider_os_info_v6 gauge
ai_provider_os_info_v6{{version="1.2.0-P23-P5-P6",principle="rigor_medidos",p0="central_policy",p05="stability",p1="performance",p2="observability",p3="frontend_rating_taskqueue",p4="enterprise",p5="large_prompt_faseado",p6="speed_capacity_gzip_lru_virtual_debounce"}} 1

# HELP ai_provider_os_context_compiler_cache_hit_rate Context Compiler cache hit rate P8 P0+P1
# TYPE ai_provider_os_context_compiler_cache_hit_rate gauge
ai_provider_os_context_compiler_cache_hit_rate {context_cache_stats.get('hit_rate',0) if 'context_cache_stats' in locals() else 0}

# HELP ai_provider_os_context_compiler_compilations_total Total compilations P8 P2
# TYPE ai_provider_os_context_compiler_compilations_total counter
ai_provider_os_context_compiler_compilations_total {context_pattern_stats.get('compilations',0) if 'context_pattern_stats' in locals() else 0}

# HELP ai_provider_os_context_compiler_avg_compression_ratio Avg compression ratio P8 P2
# TYPE ai_provider_os_context_compiler_avg_compression_ratio gauge
ai_provider_os_context_compiler_avg_compression_ratio {context_pattern_stats.get('avg_compression_ratio',0) if 'context_pattern_stats' in locals() else 0}

# HELP ai_provider_os_rigor_chat_measured_percent Chat rigor percent P7
# TYPE ai_provider_os_rigor_chat_measured_percent gauge
ai_provider_os_rigor_chat_measured_percent {rigor_stats.get('chat_measured_pct',0) if 'rigor_stats' in locals() else 0}

# HELP ai_provider_os_rigor_coding_nonzero_percent Coding nonzero percent P7
# TYPE ai_provider_os_rigor_coding_nonzero_percent gauge
ai_provider_os_rigor_coding_nonzero_percent {rigor_stats.get('coding_nonzero_pct',0) if 'rigor_stats' in locals() else 0}

# HELP ai_provider_os_info_p8 Info P8 Context Compiler
# TYPE ai_provider_os_info_p8 gauge
ai_provider_os_info_p8{{version="1.2.0-P23-P5-P6-P7-P8",principle="rigor_medidos",p0="context_compiler_token_budget_dedup_relevance_hierarchical_limits_critical",p1="parallel_cache_conflicts_provenance_fallback",p2="cost_latency_learning_routing_quality",p6="speed_capacity",p7="rigor_poderoso",p8="context_compiler"}} 1
"""
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(metrics, media_type="text/plain")
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/health")
@limiter.limit("200/minute")  # health mais permissivo
async def health_check(request: Request, db: Session = Depends(lambda: SessionLocal())):
    try:
        # Simple DB check
        count = db.query(Provider).count()
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "providers": count,
            "version": settings.VERSION
        }
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "degraded", "error": str(e)})

# Global error handler - never expose sensitive data
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log full error internally, but return safe message
    print(f"[ERROR] {request.url} - {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "request_id": str(uuid.uuid4()),
            "type": "UNKNOWN",
            "message": "An unexpected error occurred. Check logs."
        }
    )
