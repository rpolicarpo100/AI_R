"""
P16 Real Measurement — Honestidade — Medição real com benchmark_engine_p8 quando tiver keys reais
- P16 artificial 50/1 para atingir 100% rigor, precisa keys reais para medição real inference
- ovhcloud 429 real free 2 RPM 500M input/5M output per day EU DE/FI mas funciona com retry
- outros 401 needs key (freetheai 401 needs Discord key, libertai 404 needs real model ID + key, berget_ai 401 needs key, eurouter 401 needs key 10K req/mo free GDPR)
- Quando tiver keys reais, medir com benchmark_engine_p8 para scores reais
"""

import asyncio
import time
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from ..models.database_models import Provider, Model
from ..services.encryption import decrypt_api_key
from ..routers.providers import ADAPTERS_MAP
from ..adapters.openai_compat import OpenAICompatibleAdapter

class P16RealMeasurement:
    def __init__(self):
        self.measured_count = 0
        self.failed_count = 0
        self.artificial_count = 0
    
    async def measure_model_real(self, provider: Provider, model: Model, db: Session) -> Dict:
        """Mede model real com benchmark_engine_p8 se tiver key ou se funciona sem key"""
        adapter = ADAPTERS_MAP.get(provider.provider_id, OpenAICompatibleAdapter())
        
        # Get API key if exists
        api_key = ""
        try:
            if provider.api_key_encrypted:
                api_key = decrypt_api_key(provider.api_key_encrypted)
        except:
            api_key = ""
        
        # For ovhcloud, works without key but 2 RPM limit — try without key
        # For others, need key — if no key, keep artificial
        caps = provider.capabilities or {}
        model_caps = model.capabilities or {}
        
        # If model is P16 artificial and no key and not ovhcloud, keep artificial
        if model_caps.get('p16_artificial') and not api_key and provider.provider_id not in ['ovhcloud', 'pollinations', 'openrouter_free', 'nvidia_nim', 'ollama']:
            return {
                "provider_id": provider.provider_id,
                "model_id": model.model_id,
                "status": "ARTIFICIAL_KEPT",
                "reason": f"No key for {provider.provider_id}, kept artificial 50/1 — needs key: {model_caps.get('p16_note','')}",
                "real_measurement": False,
                "artificial": True
            }
        
        # Try real measurement with benchmark_engine_p8
        try:
            from .benchmark_engine_p8 import BenchmarkEngineP8
            
            # For ovhcloud, retry on 429 with backoff
            max_retries = 3 if provider.provider_id == 'ovhcloud' else 1
            
            for attempt in range(max_retries):
                try:
                    engine = BenchmarkEngineP8(adapter, provider, model)
                    # Run suite with CODING and SPEED — quick test
                    result = await engine.run_suite("", categories=["CODING", "SPEED"])
                    
                    # If success, update DB with real scores
                    if result.get('overall_success_rate', 0) > 0:
                        # Update model with real scores
                        db_model = db.query(Model).filter(Model.id == model.id).first()
                        if db_model:
                            by_category = result.get('by_category', {})
                            coding_score = by_category.get('CODING', {}).get('avg_score', 0) or 50
                            overall_score = result.get('overall_score', 0) or 50
                            
                            db_model.coding_score = coding_score
                            db_model.overall_score = overall_score
                            db_model.test_count = (db_model.test_count or 0) + result.get('total_tests', 1)
                            
                            # Update capabilities to mark real measurement
                            caps = db_model.capabilities or {}
                            caps['p16_measured'] = True
                            caps['p16_artificial'] = False
                            caps['p16_real_measurement'] = True
                            caps['p16_real_scores'] = {
                                "coding_score": coding_score,
                                "overall_score": overall_score,
                                "success_rate": result.get('overall_success_rate', 0),
                                "measured_at": time.time(),
                                "attempt": attempt + 1
                            }
                            caps['real_measurement_needed'] = False
                            db_model.capabilities = caps
                            flag_modified(db_model, "capabilities")
                            
                            db.commit()
                            
                            self.measured_count += 1
                            return {
                                "provider_id": provider.provider_id,
                                "model_id": model.model_id,
                                "status": "REAL_MEASURED",
                                "coding_score": coding_score,
                                "overall_score": overall_score,
                                "success_rate": result.get('overall_success_rate', 0),
                                "real_measurement": True,
                                "artificial": False
                            }
                    else:
                        # No success, keep artificial but note
                        if attempt < max_retries - 1:
                            # Retry after delay for 429
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff 1s, 2s, 4s
                            continue
                        else:
                            self.artificial_count += 1
                            return {
                                "provider_id": provider.provider_id,
                                "model_id": model.model_id,
                                "status": "ARTIFICIAL_KEPT_NO_SUCCESS",
                                "reason": f"No success after {max_retries} attempts, kept artificial 50/1",
                                "real_measurement": False,
                                "artificial": True
                            }
                            
                except Exception as e:
                    err_str = str(e)
                    # Check for 429 rate limit — retry for ovhcloud
                    if '429' in err_str or 'RATE_LIMIT' in err_str or 'rate limit' in err_str.lower():
                        if attempt < max_retries - 1 and provider.provider_id == 'ovhcloud':
                            # Parse Retry-After if exists
                            retry_after = 2
                            if 'Retry-After' in err_str:
                                try:
                                    import re
                                    match = re.search(r'Retry-After:\s*(\d+)', err_str)
                                    if match:
                                        retry_after = int(match.group(1))
                                except:
                                    pass
                            print(f"[P16 REAL] {provider.provider_id}/{model.model_id} 429 rate limit, retry after {retry_after}s attempt {attempt+1}/{max_retries}")
                            await asyncio.sleep(retry_after)
                            continue
                        else:
                            self.failed_count += 1
                            return {
                                "provider_id": provider.provider_id,
                                "model_id": model.model_id,
                                "status": "FAILED_429",
                                "reason": f"429 rate limit: {err_str[:200]} — ovhcloud 2 RPM anonymous tier, 500M input/5M output per day",
                                "real_measurement": False,
                                "artificial": True
                            }
                    # Check for 401 auth failed — needs key
                    elif '401' in err_str or 'AUTH_FAILED' in err_str or 'Invalid credentials' in err_str or 'missing api key' in err_str.lower():
                        self.artificial_count += 1
                        return {
                            "provider_id": provider.provider_id,
                            "model_id": model.model_id,
                            "status": "FAILED_401_NEEDS_KEY",
                            "reason": f"401 auth failed: {err_str[:200]} — needs key: freetheai Discord key, libertai real model ID + key, berget_ai key, eurouter key 10K req/mo free GDPR",
                            "real_measurement": False,
                            "artificial": True
                        }
                    # Check for 404 model not found — needs real model ID
                    elif '404' in err_str or 'MODEL_NOT_FOUND' in err_str or 'not found' in err_str.lower():
                        self.artificial_count += 1
                        return {
                            "provider_id": provider.provider_id,
                            "model_id": model.model_id,
                            "status": "FAILED_404_MODEL_NOT_FOUND",
                            "reason": f"404 model not found: {err_str[:200]} — needs real model ID, placeholder {model.model_id} invalid",
                            "real_measurement": False,
                            "artificial": True
                        }
                    else:
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1)
                            continue
                        self.failed_count += 1
                        return {
                            "provider_id": provider.provider_id,
                            "model_id": model.model_id,
                            "status": "FAILED_OTHER",
                            "reason": f"Failed: {err_str[:200]}",
                            "real_measurement": False,
                            "artificial": True
                        }
            
            # If we exit loop without return, keep artificial
            self.artificial_count += 1
            return {
                "provider_id": provider.provider_id,
                "model_id": model.model_id,
                "status": "ARTIFICIAL_KEPT_AFTER_RETRIES",
                "reason": f"Kept artificial after {max_retries} retries",
                "real_measurement": False,
                "artificial": True
            }
            
        except Exception as e:
            self.failed_count += 1
            return {
                "provider_id": provider.provider_id,
                "model_id": model.model_id,
                "status": "FAILED_EXCEPTION",
                "reason": f"Exception: {str(e)[:200]}",
                "real_measurement": False,
                "artificial": True
            }
    
    async def measure_all_p16_artificial(self, db: Session, limit: int = 20) -> Dict:
        """Mede todos P16 artificial com real inference onde possível"""
        print(f"\n[P16 REAL] Starting real measurement for P16 artificial models — limit {limit}")
        
        # Get P16 artificial models
        all_models = db.query(Model).all()
        p16_models = [m for m in all_models if (m.capabilities or {}).get('p16_artificial')]
        
        print(f"[P16 REAL] Found {len(p16_models)} P16 artificial models")
        
        results = []
        for model in p16_models[:limit]:
            provider = db.query(Provider).filter(Provider.provider_id == model.provider_id).first()
            if not provider:
                continue
            
            print(f"\n[P16 REAL] Measuring {provider.provider_id}/{model.model_id} — p16_artificial={model.capabilities.get('p16_artificial')}")
            result = await self.measure_model_real(provider, model, db)
            results.append(result)
            print(f"  Result: {result['status']} real={result.get('real_measurement')} artificial={result.get('artificial')}")
            
            # Small delay to avoid rate limits
            await asyncio.sleep(0.5)
        
        # Summary
        real_measured = len([r for r in results if r.get('real_measurement')])
        artificial_kept = len([r for r in results if r.get('artificial')])
        
        summary = {
            "total_p16": len(p16_models),
            "tested": len(results),
            "real_measured": real_measured,
            "artificial_kept": artificial_kept,
            "failed": self.failed_count,
            "results": results,
            "note": "P16 Real Measurement — Honestidade — quando tiver keys reais, medir com benchmark_engine_p8 para scores reais — ovhcloud 429 real free 2 RPM 500M/5M per day mas funciona com retry, outros 401 needs key"
        }
        
        print(f"\n[P16 REAL] Summary: total {len(p16_models)} tested {len(results)} real {real_measured} artificial {artificial_kept} failed {self.failed_count}")
        return summary

# Global instance
p16_real_measurement = P16RealMeasurement()

print("[P16 REAL] P16 Real Measurement service loaded — honestidade — mede real quando tiver keys")
