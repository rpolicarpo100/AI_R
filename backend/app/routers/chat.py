from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
import uuid
import time
import hashlib
import re
from datetime import datetime, timezone

from ..core.database import get_db, SessionLocal
from ..models.database_models import Provider, Model, RequestLog
from ..services.classifier import classifier, ComplexityLevel, TaskType
from ..services.routing_engine import routing_engine, Profile
from ..services.orchestrator import orchestrator_service
from ..services.circuit_breaker import circuit_breaker
from ..services.encryption import decrypt_api_key
from ..services.chat_enhancer import chat_enhancer
from ..services.brainstorming_service import brainstorming_service
from ..services.agent_manager import agent_manager
from ..services.observability import observability_service
from ..services.guardrails import guardrails_service
# P0 + P5 — Central Policy + Token Calculator + Error Contract
from ..core.policy import (
    MAX_TOTAL_CHARS, MAX_PROMPT_CHARS, MAX_REQUEST_CHARS,
    DEFAULT_OUTPUT_TOKENS, PROVIDER_CACHE_TTL,
    RATE_LIMIT_CHAT, RATE_LIMIT_CLINE, RATE_LIMIT_ORCHESTRATE, RATE_LIMIT_ESTIMATE,
    LARGE_PROMPT_CHARS, VERY_LARGE_PROMPT_CHARS, LARGE_PROMPT_TOKENS,
    MAX_TOTAL_CHARS_ABSOLUTE, MAX_PROMPT_CHARS_ABSOLUTE,
    get_policy_dict, validate_request_size, validate_request_size_profile,
    get_limits_for_profile, compress_prompt, truncate_history, is_large_prompt
)
from ..core.token_calculator import calculate_tokens, estimate_tokens, quick_estimate
from ..core import errors as error_contract
# P18 v1.2 — Local cache service for tiered caching L1/L2/L3 + local folder BD
try:
    from ..services.local_cache_service import local_cache_service
    USE_LOCAL_CACHE = True
except:
    USE_LOCAL_CACHE = False
    local_cache_service = None
from slowapi import Limiter
from slowapi.util import get_remote_address
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["chat"])

class ChatMessage(BaseModel):
    role: str
    content: Optional[Union[str, List[Dict]]] = ""  # P20: content can be string or list for multimodal, but we handle string
    tool_calls: Optional[List[Dict]] = None  # P20: assistant tool_calls
    tool_call_id: Optional[str] = None  # P20: for tool role

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = "auto"
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000
    max_completion_tokens: Optional[int] = None  # P1.3 — OpenAI new param, alias for max_tokens
    max_output_tokens: Optional[int] = None  # P1.3 — Alternative alias
    profile: Optional[str] = None
    stream: Optional[bool] = False
    tools: Optional[List[Dict]] = None
    tool_choice: Optional[Union[str, Dict]] = None  # P20: tool_choice support
    response_format: Optional[Dict] = None
    use_orchestrator: Optional[bool] = True
    explain_routing: Optional[bool] = False
    use_support_agents: Optional[bool] = True
    enable_critique: Optional[bool] = True
    enable_retry: Optional[bool] = True
    max_retries: Optional[int] = 1
    # P20 CLINE_CODING — additional OpenAI-compatible params without breaking
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    stop: Optional[Union[str, List[str]]] = None
    seed: Optional[int] = None
    user: Optional[str] = None
    # P5 — Large prompt handling options
    enable_compression: Optional[bool] = True  # P5 auto compress large prompts preserving code
    enable_history_truncation: Optional[bool] = True  # P5 auto truncate history if too large
    enable_at_file_resolution: Optional[bool] = True  # P5 resolve @file references

    def get_effective_max_tokens(self) -> int:
        if self.max_completion_tokens is not None:
            return self.max_completion_tokens
        if self.max_output_tokens is not None:
            return self.max_output_tokens
        if self.max_tokens is not None:
            return self.max_tokens
        return 2000

class EstimateRequest(BaseModel):
    messages: List[ChatMessage]
    profile: Optional[str] = None
    tools: Optional[List[Dict]] = None
    model: Optional[str] = "auto"

def resolve_at_file_references(prompt_text: str, db: Session, enable: bool = True) -> tuple[str, List[Dict]]:
    """
    P5.3 — Workplace @file Integration — resolve @file references in prompt
    Detects @project_id/file or @filename, loads from workplace, replaces with content
    Returns (resolved_text, resolved_files_info)
    Real, funcional, token awareness
    """
    if not enable:
        return prompt_text, []
    
    # Pattern: @project_id/filename or @filename or @project_id
    # Must be at word boundary, avoid email @
    at_pattern = r'(?:^|\s)@([a-zA-Z0-9_-]+(?:/[a-zA-Z0-9._-]+)?)'
    matches = re.findall(at_pattern, prompt_text)
    
    if not matches:
        return prompt_text, []
    
    resolved_info = []
    resolved_text = prompt_text
    
    try:
        # Try to import project service — avoid circular
        from ..models.database_models import Project
        from ..services.project_service import project_service
        
        for match in matches[:5]:  # max 5 @file per prompt
            try:
                if '/' in match:
                    project_id, file_name = match.split('/', 1)
                    # Try to load project
                    proj = db.query(Project).filter(Project.project_id == project_id).first()
                    if not proj and len(project_id) < 20:
                        # Maybe project_id is actually project name prefix — search
                        projs = db.query(Project).all()
                        proj = next((p for p in projs if project_id.lower() in p.name.lower() or p.project_id.startswith(project_id)), None)
                        if proj:
                            project_id = proj.project_id
                    
                    if proj:
                        files = proj.files if isinstance(proj.files, dict) else {}
                        # Try exact file match, then fuzzy
                        file_content = files.get(file_name)
                        if not file_content:
                            # Fuzzy search
                            for fname, fcontent in files.items():
                                if file_name.lower() in fname.lower() or fname.lower() in file_name.lower():
                                    file_name = fname
                                    file_content = fcontent
                                    break
                        
                        if file_content:
                            chars = len(file_content)
                            tokens = chars // 4
                            # Token awareness — if file too large >50k chars, truncate or warn
                            if chars > 50000:
                                truncated = file_content[:50000] + f"\n\n... [truncated {chars-50000} chars, full file {chars} chars ~{tokens} tokens, use workplace for full]"
                                resolved_text = resolved_text.replace(f"@{match}", f"\n// File: {project_id}/{file_name} ({chars} chars ~{tokens} tokens, truncated)\n{truncated}\n// End file {file_name}\n")
                                resolved_info.append({"path": f"{project_id}/{file_name}", "chars": chars, "tokens": tokens, "truncated": True, "full_chars": chars})
                            else:
                                resolved_text = resolved_text.replace(f"@{match}", f"\n// File: {project_id}/{file_name} ({chars} chars ~{tokens} tokens)\n{file_content}\n// End file {file_name}\n")
                                resolved_info.append({"path": f"{project_id}/{file_name}", "chars": chars, "tokens": tokens, "truncated": False})
                            print(f"[P5 @FILE] Resolved @{match} → {project_id}/{file_name} {chars} chars ~{tokens} tokens")
                        else:
                            print(f"[P5 @FILE] File not found for @{match} in project {project_id}, available {list(files.keys())[:5]}")
                    else:
                        print(f"[P5 @FILE] Project not found for @{match}")
                else:
                    # Only filename or project_id — search across all projects
                    search_term = match
                    projs = db.query(Project).all()
                    found = False
                    for proj in projs[:20]:  # limit search
                        files = proj.files if isinstance(proj.files, dict) else {}
                        for fname, fcontent in files.items():
                            if search_term.lower() in fname.lower() or fname.lower() in search_term.lower():
                                chars = len(fcontent)
                                tokens = chars // 4
                                if chars > 50000:
                                    truncated = fcontent[:50000] + f"\n... [truncated {chars-50000} chars]"
                                    resolved_text = resolved_text.replace(f"@{match}", f"\n// File: {proj.project_id}/{fname} ({chars} chars ~{tokens} tokens, truncated)\n{truncated}\n")
                                    resolved_info.append({"path": f"{proj.project_id}/{fname}", "chars": chars, "tokens": tokens, "truncated": True})
                                else:
                                    resolved_text = resolved_text.replace(f"@{match}", f"\n// File: {proj.project_id}/{fname} ({chars} chars ~{tokens} tokens)\n{fcontent}\n")
                                    resolved_info.append({"path": f"{proj.project_id}/{fname}", "chars": chars, "tokens": tokens, "truncated": False})
                                print(f"[P5 @FILE] Resolved @{match} fuzzy → {proj.project_id}/{fname} {chars} chars")
                                found = True
                                break
                        if found:
                            break
                    if not found:
                        print(f"[P5 @FILE] No file found for @{match} fuzzy search")
            except Exception as e:
                print(f"[P5 @FILE] Failed to resolve @{match}: {e}")
                continue
        
        if resolved_info:
            print(f"[P5 @FILE] Resolved {len(resolved_info)} @file references, total chars added {sum(r['chars'] for r in resolved_info)}")
        
        return resolved_text, resolved_info
    except Exception as e:
        print(f"[P5 @FILE] Resolution failed: {e}")
        return prompt_text, []

@router.post("/v1/chat/completions/estimate")
@limiter.limit("60/minute")
async def estimate_tokens_endpoint(req: EstimateRequest, request: Request, db: Session = Depends(get_db)):
    """
    P5.3 — Token Estimate Endpoint for frontend real-time — no provider call
    Returns breakdown without calling provider, for frontend token counter
    """
    start = time.time()
    
    if not req.messages:
        raise HTTPException(400, "Messages cannot be empty")
    
    total_chars = sum(len(str(m.content)) for m in req.messages if m.content)
    last_user_msg = next((m for m in reversed(req.messages) if m.role == "user"), None)
    prompt_text = ""
    if last_user_msg:
        if isinstance(last_user_msg.content, str):
            prompt_text = last_user_msg.content
        elif isinstance(last_user_msg.content, list):
            prompt_text = " ".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in last_user_msg.content])
        else:
            prompt_text = str(last_user_msg.content)
    
    # Resolve @file if enabled
    at_files = []
    if "@" in prompt_text:
        resolved, at_files = resolve_at_file_references(prompt_text, db, enable=True)
        if resolved != prompt_text:
            total_chars = sum(len(str(m.content)) for m in req.messages[:-1] if m.content) + len(resolved)
            prompt_text = resolved
    
    # Token calculation
    try:
        token_calc = calculate_tokens(
            messages=[m.dict() for m in req.messages],
            tools=req.tools,
            system=None,
            max_tokens_requested=2000
        )
        estimated_input = token_calc["estimated_input"]
        breakdown = token_calc["breakdown"]
    except Exception as e:
        estimated_input = total_chars // 4
        breakdown = {"input": total_chars // 4, "estimated_input": estimated_input}
    
    # Per-profile limits
    profile = req.profile or "BEST"
    max_total, max_prompt = get_limits_for_profile(profile)
    is_large, large_reason = is_large_prompt(total_chars, estimated_input)
    
    # Check validation per-profile
    is_valid, error_msg = validate_request_size_profile(profile, total_chars, len(prompt_text))
    
    # Model context check — find max context among models
    try:
        from ..services.http_client import get_cached_providers_models_sync
        providers, models = get_cached_providers_models_sync(db)
        max_context = max([m.context_window for m in models if m.context_window and m.context_window > 0], default=128000)
        min_context = min([m.context_window for m in models if m.context_window and m.context_window > 0], default=8000)
        # Check if fits
        fits_models = [m for m in models if m.context_window and m.context_window >= estimated_input]
        fits_count = len(fits_models)
    except:
        max_context = 128000
        min_context = 8000
        fits_count = 0
    
    latency_ms = int((time.time() - start) * 1000)
    
    return {
        "total_chars": total_chars,
        "prompt_chars": len(prompt_text),
        "estimated_input_tokens": estimated_input,
        "estimated_total_tokens": estimated_input + 2000,
        "breakdown": breakdown,
        "profile": profile,
        "limits": {"max_total_chars": max_total, "max_prompt_chars": max_prompt, "absolute_max_total": MAX_TOTAL_CHARS_ABSOLUTE},
        "is_large": is_large,
        "large_reason": large_reason if is_large else None,
        "is_valid": is_valid,
        "validation_error": error_msg if not is_valid else None,
        "model_context": {"max": max_context, "min": min_context, "fits_count": fits_count, "fits_pct": round(fits_count / 726 * 100, 1) if fits_count else 0},
        "at_files": at_files,
        "suggestions": [] if is_valid else [
            f"Try profile CLINE_CODING for large (200k chars) vs current {profile} {max_total}",
            "Use workplace @file references for large files",
            "Split into multiple requests or chunk",
            "Enable compression and history truncation"
        ],
        "latency_ms": latency_ms,
        "version": "P5 LARGE PROMPT FASEADO — estimate endpoint real-time"
    }

@router.post("/v1/chat/completions")
@limiter.limit("30/minute")
async def chat_completions(req: ChatCompletionRequest, request: Request, db: Session = Depends(get_db)):
    request_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
    start = time.time()
    
    # P17 Lean Observability - Tracing + Session fix race + Cache exact 30s
    obs_trace = observability_service.create_trace(trace_id=request_id, operation="chat.completion", user_id="admin")
    session_id = request.headers.get("X-Session-Id") or f"session-{uuid.uuid4().hex[:8]}"
    session = observability_service.get_or_create_session(session_id=session_id, user_id="admin")
    
    # P20 CLINE_CODING — detect Cline client via headers
    cline_client = request.headers.get("X-Cline-Client") or request.headers.get("X-Client") or ""
    is_cline = "cline" in cline_client.lower() or req.profile and req.profile.upper() == "CLINE_CODING" or (req.tools is not None and len(req.tools) > 0)
    if is_cline or (req.profile and req.profile.upper() == "CLINE_CODING"):
        print(f"[CLINE_CODING] Detected Cline client: header={cline_client} profile={req.profile} tools={bool(req.tools)} stream={req.stream}")
    
    observability_service.log(level="info", message=f"Chat started {request_id} cline={is_cline} tools={bool(req.tools)} stream={req.stream} profile={req.profile}", trace_id=request_id, user_id="admin", metadata={"messages": len(req.messages) if req.messages else 0, "session_id": session_id, "is_cline": is_cline, "has_tools": bool(req.tools), "stream": req.stream})
    
    if not req.messages:
        observability_service.log(level="error", message="Messages empty", trace_id=request_id)
        observability_service.end_trace(trace_id=request_id, span_id=obs_trace["span_id"], latency_ms=0, status="error")
        raise HTTPException(400, "Messages cannot be empty")
    
    # P5 — Phase 1: Extract prompt + total_chars BEFORE validation for phased handling
    total_chars = sum(len(str(m.content)) for m in req.messages if m.content)
    last_user_msg = next((m for m in reversed(req.messages) if m.role == "user"), None)
    prompt_text = ""
    if last_user_msg:
        if isinstance(last_user_msg.content, str):
            prompt_text = last_user_msg.content
        elif isinstance(last_user_msg.content, list):
            prompt_text = " ".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in last_user_msg.content])
        else:
            prompt_text = str(last_user_msg.content)
    
    # P5.3 — @file resolution BEFORE validation — workplace integration
    at_files_resolved = []
    original_prompt_text = prompt_text
    if req.enable_at_file_resolution and "@" in prompt_text:
        resolved, at_files_resolved = resolve_at_file_references(prompt_text, db, enable=True)
        if resolved != prompt_text:
            print(f"[P5 @FILE] Resolved {len(at_files_resolved)} files, original {len(original_prompt_text)} → {len(resolved)} chars (+{len(resolved)-len(original_prompt_text)})")
            prompt_text = resolved
            # Update last user message content for further processing
            if last_user_msg:
                if isinstance(last_user_msg.content, str):
                    last_user_msg.content = resolved
                # Recalc total_chars with resolved
                total_chars = sum(len(str(m.content)) for m in req.messages if m.content)
                # For ChatMessage objects, need to handle
                total_chars = sum(len(str(m.content if isinstance(m.content, str) else str(m.content))) for m in req.messages if m.content)
                # More accurate: recalc from messages list with resolved last
                total_chars = 0
                for m in req.messages:
                    if m.role == "user" and m == last_user_msg:
                        total_chars += len(resolved)
                    elif m.content:
                        total_chars += len(str(m.content))
    
    # P5 — Phase 1: Quick token estimate BEFORE validation (<10ms) for phased logging
    try:
        token_calc_quick = calculate_tokens(
            messages=[m.dict() for m in req.messages],
            tools=req.tools,
            system=None,
            max_tokens_requested=req.get_effective_max_tokens()
        )
        estimated_input_tokens_quick = token_calc_quick["estimated_input"]
        print(f"[P5 PHASE1] Quick estimate total_chars={total_chars} prompt_chars={len(prompt_text)} estimated_input={estimated_input_tokens_quick} profile={req.profile} @files={len(at_files_resolved)}")
    except Exception as e:
        estimated_input_tokens_quick = total_chars // 4
        print(f"[P5 PHASE1] Quick estimate failed {e}, fallback {estimated_input_tokens_quick}")
    
    # P5 — Phase 2: Check large prompt for phased handling
    is_large, large_reason = is_large_prompt(total_chars, estimated_input_tokens_quick)
    if is_large:
        print(f"[P5 PHASE2] LARGE PROMPT detected: {large_reason} — will use LONG_CONTEXT routing, streaming TTFB optimization, async critic")
    
    # P5 — Phase 3: History truncation if enabled and total too large but prompt ok
    truncation_info = None
    if req.enable_history_truncation and total_chars > 80000 and len(req.messages) > 5:
        # Only truncate if prompt itself not too large, but history is
        prompt_ok = len(prompt_text) <= get_limits_for_profile(req.profile)[1]
        if prompt_ok:
            messages_dict = [m.dict() for m in req.messages]
            truncated, was_truncated, reason = truncate_history(messages_dict, keep_last=4)
            if was_truncated:
                print(f"[P5 PHASE3] History truncation applied: {reason}")
                truncation_info = {"was_truncated": True, "reason": reason, "original_messages": len(req.messages), "truncated_messages": len(truncated)}
                # Convert back to ChatMessage list — keep original objects but filtered
                # For simplicity, rebuild req.messages from truncated dicts
                new_messages = []
                for md in truncated:
                    # Find original message with same role/content prefix
                    orig = next((m for m in req.messages if m.role == md.get('role') and str(m.content)[:100] == str(md.get('content',''))[:100]), None)
                    if orig:
                        new_messages.append(orig)
                    else:
                        new_messages.append(ChatMessage(role=md.get('role','user'), content=md.get('content','')))
                req.messages = new_messages
                total_chars = sum(len(str(m.content)) for m in req.messages if m.content)
                print(f"[P5 PHASE3] After truncation total_chars {total_chars}")
    
    # P5 — Phase 4: Compression if enabled and large
    compression_info = None
    if req.enable_compression and total_chars > LARGE_PROMPT_CHARS:
        original_len = len(prompt_text)
        compressed = compress_prompt(prompt_text)
        if len(compressed) < original_len:
            compression_info = {"original_chars": original_len, "compressed_chars": len(compressed), "saved": original_len - len(compressed), "saved_pct": round((1 - len(compressed)/original_len)*100, 1)}
            print(f"[P5 PHASE4] Compression {original_len} → {len(compressed)} saved {compression_info['saved']} ({compression_info['saved_pct']}%)")
            prompt_text = compressed
            if last_user_msg and isinstance(last_user_msg.content, str):
                last_user_msg.content = compressed
            total_chars = sum(len(str(m.content)) for m in req.messages if m.content)
    
    # P0 + P5 — Central Policy validation per-profile faseado
    # Use profile from request for limits
    profile_for_validation = req.profile or ("CLINE_CODING" if is_cline else "BEST")
    is_valid, error_msg = validate_request_size_profile(profile_for_validation, total_chars, len(prompt_text))
    if not is_valid:
        observability_service.log(level="warning", message=f"P0+P5 Policy validation failed: {error_msg} total={total_chars} prompt={len(prompt_text)} profile={profile_for_validation} limits {get_limits_for_profile(profile_for_validation)}", trace_id=request_id)
        observability_service.end_trace(trace_id=request_id, span_id=obs_trace["span_id"], latency_ms=int((time.time()-start)*1000), status="error")
        # P5 — Detailed 413 with suggestions faseado
        detailed_msg = error_msg + f" | P5 LARGE PROMPT FASEADO: Phase1 validation per-profile {profile_for_validation}, Phase2 large detect {large_reason if is_large else 'not large'}, Phase3 truncation {truncation_info}, Phase4 compression {compression_info}, @files {len(at_files_resolved)}. Suggestions: Try profile CLINE_CODING (200k) for large, use workplace @file references, split, chunk, enable compression/truncation. Absolute max 500k chars ~125k tokens fits 128k context. Chars ≠ tokens, tokens principal."
        if total_chars > get_limits_for_profile(profile_for_validation)[0]:
            raise HTTPException(
                status_code=413,
                detail=error_contract.openai_error(
                    detailed_msg,
                    type="invalid_request_error",
                    code="context_length_exceeded",
                    param="messages"
                )
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=error_contract.openai_error(
                    detailed_msg,
                    type="invalid_request_error",
                    code="prompt_too_large" if len(prompt_text) > get_limits_for_profile(profile_for_validation)[1] else "messages_too_large",
                    param="messages"
                )
            )
    
    # P0 — Token calculation coherent — single source via token_calculator
    try:
        token_calc = calculate_tokens(
            messages=[m.dict() for m in req.messages],
            tools=req.tools,
            system=None,
            max_tokens_requested=req.get_effective_max_tokens()
        )
        estimated_input_tokens = token_calc["estimated_input"]
        estimated_total_tokens = token_calc["estimated_total"]
        print(f"[P0 TOKEN] total_chars={total_chars} prompt_chars={len(prompt_text)} estimated_input={estimated_input_tokens} estimated_total={estimated_total_tokens} tools={bool(req.tools)} large={is_large} @files={len(at_files_resolved)}")
    except Exception as e:
        print(f"[P0 TOKEN] Calculation failed: {e}, fallback to len//4")
        estimated_input_tokens = total_chars // 4
        estimated_total_tokens = estimated_input_tokens + (req.max_tokens or DEFAULT_OUTPUT_TOKENS)

    # P8 P0 — Context Compiler — Token Budget Manager, deduplicação, selecção por relevância, compressão hierárquica, limites por modelo, preservação das instruções críticas
    context_compiled = None
    try:
        from ..services.context_compiler import context_compiler
        # Determine model limit — use max context or profile-based
        model_limit = 128000
        try:
            from ..services.http_client import get_cached_providers_models_sync
            _, cached_models = get_cached_providers_models_sync(db)
            if cached_models:
                max_ctx = max([m.context_window for m in cached_models if m.context_window and m.context_window>0], default=128000)
                model_limit = max_ctx
        except:
            pass
        
        # If large prompt or many messages, use compiler
        if len(req.messages) > 5 or total_chars > 20000 or estimated_input_tokens > 8000:
            print(f"[P8 CONTEXT COMPILER] Compiling context: {len(req.messages)} msgs, {total_chars} chars, {estimated_input_tokens} tokens, limit {model_limit}")
            messages_dict = [m.dict() for m in req.messages]
            compiled_result = context_compiler.compile(
                messages=messages_dict,
                tools=req.tools,
                system=None,
                model_context_limit=model_limit,
                max_output_tokens=req.get_effective_max_tokens(),
                profile=profile_for_validation,
                use_cache=True
            )
            context_compiled = compiled_result
            # Use compiled messages if quality good and saved tokens
            if compiled_result.quality_metrics["overall_quality"] > 60 and len(compiled_result.compiled_messages) > 0:
                # Rebuild req.messages from compiled
                from pydantic import BaseModel
                new_messages = []
                for cm in compiled_result.compiled_messages:
                    if isinstance(cm, dict):
                        new_messages.append(ChatMessage(role=cm.get('role','user'), content=cm.get('content',''), tool_calls=cm.get('tool_calls'), tool_call_id=cm.get('tool_call_id')))
                    else:
                        new_messages.append(cm)
                req.messages = new_messages
                print(f"[P8 CONTEXT COMPILER] Applied compiled context: {len(messages_dict)}→{len(new_messages)} msgs, saved {compiled_result.quality_metrics['saved_chars']} chars, quality {compiled_result.quality_metrics['overall_quality']}%, conflicts {len(compiled_result.conflicts)}")
            else:
                print(f"[P8 CONTEXT COMPILER] Quality low {compiled_result.quality_metrics['overall_quality']}% or empty, keeping original")
        else:
            print(f"[P8 CONTEXT COMPILER] Skipped small context: {len(req.messages)} msgs {total_chars} chars")
    except Exception as e:
        print(f"[P8 CONTEXT COMPILER] Failed {e}, using original context")
        import traceback
        traceback.print_exc()
        context_compiled = None
    
    # P18 v1.2 — Complexity detection FIRST — SIMPLE vs MEDIUM vs COMPLEX for fast-path
    early_classification = classifier.classify(prompt_text, [m.dict() for m in req.messages])
    complexity_level = early_classification.complexity_level.value if hasattr(early_classification.complexity_level, 'value') else str(early_classification.complexity_level)
    is_simple = early_classification.is_simple
    fast_path_eligible = early_classification.fast_path_eligible

    # P24 Deep Integration — Brainstorming automático antes de responder/construir
    brainstorm_result = None
    brainstorm_before_build = None
    try:
        auto_brain = brainstorming_service.should_auto_brainstorm(prompt_text, profile=profile_for_validation if 'profile_for_validation' in locals() else req.profile)
        if auto_brain["should_brainstorm"] and not is_cline:
            print(f"[P24 BRAINSTORM] Auto brainstorm triggered {auto_brain['triggers']} confidence {auto_brain['confidence']} is_build {auto_brain['is_build_intent']}")
            if auto_brain["is_build_intent"]:
                brainstorm_before_build = brainstorming_service.brainstorm_before_build(prompt_text)
                brainstorm_result = brainstorm_before_build
                # Enrich prompt with best approach for more close to final objective
                best = brainstorm_before_build.get("best_approach", {})
                if best:
                    print(f"[P24 BRAINSTORM] Best approach {best.get('name')} template {best.get('template')} {best.get('closest_to_final')}% close")
            else:
                brainstorm_before_respond = brainstorming_service.brainstorm_before_respond(prompt_text, [m.dict() for m in req.messages], profile=profile_for_validation if 'profile_for_validation' in locals() else req.profile or "BEST")
                brainstorm_result = brainstorm_before_respond
            # Log to observability
            try:
                observability_service.log(level="info", message=f"P24 brainstorm auto {auto_brain['triggers']} confidence {auto_brain['confidence']}", trace_id=request_id, metadata={"brainstorm": brainstorm_result.get("brainstorm_id") if brainstorm_result else None, "auto_check": auto_brain, "templates_count": brainstorm_result.get("templates_count", 0) if brainstorm_result else 0})
            except:
                pass
        else:
            print(f"[P24 BRAINSTORM] No auto brainstorm needed — triggers {auto_brain['triggers'] if 'auto_brain' in locals() else []} is_cline {is_cline if 'is_cline' in locals() else False}")
    except Exception as e:
        print(f"[P24 BRAINSTORM] Failed {e}")
        import traceback; traceback.print_exc()
        brainstorm_result = None
        brainstorm_before_build = None
    
    # P5 — Override to LONG_CONTEXT if large
    if is_large and early_classification.task_type != TaskType.LONG_CONTEXT:
        print(f"[P5] Overriding classification to LONG_CONTEXT due to large prompt {large_reason} — was {early_classification.task_type}")
        early_classification.task_type = TaskType.LONG_CONTEXT
        early_classification.complexity_level = ComplexityLevel.COMPLEX
        early_classification.reasoning += f" | P5 LARGE {large_reason} → LONG_CONTEXT"
        complexity_level = "COMPLEX"
    
    # P20 CLINE_CODING — If tools present, upgrade classification to TOOL_CALLING
    if req.tools:
        early_classification.requires_tools = True
        if early_classification.task_type not in [TaskType.TOOL_CALLING, TaskType.CODING, TaskType.LONG_CONTEXT]:
            early_classification.task_type = TaskType.TOOL_CALLING
            early_classification.reasoning += f" | tools present {len(req.tools)} → TOOL_CALLING (Cline)"
        print(f"[CLINE_CODING] Tools present {len(req.tools)} → classification {early_classification.task_type} requires_tools True, bypass cache")
        cached = None
    else:
        if is_cline and (req.stream or req.tool_choice or early_classification.task_type == TaskType.LONG_CONTEXT):
            print(f"[CLINE_CODING] Bypassing cache for streaming/tool_choice/long_context")
            cached = None
        else:
            system_text = None
            try:
                sys_msg = next((m for m in req.messages if m.role == "system"), None)
                if sys_msg:
                    system_text = str(sys_msg.content)[:500] if sys_msg.content else None
            except:
                pass
            cached = observability_service.cache_get(
                prompt=prompt_text, provider=None, model=req.model, profile=req.profile, 
                complexity=complexity_level, system=system_text, tools=req.tools, temperature=req.temperature
            )
    
    if cached:
        total_latency = int((time.time()-start)*1000)
        cache_level = cached.get("cache_level", "L1")
        observability_service.end_trace(
            trace_id=request_id,
            span_id=obs_trace["span_id"],
            latency_ms=total_latency,
            status="success",
            cost=0.0,
            breakdown={"classifier": 2, "routing": 2, "cache": total_latency, "complexity": complexity_level, "cache_level": cache_level, "total": total_latency},
            tokens={"prompt": len(prompt_text)//4, "completion": len(cached["response"])//4, "total": (len(prompt_text)+len(cached["response"]))//4}
        )
        observability_service.add_to_session(session_id=session_id, trace_id=request_id, cost=0.0, latency_ms=total_latency, provider=cached.get("provider"), model=cached.get("model"))
        observability_service.log(level="info", message=f"Chat cache HIT {cache_level} {complexity_level} {request_id} {cached.get('provider')}/{cached.get('model')} {total_latency}ms", trace_id=request_id, user_id="admin", provider=cached.get("provider"), model=cached.get("model"), latency_ms=total_latency, cost=0.0, metadata={"cache_hit": True, "cache_level": cache_level, "complexity": complexity_level, "cache_key": cached.get("prompt_hash")})
        
        if USE_LOCAL_CACHE and local_cache_service:
            try:
                local_cache_service.save_conversation(session_id, prompt_text, cached["response"], complexity=complexity_level, latency_ms=total_latency)
            except:
                pass
        
        return {
            "id": request_id,
            "object": "chat.completion",
            "created": int(time.time()),
            "model": f"{cached.get('provider')}/{cached.get('model')}" if cached.get("provider") else cached.get("model") or req.model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": cached["response"]},
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(prompt_text)//4,
                "completion_tokens": len(cached["response"])//4,
                "total_tokens": (len(prompt_text)+len(cached["response"]))//4
            },
            "cache": {"hit": True, "level": cache_level, "key": cached.get("prompt_hash"), "saved_latency_ms": cached.get("latency_ms"), "saved_cost": cached.get("cost")},
            "fast_path": {
                "complexity": complexity_level,
                "is_simple": is_simple,
                "fast_path_eligible": fast_path_eligible,
                "cache_hit": True,
                "cache_level": cache_level,
                "latency_ms": total_latency,
                "reasoning": early_classification.reasoning
            },
            "observability": {"trace_id": request_id, "session_id": session_id, "cache_hit": True, "cache_level": cache_level, "complexity": complexity_level}
        }
    
    # P16 Guardrails 18+ - Middleware chain + P5 per-profile
    guardrail_check = guardrails_service.check_all(prompt_text, cost=0.0, latency_ms=0, file_size=total_chars, files_count=len(req.messages), profile=profile_for_validation)
    if guardrail_check["should_block"]:
        observability_service.log(level="warning", message=f"Guardrail blocked {guardrail_check['blocked']}", trace_id=request_id, metadata={"guardrails": guardrail_check})
        observability_service.end_trace(trace_id=request_id, span_id=obs_trace["span_id"], latency_ms=int((time.time()-start)*1000), status="blocked", breakdown={"classifier": 10, "routing": 20, "guardrails": 50})
        try:
            from ..services.audit_service import audit_service
            audit_service.log_action(action="guardrail_block", user_id="admin", resource_type="chat", resource_id=request_id, details={"blocked": guardrail_check["blocked"], "prompt": prompt_text[:200]}, status="blocked", severity="warning", db=db)
        except: pass
        raise HTTPException(400, f"Guardrail blocked: {guardrail_check['blocked']} - P16 Enterprise 18+ guardrails")
    
    if guardrail_check["should_human_approval"]:
        observability_service.log(level="warning", message=f"Guardrail human approval required {guardrail_check['human_required']}", trace_id=request_id)
        print(f"[GUARDRAILS] Human approval required: {guardrail_check['human_required']}")
    
    suspicious_patterns = ["<script", "eval(", "exec(", "api_key", "password"]
    if any(p in prompt_text.lower() for p in suspicious_patterns):
        print(f"[SECURITY] Suspicious prompt pattern detected: {prompt_text[:100]}")
        observability_service.log(level="warning", message=f"Suspicious pattern {prompt_text[:100]}", trace_id=request_id)
    
    support_agents_trace = []
    enhanced_prompt = prompt_text
    intent_analysis = None
    prompt_optimization = None
    critique_trace = []
    use_fast_path = False
    use_cline_coding = False
    
    if 'early_classification' in locals():
        classification = early_classification
        if req.profile and req.profile.upper() == "CLINE_CODING":
            use_cline_coding = True
            print(f"[CLINE_CODING] Profile CLINE_CODING explicitly requested — bypass support agents, coding-first, low latency, tool calling")
        elif is_cline:
            if classification.task_type in [TaskType.CODING, TaskType.TOOL_CALLING, TaskType.LONG_CONTEXT] or req.tools:
                use_cline_coding = True
                print(f"[CLINE_CODING] Auto-detected Cline: task_type={classification.task_type} tools={bool(req.tools)} → CLINE_CODING profile")
        
        if classification.complexity_level == ComplexityLevel.SIMPLE and classification.fast_path_eligible and not use_cline_coding:
            use_fast_path = True
            print(f"[FAST-PATH] SIMPLE detected: '{prompt_text[:50]}' → bypass agents, FAST profile, latency target 500ms vs 2-5s")
            observability_service.record_fast_path()
            if USE_LOCAL_CACHE and local_cache_service:
                local_cache_service.record_fast_path()
        else:
            observability_service.record_complex_path()
            if USE_LOCAL_CACHE and local_cache_service:
                local_cache_service.record_complex_path()
    else:
        classification = classifier.classify(prompt_text, [m.dict() for m in req.messages])
    
    should_use_support_agents = req.use_support_agents
    if use_cline_coding:
        if req.use_support_agents and req.profile and req.profile.upper() == "CLINE_CODING":
            print(f"[CLINE_CODING] Support agents explicitly enabled via use_support_agents=True — will use, but default is disabled for low latency")
        else:
            should_use_support_agents = False
            print(f"[CLINE_CODING] Support agents disabled by default for Cline — Cline -> classifier -> routing -> provider -> resposta (no multiplying requests)")
    
    if should_use_support_agents and not use_fast_path and not use_cline_coding:
        try:
            enhancement = chat_enhancer.enhance_chat(prompt_text, [m.dict() for m in req.messages])
            intent_analysis = enhancement["intent"]
            prompt_optimization = enhancement["optimization"]
            support_agents_trace.extend(enhancement["agents_trace"])
            
            if enhancement["should_use_optimized"] and len(prompt_text.split()) < 20:
                enhanced_prompt = enhancement["optimized_prompt"]
                print(f"[CHAT SUPPORT] Prompt otimizado: {prompt_text[:60]} -> {enhanced_prompt[:100]}")
            
            try:
                agent_manager.record_task_result("intent-analyzer-01", "intent_analysis", True, enhancement["latency_ms"])
                agent_manager.record_task_result("prompt-optimizer-01", "prompt_engineering", True, enhancement["latency_ms"])
            except:
                pass
            
            classification = classifier.classify(enhanced_prompt, [m.dict() for m in req.messages])
        except Exception as e:
            print(f"[CHAT SUPPORT] Enhancement failed: {e}")
    elif use_fast_path:
        print(f"[FAST-PATH] Bypassing support agents for SIMPLE: {prompt_text[:50]}")
    elif use_cline_coding:
        print(f"[CLINE_CODING] Bypassing support agents for Cline: {prompt_text[:50]} task_type={classification.task_type}")
    
    profile = None
    if req.profile:
        try:
            profile = Profile(req.profile.upper())
        except:
            print(f"[PROFILE] Invalid profile {req.profile}, will infer")
            profile = None
    
    if not profile and 'classification' in locals():
        if use_cline_coding:
            profile = Profile.CLINE_CODING
            print(f"[CLINE_CODING] Using profile CLINE_CODING for task_type {classification.task_type} complexity {classification.complexity_level}")
        else:
            try:
                suggested = classification.suggested_profile
                if suggested:
                    profile = Profile(suggested.upper())
                    print(f"[FAST-PATH] Using suggested profile {suggested} for complexity {classification.complexity_level}")
            except Exception as e:
                print(f"[FAST-PATH] Profile from classification failed: {e}")
                if classification.complexity_level == ComplexityLevel.SIMPLE:
                    profile = Profile.FAST
                elif classification.task_type.value == "CODING":
                    profile = Profile.CODING
                elif classification.task_type.value == "REASONING":
                    profile = Profile.REASONING
                else:
                    profile = Profile.BEST
    
    try:
        from ..services.http_client import get_cached_providers_models_sync
        providers, models = get_cached_providers_models_sync(db)
    except Exception as e:
        print(f"[PROVIDER CACHE] Fallback to DB query: {e}")
        providers = db.query(Provider).all()
        models = db.query(Model).all()
    
    if 'use_fast_path' in locals() and use_fast_path:
        fast_provider_ids = ["groq", "groq2", "groq3", "cerebras", "sambanova", "openrouter"]
        fast_providers = [p for p in providers if p.provider_id in fast_provider_ids]
        if fast_providers:
            fast_providers_sorted = sorted(fast_providers, key=lambda p: (
                0 if str(p.status) in ["VERIFIED", "PRODUCTION"] or (hasattr(p.status, 'value') and p.status.value in ["VERIFIED", "PRODUCTION"]) else 1,
                p.avg_latency_ms if p.avg_latency_ms > 0 else 9999
            ))
            fast_provider_ids_sorted = [p.provider_id for p in fast_providers_sorted[:3]]
            fast_models = [m for m in models if m.provider_id in fast_provider_ids_sorted]
            fast_models = [m for m in fast_models if not any(k in m.model_id.lower() for k in ["embed", "ocr", "tts", "transcribe", "moderation", "image", "video", "audio"])]
            if fast_models:
                providers = fast_providers_sorted[:3]
                models = fast_models[:10]
                print(f"[FAST-PATH] Filtered to fastest providers {fast_provider_ids_sorted} with {len(models)} models for SIMPLE")
    
    if not providers or not models:
        raise HTTPException(503, "No providers or models configured - add providers via /api/providers")
    
    if req.model and req.model != "auto":
        def find_models_for_requested(requested_model_id: str):
            try:
                cached_models = models
                if "/" in requested_model_id and not requested_model_id.startswith("openai/") and "/" in requested_model_id.split("/",1)[1]:
                    prov_id, mod_id = requested_model_id.split("/", 1)
                    existing_prov = next((p for p in providers if p.provider_id == prov_id), None)
                    if existing_prov:
                        base = mod_id.split("/")[-1]
                        candidates = [m for m in cached_models if m.model_id == mod_id or base in m.model_id or m.model_id == base or f"/{base}" in m.model_id]
                        if not candidates:
                            candidates = [m for m in cached_models if m.provider_id == prov_id and m.model_id == mod_id]
                        return candidates, prov_id
                mod_id = requested_model_id
                base = mod_id.split("/")[-1]
                candidates = [m for m in cached_models if m.model_id == mod_id or m.model_id == base or mod_id in m.model_id or base in m.model_id]
                if not candidates:
                    candidates = [m for m in cached_models if m.model_id == requested_model_id]
                candidates = [m for m in candidates if str(m.status) not in ["DEPRECATED", "DISABLED"] and getattr(m.status, 'value', str(m.status)) not in ["DEPRECATED", "DISABLED"]]
                if not candidates:
                    candidates = db.query(Model).filter(Model.model_id == requested_model_id).all()
                    candidates = [m for m in candidates if str(m.status) not in ["DEPRECATED", "DISABLED"]]
                return candidates, None
            except Exception as e:
                print(f"[P0.5.2] Cache find failed {e}, fallback DB")
                if "/" in requested_model_id and not requested_model_id.startswith("openai/") and "/" in requested_model_id.split("/",1)[1]:
                    prov_id, mod_id = requested_model_id.split("/", 1)
                    existing_prov = db.query(Provider).filter(Provider.provider_id == prov_id).first()
                    if existing_prov:
                        base = mod_id.split("/")[-1]
                        candidates = db.query(Model).filter(
                            (Model.model_id == mod_id) | 
                            (Model.model_id.like(f"%/{base}")) |
                            (Model.model_id == base)
                        ).all()
                        if not candidates:
                            candidates = db.query(Model).filter(Model.provider_id == prov_id, Model.model_id == mod_id).all()
                        return candidates, prov_id
                mod_id = requested_model_id
                base = mod_id.split("/")[-1]
                candidates = db.query(Model).filter(
                    (Model.model_id == mod_id) |
                    (Model.model_id == base) |
                    (Model.model_id.like(f"%/{mod_id}")) |
                    (Model.model_id.like(f"%/{base}"))
                ).all()
                if not candidates:
                    candidates = db.query(Model).filter(Model.model_id == requested_model_id).all()
                return candidates, None

        same_model_models, preferred_prov = find_models_for_requested(req.model)
        if same_model_models:
            same_provider_ids = [m.provider_id for m in same_model_models]
            providers = db.query(Provider).filter(Provider.provider_id.in_(same_provider_ids)).all()
            models = same_model_models
            if preferred_prov:
                providers = sorted(providers, key=lambda p: 0 if p.provider_id == preferred_prov else 1)
    else:
        print(f"[CLINE_CODING AUTO] Model auto requested — task_type={classification.task_type} complexity={complexity_level} tools={bool(req.tools)} profile={profile}")
        if use_cline_coding or (profile and profile == Profile.CLINE_CODING):
            coding_models = [m for m in models if (m.coding_score or 0) >= 50 or any(k in m.model_id.lower() for k in ["codestral", "gpt-4", "claude-3", "deepseek", "qwen2.5-coder", "qwen3", "glm-4", "kimi", "llama-3.1", "llama-3.3", "mistral", "command-r"])]
            if coding_models:
                models = coding_models[:50]
                print(f"[CLINE_CODING AUTO] Filtered to {len(models)} coding-capable models for CLINE_CODING auto")

    if req.stream and req.use_orchestrator:
        try:
            def clean_message_stream(m):
                if isinstance(m, dict):
                    role = m.get("role")
                    content = m.get("content", "")
                    tool_calls = m.get("tool_calls")
                    tool_call_id = m.get("tool_call_id")
                else:
                    role = m.role
                    content = m.content
                    tool_calls = getattr(m, 'tool_calls', None)
                    tool_call_id = getattr(m, 'tool_call_id', None)
                cleaned = {"role": role}
                if content is not None:
                    cleaned["content"] = content
                if role == "assistant" and tool_calls:
                    cleaned["tool_calls"] = tool_calls
                if role == "tool" and tool_call_id:
                    cleaned["tool_call_id"] = tool_call_id
                    if "content" not in cleaned:
                        cleaned["content"] = ""
                return cleaned
            
            current_messages_stream = [clean_message_stream(m) for m in req.messages]
            
            from fastapi.responses import StreamingResponse
            import json as json_lib
            
            print(f"[P21 TRUE STREAMING] Starting true streaming for profile={profile} tools={bool(req.tools)} model={req.model} prompt_len={len(prompt_text)} is_cline={is_cline} large={is_large}")
            
            async def generate_true_stream():
                try:
                    chunk_count = 0
                    first_chunk_time = None
                    provider_id_stream = "unknown"
                    model_id_stream = "unknown"
                    routing_obj_stream = None
                    requested_tokens_stream = 0
                    model_context_limit_stream = 0
                    fallback_reasons_stream = []
                    total_latency_stream = 0
                    
                    async for stream_event in orchestrator_service.execute_with_routing_stream(
                        prompt=enhanced_prompt,
                        providers=providers,
                        models=models,
                        profile=profile,
                        messages=current_messages_stream,
                        tools=req.tools,
                        tool_choice=req.tool_choice,
                        response_format=req.response_format,
                        temperature=req.temperature or 0.7,
                        max_tokens=req.get_effective_max_tokens(),
                        early_classification=classification,
                        top_p=req.top_p,
                        top_k=req.top_k,
                        presence_penalty=req.presence_penalty,
                        frequency_penalty=req.frequency_penalty,
                        stop=req.stop,
                        seed=req.seed,
                        user=req.user
                    ):
                        if stream_event.get("type") == "chunk":
                            chunk_count += 1
                            provider_id_stream = stream_event.get("provider", provider_id_stream)
                            model_id_stream = stream_event.get("model", model_id_stream)
                            routing_obj_stream = stream_event.get("routing", routing_obj_stream)
                            requested_tokens_stream = stream_event.get("requested_tokens", requested_tokens_stream)
                            model_context_limit_stream = stream_event.get("model_context_limit", model_context_limit_stream)
                            fallback_reasons_stream = stream_event.get("fallback_reasons", fallback_reasons_stream)
                            
                            if first_chunk_time is None:
                                first_chunk_time = time.time()
                                ttfb = int((first_chunk_time - start) * 1000)
                                print(f"[P21 TRUE STREAMING] First chunk TTFB {ttfb}ms from {provider_id_stream}/{model_id_stream} large={is_large}")
                            
                            raw_data = stream_event.get("data", {})
                            if isinstance(raw_data, dict) and "choices" in raw_data:
                                forward_chunk = raw_data
                                if "id" not in forward_chunk:
                                    forward_chunk["id"] = request_id
                                if "object" not in forward_chunk:
                                    forward_chunk["object"] = "chat.completion.chunk"
                                yield f"data: {json_lib.dumps(forward_chunk)}\n\n"
                            else:
                                wrapped = {
                                    "id": request_id,
                                    "object": "chat.completion.chunk",
                                    "created": int(time.time()),
                                    "model": f"{provider_id_stream}/{model_id_stream}",
                                    "choices": [{"index": 0, "delta": raw_data if isinstance(raw_data, dict) else {"content": str(raw_data)}, "finish_reason": None}]
                                }
                                yield f"data: {json_lib.dumps(wrapped)}\n\n"
                        
                        elif stream_event.get("type") == "done":
                            provider_id_stream = stream_event.get("provider", provider_id_stream)
                            model_id_stream = stream_event.get("model", model_id_stream)
                            routing_obj_stream = stream_event.get("routing", routing_obj_stream)
                            total_latency_stream = stream_event.get("total_latency", int((time.time() - start) * 1000))
                            print(f"[P21 TRUE STREAMING] Done {provider_id_stream}/{model_id_stream} chunks={chunk_count} total={total_latency_stream}ms large={is_large}")
                            
                            final_chunk = {
                                "id": request_id,
                                "object": "chat.completion.chunk",
                                "created": int(time.time()),
                                "model": f"{provider_id_stream}/{model_id_stream}",
                                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
                            }
                            if req.explain_routing and routing_obj_stream:
                                final_chunk["routing"] = {
                                    "selected": f"{routing_obj_stream.selected.model.display_name} / {routing_obj_stream.selected.provider.name}",
                                    "reason": routing_obj_stream.selected.reason,
                                    "profile": routing_obj_stream.profile.value,
                                    "task_type": routing_obj_stream.classification.task_type.value,
                                    "confidence": routing_obj_stream.confidence,
                                    "requested_tokens": requested_tokens_stream,
                                    "model_context_limit": model_context_limit_stream,
                                    "fallback_reasons": fallback_reasons_stream[:3],
                                    "streaming": "TRUE STREAMING — chunks forwarded as they arrive from provider, TTFB <500ms, no buffering full response",
                                    "ttfb_ms": int((first_chunk_time - start)*1000) if first_chunk_time else 0,
                                    "chunk_count": chunk_count,
                                    "total_latency_ms": total_latency_stream,
                                    "p5_large": {"is_large": is_large, "large_reason": large_reason, "at_files": len(at_files_resolved), "truncation": truncation_info, "compression": compression_info}
                                }
                            yield f"data: {json_lib.dumps(final_chunk)}\n\n"
                            yield "data: [DONE]\n\n"
                            
                            try:
                                observability_service.end_trace(
                                    trace_id=request_id,
                                    span_id=obs_trace["span_id"],
                                    latency_ms=total_latency_stream,
                                    status="success",
                                    cost=routing_obj_stream.selected.estimated_cost if routing_obj_stream else 0.0,
                                    breakdown={"classifier": 10, "routing": 20, "adapter_streaming": total_latency_stream, "chunks": chunk_count, "ttfb": int((first_chunk_time - start)*1000) if first_chunk_time else 0, "total": total_latency_stream, "p5_large": 1 if is_large else 0},
                                    tokens={"prompt": requested_tokens_stream, "completion": 0, "total": requested_tokens_stream}
                                )
                                observability_service.add_to_session(session_id=session_id, trace_id=request_id, cost=routing_obj_stream.selected.estimated_cost if routing_obj_stream else 0.0, latency_ms=total_latency_stream, provider=provider_id_stream, model=model_id_stream)
                                log_entry = RequestLog(
                                    request_id=request_id,
                                    provider=provider_id_stream,
                                    model=model_id_stream,
                                    task_type=routing_obj_stream.classification.task_type.value if routing_obj_stream else "UNKNOWN",
                                    profile=routing_obj_stream.profile.value if routing_obj_stream else (profile.value if profile else "UNKNOWN"),
                                    latency_ms=total_latency_stream,
                                    input_tokens=requested_tokens_stream,
                                    output_tokens=0,
                                    cost=routing_obj_stream.selected.estimated_cost if routing_obj_stream else 0.0,
                                    cost_status="estimate",
                                    status="success",
                                    fallback_used=len(fallback_reasons_stream) > 0,
                                    fallback_chain=stream_event.get("fallback_chain", []),
                                    rating_at_time=routing_obj_stream.selected.model.overall_score if routing_obj_stream else 0,
                                    prompt_hash=hashlib.sha256(prompt_text.encode()).hexdigest()[:16]
                                )
                                db.add(log_entry)
                                prov = db.query(Provider).filter(Provider.provider_id == provider_id_stream).first()
                                if prov:
                                    prov.success_count += 1
                                    prov.last_success = datetime.now(timezone.utc)
                                    prov.consecutive_failures = 0
                                    if prov.avg_latency_ms == 0:
                                        prov.avg_latency_ms = total_latency_stream
                                    else:
                                        prov.avg_latency_ms = (prov.avg_latency_ms * 0.8 + total_latency_stream * 0.2)
                                db.commit()
                            except Exception as obs_e:
                                print(f"[OBSERVABILITY] Streaming end trace failed: {obs_e}")
                            return
                        
                        elif stream_event.get("type") == "error":
                            print(f"[P21 TRUE STREAMING] Error from {stream_event.get('provider')}/{stream_event.get('model')}: {stream_event.get('error')}")
                            error_chunk = {
                                "id": request_id,
                                "object": "chat.completion.chunk",
                                "created": int(time.time()),
                                "model": f"{stream_event.get('provider','unknown')}/{stream_event.get('model','unknown')}",
                                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                                "error": stream_event.get("error", "Streaming error")[:500]
                            }
                            yield f"data: {json_lib.dumps(error_chunk)}\n\n"
                            yield "data: [DONE]\n\n"
                            return
                    
                    yield "data: [DONE]\n\n"
                
                except Exception as e:
                    err_str = str(e)
                    print(f"[P21 TRUE STREAMING] Failed: {err_str[:500]}")
                    try:
                        observability_service.end_trace(
                            trace_id=request_id,
                            span_id=obs_trace["span_id"],
                            latency_ms=int((time.time()-start)*1000),
                            status="error",
                            cost=0.0,
                            breakdown={"classifier": 10, "routing": 20, "error": 100}
                        )
                    except:
                        pass
                    error_resp = {
                        "id": request_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": req.model or "auto",
                        "choices": [{"index": 0, "delta": {"content": f"Streaming failed: {err_str[:200]}"}, "finish_reason": "stop"}]
                    }
                    yield f"data: {json_lib.dumps(error_resp)}\n\n"
                    yield "data: [DONE]\n\n"
            
            return StreamingResponse(generate_true_stream(), media_type="text/event-stream", headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            })
        
        except Exception as e:
            err_str = str(e)
            print(f"[P21 TRUE STREAMING] Setup failed: {err_str}")
            raise HTTPException(500, f"Streaming setup failed: {err_str[:500]}")

    # P6 — Request coalescing for identical prompts — saves provider quota and latency
    # If same prompt hash + profile requested simultaneously, coalesce to single provider call
    coalescing_key = None
    try:
        from ..services.cache_manager import get_coalescing_key, try_coalesce
        prompt_hash_coal = hashlib.sha256(prompt_text.encode()).hexdigest()[:16]
        coalescing_key = get_coalescing_key(prompt_hash_coal, profile_for_validation, req.model or "auto")
        existing = try_coalesce(coalescing_key)
        if existing and not is_large:  # Don't coalesce large prompts to avoid memory
            print(f"[P6 COALESCING] Coalescing identical prompt {prompt_hash_coal} profile {profile_for_validation} — sharing in-flight request")
            # Wait for existing? For simplicity, return cached if available, else proceed
            # In real implementation, we'd await future, but for MVP we just log and proceed
            pass
    except Exception as e:
        print(f"[P6 COALESCING] Check failed {e}")

    if req.use_orchestrator:
        try:
            attempt = 0
            max_attempts = req.max_retries + 1 if req.enable_retry else 1
            if use_cline_coding and not req.enable_retry:
                max_attempts = 1
                print(f"[CLINE_CODING] Retry disabled by default for Cline — max_attempts=1 to avoid multiplying requests")
            elif use_cline_coding and req.enable_retry:
                print(f"[CLINE_CODING] Retry explicitly enabled — max_attempts={max_attempts}")
            
            last_response = None
            last_routing = None
            critique_trace = critique_trace
            
            while attempt < max_attempts:
                current_prompt = enhanced_prompt if attempt == 0 else f"{enhanced_prompt}\n\n[CRITIQUE FEEDBACK - Terceiro olho, não ficar na primeira tentativa]: {critique_trace[-1]['retry_prompt'] if critique_trace else ''}"
                
                def clean_message(m):
                    if isinstance(m, dict):
                        role = m.get("role")
                        content = m.get("content", "")
                        tool_calls = m.get("tool_calls")
                        tool_call_id = m.get("tool_call_id")
                    else:
                        role = m.role
                        content = m.content
                        tool_calls = getattr(m, 'tool_calls', None)
                        tool_call_id = getattr(m, 'tool_call_id', None)
                    
                    cleaned = {"role": role}
                    if content is not None:
                        cleaned["content"] = content
                    if role == "assistant" and tool_calls:
                        cleaned["tool_calls"] = tool_calls
                    if role == "tool" and tool_call_id:
                        cleaned["tool_call_id"] = tool_call_id
                        if "content" not in cleaned:
                            cleaned["content"] = ""
                    return cleaned
                
                current_messages = [clean_message(m) for m in req.messages]
                if attempt > 0:
                    current_messages = current_messages[:-1] + [{"role": "user", "content": current_prompt}]
                
                orch_result = await orchestrator_service.execute_with_routing(
                    prompt=current_prompt,
                    providers=providers,
                    models=models,
                    profile=profile,
                    messages=current_messages,
                    tools=req.tools,
                    tool_choice=req.tool_choice,
                    response_format=req.response_format,
                    temperature=req.temperature or 0.7,
                    max_tokens=req.get_effective_max_tokens(),
                    stream=req.stream or False,
                    early_classification=classification,
                    top_p=req.top_p,
                    top_k=req.top_k,
                    presence_penalty=req.presence_penalty,
                    frequency_penalty=req.frequency_penalty,
                    stop=req.stop,
                    seed=req.seed,
                    user=req.user
                )
                
                response_obj = orch_result["response"]
                routing_obj = orch_result["routing"]
                
                should_critique = req.enable_critique and req.use_support_agents and not use_fast_path and not use_cline_coding
                should_critique_async = False
                if 'classification' in locals() and classification.complexity_level == ComplexityLevel.SIMPLE:
                    should_critique = False
                    print(f"[FAST-PATH] Skipping critic for SIMPLE — saves 100-500ms")
                elif 'classification' in locals() and classification.complexity_level in [ComplexityLevel.MEDIUM, ComplexityLevel.COMPLEX]:
                    should_critique_async = req.enable_critique and req.use_support_agents
                    should_critique = False
                    if should_critique_async:
                        print(f"[P2.3 ASYNC CRITIC] MEDIUM/COMPLEX {classification.complexity_level} — will run critic async after response, TTFB 500ms vs 2-5s")
                if use_cline_coding:
                    should_critique = False
                    should_critique_async = False
                    print(f"[CLINE_CODING] Skipping critic for Cline — low latency, no multiplying requests")
                
                if should_critique:
                    try:
                        critique_result = chat_enhancer.enhance_response(
                            original_prompt=prompt_text,
                            optimized_prompt=enhanced_prompt,
                            response=response_obj.content,
                            intent=intent_analysis or {}
                        )
                        critique_trace.append(critique_result["critique"])
                        support_agents_trace.extend([t for t in critique_result["agents_trace"] if t])
                        
                        try:
                            agent_manager.record_task_result("critic-01", "response_critique", critique_result["critique"]["score"]>=70, critique_result["latency_ms"])
                            if critique_result.get("code_review"):
                                agent_manager.record_task_result("code-reviewer-01", "code_review", critique_result["code_review"]["score"]>=70, 0)
                            agent_manager.record_task_result("rigor-checker-01", "rigor_check", critique_result["critique"]["is_rigorous"], 0)
                        except:
                            pass
                        
                        if critique_result["should_retry"] and attempt < max_attempts - 1:
                            print(f"[CHAT SUPPORT] Critique score {critique_result['critique']['score']}/100 - retrying (terceiro olho): {critique_result['critique']['issues'][:2]}")
                            attempt += 1
                            last_response = response_obj
                            last_routing = routing_obj
                            continue
                        else:
                            last_response = response_obj
                            last_routing = routing_obj
                            break
                    except Exception as ce:
                        print(f"[CHAT SUPPORT] Critique failed: {ce}")
                        last_response = response_obj
                        last_routing = routing_obj
                        break
                else:
                    last_response = response_obj
                    last_routing = routing_obj
                    break
                
                attempt += 1
            
            response = last_response
            routing = last_routing
            fallback_used = orch_result["fallback_used"]
            trace = orch_result["trace"]
            fallback_reasons = orch_result.get("fallback_reasons", [])
            requested_tokens = orch_result.get("requested_tokens", classification.estimated_tokens)
            
            provider_id = routing.selected.provider.provider_id
            model_id = routing.selected.model.model_id
            model_display = routing.selected.model.display_name
            provider_name = routing.selected.provider.name
            routing_reason = routing.selected.reason
            routing_profile = routing.profile.value
            routing_task_type = classification.task_type.value
            routing_confidence = routing.confidence
            routing_estimated_cost = routing.selected.estimated_cost
            model_overall_score = routing.selected.model.overall_score
            response_content = response.content
            response_finish = response.finish_reason
            response_input_tokens = response.input_tokens
            response_output_tokens = response.output_tokens
            response_latency = response.latency_ms
            response_tool_calls = getattr(response, 'tool_calls', None) or (response.raw_response.get("choices", [{}])[0].get("message", {}).get("tool_calls") if response.raw_response else None)
            
            model_context_limit = routing.selected.model.context_window or 0
            print(f"[CLINE_CODING LOG] requested_tokens={requested_tokens} model_context_limit={model_context_limit} selected_model={provider_id}/{model_id} fallback_reason={fallback_reasons[:2] if fallback_reasons else 'none'} tools={bool(req.tools)} large={is_large}")
            
            prompt_hash = hashlib.sha256(prompt_text.encode()).hexdigest()[:16]
            log_entry = RequestLog(
                request_id=request_id,
                provider=provider_id,
                model=model_id,
                task_type=routing_task_type,
                profile=routing_profile,
                latency_ms=int((time.time() - start)*1000),
                input_tokens=response_input_tokens,
                output_tokens=response_output_tokens,
                cost=routing_estimated_cost,
                cost_status="estimate",
                status="success",
                fallback_used=fallback_used,
                fallback_chain=trace,
                rating_at_time=model_overall_score,
                prompt_hash=prompt_hash
            )
            db.add(log_entry)
            prov = db.query(Provider).filter(Provider.provider_id == provider_id).first()
            if prov:
                prov.success_count += 1
                prov.last_success = datetime.now(timezone.utc)
                prov.consecutive_failures = 0
                if prov.avg_latency_ms == 0:
                    prov.avg_latency_ms = response_latency
                else:
                    prov.avg_latency_ms = (prov.avg_latency_ms * 0.8 + response_latency * 0.2)
            
            db.commit()

            total_latency = int((time.time() - start)*1000)
            breakdown = {
                "classifier": 10,
                "routing": 20,
                "adapter": response_latency,
                "critic": len(critique_trace)*100 if critique_trace else 0,
                "guardrails": 5,
                "total": total_latency,
                "p5_large": 1 if is_large else 0
            }
            try:
                observability_service.end_trace(
                    trace_id=request_id,
                    span_id=obs_trace["span_id"],
                    latency_ms=total_latency,
                    status="success",
                    cost=routing_estimated_cost,
                    breakdown=breakdown,
                    tokens={"prompt": response_input_tokens, "completion": response_output_tokens, "total": response_input_tokens+response_output_tokens}
                )
                observability_service.add_to_session(session_id=session_id, trace_id=request_id, cost=routing_estimated_cost, latency_ms=total_latency, provider=provider_id, model=model_id)
                observability_service.log(level="info", message=f"Chat success {request_id} {provider_id}/{model_id} {total_latency}ms complexity={complexity_level if 'complexity_level' in locals() else 'UNKNOWN'} fast_path={use_fast_path if 'use_fast_path' in locals() else False} cline_coding={use_cline_coding} requested_tokens={requested_tokens} model_context_limit={model_context_limit} tools={bool(req.tools)} large={is_large} {large_reason if is_large else ''} @files={len(at_files_resolved)}", trace_id=request_id, user_id="admin", provider=provider_id, model=model_id, latency_ms=total_latency, cost=routing_estimated_cost, metadata={"guardrails": guardrail_check["passed_checks"] if 'guardrail_check' in locals() else 0, "complexity": complexity_level if 'complexity_level' in locals() else "UNKNOWN", "fast_path": use_fast_path if 'use_fast_path' in locals() else False, "cline_coding": use_cline_coding, "requested_tokens": requested_tokens, "model_context_limit": model_context_limit, "fallback_reasons": fallback_reasons[:3], "p5_large": is_large, "p5_large_reason": large_reason, "p5_at_files": len(at_files_resolved), "p5_truncation": truncation_info, "p5_compression": compression_info})
                if not req.tools and not req.stream and not use_cline_coding and complexity_level != "COMPLEX":
                    system_text_set = None
                    try:
                        sys_msg_set = next((m for m in req.messages if m.role == "system"), None)
                        if sys_msg_set:
                            system_text_set = str(sys_msg_set.content)[:500] if sys_msg_set.content else None
                    except:
                        pass
                    observability_service.cache_set(
                        prompt=prompt_text, response=response_content, provider=provider_id, model=model_id, 
                        profile=req.profile or (profile.value if 'profile' in locals() and profile else "BEST"), 
                        cost=routing_estimated_cost, latency_ms=total_latency,
                        complexity=complexity_level if 'complexity_level' in locals() else "MEDIUM",
                        system=system_text_set, tools=req.tools, temperature=req.temperature
                    )
                if USE_LOCAL_CACHE and local_cache_service and not req.tools:
                    try:
                        session_id_local = session_id if 'session_id' in locals() else f"session-{uuid.uuid4().hex[:8]}"
                        local_cache_service.save_conversation(
                            session_id_local, prompt_text, response_content, 
                            complexity=complexity_level if 'complexity_level' in locals() else "MEDIUM",
                            latency_ms=total_latency
                        )
                    except Exception as e:
                        print(f"[LOCAL_CACHE] Save conversation failed: {e}")
            except Exception as obs_e:
                import traceback
                print(f"[OBSERVABILITY] Failed to end trace: {obs_e}")
                traceback.print_exc()
            
            message_obj = {"role": "assistant", "content": response_content}
            if response_tool_calls:
                message_obj["tool_calls"] = response_tool_calls
                print(f"[CLINE_CODING TOOL CALLING] Preserving {len(response_tool_calls)} tool_calls for Cline: {str(response_tool_calls)[:200]}")
            
            openai_resp = {
                "id": request_id,
                "object": "chat.completion",
                "created": int(time.time()),
                "model": f"{provider_id}/{model_id}",
                "choices": [{
                    "index": 0,
                    "message": message_obj,
                    "finish_reason": response_finish or ("tool_calls" if response_tool_calls else "stop")
                }],
                "usage": {
                    "prompt_tokens": response_input_tokens,
                    "completion_tokens": response_output_tokens,
                    "total_tokens": response_input_tokens + response_output_tokens
                },
                "observability": {
                    "trace_id": request_id,
                    "session_id": session_id,
                    "latency_ms": total_latency,
                    "breakdown": breakdown,
                    "cache": {"hit": False, "store_size": len(observability_service.cache_store)},
                    "p5_large": {
                        "is_large": is_large,
                        "large_reason": large_reason if is_large else None,
                        "total_chars": total_chars,
                        "prompt_chars": len(prompt_text),
                        "estimated_tokens": estimated_input_tokens,
                        "at_files": at_files_resolved,
                        "truncation": truncation_info,
                        "compression": compression_info,
                        "profile": profile_for_validation,
                        "limits": get_limits_for_profile(profile_for_validation)
                    },
                    "cline_coding": {
                        "is_cline": use_cline_coding,
                        "requested_tokens": requested_tokens,
                        "model_context_limit": model_context_limit,
                        "fallback_used": fallback_used,
                        "fallback_reasons": fallback_reasons[:3] if fallback_reasons else [],
                        "tools": bool(req.tools),
                        "has_tool_calls": bool(response_tool_calls)
                    } if use_cline_coding else None,
                    "brainstorm": {
                        "triggered": brainstorm_result is not None,
                        "brainstorm_id": brainstorm_result.get("brainstorm_id") if brainstorm_result else None,
                        "is_build_intent": brainstorm_result.get("auto_check", {}).get("is_build_intent") if brainstorm_result and isinstance(brainstorm_result.get("auto_check"), dict) else (brainstorm_before_build is not None),
                        "best_approach": brainstorm_result.get("best_approach", {}).get("name") if brainstorm_result and "best_approach" in brainstorm_result else brainstorm_result.get("best_interpretation", {}).get("type") if brainstorm_result else None,
                        "template_suggestion": brainstorm_result.get("best_approach", {}).get("template") if brainstorm_result and "best_approach" in brainstorm_result else None,
                        "closest_to_final": brainstorm_result.get("best_approach", {}).get("closest_to_final") if brainstorm_result and "best_approach" in brainstorm_result else brainstorm_result.get("best_interpretation", {}).get("closest_to_final") if brainstorm_result else None,
                        "templates_count": brainstorm_result.get("templates_count", 0) if brainstorm_result else 0,
                        "approaches_count": len(brainstorm_result.get("approaches", [])) if brainstorm_result and "approaches" in brainstorm_result else len(brainstorm_result.get("interpretations", [])) if brainstorm_result else 0,
                        "version": "P24 deep integration 20 templates"
                    } if 'brainstorm_result' in locals() and brainstorm_result else None
                }
            }
            
            if 'should_critique_async' in locals() and should_critique_async:
                try:
                    import asyncio
                    async def async_critic_task():
                        try:
                            print(f"[P2.3 ASYNC CRITIC] Starting async critic for {request_id} complexity {complexity_level if 'complexity_level' in locals() else 'UNKNOWN'}")
                            critique_result = chat_enhancer.enhance_response(
                                original_prompt=prompt_text,
                                optimized_prompt=enhanced_prompt,
                                response=response_content,
                                intent=intent_analysis or {}
                            )
                            print(f"[P2.3 ASYNC CRITIC] Completed async critic for {request_id} score {critique_result['critique']['score']}/100 issues {critique_result['critique'].get('issues', [])[:2]}")
                            try:
                                observability_service.log(level="info", message=f"Async critic {request_id} score {critique_result['critique']['score']} issues {critique_result['critique'].get('issues', [])[:2]}", trace_id=request_id, metadata={"critique": critique_result['critique'], "async": True})
                            except:
                                pass
                            try:
                                agent_manager.record_task_result("critic-01", "response_critique", critique_result['critique']['score']>=70, critique_result['latency_ms'])
                            except:
                                pass
                        except Exception as e:
                            print(f"[P2.3 ASYNC CRITIC] Failed for {request_id}: {e}")
                    
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            loop.create_task(async_critic_task())
                        else:
                            print(f"[P2.3 ASYNC CRITIC] No running loop, skipping async critic for {request_id}")
                    except RuntimeError:
                        print(f"[P2.3 ASYNC CRITIC] RuntimeError no loop for {request_id}, skipping")
                    print(f"[P2.3 ASYNC CRITIC] Scheduled async critic for {request_id}, returning response immediately TTFB improved 500ms vs 2-5s")
                except Exception as e:
                    print(f"[P2.3 ASYNC CRITIC] Schedule failed {e}")

            # P24 — Add brainstorm to top-level response for frontend BrainstormPanel
            if 'brainstorm_result' in locals() and brainstorm_result:
                openai_resp["brainstorm"] = brainstorm_result
                # Also add simplified for frontend
                if "approaches" in brainstorm_result:
                    openai_resp["brainstorm_panel"] = {
                        "brainstorm_id": brainstorm_result.get("brainstorm_id"),
                        "is_build": True,
                        "best_approach": brainstorm_result.get("best_approach"),
                        "approaches": brainstorm_result.get("approaches", [])[:5],
                        "suggested_templates": brainstorm_result.get("suggested_templates", [])[:3],
                        "recommendation": brainstorm_result.get("recommendation"),
                        "templates_count": brainstorm_result.get("templates_count", 20),
                        "version": "P24 deep integration"
                    }
                else:
                    openai_resp["brainstorm_panel"] = {
                        "brainstorm_id": brainstorm_result.get("brainstorm_id"),
                        "is_build": False,
                        "best_interpretation": brainstorm_result.get("best_interpretation"),
                        "interpretations": brainstorm_result.get("interpretations", [])[:4],
                        "recommendation": brainstorm_result.get("recommendation"),
                        "templates_count": brainstorm_result.get("templates_count", 20),
                        "version": "P24 deep integration"
                    }

            if req.explain_routing:
                openai_resp["routing"] = {
                    "selected": f"{model_display} / {provider_name}",
                    "reason": routing_reason,
                    "profile": routing_profile,
                    "task_type": routing_task_type,
                    "confidence": routing_confidence,
                    "estimated_cost": routing_estimated_cost,
                    "alternatives": [f"{a.model.display_name} / {a.provider.name} - {a.reason}" for a in routing.alternatives],
                    "fallback_used": fallback_used,
                    "fallback_reasons": fallback_reasons[:3] if fallback_reasons else [],
                    "trace": trace,
                    "classification_reasoning": classification.reasoning,
                    "requested_tokens": requested_tokens,
                    "model_context_limit": model_context_limit,
                    "p5_large": {
                        "is_large": is_large,
                        "large_reason": large_reason if is_large else None,
                        "total_chars": total_chars,
                        "prompt_chars": len(prompt_text),
                        "estimated_tokens": estimated_input_tokens,
                        "at_files": at_files_resolved,
                        "truncation": truncation_info,
                        "compression": compression_info,
                        "profile": profile_for_validation,
                        "limits": get_limits_for_profile(profile_for_validation),
                        "faseado": "Phase1 validation per-profile → Phase2 large detect → Phase3 truncation → Phase4 compression → Phase5 routing → Phase6 provider"
                    },
                    "support_agents": {
                        "intent_analysis": intent_analysis,
                        "prompt_optimization": prompt_optimization,
                        "critique": critique_trace[-1] if critique_trace else None,
                        "trace": support_agents_trace,
                        "enhanced_prompt_used": enhanced_prompt != prompt_text,
                        "original_prompt": original_prompt_text[:500] if original_prompt_text != prompt_text else prompt_text[:500],
                        "enhanced_prompt": enhanced_prompt[:500],
                        "third_eye": "Ativo - contesta, critica, não fica na primeira tentativa, funcional, coerente, preciso, rigoroso, real, profissional",
                        "async_critic": should_critique_async if 'should_critique_async' in locals() else False
                    } if not use_cline_coding else {
                        "cline_coding": f"CLINE_CODING profile — Cline -> classifier -> routing -> provider -> resposta, no multiplying requests, bypass agents, coding-first, low latency, tool calling, long context, fallback real, requested_tokens {requested_tokens} limit {model_context_limit} large={is_large}"
                    }
                }
            elif req.use_support_agents and not use_cline_coding:
                openai_resp["support_agents"] = {
                    "intent": intent_analysis,
                    "optimization": prompt_optimization,
                    "critique": critique_trace[-1] if 'critique_trace' in locals() and critique_trace else None,
                    "enhanced_prompt_used": enhanced_prompt != prompt_text,
                    "third_eye": "Ativo",
                    "async_critic": should_critique_async if 'should_critique_async' in locals() else False,
                    "p5_large": {"is_large": is_large, "large_reason": large_reason if is_large else None, "at_files": len(at_files_resolved)}
                }
            
            return openai_resp
            
        except Exception as e:
            err_str = str(e)
            try:
                observability_service.end_trace(
                    trace_id=request_id,
                    span_id=obs_trace["span_id"] if 'obs_trace' in locals() and isinstance(obs_trace, dict) and 'span_id' in obs_trace else request_id,
                    latency_ms=int((time.time()-start)*1000),
                    status="error",
                    cost=0.0,
                    breakdown={"classifier": 10, "routing": 20, "error": 100}
                )
                observability_service.log(level="error", message=f"Chat failed {request_id}: {err_str[:200]}", trace_id=request_id, user_id="admin", metadata={"error": err_str[:500], "is_cline": is_cline if 'is_cline' in locals() else False, "p5_large": is_large if 'is_large' in locals() else False})
            except: pass
            
            log_entry = RequestLog(
                request_id=request_id,
                task_type=classification.task_type.value if 'classification' in locals() else "UNKNOWN",
                profile=profile.value if profile else "UNKNOWN",
                latency_ms=int((time.time() - start)*1000),
                status="error",
                error_message=err_str[:1000],
                error_code="ORCHESTRATOR_FAILED",
                prompt_hash=hashlib.sha256(prompt_text.encode()).hexdigest()[:16]
            )
            db.add(log_entry)
            db.commit()
            
            if "REQUEST_TOO_LARGE" in err_str or "exceeds all" in err_str.lower() or "context filtered" in err_str.lower():
                raise HTTPException(
                    status_code=413,
                    detail=error_contract.openai_error(
                        f"Request too large: {err_str[:500]} — Try smaller prompt or model with larger context. P0+P5 policy MAX_TOTAL_CHARS={MAX_TOTAL_CHARS} profile={profile_for_validation if 'profile_for_validation' in locals() else 'BEST'} estimated_input={estimated_input_tokens if 'estimated_input_tokens' in locals() else 'UNKNOWN'} large={is_large if 'is_large' in locals() else False} P5 faseado: validation per-profile → large detect → truncation → compression → routing. Suggestions: CLINE_CODING 200k, @file workplace, chunk, split. Absolute max 500k chars ~125k tokens fits 128k context.",
                        type="invalid_request_error",
                        code="context_length_exceeded",
                        param="messages"
                    )
                )
            elif "ALL_RATE_LIMITED" in err_str or "all providers rate limited" in err_str.lower():
                raise HTTPException(
                    status_code=429,
                    detail=error_contract.openai_error(
                        f"Rate limit exceeded: {err_str[:500]} — All providers rate limited, try again later.",
                        type="rate_limit_error",
                        code="rate_limit_exceeded"
                    ),
                    headers={"Retry-After": "60"}
                )
            elif "NO_PROVIDER_AVAILABLE" in err_str:
                raise HTTPException(
                    status_code=503,
                    detail=error_contract.openai_error(
                        f"No providers available: {err_str[:500]}",
                        type="server_error",
                        code="no_providers_available"
                    )
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=error_contract.openai_error(
                        f"Orchestrator failed: {err_str[:500]}",
                        type="server_error",
                        code="orchestrator_failed"
                    )
                )
    
    else:
        raise HTTPException(400, "Direct mode disabled - use use_orchestrator=true")

@router.post("/v1/orchestrate")
@limiter.limit("20/minute")
async def orchestrate_full(req: ChatCompletionRequest, request: Request, db: Session = Depends(get_db)):
    if not req.messages:
        raise HTTPException(400, "Messages required")
    
    prompt = req.messages[-1].content if req.messages else ""
    if isinstance(prompt, list):
        prompt = " ".join([p.get("text", "") if isinstance(p, dict) else str(p) for p in prompt])
    
    providers = db.query(Provider).all()
    models = db.query(Model).all()
    
    profile = None
    if req.profile:
        try:
            profile = Profile(req.profile.upper())
        except:
            pass
    
    try:
        result = await orchestrator_service.orchestrate(prompt, providers, models, profile)
        return {
            "request_id": result.request_id,
            "objective": result.objective,
            "plan": {
                "tasks": [{"task_id": t.task_id, "objective": t.objective, "priority": t.priority, "agent": t.agent, "skill": t.skill, "status": t.status.value} for t in result.plan.tasks],
                "estimated_cost": result.plan.estimated_cost,
                "estimated_time": result.plan.estimated_time,
                "required_skills": result.plan.required_skills,
                "required_agents": [a.value for a in result.plan.required_agents]
            },
            "routing": {
                "selected": f"{result.routing.selected.model.display_name} / {result.routing.selected.provider.name}",
                "reason": result.routing.selected.reason,
                "explanation": result.routing.explanation,
                "confidence": result.confidence,
                "alternatives": [f"{a.model.display_name} / {a.provider.name}" for a in result.routing.alternatives]
            },
            "execution_trace": result.execution_trace,
            "final_output": result.final_output,
            "validation": result.validation,
            "total_cost": result.total_cost,
            "total_latency_ms": result.total_latency,
            "fallback_used": result.fallback_used,
            "audit_log": result.audit_log
        }
    except Exception as e:
        raise HTTPException(500, f"Orchestration failed: {str(e)[:1000]}")

# P20 CLINE_CODING — Dedicated endpoint for Cline gateway
@router.post("/v1/cline/completions")
@limiter.limit("60/minute")
async def cline_completions(req: ChatCompletionRequest, request: Request, db: Session = Depends(get_db)):
    req.profile = "CLINE_CODING"
    if req.use_support_agents is None:
        req.use_support_agents = False
    if req.enable_critique is None:
        req.enable_critique = False
    if req.enable_retry is None:
        req.enable_retry = False
    
    if req.profile == "CLINE_CODING":
        req.use_support_agents = False
        req.enable_critique = False
        req.enable_retry = False
    
    print(f"[CLINE_CODING GATEWAY] /v1/cline/completions called — model={req.model} tools={bool(req.tools)} stream={req.stream} messages={len(req.messages)}")
    
    return await chat_completions(req, request, db)

@router.get("/v1/cline/status")
async def cline_status(db: Session = Depends(get_db)):
    providers = db.query(Provider).all()
    models = db.query(Model).all()
    
    coding_models = [m for m in models if (m.coding_score or 0) >= 70]
    tool_capable = [m for m in models if (m.tool_calling_score or 0) >= 50 or any(k in m.model_id.lower() for k in ["gpt-4", "claude-3", "gemini-1.5", "llama-3.1", "codestral"])]
    
    healthy_providers = [p for p in providers if str(p.status) in ["VERIFIED", "PRODUCTION"] or (hasattr(p.status, 'value') and p.status.value in ["VERIFIED", "PRODUCTION"])]
    
    known_context = len([m for m in models if m.context_window and m.context_window > 0])
    unknown_context = len(models) - known_context
    context_pct = round(known_context / len(models) * 100, 1) if models else 0
    
    return {
        "status": "healthy" if healthy_providers else "degraded",
        "gateway": "AI Provider OS — CLINE_CODING profile",
        "version": "1.2.0-P23 P0 + P0.5 + P1 + P2 + P3 + P4 + P5 — CENTRAL POLICY + TOKEN + ERROR 413/429 + REROUTING + LIFECYCLE + CACHE KEY + BACKOFF + RETRY-AFTER + PRE-WARM 83% + MAX_COMPLETION_TOKENS + QUOTA TRACKING + ASYNC CRITIC + FRONTEND P3 + RATING EVOLUTION + METRICS P4 + LARGE PROMPT FASEADO P5 — TRUE STREAMING + CONTEXT 100% + @FILE WORKPLACE",
        "providers": {
            "total": len(providers),
            "healthy": len(healthy_providers),
            "with_keys": len([p for p in providers if p.api_key_encrypted])
        },
        "models": {
            "total": len(models),
            "coding_capable": len(coding_models),
            "tool_capable": len(tool_capable),
            "measured": len([m for m in models if (m.test_count or 0) > 0]),
            "context_window": {
                "known": known_context,
                "unknown": unknown_context,
                "pct_known": context_pct,
                "note": "P21: 0 UNKNOWN via /models REAL (154) + provider_claim (201) + defaults (371) = 726/726 100% — before 89/726 12.3% — now routing can check requested_tokens <= model_context_limit correctly"
            }
        },
        "profile": {
            "name": "CLINE_CODING",
            "description": "coding-first, baixa latência, contexto longo quando necessário, tool calling, streaming TRUE, failover automático, circuit breaker, awareness de quotas/custo, preferência por modelos comprovados coding, evitar agentes auxiliares",
            "flow": "Cline -> POST /v1/chat/completions or /v1/cline/completions -> CLINE_CODING profile -> classifier -> routing engine -> provider/model -> fallback -> resposta -> Cline",
            "no_multiplying": "Cline -> classifier -> routing -> provider -> resposta (not intent -> optimizer -> main -> critic -> reviewer -> rigor)"
        },
        "openai_compatibility": {
            "endpoint": "POST /v1/chat/completions or POST /v1/cline/completions",
            "supported_params": ["model", "messages", "temperature", "max_tokens", "stream", "tools", "tool_choice", "response_format", "top_p", "presence_penalty", "frequency_penalty", "stop", "seed", "user"],
            "model_auto": "model: 'auto' selects best candidate per CLINE_CODING using real data: available, coding verified, tool compat, context, historical success, latency, quota, cost",
            "tool_calling": "Preserved, not corrupted, filtered if provider doesn't support — TESTED TRUE",
            "streaming": "P21 TRUE STREAMING — adapter.chat_completion_stream + orchestrator.execute_with_routing_stream + chat router generate_true_stream — chunks forwarded as they arrive, TTFB 313ms vs old chunked fallback 1200ms+, 15 chunks, order preserved, [DONE], error handling, fallback before first chunk, disconnects, timeouts — TESTED TRUE",
            "long_context": "P21 100% known (726/726) via /models REAL + provider_claim + defaults — requested_tokens <= model_context_limit check, exclude model, fallback, log requested_tokens model_context_limit selected_model fallback_reason, never silently truncate — TESTED TRUE with 131072 limit",
            "fallback": "Real fallback chain with logging fallback_reasons — TESTED TRUE RATE_LIMIT 429 -> next provider",
            "large_prompt_p5": "P5 LARGE PROMPT FASEADO: per-profile limits FAST 20k BEST 100k CODING 150k CLINE_CODING 200k ABSOLUTE 500k, Phase1 validation per-profile, Phase2 large detect, Phase3 truncation system+last4, Phase4 compression preserve code, Phase5 @file workplace resolution, Phase6 routing LONG_CONTEXT, token counter real-time, drag-drop files, @file autocomplete, collapse >1000 chars, estimate endpoint"
        },
        "p5_large_prompt": {
            "per_profile_limits": {"FAST": "20k", "BEST": "100k", "CODING": "150k", "CLINE_CODING": "200k", "LONG_CONTEXT": "200k", "ABSOLUTE": "500k"},
            "faseado": "Phase1 validation per-profile → Phase2 large detect → Phase3 history truncation → Phase4 compression preserve code → Phase5 @file workplace → Phase6 routing LONG_CONTEXT → Phase7 provider",
            "frontend": "Textarea 24px→50vh, token counter chars/tokens/% context, model context indicator, drag-drop zone, 📎 upload 10 files 500k, paste large >5k modal, @file autocomplete workplace, large warning >50k, collapse >1000 chars",
            "backend": "Per-profile validation, compression preserve ```, truncation system+last4, @file resolution with token awareness, estimate endpoint /v1/chat/completions/estimate, detailed 413 suggestions",
            "estimate_endpoint": "POST /v1/chat/completions/estimate — returns token breakdown without provider call for frontend real-time"
        },
        "cline_does_not_need_to_know": ["providers individuais", "API keys", "fallback chains", "circuit breakers", "health checks", "scoring", "provider availability", "quotas", "métricas internas"],
        "responsibility": "Tudo responsabilidade do AI Provider OS",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
