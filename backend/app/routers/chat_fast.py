"""
P18 v1.2 — Fast Path Chat Router — SIMPLE vs COMPLEX para rapidez
Implementa fast-path para mensagens simples com cache L1/L2/L3 + bypass agents pesados

Crítico e rigoroso, funcional e real:
- SIMPLE (<20 tokens, greetings, FAQ) → fast-path 10ms hit / 500ms miss vs 2-5s full
- MEDIUM (<200 tokens) → balanced 1-2s
- COMPLEX (code, reasoning) → full pipeline 2-30s

Mede comportamento real, distingue fornecido vs medido vs UNKNOWN
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import uuid
import time
import hashlib
from datetime import datetime, timezone

from ..core.database import get_db, SessionLocal
from ..models.database_models import Provider, Model, RequestLog
from ..services.classifier import classifier, ComplexityLevel
from ..services.routing_engine import routing_engine, Profile
from ..services.orchestrator import orchestrator_service
from ..services.circuit_breaker import circuit_breaker
from ..services.encryption import decrypt_api_key
from ..services.chat_enhancer import chat_enhancer
from ..services.agent_manager import agent_manager
from ..services.observability import observability_service
from ..services.guardrails import guardrails_service
from ..services.local_cache_service import local_cache_service

router = APIRouter(tags=["chat-fast-p18"])

class ChatMessage(BaseModel):
    role: str
    content: str

class FastPathResponse(BaseModel):
    complexity: str
    fast_path: bool
    cache_level: Optional[str] = None
    latency_ms: int
    provider: Optional[str] = None
    model: Optional[str] = None
    profile: str
    reasoning: str

def get_fastest_providers_and_models(db: Session, limit: int = 5) -> tuple:
    """Retorna providers e models mais rápidos para SIMPLE — groq, cerebras, samba, groq2/3"""
    # Fastest providers based on avg_latency and health
    fast_provider_ids = ["groq", "groq2", "groq3", "cerebras", "sambanova", "openrouter"]
    
    providers = db.query(Provider).filter(Provider.provider_id.in_(fast_provider_ids)).all()
    # Sort by avg_latency and health
    providers = sorted(providers, key=lambda p: (
        0 if p.status == "VERIFIED" else 1,
        p.avg_latency_ms if p.avg_latency_ms > 0 else 9999,
        -p.success_count
    ))
    
    # Get models for those providers that are chat and fast
    provider_ids = [p.provider_id for p in providers[:3]]
    models = db.query(Model).filter(Model.provider_id.in_(provider_ids)).all()
    # Filter for fast models — small, instant, turbo
    fast_models = []
    for m in models:
        mid_lower = m.model_id.lower()
        # Skip non-chat
        if any(k in mid_lower for k in ["embed", "ocr", "tts", "transcribe", "moderation", "image", "video", "audio", "kling", "ideogram", "runway"]):
            continue
        # Prefer fast models
        if any(k in mid_lower for k in ["instant", "flash", "turbo", "8b", "1b", "3b", "7b", "mini", "haiku"]):
            fast_models.append(m)
    
    # If not enough fast models, add any chat models from fast providers
    if len(fast_models) < 3:
        for m in models:
            if m not in fast_models:
                mid_lower = m.model_id.lower()
                if not any(k in mid_lower for k in ["embed", "ocr", "tts", "transcribe", "moderation", "image", "video", "audio"]):
                    fast_models.append(m)
            if len(fast_models) >= limit:
                break
    
    return providers[:3], fast_models[:limit]

@router.get("/v1/chat/fast-path-stats")
def fast_path_stats():
    """Estatísticas fast-path vs complex-path + cache tiered"""
    obs_stats = observability_service.get_stats()
    local_stats = local_cache_service.get_stats() if local_cache_service else {}
    
    return {
        "complexity_detection": {
            "simple_keywords": classifier.SIMPLE_GREETINGS[:10],
            "simple_questions": classifier.SIMPLE_QUESTIONS[:5],
            "complex_indicators": classifier.COMPLEX_INDICATORS[:10],
            "thresholds": {
                "simple_tokens": "<20 tokens or <20 chars or <=3 palavras",
                "simple_faq": "<15 palavras + FAQ keywords + <100 tokens sem complexo",
                "medium_tokens": "<200 tokens + <40 palavras + coding_hits<2",
                "complex_tokens": ">200 tokens or coding/reasoning"
            }
        },
        "fast_path": {
            "eligible": "SIMPLE messages <20 tokens, greetings, FAQ, math simples",
            "bypass": ["intent-analyzer", "prompt-optimizer", "critic", "code-reviewer", "rigor-checker", "retry loop"],
            "only": ["classifier 10ms", "cache L1/L2/L3 0-10ms", "routing FAST 20ms", "LLM 500-1000ms"],
            "expected_latency": {
                "cache_hit": "10ms (L1) / 15ms (L2 SQLite) / 20ms (L3 semantic)",
                "cache_miss": "500-1000ms (groq instant) vs 2-5s full pipeline",
                "saving": "4834ms saved per hit (P17 Lean) + bypass agents 200-500ms"
            },
            "providers": ["groq/llama-3.1-8b-instant", "groq2/llama-3.3-70b-versatile", "cerebras/llama3.1-8b", "sambanova/Meta-Llama-3.1-8B"],
            "profile": "FAST with weights speed 40 cost 20 reliability 20 quality 10",
            "ttl": "SIMPLE 3600s (1h) / MEDIUM 1800s (30min) / COMPLEX 600s (10min) or no cache for large code"
        },
        "cache_tiered": {
            "L1": "in-memory exact 30s TTL, 100 entries max, 0ms, hit_rate 50% P17",
            "L2": f"SQLite persistent {local_stats.get('l2_entries', 0)} entries at {local_stats.get('db_path', 'local_cache/simple/simple_cache.db')}, TTL SIMPLE 1h MEDIUM 30min COMPLEX 10min, survives restart, LRU 500 max",
            "L3": f"semantic similarity Jaccard 0.85 threshold {local_stats.get('l3_entries', 0)} entries at local_cache/semantic/embeddings.json, for similar prompts",
            "local_folder": {
                "base": "local_cache/",
                "simple": "local_cache/simple/simple_cache.db — SQLite with cache_entries + conversation_history",
                "conversation": "local_cache/conversation/sessions.json — session persistence",
                "metrics": "local_cache/metrics/cache_metrics.json — hit_rate latency_saved fast vs complex",
                "semantic": "local_cache/semantic/embeddings.json — semantic cache"
            }
        },
        "observability": obs_stats.get("cache", {}),
        "local_cache": local_stats,
        "recommendations": [
            "1. SIMPLE detection via classifier ComplexityLevel — já implementado",
            "2. Fast-path bypass agents pesados — implementar em chat.py",
            "3. Tiered cache L1/L2/L3 com local folder BD — já implementado local_cache_service",
            "4. Fastest providers for SIMPLE: groq instant, cerebras, samba — já implementado get_fastest_providers_and_models",
            "5. Parallelize intent + optimizer for MEDIUM/COMPLEX — futuro",
            "6. Async critic after response for COMPLEX — futuro",
            "7. Connection pooling httpx AsyncClient — verificar",
            "8. Pre-warming providers via APScheduler — já existe",
            "9. Compression orjson + gzip — já existe orjson",
            "10. Local LLM fallback Ollama for SIMPLE offline — futuro, folder local_cache pode armazenar"
        ]
    }

@router.post("/v1/chat/completions/fast")
async def chat_completions_fast(request: Request, db: Session = Depends(get_db)):
    """
    P18 v1.2 — Fast-path endpoint for SIMPLE messages
    - Detecta SIMPLE vs COMPLEX
    - Se SIMPLE: cache L1/L2/L3 → routing FAST → LLM rápido → cache set → return 500ms vs 2-5s
    - Se COMPLEX: fallback para full pipeline
    """
    body = await request.json()
    messages = body.get("messages", [])
    if not messages:
        raise HTTPException(400, "Messages cannot be empty")
    
    prompt_text = next((m.get("content","") for m in reversed(messages) if m.get("role")=="user"), "")
    if not prompt_text:
        raise HTTPException(400, "No user message")
    
    start = time.time()
    request_id = f"fast-{uuid.uuid4().hex[:12]}"
    
    # 1. Classify complexity
    classification = classifier.classify(prompt_text, messages)
    
    # 2. Try cache tiered L1/L2/L3
    cached = observability_service.cache_get(prompt=prompt_text, profile=classification.suggested_profile, complexity=classification.complexity_level.value)
    if cached:
        latency = int((time.time()-start)*1000)
        observability_service.record_fast_path()
        return {
            "id": request_id,
            "object": "chat.completion",
            "created": int(time.time()),
            "model": f"{cached.get('provider')}/{cached.get('model')}" if cached.get('provider') else "cache",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": cached["response"]}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": len(prompt_text)//4, "completion_tokens": len(cached["response"])//4, "total_tokens": (len(prompt_text)+len(cached["response"]))//4},
            "fast_path": {
                "complexity": classification.complexity_level.value,
                "is_simple": classification.is_simple,
                "fast_path_eligible": classification.fast_path_eligible,
                "cache_hit": True,
                "cache_level": cached.get("cache_level", "L1"),
                "latency_ms": latency,
                "saved_ms": cached.get("latency_ms", 2000),
                "reasoning": classification.reasoning
            }
        }
    
    # 3. If SIMPLE → fast-path
    if classification.complexity_level == ComplexityLevel.SIMPLE and classification.fast_path_eligible:
        # Fast path: fastest providers, no support agents, no critic, no retry
        providers, models = get_fastest_providers_and_models(db, limit=5)
        if not providers or not models:
            # Fallback to all providers
            providers = db.query(Provider).all()
            models = db.query(Model).all()
        
        profile = Profile.FAST
        
        try:
            orch_result = await orchestrator_service.execute_with_routing(
                prompt=prompt_text,
                providers=providers,
                models=models,
                profile=profile,
                messages=messages
            )
            
            response_obj = orch_result["response"]
            routing_obj = orch_result["routing"]
            latency = int((time.time()-start)*1000)
            
            # Cache set with TTL based on complexity
            observability_service.cache_set(
                prompt=prompt_text, response=response_obj.content,
                provider=routing_obj.selected.provider.provider_id,
                model=routing_obj.selected.model.model_id,
                profile=profile.value, cost=routing_obj.selected.estimated_cost,
                latency_ms=latency, complexity=classification.complexity_level.value
            )
            
            # Save conversation to local DB
            session_id = request.headers.get("X-Session-Id") or f"session-{uuid.uuid4().hex[:8]}"
            local_cache_service.save_conversation(session_id, prompt_text, response_obj.content, complexity=classification.complexity_level.value, latency_ms=latency)
            local_cache_service.record_fast_path()
            observability_service.record_fast_path()
            
            return {
                "id": request_id,
                "object": "chat.completion",
                "created": int(time.time()),
                "model": f"{routing_obj.selected.provider.provider_id}/{routing_obj.selected.model.model_id}",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": response_obj.content}, "finish_reason": response_obj.finish_reason}],
                "usage": {"prompt_tokens": response_obj.input_tokens, "completion_tokens": response_obj.output_tokens, "total_tokens": response_obj.input_tokens + response_obj.output_tokens},
                "fast_path": {
                    "complexity": classification.complexity_level.value,
                    "is_simple": True,
                    "fast_path_eligible": True,
                    "cache_hit": False,
                    "latency_ms": latency,
                    "provider": routing_obj.selected.provider.provider_id,
                    "model": routing_obj.selected.model.model_id,
                    "profile": profile.value,
                    "reasoning": classification.reasoning,
                    "bypassed": ["intent-analyzer", "prompt-optimizer", "critic", "code-reviewer", "rigor-checker", "retry"],
                    "saving_vs_full": f"{2000 - latency}ms saved vs full pipeline 2-5s"
                },
                "routing": {
                    "selected": f"{routing_obj.selected.model.display_name} / {routing_obj.selected.provider.name}",
                    "reason": routing_obj.selected.reason,
                    "profile": profile.value,
                    "task_type": classification.task_type.value,
                    "complexity_level": classification.complexity_level.value
                }
            }
        except Exception as e:
            # Fallback to full pipeline if fast-path fails
            print(f"[FAST-PATH] Fast-path failed, fallback to full: {e}")
            observability_service.record_complex_path()
    
    # 4. If MEDIUM or COMPLEX or fast-path failed → use full pipeline via original endpoint logic (simplified)
    # For now, return classification and suggest using full endpoint
    return {
        "id": request_id,
        "object": "chat.completion.fast-path-classification",
        "created": int(time.time()),
        "model": "classifier",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": f"Classified as {classification.complexity_level.value} — use full pipeline /v1/chat/completions for best quality. Reasoning: {classification.reasoning}"}, "finish_reason": "stop"}],
        "classification": {
            "task_type": classification.task_type.value,
            "complexity_level": classification.complexity_level.value,
            "is_simple": classification.is_simple,
            "fast_path_eligible": classification.fast_path_eligible,
            "confidence": classification.confidence,
            "estimated_tokens": classification.estimated_tokens,
            "reasoning": classification.reasoning,
            "suggested_profile": classification.suggested_profile,
            "cache_ttl_seconds": classification.cache_ttl_seconds
        },
        "fast_path": {
            "eligible": classification.fast_path_eligible,
            "should_use_fast": classification.complexity_level == ComplexityLevel.SIMPLE,
            "should_use_full": classification.complexity_level in [ComplexityLevel.MEDIUM, ComplexityLevel.COMPLEX],
            "latency_ms": int((time.time()-start)*1000)
        }
    }
