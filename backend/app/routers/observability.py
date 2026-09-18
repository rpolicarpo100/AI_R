"""
P16 Observability Enterprise Router - Tracing, Sessions, Cost, Cache, Logs, Alerts, Guardrails
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import Optional

from ..core.database import get_db
from ..services.observability import observability_service
from ..services.guardrails import guardrails_service

router = APIRouter(prefix="/observability", tags=["observability"])

@router.get("/stats")
def get_observability_stats():
    """P16 Enterprise - Tracing detalhado + Sessions + Cost + Cache + Logs + Alerts + P1.5 P0.5 metrics"""
    obs_stats = observability_service.get_stats()
    guard_stats = guardrails_service.get_stats()
    
    # P1.5 — P0.5 metrics: circuit breaker, Retry-After, DEPRECATED, provider cache
    try:
        from ..services.circuit_breaker import circuit_breaker
        from ..services.http_client import get_provider_cache_stats, get_client_stats
        from ..core.database import SessionLocal
        from ..models.database_models import Model
        db = SessionLocal()
        try:
            deprecated_count = db.query(Model).filter(Model.status == "DEPRECATED").count() if hasattr(Model, 'status') else 0
        except:
            deprecated_count = 0
        finally:
            db.close()
        cb_stats = {
            "model_failures": circuit_breaker.get_model_failures(),
            "deprecated_count": deprecated_count,
            "retry_after_active": len([k for k,v in circuit_breaker.retry_after.items() if v > __import__('time').time()]),
            "circuits": {k: {"state": v.get("state").value if hasattr(v.get("state"), 'value') else str(v.get("state")), "failures": v.get("failures"), "backoff": v.get("backoff_seconds")} for k,v in circuit_breaker.circuits.items()} if hasattr(circuit_breaker, 'circuits') else {}
        }
        provider_cache_stats = get_provider_cache_stats()
        client_stats = get_client_stats()
    except Exception as e:
        cb_stats = {"error": str(e)}
        provider_cache_stats = {"error": str(e)}
        client_stats = {"error": str(e)}
    
    return {
        "observability": obs_stats,
        "guardrails": guard_stats,
        "p0_5_stability": cb_stats,
        "provider_cache": provider_cache_stats,
        "http_pool": client_stats,
        "p16_enterprise": True,
        "otel": True,
        "pattern": "Helicone + Portkey + Future AGI",
        "tracing": {
            "trace_id": "trace_id span_id parent_span_id latency breakdown classifier 10ms routing 20ms adapter 2000ms critic 500ms",
            "total": obs_stats["traces"]["total"],
            "error_rate": obs_stats["traces"]["error_rate"],
            "p50": obs_stats["traces"]["p50_ms"],
            "p95": obs_stats["traces"]["p95_ms"],
            "p99": obs_stats["traces"]["p99_ms"],
        },
        "sessions": obs_stats["sessions"],
        "costs": obs_stats["costs"],
        "cache": obs_stats["cache"],
        "alerts": obs_stats["alerts"],
        "logs": obs_stats["logs"],
        "guardrails_18_plus": {
            "count": guard_stats["count"],
            "enabled": guard_stats["enabled"],
            "total_hits": guard_stats["total_hits"],
            "by_guardrail": guard_stats["by_guardrail"],
            "config": guard_stats["config"],
        }
    }

@router.get("/traces")
def get_traces(limit: int = 50):
    """OTel traces"""
    return {
        "traces": observability_service.get_traces(limit),
        "count": len(observability_service.get_traces(limit)),
        "p16": True
    }

@router.get("/sessions")
def get_sessions(limit: int = 20):
    """Sessions multi-turn tracking"""
    return {
        "sessions": observability_service.get_sessions(limit),
        "count": len(observability_service.get_sessions(limit)),
        "p16": True
    }

@router.get("/alerts")
def get_alerts(limit: int = 20):
    """Alerts rigor <50% latency >5s error >10% cost >budget provider offline"""
    return {
        "alerts": observability_service.get_alerts(limit),
        "count": len(observability_service.get_alerts(limit)),
        "p16": True
    }

@router.get("/guardrails")
def get_guardrails():
    """18+ guardrails config + hits"""
    return guardrails_service.get_stats()

@router.post("/guardrails/check")
def check_guardrails(text: str, cost: float = 0.0, latency_ms: int = 0):
    """Check guardrails for text"""
    result = guardrails_service.check_all(text, cost=cost, latency_ms=latency_ms)
    return result

@router.get("/costs")
def get_costs():
    """Cost tracking per provider/model/user/session/day budget alerts"""
    stats = observability_service.get_stats()
    return stats["costs"]

@router.get("/cache")
def get_cache_stats():
    """Caching Redis 30s encrypted semantic"""
    stats = observability_service.get_stats()
    return stats["cache"]

@router.get("/quotas")
def get_quota_stats():
    """P2.2 — Provider quota tracking real-time"""
    try:
        from ..services.quota_tracker import quota_tracker
        return quota_tracker.get_stats()
    except Exception as e:
        return {"error": str(e), "total_providers_tracked": 0}

@router.get("/p0_5")
def get_p05_stats():
    """P0.5 + P1 + P2 metrics"""
    try:
        from ..services.circuit_breaker import circuit_breaker
        from ..services.http_client import get_provider_cache_stats, get_client_stats
        from ..services.quota_tracker import quota_tracker
        from ..core.database import SessionLocal
        from ..models.database_models import Model
        db = SessionLocal()
        try:
            deprecated = db.query(Model).filter(Model.status == "DEPRECATED").count()
        except:
            deprecated = 0
        finally:
            db.close()
        return {
            "circuit_breaker": {
                "model_failures": circuit_breaker.get_model_failures(),
                "retry_after_active": len([k for k,v in circuit_breaker.retry_after.items() if v > __import__('time').time()]),
                "circuits": {k: {"state": str(v.get("state")), "failures": v.get("failures"), "backoff": v.get("backoff_seconds")} for k,v in circuit_breaker.circuits.items()} if hasattr(circuit_breaker, 'circuits') else {}
            },
            "deprecated_count": deprecated,
            "provider_cache": get_provider_cache_stats(),
            "http_pool": get_client_stats(),
            "quotas": quota_tracker.get_stats()
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/network")
def get_network_stats():
    """P2.1 — Network detailed for dashboard"""
    try:
        from ..core.database import SessionLocal
        from ..models.database_models import Provider, Model
        from ..services.circuit_breaker import circuit_breaker
        from ..services.quota_tracker import quota_tracker
        db = SessionLocal()
        try:
            providers = db.query(Provider).all()
            models = db.query(Model).all()
            network = []
            for p in providers:
                quota = quota_tracker.get_quota(p.provider_id)
                circuit = circuit_breaker.get_state(p.provider_id)
                quota_score = quota_tracker.get_quota_score(p.provider_id)
                models_count = len([m for m in models if m.provider_id == p.provider_id])
                network.append({
                    "provider_id": p.provider_id,
                    "name": p.name,
                    "status": p.status.value if hasattr(p.status, 'value') else str(p.status),
                    "rating": p.rating,
                    "success_count": p.success_count,
                    "failure_count": p.failure_count,
                    "success_rate": round(p.success_count / (p.success_count + p.failure_count) * 100, 1) if (p.success_count + p.failure_count) > 0 else 0,
                    "avg_latency_ms": p.avg_latency_ms,
                    "consecutive_failures": p.consecutive_failures,
                    "models_count": models_count,
                    "has_key": bool(p.api_key_encrypted),
                    "circuit_state": str(circuit.get("state")),
                    "circuit_failures": circuit.get("failures"),
                    "circuit_backoff": circuit.get("backoff_seconds"),
                    "quota_remaining": quota.get("remaining"),
                    "quota_limit": quota.get("limit"),
                    "quota_reset_seconds": quota.get("reset_seconds"),
                    "quota_score": quota_score,
                    "rate_limit_hits": quota.get("rate_limit_hits", 0),
                    "last_429": quota.get("last_429")
                })
            return sorted(network, key=lambda x: x["rating"], reverse=True)
        finally:
            db.close()
    except Exception as e:
        return {"error": str(e)}

