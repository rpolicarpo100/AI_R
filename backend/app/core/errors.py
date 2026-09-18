"""
P0.3 — Error Contract — 413 + 429 + OpenAI Format
Antes: todos provider failures viram 500 All providers failed, mesmo se todos 429 → cliente devia receber 429
       falta 413 Request Too Large para request > todos modelos
Depois: contrato claro 400/401/403/404/408/413/429/500/502/503/504 com formato OpenAI-compatible + Retry-After
"""

from fastapi import HTTPException
from typing import Optional, List, Dict, Any
import time

# OpenAI-compatible error format
def openai_error(
    message: str,
    type: str = "invalid_request_error",
    code: Optional[str] = None,
    param: Optional[str] = None
) -> Dict[str, Any]:
    """Formato OpenAI-compatible error"""
    err = {
        "message": message,
        "type": type,
    }
    if code:
        err["code"] = code
    if param:
        err["param"] = param
    return {"error": err}

# ===== 400 Bad Request =====
def bad_request(message: str, code: str = "bad_request", param: Optional[str] = None):
    raise HTTPException(
        status_code=400,
        detail=openai_error(message, type="invalid_request_error", code=code, param=param)
    )

def validation_error(message: str, param: Optional[str] = None):
    raise HTTPException(
        status_code=400,
        detail=openai_error(message, type="invalid_request_error", code="validation_error", param=param)
    )

# ===== 401 Unauthorized =====
def unauthorized(message: str = "Invalid authentication"):
    raise HTTPException(
        status_code=401,
        detail=openai_error(message, type="invalid_request_error", code="invalid_api_key")
    )

# ===== 403 Forbidden =====
def forbidden(message: str = "Forbidden"):
    raise HTTPException(
        status_code=403,
        detail=openai_error(message, type="invalid_request_error", code="forbidden")
    )

# ===== 404 Not Found =====
def not_found(message: str, code: str = "not_found"):
    raise HTTPException(
        status_code=404,
        detail=openai_error(message, type="invalid_request_error", code=code)
    )

def model_not_found(model_id: str):
    raise HTTPException(
        status_code=404,
        detail=openai_error(
            f"The model '{model_id}' does not exist or you do not have access to it.",
            type="invalid_request_error",
            code="model_not_found",
            param="model"
        )
    )

# ===== 408 Timeout =====
def request_timeout(message: str = "Request timed out"):
    raise HTTPException(
        status_code=408,
        detail=openai_error(message, type="timeout_error", code="timeout")
    )

# ===== 413 Request Too Large — P0 NOVO =====
def request_too_large(
    estimated_tokens: int,
    max_limit: int,
    requested_chars: Optional[int] = None,
    message: Optional[str] = None
):
    """
    P0 — 413 Request Too Large
    Quando request > todos os modelos disponíveis ou > MAX_TOTAL_CHARS
    Nunca truncar silenciosamente — rejeitar com erro claro OpenAI-compatible
    """
    if not message:
        if requested_chars:
            message = f"Request too large: {requested_chars} chars / {estimated_tokens} tokens exceeds maximum context length for all available models (max {max_limit} tokens). Try smaller prompt, split into multiple requests, or use model with larger context."
        else:
            message = f"Request too large: {estimated_tokens} tokens exceeds maximum context length for all available models (max {max_limit} tokens). Requested {estimated_tokens} > limit {max_limit}. Try smaller prompt or model with larger context."
    
    raise HTTPException(
        status_code=413,
        detail=openai_error(
            message,
            type="invalid_request_error",
            code="context_length_exceeded",
            param="messages"
        )
    )

def prompt_too_large(chars: int, limit: int):
    """Para compatibilidade — agora usa policy centralizada, mas retorna 413 se > limite, 400 se validation"""
    # Se chars > limit e limit é safety guardrail, retorna 413 para ser claro
    # Mas para manter compatibilidade OpenAI, usamos 400 com code context_length_exceeded?
    # Decisão P0: se chars > MAX_TOTAL_CHARS (100000) → 413, se apenas > MAX_PROMPT_CHARS mas < total → 400
    from .policy import MAX_TOTAL_CHARS
    if chars > MAX_TOTAL_CHARS:
        request_too_large(
            estimated_tokens=chars // 4,
            max_limit=MAX_TOTAL_CHARS // 4,
            requested_chars=chars,
            message=f"Messages too large: {chars} chars > {limit} limit. Try smaller prompt."
        )
    else:
        bad_request(
            f"Prompt too large: {chars} chars > {limit} limit. Last user message too large.",
            code="context_length_exceeded",
            param="messages"
        )

# ===== 429 Rate Limited — P0 NOVO =====
def rate_limited(
    message: str = "Rate limit exceeded",
    retry_after: Optional[int] = None,
    fallback_reasons: Optional[List[str]] = None
):
    """
    P0 — 429 Rate Limited
    Quando todos providers rate limited
    Inclui Retry-After header se disponível
    """
    detail = openai_error(
        message,
        type="rate_limit_error",
        code="rate_limit_exceeded"
    )
    if fallback_reasons:
        detail["error"]["fallback_reasons"] = fallback_reasons[:5]
    
    headers = {}
    if retry_after:
        headers["Retry-After"] = str(retry_after)
    
    raise HTTPException(
        status_code=429,
        detail=detail,
        headers=headers if headers else None
    )

def all_providers_rate_limited(fallback_reasons: List[str], retry_after: Optional[int] = None):
    """Quando todos providers falharam com 429"""
    message = f"All providers rate limited. Tried {len(fallback_reasons)} providers, all rate limited. Reasons: {'; '.join(fallback_reasons[:3])}. Try again later."
    if retry_after:
        message += f" Retry after {retry_after}s."
    rate_limited(message, retry_after=retry_after, fallback_reasons=fallback_reasons)

# ===== 500 Internal =====
def internal_error(message: str = "Internal server error", details: Optional[str] = None):
    detail = openai_error(message, type="server_error", code="internal_error")
    if details:
        detail["error"]["details"] = details[:500]
    raise HTTPException(status_code=500, detail=detail)

def orchestrator_failed(error: str, trace: Optional[str] = None):
    message = f"Orchestrator failed: {error[:500]}"
    detail = openai_error(message, type="server_error", code="orchestrator_failed")
    if trace:
        detail["error"]["trace"] = trace[:1000]
    raise HTTPException(status_code=500, detail=detail)

# ===== 502 Bad Gateway =====
def bad_gateway(message: str = "Bad gateway", provider: Optional[str] = None):
    detail = openai_error(message, type="server_error", code="bad_gateway")
    if provider:
        detail["error"]["provider"] = provider
    raise HTTPException(status_code=502, detail=detail)

# ===== 503 Service Unavailable =====
def service_unavailable(message: str = "Service unavailable", provider: Optional[str] = None):
    detail = openai_error(message, type="server_error", code="service_unavailable")
    if provider:
        detail["error"]["provider"] = provider
    raise HTTPException(status_code=503, detail=detail)

def no_providers_available(message: str = "No providers or models configured"):
    raise HTTPException(
        status_code=503,
        detail=openai_error(
            message,
            type="server_error",
            code="no_providers_available"
        )
    )

def provider_circuit_open(provider_id: str):
    raise HTTPException(
        status_code=503,
        detail=openai_error(
            f"Provider {provider_id} circuit open — too many failures, cooling down. Try another provider or later.",
            type="server_error",
            code="circuit_open"
        )
    )

# ===== 504 Gateway Timeout =====
def gateway_timeout(message: str = "Gateway timeout", provider: Optional[str] = None):
    detail = openai_error(message, type="timeout_error", code="gateway_timeout")
    if provider:
        detail["error"]["provider"] = provider
    raise HTTPException(status_code=504, detail=detail)

# ===== Helper to map provider errors to correct HTTP status =====
def map_provider_error_to_http(
    error_msg: str,
    fallback_reasons: List[str],
    fallback_chain: List[Dict],
    requested_tokens: int = 0,
    model_context_limit: int = 0
):
    """
    Mapeia erro de provider para HTTP status correto — P0 error contract
    Antes: tudo 500 All providers failed
    Depois: distingue 413, 429, 503, 504, etc
    """
    error_lower = error_msg.lower()
    
    # Check if all rate limited
    rate_limited_count = sum(1 for r in fallback_reasons if "rate_limit" in r.lower() or "429" in r)
    if rate_limited_count > 0 and rate_limited_count == len(fallback_reasons) and len(fallback_reasons) > 0:
        # All rate limited → 429
        # Try to parse Retry-After from error
        retry_after = None
        for reason in fallback_reasons:
            if "retry-after" in reason.lower() or "retry after" in reason.lower():
                # Try extract number
                import re
                m = re.search(r'retry.*?(\d+)', reason.lower())
                if m:
                    retry_after = int(m.group(1))
                    break
        all_providers_rate_limited(fallback_reasons, retry_after=retry_after)
    
    # Check if context too large for all models
    context_filtered = [r for r in fallback_reasons if "context" in r.lower() or "requested_tokens" in r.lower() or "model_context_limit" in r.lower()]
    if context_filtered and len(context_filtered) == len(fallback_chain):
        # All filtered by context → 413
        max_limit = model_context_limit or 0
        # Try find max limit from chain
        for item in fallback_chain:
            if item.get("model_context_limit", 0) > max_limit:
                max_limit = item.get("model_context_limit", 0)
        request_too_large(
            estimated_tokens=requested_tokens,
            max_limit=max_limit or 128000,
            message=f"Request too large: {requested_tokens} tokens exceeds all available models (max {max_limit} tokens). Try smaller prompt or model with larger context. Chain: {fallback_chain[:2]}"
        )
    
    # Check circuit open
    circuit_open_count = sum(1 for r in fallback_reasons if "circuit open" in r.lower())
    if circuit_open_count > 0 and circuit_open_count == len(fallback_reasons):
        service_unavailable(
            f"All providers circuit open — too many failures. Reasons: {'; '.join(fallback_reasons[:3])}",
            provider="all"
        )
    
    # Default: 500 with details
    orchestrator_failed(
        error=f"All providers failed. Chain: {fallback_chain} | Reasons: {fallback_reasons} | Requested tokens: {requested_tokens} Limit: {model_context_limit}",
        trace=error_msg
    )

print(f"[ERRORS P0] Loaded error contract: 400/401/403/404/408/413/429/500/502/503/504 with OpenAI-compatible format + Retry-After + 413 Request Too Large")
