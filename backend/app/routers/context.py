"""
P8 — Context Compiler API — P0/P1/P2
Endpoints para compilação de contexto poderoso contínuo fluido
"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import time
from ..core.database import get_db
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/context", tags=["context"])

class ContextCompileRequest(BaseModel):
    messages: List[Dict[str, Any]]
    tools: Optional[List[Dict]] = None
    system: Optional[str] = None
    model_context_limit: Optional[int] = 128000
    max_output_tokens: Optional[int] = 2000
    profile: Optional[str] = "BEST"
    use_cache: Optional[bool] = True

@router.post("/compile")
@limiter.limit("60/minute")
async def compile_context(req: ContextCompileRequest, request: Request, db: Session = Depends(get_db)):
    """P8 P0 — Context Compiler — compila contexto com budget, dedup, relevância, compressão hierárquica, limites, preservação críticas"""
    start = time.time()
    
    try:
        from ..services.context_compiler import context_compiler
        
        compiled = context_compiler.compile(
            messages=req.messages,
            tools=req.tools,
            system=req.system,
            model_context_limit=req.model_context_limit,
            max_output_tokens=req.max_output_tokens,
            profile=req.profile,
            use_cache=req.use_cache
        )
        
        latency_ms = int((time.time() - start) * 1000)
        
        return {
            "compiled_messages": compiled.compiled_messages,
            "original_count": len(req.messages),
            "compiled_count": len(compiled.compiled_messages),
            "token_budget": {
                "model_limit": compiled.token_budget.model_context_limit,
                "max_output": compiled.token_budget.max_output_tokens,
                "estimated_input": compiled.token_budget.total_estimated_input,
                "is_within_limit": compiled.token_budget.is_within_limit,
                "available_history": compiled.token_budget.available_for_history,
                "available_prompt": compiled.token_budget.available_for_prompt,
                "breakdown": compiled.token_budget.budget_breakdown
            },
            "deduplication": compiled.dedup_info,
            "relevance": {
                "scores": compiled.relevance_scores[:10],
                "top_score": compiled.relevance_scores[0]["total_score"] if compiled.relevance_scores else 0
            },
            "compression": compiled.compression_info,
            "preserved_critical": {
                "count": len(compiled.preserved_critical),
                "items": compiled.preserved_critical[:5]
            },
            "provenance": {
                "count": len(compiled.provenance),
                "items": compiled.provenance[:5]
            },
            "conflicts": {
                "count": len(compiled.conflicts),
                "items": compiled.conflicts
            },
            "quality_metrics": compiled.quality_metrics,
            "latency_ms": compiled.latency_ms,
            "total_latency_ms": latency_ms,
            "version": "P8 P0 — Context Compiler — budget, dedup, relevance, hierarchical compression, limits, critical preservation"
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "error": str(e)[:500],
            "version": "P8 error"
        }

@router.get("/cache/stats")
async def cache_stats():
    """P1 — cache dos contextos já compilados"""
    from ..services.context_compiler import context_compiler
    return {
        "cache": context_compiler.get_cache_stats(),
        "patterns": context_compiler.get_pattern_stats(),
        "version": "P8 P1 — cache compilados + aprendizagem padrões"
    }

@router.post("/detect/conflicts")
@limiter.limit("60/minute")
async def detect_conflicts(req: ContextCompileRequest, request: Request):
    """P1 — detecção de conflitos/contradições"""
    from ..services.context_compiler import context_compiler
    
    conflicts = context_compiler._detect_conflicts(req.messages)
    
    return {
        "conflicts": conflicts,
        "count": len(conflicts),
        "has_conflicts": len(conflicts) > 0,
        "version": "P8 P1 — detecção conflitos"
    }

@router.post("/provenance")
async def get_provenance(req: ContextCompileRequest):
    """P1 — provenance das informações"""
    from ..services.context_compiler import context_compiler
    
    # Compile to get provenance
    compiled = context_compiler.compile(
        messages=req.messages,
        tools=req.tools,
        system=req.system,
        model_context_limit=req.model_context_limit,
        max_output_tokens=req.max_output_tokens,
        profile=req.profile,
        use_cache=False
    )
    
    return {
        "provenance": compiled.provenance,
        "count": len(compiled.provenance),
        "version": "P8 P1 — provenance"
    }

@router.get("/metrics/quality")
async def quality_metrics():
    """P2 — métricas de qualidade da compilação + aprendizagem padrões"""
    from ..services.context_compiler import context_compiler
    
    cache_stats = context_compiler.get_cache_stats()
    pattern_stats = context_compiler.get_pattern_stats()
    
    return {
        "cache": cache_stats,
        "patterns": {
            "compilations": pattern_stats["compilations"],
            "avg_compression_ratio": round(pattern_stats["avg_compression_ratio"],1),
            "avg_relevance_score": round(pattern_stats["avg_relevance_score"],1),
            "avg_dedup_saved": pattern_stats["avg_dedup_saved"]
        },
        "optimizations": {
            "cost_latency": "P2 — saved tokens = saved cost, cache hit = 0ms latency vs 10-50ms compile",
            "routing_size_complexity": "P2 — small SIMPLE→FAST, large COMPLEX→BEST/LONG_CONTEXT, based on token budget + classifier",
            "learning_patterns": "P2 — avg_compression_ratio, avg_relevance, avg_dedup_saved learned over compilations"
        },
        "version": "P8 P2 — optimização custo/latência, aprendizagem padrões, routing tamanho/complexidade, métricas qualidade"
    }

@router.post("/optimize/cost-latency")
async def optimize_cost_latency(req: ContextCompileRequest):
    """P2 — optimização custo/latência + routing baseado tamanho/complexidade"""
    from ..services.context_compiler import context_compiler
    from ..services.classifier import classifier
    
    start = time.time()
    
    # Compile
    compiled = context_compiler.compile(
        messages=req.messages,
        tools=req.tools,
        system=req.system,
        model_context_limit=req.model_context_limit,
        max_output_tokens=req.max_output_tokens,
        profile=req.profile,
        use_cache=True
    )
    
    # Classify for routing
    last_prompt = req.messages[-1].get('content','') if req.messages else ''
    classification = classifier.classify(last_prompt, req.messages[:-1])
    
    # Routing based on size/complexity P2
    total_chars = sum(len(str(m.get('content',''))) for m in req.messages)
    estimated_tokens = compiled.token_budget.total_estimated_input
    
    # Determine optimal profile based on size/complexity
    if classification.complexity_level.value == "SIMPLE" and estimated_tokens < 2000:
        optimal_profile = "FAST"
        reason = f"SIMPLE {classification.complexity_level} + small {estimated_tokens} tokens <2000 → FAST low latency cost"
    elif estimated_tokens > 15000 or classification.task_type.value == "LONG_CONTEXT":
        optimal_profile = "LONG_CONTEXT"
        reason = f"LARGE {estimated_tokens} tokens >15000 or LONG_CONTEXT → LONG_CONTEXT profile 200k"
    elif classification.task_type.value == "CODING":
        optimal_profile = "CODING"
        reason = f"CODING task_type → CODING profile 150k coding-first"
    elif classification.task_type.value == "TOOL_CALLING":
        optimal_profile = "CLINE_CODING"
        reason = f"TOOL_CALLING → CLINE_CODING 200k tool calling"
    else:
        optimal_profile = "BEST"
        reason = f"Default BEST for {classification.task_type} {estimated_tokens} tokens"
    
    # Cost/latency optimization
    saved_tokens = compiled.quality_metrics["saved_tokens"]
    # Rough cost: $0.001 per 1k tokens saved
    saved_cost = saved_tokens / 1000 * 0.001
    # Latency: cache hit 0ms vs compile 10-50ms
    cache_stats = context_compiler.get_cache_stats()
    
    latency_ms = int((time.time() - start) * 1000)
    
    return {
        "original": {
            "messages": len(req.messages),
            "chars": total_chars,
            "estimated_tokens": estimated_tokens
        },
        "compiled": {
            "messages": len(compiled.compiled_messages),
            "chars": compiled.quality_metrics["compiled_chars"],
            "saved_chars": compiled.quality_metrics["saved_chars"],
            "saved_tokens": saved_tokens,
            "quality": compiled.quality_metrics["overall_quality"]
        },
        "routing": {
            "optimal_profile": optimal_profile,
            "reason": reason,
            "classification": {
                "task_type": classification.task_type.value,
                "complexity_level": classification.complexity_level.value,
                "is_simple": classification.is_simple,
                "estimated_tokens": classification.estimated_tokens,
                "suggested_profile": classification.suggested_profile
            },
            "size_based": {
                "total_chars": total_chars,
                "estimated_tokens": estimated_tokens,
                "is_large": total_chars > 50000,
                "model_limit": req.model_context_limit
            }
        },
        "cost_latency": {
            "saved_tokens": saved_tokens,
            "saved_cost_estimate": f"${saved_cost:.6f}",
            "cache_hit_rate": cache_stats["hit_rate"],
            "compilation_latency_ms": compiled.latency_ms,
            "total_latency_ms": latency_ms,
            "optimization": f"Cache {cache_stats['hit_rate']}% hit saves {compiled.latency_ms}ms, dedup saved {compiled.dedup_info['saved_tokens']} tokens, compression saved {compiled.compression_info.get('total_saved',0)//4} tokens"
        },
        "quality_metrics": compiled.quality_metrics,
        "version": "P8 P2 — cost/latency + routing size/complexity"
    }
