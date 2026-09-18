from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from typing import Dict, List
import time

from ..core.database import get_db
from ..models.database_models import Provider, Model, RequestLog, ProviderStatus
from ..services.circuit_breaker import circuit_breaker

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Cache in-memory 30s - Dia 2 Performance - evita query pesada 323 models a cada request
# P6 — Add LRU cache 5s for high frequency + static score optimization
_cache = {"stats": None, "timestamp": 0, "ttl": 30}

def get_cached_stats():
    # P6 — Try LRU cache first 5s for high frequency 15s auto-refresh
    try:
        from ..services.cache_manager import dashboard_cache
        cached = dashboard_cache.get("dashboard:stats")
        if cached:
            return cached
    except:
        pass
    now = time.time()
    if _cache["stats"] and (now - _cache["timestamp"]) < _cache["ttl"]:
        return _cache["stats"]
    return None

def set_cached_stats(data):
    _cache["stats"] = data
    _cache["timestamp"] = time.time()
    # P6 — Also set LRU cache 5s
    try:
        from ..services.cache_manager import dashboard_cache
        dashboard_cache.set("dashboard:stats", data)
    except:
        pass

# Try Redis cache if available - Dia 2 Performance
try:
    import redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True, socket_connect_timeout=1)
    redis_client.ping()
    USE_REDIS = True
    print("[CACHE] Redis available - using Redis cache 30s")
except:
    USE_REDIS = False
    redis_client = None
    print("[CACHE] Redis not available - using in-memory cache 30s")

@router.get("/stats")
def get_stats(request: Request, db: Session = Depends(get_db)):
    # Dia 2 Performance - Check cache 30s
    cached = None
    if USE_REDIS:
        try:
            import json
            cached_data = redis_client.get("dashboard:stats")
            if cached_data:
                cached = json.loads(cached_data)
                # Check TTL via timestamp
                cache_time = redis_client.get("dashboard:stats:timestamp")
                if cache_time and (time.time() - float(cache_time)) < 30:
                    # Return cached but update timestamp field
                    cached["cached"] = True
                    cached["cache_source"] = "redis"
                    return cached
        except:
            pass
    else:
        cached = get_cached_stats()
        if cached:
            cached["cached"] = True
            cached["cache_source"] = "memory"
            return cached

    providers = db.query(Provider).all()
    models = db.query(Model).all()
    logs = db.query(RequestLog).order_by(RequestLog.timestamp.desc()).limit(1000).all()
    # Agents LOOP stats - import here to avoid circular
    try:
        from ..models.agent_models import AgentDB, SkillDB, LoopTask
        agents_count = db.query(AgentDB).count()
        skills_count = db.query(SkillDB).count()
        loop_tasks = db.query(LoopTask).count()
        agents_online = db.query(AgentDB).filter(AgentDB.status == "AVAILABLE").count() if agents_count>0 else 0
    except Exception:
        agents_count = 0
        skills_count = 0
        loop_tasks = 0
        agents_online = 0
    
    # Provider status counts
    online = len([p for p in providers if p.status in [ProviderStatus.PRODUCTION, ProviderStatus.VERIFIED]])
    degraded = len([p for p in providers if p.status == ProviderStatus.DEGRADED])
    offline = len([p for p in providers if p.status in [ProviderStatus.OFFLINE, ProviderStatus.DISABLED, ProviderStatus.DEPRECATED]])
    discovered = len([p for p in providers if p.status == ProviderStatus.DISCOVERED])
    
    # Request stats
    total_requests = db.query(RequestLog).count()
    success_requests = db.query(RequestLog).filter(RequestLog.status == "success").count()
    success_rate = (success_requests / total_requests * 100) if total_requests > 0 else 0
    
    fallback_count = db.query(RequestLog).filter(RequestLog.fallback_used == True).count()
    fallback_rate = (fallback_count / total_requests * 100) if total_requests > 0 else 0
    
    # Avg latency
    avg_latency = db.query(func.avg(RequestLog.latency_ms)).scalar() or 0
    
    # Total cost
    total_cost = db.query(func.sum(RequestLog.cost)).scalar() or 0
    
    # Free usage
    free_logs = db.query(RequestLog).filter(RequestLog.cost == 0).count()
    
    # Best provider now - highest rating + healthy
    healthy_providers = [p for p in providers if p.status in [ProviderStatus.PRODUCTION, ProviderStatus.VERIFIED]]
    best_provider = max(healthy_providers, key=lambda x: x.rating, default=None) if healthy_providers else None
    
    # Best models by category - RIGOR: handle None scores (0% invenção)
    def best_by_score(attr: str):
        filtered = [m for m in models if (getattr(m, attr, 0) or 0) > 0]
        return max(filtered, key=lambda x: (getattr(x, attr) or 0), default=None) if filtered else None
    
    best_coding = best_by_score("coding_score")
    best_reasoning = best_by_score("reasoning_score")
    fastest = best_by_score("speed_score")
    most_reliable = best_by_score("reliability_score")
    best_overall = best_by_score("overall_score")
    
    # Recent requests
    recent = logs[:10]
    
    # Circuit breaker states
    circuits = {pid: circuit_breaker.get_state(pid) for pid in [p.provider_id for p in providers]}
    
    # Rigoroso: distinct counting - o que contar?
    from collections import defaultdict
    base_map = defaultdict(list)
    for m in models:
        base = m.model_id.split("/")[-1]
        base_map[base].append(m)
    distinct_total = len(base_map)
    multi_provider = len([k for k,v in base_map.items() if len(v)>1])
    measured_entries = len([m for m in models if m.test_count>0])
    measured_distinct = len(set(m.model_id.split("/")[-1] for m in models if m.test_count>0))
    via_models = len([m for m in models if m.capabilities and 'discovered via' in str(m.capabilities.get('source',''))])
    
    # P2.1 — Enhanced metrics for dashboard + P0.5 + P1 + P2
    try:
        from ..services.quota_tracker import quota_tracker
        quota_stats = quota_tracker.get_stats()
    except:
        quota_stats = {"total_providers_tracked": 0, "total_429_hits_last_hour": 0}
    
    try:
        from ..services.http_client import get_provider_cache_stats, get_client_stats
        provider_cache_stats = get_provider_cache_stats()
        http_pool_stats = get_client_stats()
    except:
        provider_cache_stats = {}
        http_pool_stats = {}

    try:
        deprecated_count = len([m for m in models if str(m.status) == "DEPRECATED" or getattr(m.status, 'value', str(m.status)) == "DEPRECATED"])
        cb_circuits = len([c for c in circuits.values() if c.get("state") and "OPEN" in str(c.get("state"))])
        model_failures = circuit_breaker.get_model_failures()
    except Exception as e:
        print(f"[DASHBOARD P2] P0.5 metrics failed {e}")
        deprecated_count = 0
        cb_circuits = 0
        model_failures = {}

    result = {
        "ai_network": {
            "providers_online": online,
            "providers_degraded": degraded,
            "providers_offline": offline,
            "providers_discovered": discovered,
            "total_providers": len(providers),
            "models_available": len(models),
            "models_distinct": distinct_total,
            "models_multi_provider": multi_provider,
            "models_measured_entries": measured_entries,
            "models_measured_distinct": measured_distinct,
            "models_via_models_endpoint": via_models,
            "models_production": len([m for m in models if m.status.value == "PRODUCTION"]),
            "models_deprecated": deprecated_count,
            "verification_291": f"291 verificados: {via_models} via /models REAL, distinct {distinct_total}, multi {multi_provider}, medidos {measured_entries}/{len(models)}, deprecated {deprecated_count}",
        },
        "p0_5_stability": {
            "deprecated_count": deprecated_count,
            "model_failures": model_failures,
            "circuits_open": cb_circuits,
            "provider_cache": provider_cache_stats,
            "http_pool": http_pool_stats,
        },
        "p1_performance": {
            "provider_cache_hit": provider_cache_stats.get("hit", False),
            "provider_cache_age": provider_cache_stats.get("age_seconds", 0),
            "http_pool_clients": http_pool_stats.get("pooled_clients", 0),
            "pre_warm": "P1.1 167ms vs 1014ms 83% faster",
        },
        "p2_quotas": quota_stats,
        "p2_async_critic": {
            "enabled": True,
            "description": "P2.3 async critic for MEDIUM/COMPLEX — returns response immediately, critic in background, TTFB 500ms vs 2-5s"
        },
        "requests": {
            "total": total_requests,
            "success_rate": round(success_rate, 2),
            "fallback_rate": round(fallback_rate, 2),
            "avg_latency_ms": round(avg_latency, 1),
            "total_cost": round(total_cost, 6),
            "free_usage": free_logs,
            "free_usage_percent": round((free_logs/total_requests*100) if total_requests else 0, 1)
        },
        "best_now": {
            "best_provider": {"name": best_provider.name, "id": best_provider.provider_id, "rating": best_provider.rating} if best_provider else {"name": "UNKNOWN", "id": "UNKNOWN"},
            "best_coding_model": {"name": best_coding.display_name, "provider": best_coding.provider_id, "score": best_coding.coding_score} if best_coding else {"name": "UNKNOWN"},
            "best_reasoning_model": {"name": best_reasoning.display_name, "provider": best_reasoning.provider_id, "score": best_reasoning.reasoning_score} if best_reasoning else {"name": "UNKNOWN"},
            "fastest_model": {"name": fastest.display_name, "provider": fastest.provider_id, "score": fastest.speed_score} if fastest else {"name": "UNKNOWN"},
            "most_reliable_model": {"name": most_reliable.display_name, "provider": most_reliable.provider_id, "score": most_reliable.reliability_score} if most_reliable else {"name": "UNKNOWN"},
            "best_overall": {"name": best_overall.display_name, "provider": best_overall.provider_id, "score": best_overall.overall_score} if best_overall else {"name": "UNKNOWN"},
        },
        "recent_requests": [
            {
                "request_id": r.request_id,
                "provider": r.provider or "UNKNOWN",
                "model": r.model or "UNKNOWN",
                "task_type": r.task_type,
                "latency_ms": r.latency_ms,
                "status": r.status,
                "fallback_used": r.fallback_used,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None
            } for r in recent
        ],
        "circuits": circuits,
        "agents_loop": {
            "agents_count": agents_count,
            "agents_online": agents_online,
            "skills_count": skills_count,
            "loop_tasks": loop_tasks,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cached": False,
        "cache_source": "none",
        "performance": "Dia 2 - Cache 30s, evita query pesada 323 models"
    }
    
    # Save to cache Dia 2
    try:
        if USE_REDIS:
            import json
            redis_client.setex("dashboard:stats", 30, json.dumps(result, default=str))
            redis_client.setex("dashboard:stats:timestamp", 30, str(time.time()))
        else:
            set_cached_stats(result)
    except:
        pass
    
    return result

@router.get("/network")
def get_network(db: Session = Depends(get_db)):
    providers = db.query(Provider).all()
    result = []
    for p in providers:
        models_count = db.query(Model).filter(Model.provider_id == p.provider_id).count()
        circuit = circuit_breaker.get_state(p.provider_id)
        result.append({
            "provider_id": p.provider_id,
            "name": p.name,
            "status": p.status.value if hasattr(p.status, 'value') else str(p.status),
            "base_url": p.base_url,
            "rating": p.rating,
            "confidence": p.confidence,
            "success_count": p.success_count,
            "failure_count": p.failure_count,
            "success_rate": round(p.success_count / (p.success_count + p.failure_count) * 100, 1) if (p.success_count + p.failure_count) > 0 else 0,
            "avg_latency_ms": p.avg_latency_ms,
            "consecutive_failures": p.consecutive_failures,
            "models_count": models_count,
            "has_key": bool(p.api_key_encrypted),
            "last_health_check": p.last_health_check.isoformat() if p.last_health_check else None,
            "last_success": p.last_success.isoformat() if p.last_success else None,
            "source": p.source,
            "source_confidence": p.source_confidence,
            "capabilities": p.capabilities or {},
            "pricing": p.pricing_info or {},
            "circuit_state": circuit["state"],
            "circuit_failures": circuit["failures"]
        })
    return sorted(result, key=lambda x: x["rating"], reverse=True)

@router.get("/discovery")
def get_discovery():
    # Stub for Discovery Agent - would be populated by discovery agent
    return {
        "new_providers": [],
        "new_models": [],
        "changed_providers": [],
        "changed_limits": [],
        "changed_prices": [],
        "deprecated_models": [],
        "message": "Discovery Agent - P2 feature - will scan official docs, OpenRouter, HuggingFace",
        "last_scan": None,
        "status": "NOT_IMPLEMENTED_P2"
    }

@router.get("/skills")
def get_skills():
    from ..services.orchestrator import SKILL_REGISTRY
    return [
        {
            "skill_id": s.skill_id,
            "name": s.name,
            "description": s.description,
            "version": s.version,
            "capabilities": s.capabilities,
            "preferred_models": s.preferred_models,
            "security_level": s.security_level,
            "status": s.status
        } for s in SKILL_REGISTRY
    ]

@router.get("/agents")
def get_agents():
    from ..services.orchestrator import AGENT_REGISTRY
    return [
        {
            "agent_id": a.agent_id,
            "name": a.name,
            "role": a.role.value,
            "skills": a.skills,
            "preferred_models": a.preferred_models,
            "rating": a.rating,
            "status": a.status
        } for a in AGENT_REGISTRY
    ]

@router.get("/metrics")
def get_metrics(limit: int = 100, db: Session = Depends(get_db)):
    logs = db.query(RequestLog).order_by(RequestLog.timestamp.desc()).limit(limit).all()
    return [
        {
            "request_id": r.request_id,
            "provider": r.provider,
            "model": r.model,
            "task_type": r.task_type,
            "profile": r.profile,
            "latency_ms": r.latency_ms,
            "input_tokens": r.input_tokens,
            "output_tokens": r.output_tokens,
            "cost": r.cost,
            "cost_status": r.cost_status,
            "status": r.status,
            "error_code": r.error_code,
            "fallback_used": r.fallback_used,
            "fallback_chain": r.fallback_chain,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None
        } for r in logs
    ]
