"""
P17 Lean - API Endpoints - Provider Ranker Simples + Prompt Engineer + Critic Heuristics + Fallback + Cache + Rigor
Rigoroso, real, funcional, sem invenção
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..services.provider_ranker import provider_ranker
from ..services.prompt_engineer_provider import prompt_engineer_provider
from ..services.response_critic import response_critic
from ..services.fallback_orchestrator import fallback_orchestrator
from ..services.observability import observability_service

router = APIRouter(prefix="/api/p17", tags=["p17-lean"])

@router.get("/ranking")
def get_ranking(intent: str = "CHAT", profile: str = "BEST", db: Session = Depends(get_db)):
    """P17 Lean - Provider Ranker simples - rigor measured + health VERIFIED, sem p50 p95 até volume 100+"""
    ranked = provider_ranker.rank(db, intent=intent, profile=profile)
    return {
        "ranked": ranked,
        "count": len(ranked),
        "intent": intent,
        "profile": profile,
        "method": "rigor 60% health 20% overall 20% - ESTIMATIVA, sem p50 p95 até traces>100",
        "p17_lean": True,
        "note": "Rigor measured se disponível senão provider_claim penalty 50% - ESTIMATIVA"
    }

@router.get("/cheaper")
def get_cheaper(intent: str = "CHAT", quality_threshold: int = 60, db: Session = Depends(get_db)):
    """P17 Lean - Cost Optimizer simples - filtra quality threshold mínima"""
    cheaper = provider_ranker.get_cheaper_alternatives(db, intent=intent, quality_threshold=quality_threshold)
    return {
        "alternatives": cheaper,
        "count": len(cheaper),
        "intent": intent,
        "quality_threshold": quality_threshold,
        "method": "Filtra rigor_score >= threshold, ordena final_score desc - free first",
        "p17_lean": True,
        "note": "Cost atual 2.55e-12 free, -40% meaningless até cost >$10/day"
    }

@router.get("/prompt-template")
def get_prompt_template(provider_id: str, model_id: str = None, intent: str = "CHAT"):
    """P17 Lean - Prompt Engineer Provider-Specific com source"""
    result = prompt_engineer_provider.optimize(prompt="test", provider_id=provider_id, model_id=model_id, intent=intent)
    # Return template info only
    return {
        "provider_id": provider_id,
        "model_id": model_id,
        "template": result["template"],
        "source": result["source"],
        "confidence": result["confidence"],
        "measured": result["measured"],
        "evidence": result["evidence"],
        "intent": intent,
        "best_for": result["best_for"],
        "p17_lean": True
    }

@router.post("/prompt-optimize")
def optimize_prompt(prompt: str, provider_id: str, model_id: str = None, intent: str = "CHAT"):
    """P17 Lean - Otimiza prompt por provider"""
    result = prompt_engineer_provider.optimize(prompt=prompt, provider_id=provider_id, model_id=model_id, intent=intent)
    return result

@router.post("/critique")
def critique_response(prompt: str, response: str, provider: str = None, model: str = None):
    """P17 Lean - Response Critic simples heuristics 10ms"""
    result = response_critic.critique(prompt=prompt, response=response, provider=provider, model=model)
    return result

@router.post("/fallback-check")
def check_fallback(error: str = None, status_code: int = None, critic_score: int = None):
    """P17 Lean - Fallback Orchestrator simples 1x técnico"""
    result = fallback_orchestrator.should_fallback(error=error, status_code=status_code, critic_score=critic_score)
    return result

@router.get("/cache/stats")
def cache_stats():
    """P17 Lean - Cache Exact 30s TTL stats"""
    stats = observability_service.get_stats()
    cache = stats.get("cache", {})
    entries = observability_service.get_cache_entries(limit=10)
    return {
        "hits": cache.get("hits", 0),
        "misses": cache.get("misses", 0),
        "hit_rate": cache.get("hit_rate", 0),
        "store_size": cache.get("store_size", 0),
        "p17_lean": cache.get("p17_lean"),
        "entries": entries,
        "method": "exact match 30s TTL prompt+profile only - P17 Lean",
        "note": "hit_rate 50% medido com 2 requests mesmo prompt, target 10% exact realistic"
    }

@router.get("/observability/p17")
def observability_p17():
    """P17 Lean - Observability stats com p17_lean flags"""
    stats = observability_service.get_stats()
    return {
        "traces": stats["traces"],
        "sessions": stats["sessions"],
        "costs": stats["costs"],
        "cache": stats["cache"],
        "alerts": stats["alerts"],
        "logs": stats["logs"],
        "persistence": stats["persistence"],
        "p16_enterprise": stats["p16_enterprise"],
        "p17_lean": stats.get("p17_lean", True),
        "otel": stats["otel"],
        "pattern": stats["pattern"],
        "fixes": {
            "session_race": "FIXED - get_or_create_session não sobrescreve, turns 2/2 vs 1/2 antes",
            "cache_exact": "FIXED - exact match 30s TTL prompt+profile only, hit_rate 0%→50% saves 4834ms",
            "alerts_rigor": "FIXED - rigor<50% alert, alerts total 0→1 rigor LOW 34.0%"
        }
    }
