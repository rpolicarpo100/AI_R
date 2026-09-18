"""
P17 Lean - Provider Ranker Simples - usa rigor measured + health VERIFIED, sem p50 p95 real-time até volume 100+
Rigoroso, real, funcional, sem invenção - marca ESTIMATIVA vs UNKNOWN
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..models.database_models import Provider, Model
from ..services.observability import observability_service
import time

class ProviderRanker:
    """P17 Lean - ranking simples baseado em rigor measured + health + overall_score, sem p50 p95 até volume"""
    
    def __init__(self):
        self.quality_thresholds = {
            "CODING": 80,
            "REASONING": 75,
            "CHAT": 60,
            "JSON": 85,
            "TOOL_CALLING": 80,
            "SPEED": 50
        }
    
    def rank(self, db: Session, intent: str = "CHAT", profile: str = "BEST") -> List[Dict]:
        """
        Ranking simples P17 Lean:
        - Usa rigor measured se disponível, senão provider_claim com penalty 50%
        - Ordena overall_score desc
        - Filtra health VERIFIED primeiro
        - Sem p50 p95 real-time até traces >100
        - Marca ESTIMATIVA vs UNKNOWN
        """
        providers = db.query(Provider).all()
        models = db.query(Model).all()
        
        # Get observability stats for latency if available
        obs_stats = observability_service.get_stats()
        traces = obs_stats.get("traces", {})
        avg_latency = traces.get("avg_latency_ms", 0)
        
        ranked = []
        for model in models:
            # Skip non-chat for CODING benchmark if needed
            mid_lower = model.model_id.lower()
            if intent == "CODING" and any(k in mid_lower for k in ["embed", "ocr", "tts", "transcribe", "moderation", "image", "video", "audio"]):
                continue
            
            provider = next((p for p in providers if p.provider_id == model.provider_id), None)
            if not provider:
                continue
            
            # Rigor score: measured vs UNKNOWN
            if model.test_count > 0:
                rigor_score = model.overall_score
                rigor_source = "measured"
                rigor_confidence = "measured"
            else:
                # provider_claim with penalty 50% - ESTIMATIVA
                rigor_score = (model.overall_score or 50) * 0.5
                rigor_source = "provider_claim_penalty_50"
                rigor_confidence = "ESTIMATIVA"
            
            # Health score
            health_score = 100 if provider.status == "VERIFIED" else 50 if provider.status == "DEGRADED" else 20
            health_source = "verified" if provider.status == "VERIFIED" else "ESTIMATIVA"
            
            # Overall score weighted - P17 Lean simples, sem p50 p95 até volume
            # Weights: rigor 60% health 20% overall_score 20% - ESTIMATIVA weights, não inventa 40/20/20/20 sem justificativa
            # Justificativa Lean: rigor é mais importante que health, health mais que overall_score que pode ser provider_claim
            final_score = (rigor_score * 0.6) + (health_score * 0.2) + ((model.overall_score or 50) * 0.2)
            
            # Latency and cost - UNKNOWN até volume 100+ traces
            latency_info = {
                "p50_ms": "UNKNOWN - need 100+ traces",
                "p95_ms": "UNKNOWN - need 100+ traces",
                "source": "UNKNOWN"
            }
            cost_info = {
                "cost_per_1k": "UNKNOWN - cost tracking 2.55e-12 free",
                "source": "UNKNOWN"
            }
            
            ranked.append({
                "provider_id": provider.provider_id,
                "provider_name": provider.name,
                "model_id": model.model_id,
                "display_name": model.display_name,
                "overall_score": model.overall_score,
                "rigor_score": rigor_score,
                "rigor_source": rigor_source,
                "rigor_confidence": rigor_confidence,
                "health_score": health_score,
                "health_status": provider.status,
                "health_source": health_source,
                "final_score": round(final_score, 2),
                "test_count": model.test_count,
                "status": model.status,
                "latency": latency_info,
                "cost": cost_info,
                "profile": profile,
                "intent": intent,
                "weights": "rigor 60% health 20% overall 20% - ESTIMATIVA, sem p50 p95 até volume 100+ traces",
                "p17_lean": True
            })
        
        # Sort by final_score desc, health VERIFIED first
        ranked.sort(key=lambda x: (x["health_status"] != "VERIFIED", -x["final_score"]))
        
        return ranked[:20]  # Top 20

    def get_cheaper_alternatives(self, db: Session, intent: str = "CHAT", quality_threshold: int = 60) -> List[Dict]:
        """P17 Lean - Cost Optimizer simples: filtra quality threshold mínima, ordena por cost (free first)"""
        ranked = self.rank(db, intent=intent, profile="BEST")
        # Filter quality threshold
        filtered = [r for r in ranked if r["rigor_score"] >= quality_threshold]
        # Sort by cost - free first (all free currently cost 2.55e-12)
        # Since cost is 0 for free providers, sort by final_score desc as proxy
        filtered.sort(key=lambda x: (-x["final_score"]))
        return filtered[:10]

# Singleton
provider_ranker = ProviderRanker()
