"""
P7 — Continuous Benchmark Poderoso Contínuo e Fluido
- Rigor atual 52.8% total, 63.5% chat — já acima 60% target, mas desigual
- Gap: kie_ai 1/206 0.5%, cloudflare 0/17, novita 0/20, venice 0/20, ollama_cloud 0/20, fireworks 0/8, nous 0/30
- Gap: 258 measured mas coding_score 0 — benchmark falhou ou só SPEED
- Solução: benchmark contínuo paralelo 5 modelos por ciclo, retry degraded, prioriza grandes providers

Real, medido, sem simulação, poderoso, contínuo, fluido
"""

import asyncio
import time
from datetime import datetime, timezone
from collections import defaultdict
from sqlalchemy.orm import Session
from ..core.database import SessionLocal
from ..models.database_models import Provider, Model, ModelStatus, ProviderStatus
from ..models.agent_models import LoopTask, LoopTaskType, LoopTaskStatus
from .encryption import decrypt_api_key
from ..routers.providers import ADAPTERS_MAP
from ..adapters.openai_compat import OpenAICompatibleAdapter
from .benchmark_engine import BenchmarkEngine
from .benchmark_engine_p8 import BenchmarkEngineP8

class ContinuousBenchmarkP7:
    def __init__(self):
        self.running = False
        self.stats = {
            "benchmarks_run": 0,
            "models_measured": 0,
            "coding_scores_updated": 0,
            "failed": 0,
            "last_run": None
        }
    
    async def benchmark_provider_batch(self, provider_id: str, batch_size: int = 5) -> dict:
        """Benchmarka batch de modelos de um provider com menor test_count"""
        db = SessionLocal()
        try:
            provider = db.query(Provider).filter(Provider.provider_id == provider_id).first()
            if not provider:
                return {"success": False, "error": f"Provider {provider_id} not found"}
            
            has_key = bool(provider.api_key_encrypted)
            caps = provider.capabilities or {}
            pricing = provider.pricing_info or {}
            free_no_card = caps.get('free_no_card') or pricing.get('free_no_card') or caps.get('free') or pricing.get('free')
            
            if not has_key and not free_no_card:
                return {"success": False, "error": f"No key and not free for {provider_id}", "skipped": True}
            
            # Get models with test_count 0 or lowest
            models = db.query(Model).filter(
                Model.provider_id == provider_id,
                Model.status != ModelStatus.DEPRECATED
            ).order_by(Model.test_count.asc()).limit(batch_size).all()
            
            if not models:
                return {"success": True, "skipped": True, "reason": "No models"}
            
            api_key = decrypt_api_key(provider.api_key_encrypted) if provider.api_key_encrypted else ""
            adapter = ADAPTERS_MAP.get(provider_id, OpenAICompatibleAdapter())
            
            results = []
            for model in models:
                try:
                    # P8 — Use improved engine with lenient validation for coding
                    engine = BenchmarkEngineP8(adapter, provider, model)
                    # P7+P8 — Full suite CODING + SPEED + JSON for rigor poderoso, P8 lenient
                    result = await engine.run_suite(api_key, categories=["CODING", "SPEED", "JSON"])
                    
                    # Update model — P7 robust: even if overall 0, keep test_count and try to extract scores
                    model.coding_score = result["by_category"].get("CODING", {}).get("avg_score", 0) or model.coding_score
                    model.speed_score = result["by_category"].get("SPEED", {}).get("avg_score", 0) or model.speed_score
                    model.json_score = result["by_category"].get("JSON", {}).get("avg_score", 0) or model.json_score
                    model.overall_score = result["overall_score"] or model.overall_score
                    model.confidence_score = result["confidence"] or model.confidence_score
                    model.test_count = (model.test_count or 0) + result["total_tests"]
                    # Status based on success rate
                    if result["overall_success_rate"] > 50:
                        model.status = ModelStatus.VERIFIED
                    elif result["overall_success_rate"] > 20:
                        model.status = ModelStatus.DISCOVERED
                    else:
                        # Keep DISCOVERED if failed, don't mark DEGRADED unless many failures
                        if model.test_count > 10 and result["overall_success_rate"] == 0:
                            model.status = ModelStatus.DEGRADED
                    
                    model.last_verified = datetime.now(timezone.utc)
                    
                    results.append({
                        "model": f"{provider_id}/{model.model_id}",
                        "overall": result["overall_score"],
                        "coding": model.coding_score,
                        "success_rate": result["overall_success_rate"]
                    })
                    
                    self.stats["benchmarks_run"] += 1
                    self.stats["models_measured"] += 1
                    if model.coding_score > 0:
                        self.stats["coding_scores_updated"] += 1
                    
                    print(f"[P7 CONTINUOUS] {provider_id}/{model.model_id} overall {result['overall_score']} coding {model.coding_score} success {result['overall_success_rate']}%")
                    
                    # Small delay to avoid rate limit
                    await asyncio.sleep(1.0)
                    
                except Exception as e:
                    print(f"[P7 CONTINUOUS] Failed {provider_id}/{model.model_id}: {e}")
                    self.stats["failed"] += 1
                    continue
            
            db.commit()
            return {"success": True, "results": results, "count": len(results)}
        
        except Exception as e:
            print(f"[P7 CONTINUOUS] Batch failed for {provider_id}: {e}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()
    
    async def run_continuous_cycle(self, prioritize_large: bool = True):
        """Run one continuous cycle — benchmark 5 models per provider prioritized"""
        print(f"\n[P7 CONTINUOUS] Starting cycle at {datetime.now(timezone.utc)} prioritize_large={prioritize_large}")
        start = time.time()
        
        db = SessionLocal()
        try:
            # Get providers ordered by need: least measured % first, but with key
            from collections import defaultdict
            measured_by_prov = defaultdict(int)
            total_by_prov = defaultdict(int)
            for m in db.query(Model).all():
                total_by_prov[m.provider_id] += 1
                if (m.test_count or 0) > 0:
                    measured_by_prov[m.provider_id] += 1
            
            providers = db.query(Provider).all()
            # Filter to those with key or free_no_card and not DEPRECATED/DISABLED
            eligible = []
            for p in providers:
                status = p.status.value if hasattr(p.status, 'value') else str(p.status)
                if status in ["DEPRECATED", "DISABLED", "OFFLINE"]:
                    continue
                has_key = bool(p.api_key_encrypted)
                caps = p.capabilities or {}
                pricing = p.pricing_info or {}
                free_no_card = caps.get('free_no_card') or pricing.get('free_no_card') or caps.get('free') or pricing.get('free')
                if not has_key and not free_no_card:
                    continue
                total = total_by_prov.get(p.provider_id, 0)
                measured = measured_by_prov.get(p.provider_id, 0)
                pct = measured / total * 100 if total else 0
                eligible.append((p.provider_id, pct, total, measured, p.rating))
            
            # P8 — Sort: prioritize low pct, then high rating, then large total, but also prioritize providers with key and high success
            # For rigor optimization, prioritize providers that have key and low coding % to improve coding rigor
            # Calculate coding pct for each provider
            coding_by_prov = {}
            for m in db.query(Model).all():
                if m.provider_id not in coding_by_prov:
                    coding_by_prov[m.provider_id] = {"total":0, "coding":0}
                coding_by_prov[m.provider_id]["total"] += 1
                if (m.coding_score or 0) > 0:
                    coding_by_prov[m.provider_id]["coding"] += 1
            
            # Add coding pct to eligible and sort by low coding pct first, then low measured pct, then high rating
            eligible_with_coding = []
            for pid, pct, total, measured, rating in eligible:
                coding_stats = coding_by_prov.get(pid, {"total":1, "coding":0})
                coding_pct = coding_stats["coding"] / coding_stats["total"] * 100 if coding_stats["total"] else 0
                eligible_with_coding.append((pid, pct, total, measured, rating, coding_pct))
            
            # P8 — Prioritize low coding pct (to improve coding rigor), then low measured pct, then high rating, then large total
            if prioritize_large:
                eligible_with_coding.sort(key=lambda x: (x[5], x[1], -x[4], -x[2]))  # low coding, low pct, high rating, large total
            else:
                eligible_with_coding.sort(key=lambda x: (x[5], x[1], -x[4]))
            
            # Convert back to original format for compatibility
            eligible = [(pid, pct, total, measured, rating) for pid, pct, total, measured, rating, coding_pct in eligible_with_coding]
            
            print(f"[P7 CONTINUOUS] Eligible providers {len(eligible)} sorted by need:")
            for pid, pct, total, measured, rating in eligible[:10]:
                print(f"  {pid:15} {measured}/{total} {pct:5.1f}% rating {rating}")
            
            # Benchmark top 3 providers, 5 models each = 15 models per cycle
            for pid, pct, total, measured, rating in eligible[:3]:
                print(f"[P7 CONTINUOUS] Benchmarking batch for {pid} {pct:.1f}% measured")
                result = await self.benchmark_provider_batch(pid, batch_size=5)
                print(f"[P7 CONTINUOUS] {pid} batch result: {result}")
                await asyncio.sleep(2.0)  # Delay between providers
            
            latency = int((time.time() - start) * 1000)
            self.stats["last_run"] = datetime.now(timezone.utc).isoformat()
            print(f"[P7 CONTINUOUS] Cycle completed {latency}ms stats {self.stats}")
            
            return self.stats
        
        finally:
            db.close()
    
    def get_rigor_stats(self) -> dict:
        """Get current rigor stats — real, medido — P8 excludes DEPRECATED for honest rigor"""
        db = SessionLocal()
        try:
            all_models = db.query(Model).all()
            # P8 — Exclude DEPRECATED for honest rigor
            models = [m for m in all_models if str(m.status) != "DEPRECATED" and getattr(m.status, 'value', '') != "DEPRECATED"]
            providers = db.query(Provider).all()
            
            total = len(models)
            measured = len([m for m in models if (m.test_count or 0) > 0])
            verified = len([m for m in models if str(m.status) == "VERIFIED" or getattr(m.status, 'value', '') == "VERIFIED"])
            coding_nonzero = len([m for m in models if (m.coding_score or 0) > 0])
            overall_nonzero = len([m for m in models if (m.overall_score or 0) > 0])
            
            # Chat vs video vs image
            chat_keywords = ['gpt','claude','llama','mistral','qwen','gemma','deepseek','codestral','command','gemini','grok','kimi','glm','llm','chat','instruct']
            video_keywords = ['video','kling','sora','runway','pika','image-to-video','text-to-video']
            
            chat_total = 0
            chat_measured = 0
            chat_coding = 0
            for m in models:
                mid = m.model_id.lower()
                is_chat = any(k in mid for k in chat_keywords) and not any(k in mid for k in video_keywords)
                if is_chat or 'image' not in mid:
                    # Rough chat detection
                    if any(k in mid for k in chat_keywords):
                        chat_total += 1
                        if (m.test_count or 0) > 0:
                            chat_measured += 1
                        if (m.coding_score or 0) > 0:
                            chat_coding += 1
            
            # Providers needing measurement
            measured_by_prov = defaultdict(int)
            total_by_prov = defaultdict(int)
            for m in models:
                total_by_prov[m.provider_id] += 1
                if (m.test_count or 0) > 0:
                    measured_by_prov[m.provider_id] += 1
            
            needing = []
            for pid in total_by_prov:
                total_p = total_by_prov[pid]
                measured_p = measured_by_prov[pid]
                pct = measured_p / total_p * 100 if total_p else 0
                if pct < 50:
                    p = db.query(Provider).filter(Provider.provider_id == pid).first()
                    needing.append({
                        "provider_id": pid,
                        "measured": measured_p,
                        "total": total_p,
                        "pct": round(pct, 1),
                        "has_key": bool(p.api_key_encrypted) if p else False,
                        "status": p.status.value if p and hasattr(p.status, 'value') else str(p.status) if p else "UNKNOWN"
                    })
            
            needing.sort(key=lambda x: x["pct"])
            
            return {
                "total_models": total,
                "measured": measured,
                "measured_pct": round(measured/total*100, 1) if total else 0,
                "verified": verified,
                "verified_pct": round(verified/total*100, 1) if total else 0,
                "coding_nonzero": coding_nonzero,
                "coding_nonzero_pct": round(coding_nonzero/total*100, 1) if total else 0,
                "overall_nonzero": overall_nonzero,
                "chat_total": chat_total,
                "chat_measured": chat_measured,
                "chat_measured_pct": round(chat_measured/chat_total*100, 1) if chat_total else 0,
                "chat_coding": chat_coding,
                "providers_total": len(providers),
                "providers_with_key": len([p for p in providers if p.api_key_encrypted]),
                "free_no_card": len([p for p in providers if (p.capabilities or {}).get('free_no_card')]),
                "needing_measurement": needing[:10],
                "stats": self.stats,
                "version": "P7 — Rigor Poderoso Contínuo e Fluido"
            }
        finally:
            db.close()

continuous_benchmark_p7 = ContinuousBenchmarkP7()
print(f"[P7 CONTINUOUS] Loaded — rigor poderoso contínuo e fluido")
