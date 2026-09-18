"""
P0.1 + P5 — Central Policy — Single Source + Large Prompt Handling Faseado

P0: centraliza 33 números hardcoded
P5: per-profile limits + compression + history truncation + large handling

Antes P22:
- chat.py: total_chars >20000 + prompt_text >10000 duplicados conflitam → 12435 falha um passa outro
- guardrails.py: token_limit 50000, file_size 100000, files_count 20, latency_max 10000
- projects.py: prompt >10000, response >50000, total_file_size >100000
- observability.py: cache L1 30s max 100, L2 3600/1800/600
- http_client.py: provider cache 60s, http pool keepalive 20 max 100 expiry 30s
- database.py: pool_size 10 max_overflow 20 timeout 30 recycle 3600
- main.py: rate limit 100/min global, chat 30/min, cline 60/min

Depois P0: Todos centralizados, env vars com defaults documentados, coerentes
MAX_TOTAL_CHARS 100000 (era 20000) + MAX_PROMPT_CHARS 50000 (era 10000) → 12435 passa ambos
Razão: safety guardrail vs model_context_limit (726/726 100% known) — chars é safety, tokens é principal

P5 Large Prompt:
- Per-profile limits: CLINE_CODING 200k, BEST 100k, FAST 20k, CODING 150k, REASONING 100k
- chars ≠ tokens, tokens principal, chars safety — CLINE_CODING precisa 200k porque envia files
- Compression preserve code inside ```
- History truncation: keep system + last 2 user/assistant
- Estimate endpoint for frontend real-time
"""

import os
import re
from typing import Dict, Any, List, Optional, Tuple

def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except:
        return default

def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except:
        return default

# ===== REQUEST LIMITS — Safety Guardrails (chars) — P0 fix duplicados =====
# P5: per-profile limits — CLINE_CODING larger for Cline file context
MAX_TOTAL_CHARS = _env_int("MAX_TOTAL_CHARS", 100000)  # default BEST
MAX_PROMPT_CHARS = _env_int("MAX_PROMPT_CHARS", 100000)  # default BEST
MAX_REQUEST_CHARS = _env_int("MAX_REQUEST_CHARS", 100000)
MAX_SYSTEM_CHARS = _env_int("MAX_SYSTEM_CHARS", 20000)

# P5 — Per-profile limits — chars safety, tokens principal
MAX_TOTAL_CHARS_FAST = _env_int("MAX_TOTAL_CHARS_FAST", 20000)  # FAST: greeting, FAQ
MAX_PROMPT_CHARS_FAST = _env_int("MAX_PROMPT_CHARS_FAST", 20000)

MAX_TOTAL_CHARS_BEST = _env_int("MAX_TOTAL_CHARS_BEST", 100000)
MAX_PROMPT_CHARS_BEST = _env_int("MAX_PROMPT_CHARS_BEST", 100000)

MAX_TOTAL_CHARS_CODING = _env_int("MAX_TOTAL_CHARS_CODING", 150000)  # coding files
MAX_PROMPT_CHARS_CODING = _env_int("MAX_PROMPT_CHARS_CODING", 150000)

MAX_TOTAL_CHARS_REASONING = _env_int("MAX_TOTAL_CHARS_REASONING", 100000)
MAX_PROMPT_CHARS_REASONING = _env_int("MAX_PROMPT_CHARS_REASONING", 100000)

MAX_TOTAL_CHARS_CLINECODING = _env_int("MAX_TOTAL_CHARS_CLINECODING", 200000)  # Cline sends files
MAX_PROMPT_CHARS_CLINECODING = _env_int("MAX_PROMPT_CHARS_CLINECODING", 200000)

MAX_TOTAL_CHARS_LONG_CONTEXT = _env_int("MAX_TOTAL_CHARS_LONG_CONTEXT", 200000)
MAX_PROMPT_CHARS_LONG_CONTEXT = _env_int("MAX_PROMPT_CHARS_LONG_CONTEXT", 200000)

# Absolute max — safety cap even for CLINE_CODING
MAX_TOTAL_CHARS_ABSOLUTE = _env_int("MAX_TOTAL_CHARS_ABSOLUTE", 500000)  # 500k chars ~125k tokens, fits 128k context
MAX_PROMPT_CHARS_ABSOLUTE = _env_int("MAX_PROMPT_CHARS_ABSOLUTE", 500000)

# ===== CONTEXT TOKENS — Principal, não safety — model_context_limit é real 726/726 100% =====
MAX_CONTEXT_TOKENS = _env_int("MAX_CONTEXT_TOKENS", 128000)  # safety max, não model limit
DEFAULT_OUTPUT_TOKENS = _env_int("DEFAULT_OUTPUT_TOKENS", 2000)
MAX_OUTPUT_TOKENS = _env_int("MAX_OUTPUT_TOKENS", 8192)
TOKEN_ESTIMATE_RATIO = _env_int("TOKEN_ESTIMATE_RATIO", 4)  # chars // 4
CONTEXT_OVERHEAD = _env_int("CONTEXT_OVERHEAD", 200)  # system+tools+overhead

# P5 — Large prompt thresholds for phased handling
LARGE_PROMPT_CHARS = _env_int("LARGE_PROMPT_CHARS", 50000)  # >50k = large
VERY_LARGE_PROMPT_CHARS = _env_int("VERY_LARGE_PROMPT_CHARS", 100000)  # >100k = very large
LARGE_PROMPT_TOKENS = _env_int("LARGE_PROMPT_TOKENS", 15000)  # >15k tokens = large
HISTORY_TRUNCATION_KEEP_LAST = _env_int("HISTORY_TRUNCATION_KEEP_LAST", 4)  # keep last 4 messages (2 user + 2 assistant)

# ===== FILES & TOKENS GUARDRAILS =====
MAX_FILES = _env_int("MAX_FILES", 20)
MAX_FILE_SIZE = _env_int("MAX_FILE_SIZE", 100000)
TOKEN_LIMIT = _env_int("TOKEN_LIMIT", 50000)  # guardrail, não model limit
LATENCY_MAX_MS = _env_int("LATENCY_MAX_MS", 10000)
COST_MAX = _env_float("COST_MAX", 1.0)

# ===== PROJECTS =====
PROJECT_MAX_PROMPT = _env_int("PROJECT_MAX_PROMPT", 20000)
PROJECT_MAX_RESPONSE = _env_int("PROJECT_MAX_RESPONSE", 50000)
PROJECT_MAX_TOTAL_FILE_SIZE = _env_int("PROJECT_MAX_TOTAL_FILE_SIZE", 100000)

# ===== CACHE =====
CACHE_L1_TTL = _env_int("CACHE_L1_TTL", 30)
CACHE_L1_MAX = _env_int("CACHE_L1_MAX", 100)
CACHE_L2_TTL_SIMPLE = _env_int("CACHE_L2_TTL_SIMPLE", 3600)
CACHE_L2_TTL_MEDIUM = _env_int("CACHE_L2_TTL_MEDIUM", 1800)
CACHE_L2_TTL_COMPLEX = _env_int("CACHE_L2_TTL_COMPLEX", 600)
PROVIDER_CACHE_TTL = _env_int("PROVIDER_CACHE_TTL", 60)

# ===== HTTP POOL =====
HTTP_POOL_KEEPALIVE = _env_int("HTTP_POOL_KEEPALIVE", 50)  # P24 200 providers — 20→50 for 200 providers
HTTP_POOL_MAX = _env_int("HTTP_POOL_MAX", 200)  # P24 200 providers — 100→200 for 200 providers
HTTP_POOL_EXPIRY = _env_float("HTTP_POOL_EXPIRY", 30.0)
HTTP_TIMEOUT_CONNECT = _env_float("HTTP_TIMEOUT_CONNECT", 5.0)
HTTP_TIMEOUT_READ = _env_float("HTTP_TIMEOUT_READ", 60.0)
HTTP_TIMEOUT_WRITE = _env_float("HTTP_TIMEOUT_WRITE", 10.0)
HTTP_TIMEOUT_POOL = _env_float("HTTP_TIMEOUT_POOL", 5.0)
REQUEST_TIMEOUT = _env_int("REQUEST_TIMEOUT", 60)
REQUEST_TIMEOUT_CAP = _env_int("REQUEST_TIMEOUT_CAP", 120)

# ===== DB POOL =====
DB_POOL_SIZE = _env_int("DB_POOL_SIZE", 10)
DB_MAX_OVERFLOW = _env_int("DB_MAX_OVERFLOW", 20)
DB_POOL_TIMEOUT = _env_int("DB_POOL_TIMEOUT", 30)
DB_POOL_RECYCLE = _env_int("DB_POOL_RECYCLE", 3600)
DB_CACHE_SIZE_MB = _env_int("DB_CACHE_SIZE_MB", 64)
DB_MMAP_SIZE_MB = _env_int("DB_MMAP_SIZE_MB", 256)

# ===== RATE LIMIT =====
RATE_LIMIT_GLOBAL = os.getenv("RATE_LIMIT_GLOBAL", "100/minute")
RATE_LIMIT_CHAT = os.getenv("RATE_LIMIT_CHAT", "30/minute")
RATE_LIMIT_CLINE = os.getenv("RATE_LIMIT_CLINE", "60/minute")
RATE_LIMIT_ORCHESTRATE = os.getenv("RATE_LIMIT_ORCHESTRATE", "20/minute")
RATE_LIMIT_ESTIMATE = os.getenv("RATE_LIMIT_ESTIMATE", "60/minute")

# ===== FALLBACK =====
MAX_RETRIES = _env_int("MAX_RETRIES", 1)
MAX_FALLBACKS = _env_int("MAX_FALLBACKS", 4)
CIRCUIT_FAILURE_THRESHOLD = _env_int("CIRCUIT_FAILURE_THRESHOLD", 5)
CIRCUIT_RECOVERY_TIMEOUT = _env_int("CIRCUIT_RECOVERY_TIMEOUT", 60)

# ===== AUTH =====
REQUIRE_AUTH_FOR_CHAT = os.getenv("REQUIRE_AUTH_FOR_CHAT", "false").lower() in ("true", "1", "yes")

# P5 — Profile limits map
PROFILE_LIMITS = {
    "FAST": (MAX_TOTAL_CHARS_FAST, MAX_PROMPT_CHARS_FAST),
    "BEST": (MAX_TOTAL_CHARS_BEST, MAX_PROMPT_CHARS_BEST),
    "CODING": (MAX_TOTAL_CHARS_CODING, MAX_PROMPT_CHARS_CODING),
    "REASONING": (MAX_TOTAL_CHARS_REASONING, MAX_PROMPT_CHARS_REASONING),
    "CLINE_CODING": (MAX_TOTAL_CHARS_CLINECODING, MAX_PROMPT_CHARS_CLINECODING),
    "LONG_CONTEXT": (MAX_TOTAL_CHARS_LONG_CONTEXT, MAX_PROMPT_CHARS_LONG_CONTEXT),
    "TOOL_CALLING": (MAX_TOTAL_CHARS_CODING, MAX_PROMPT_CHARS_CODING),
    "JSON": (MAX_TOTAL_CHARS_BEST, MAX_PROMPT_CHARS_BEST),
    "FREE": (MAX_TOTAL_CHARS_BEST, MAX_PROMPT_CHARS_BEST),
    "CHEAP": (MAX_TOTAL_CHARS_BEST, MAX_PROMPT_CHARS_BEST),
}

def get_limits_for_profile(profile: Optional[str]) -> Tuple[int, int]:
    """P5 — Get limits for profile, default BEST"""
    if not profile:
        return MAX_TOTAL_CHARS, MAX_PROMPT_CHARS
    upper = profile.upper()
    return PROFILE_LIMITS.get(upper, (MAX_TOTAL_CHARS, MAX_PROMPT_CHARS))

def get_policy_dict() -> Dict[str, Any]:
    """Retorna todas policies para observability / status"""
    return {
        "request": {
            "max_total_chars": MAX_TOTAL_CHARS,
            "max_prompt_chars": MAX_PROMPT_CHARS,
            "max_request_chars": MAX_REQUEST_CHARS,
            "max_system_chars": MAX_SYSTEM_CHARS,
            "max_context_tokens": MAX_CONTEXT_TOKENS,
            "default_output_tokens": DEFAULT_OUTPUT_TOKENS,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            "token_estimate_ratio": TOKEN_ESTIMATE_RATIO,
            "context_overhead": CONTEXT_OVERHEAD,
            "large_prompt_chars": LARGE_PROMPT_CHARS,
            "very_large_prompt_chars": VERY_LARGE_PROMPT_CHARS,
            "large_prompt_tokens": LARGE_PROMPT_TOKENS,
            "absolute_max_total": MAX_TOTAL_CHARS_ABSOLUTE,
            "absolute_max_prompt": MAX_PROMPT_CHARS_ABSOLUTE,
            "per_profile": {k: {"total": v[0], "prompt": v[1]} for k, v in PROFILE_LIMITS.items()},
        },
        "files": {
            "max_files": MAX_FILES,
            "max_file_size": MAX_FILE_SIZE,
            "token_limit": TOKEN_LIMIT,
            "latency_max_ms": LATENCY_MAX_MS,
            "cost_max": COST_MAX,
            "project_max_prompt": PROJECT_MAX_PROMPT,
            "project_max_response": PROJECT_MAX_RESPONSE,
            "project_max_total_file_size": PROJECT_MAX_TOTAL_FILE_SIZE,
        },
        "cache": {
            "l1_ttl": CACHE_L1_TTL,
            "l1_max": CACHE_L1_MAX,
            "l2_ttl_simple": CACHE_L2_TTL_SIMPLE,
            "l2_ttl_medium": CACHE_L2_TTL_MEDIUM,
            "l2_ttl_complex": CACHE_L2_TTL_COMPLEX,
            "provider_cache_ttl": PROVIDER_CACHE_TTL,
        },
        "http_pool": {
            "keepalive": HTTP_POOL_KEEPALIVE,
            "max": HTTP_POOL_MAX,
            "expiry": HTTP_POOL_EXPIRY,
            "timeout_connect": HTTP_TIMEOUT_CONNECT,
            "timeout_read": HTTP_TIMEOUT_READ,
            "timeout_write": HTTP_TIMEOUT_WRITE,
            "timeout_pool": HTTP_TIMEOUT_POOL,
            "request_timeout": REQUEST_TIMEOUT,
            "request_timeout_cap": REQUEST_TIMEOUT_CAP,
        },
        "db_pool": {
            "pool_size": DB_POOL_SIZE,
            "max_overflow": DB_MAX_OVERFLOW,
            "timeout": DB_POOL_TIMEOUT,
            "recycle": DB_POOL_RECYCLE,
            "cache_size_mb": DB_CACHE_SIZE_MB,
            "mmap_size_mb": DB_MMAP_SIZE_MB,
        },
        "rate_limit": {
            "global": RATE_LIMIT_GLOBAL,
            "chat": RATE_LIMIT_CHAT,
            "cline": RATE_LIMIT_CLINE,
            "orchestrate": RATE_LIMIT_ORCHESTRATE,
            "estimate": RATE_LIMIT_ESTIMATE,
        },
        "fallback": {
            "max_retries": MAX_RETRIES,
            "max_fallbacks": MAX_FALLBACKS,
            "circuit_failure_threshold": CIRCUIT_FAILURE_THRESHOLD,
            "circuit_recovery_timeout": CIRCUIT_RECOVERY_TIMEOUT,
        },
        "auth": {
            "require_auth_for_chat": REQUIRE_AUTH_FOR_CHAT,
        },
        "version": "P0 CENTRAL POLICY + P5 LARGE PROMPT FASEADO",
        "note": "Safety guardrail chars vs model_context_limit tokens — chars é safety, tokens é principal com 726/726 100% known. P5 per-profile CLINE_CODING 200k BEST 100k FAST 20k ABSOLUTE 500k. Faseado: validação per-profile → LONG_CONTEXT → truncation → routing"
    }

def validate_request_size(total_chars: int, prompt_chars: int) -> Tuple[bool, str]:
    """P0 validation default BEST"""
    return validate_request_size_profile(None, total_chars, prompt_chars)

def validate_request_size_profile(profile: Optional[str], total_chars: int, prompt_chars: int) -> Tuple[bool, str]:
    """
    P5 — Validação per-profile faseada
    Phase 1: absolute max check 500k
    Phase 2: per-profile limits
    Returns (is_valid, error_message)
    """
    # Phase 1: absolute cap — safety
    if total_chars > MAX_TOTAL_CHARS_ABSOLUTE:
        return False, f"Messages too large: {total_chars} chars > {MAX_TOTAL_CHARS_ABSOLUTE} absolute limit (MAX_TOTAL_CHARS_ABSOLUTE). Even for CLINE_CODING max 200k per-profile, absolute 500k. Try split, workplace @file, or chunk. P5 faseado: large data should use workplace files + @file reference."
    if prompt_chars > MAX_PROMPT_CHARS_ABSOLUTE:
        return False, f"Prompt too large: {prompt_chars} chars > {MAX_PROMPT_CHARS_ABSOLUTE} absolute limit. Try smaller, workplace @file, or chunk."
    
    # Phase 2: per-profile
    max_total, max_prompt = get_limits_for_profile(profile)
    if total_chars > max_total:
        return False, f"Messages too large for profile {profile or 'BEST'}: {total_chars} chars > {max_total} limit. Profile limits: FAST 20k, BEST 100k, CODING 150k, CLINE_CODING 200k, ABSOLUTE 500k. Try profile CLINE_CODING for large, or split, or workplace @file. P5 faseado."
    if prompt_chars > max_prompt:
        return False, f"Prompt too large for profile {profile or 'BEST'}: {prompt_chars} chars > {max_prompt} limit. Last user message too large. Try smaller, profile CLINE_CODING, workplace @file, or chunk. P5 faseado."
    
    return True, ""

def compress_prompt(text: str) -> str:
    """
    P5 — Compress prompt preserving code inside ``` — removes excessive whitespace
    Real, funcional, não simulação
    """
    if not text or len(text) < 1000:
        return text
    
    # Split by code blocks to preserve code formatting
    parts = re.split(r'(```.*?```)', text, flags=re.DOTALL)
    compressed_parts = []
    
    for part in parts:
        if part.startswith('```') and part.endswith('```'):
            # Preserve code block exactly
            compressed_parts.append(part)
        else:
            # Compress non-code: remove excessive blank lines, trailing spaces, but keep single newlines
            # Remove lines with only whitespace
            lines = part.split('\n')
            # Remove trailing spaces per line
            lines = [line.rstrip() for line in lines]
            # Collapse 3+ blank lines to 2
            new_lines = []
            blank_count = 0
            for line in lines:
                if not line.strip():
                    blank_count += 1
                    if blank_count <= 2:
                        new_lines.append(line)
                else:
                    blank_count = 0
                    new_lines.append(line)
            compressed = '\n'.join(new_lines)
            # Collapse multiple spaces to single (but not in code)
            compressed = re.sub(r' {3,}', '  ', compressed)
            compressed_parts.append(compressed)
    
    result = ''.join(compressed_parts)
    # Only return compressed if actually smaller and not too aggressive
    if len(result) < len(text) * 0.95:  # at least 5% saving
        print(f"[P5 COMPRESS] Compressed {len(text)} → {len(result)} chars saved {len(text)-len(result)} ({100-len(result)/len(text)*100:.1f}%)")
        return result
    return text

def truncate_history(messages: List[Dict], keep_last: int = 4) -> Tuple[List[Dict], bool, str]:
    """
    P5 — History truncation faseado: keep system + last N messages
    Returns (truncated_messages, was_truncated, reason)
    """
    if len(messages) <= keep_last + 1:  # +1 for system
        return messages, False, ""
    
    system_msgs = [m for m in messages if m.get('role') == 'system']
    non_system = [m for m in messages if m.get('role') != 'system']
    
    if len(non_system) <= keep_last:
        return messages, False, ""
    
    truncated_non_system = non_system[-keep_last:]
    truncated = system_msgs + truncated_non_system
    
    original_chars = sum(len(str(m.get('content',''))) for m in messages)
    truncated_chars = sum(len(str(m.get('content',''))) for m in truncated)
    
    reason = f"History truncated {len(messages)} → {len(truncated)} messages, {original_chars} → {truncated_chars} chars saved {original_chars-truncated_chars}, kept system + last {keep_last}"
    print(f"[P5 TRUNCATION] {reason}")
    
    return truncated, True, reason

def is_large_prompt(total_chars: int, estimated_tokens: int) -> Tuple[bool, str]:
    """P5 — Detect large prompt for phased handling"""
    if total_chars > VERY_LARGE_PROMPT_CHARS or estimated_tokens > LARGE_PROMPT_TOKENS * 2:
        return True, f"VERY_LARGE {total_chars} chars ~{estimated_tokens} tokens > {VERY_LARGE_PROMPT_CHARS} chars"
    if total_chars > LARGE_PROMPT_CHARS or estimated_tokens > LARGE_PROMPT_TOKENS:
        return True, f"LARGE {total_chars} chars ~{estimated_tokens} tokens > {LARGE_PROMPT_CHARS} chars"
    return False, ""

# Log on import
print(f"[POLICY P0+P5] Loaded central policy: MAX_TOTAL_CHARS={MAX_TOTAL_CHARS} MAX_PROMPT_CHARS={MAX_PROMPT_CHARS} MAX_CONTEXT_TOKENS={MAX_CONTEXT_TOKENS} PROVIDER_CACHE_TTL={PROVIDER_CACHE_TTL}s HTTP_POOL keepalive={HTTP_POOL_KEEPALIVE} max={HTTP_POOL_MAX}")
print(f"[POLICY P5] Per-profile limits: FAST 20k BEST 100k CODING 150k CLINE_CODING 200k LONG_CONTEXT 200k ABSOLUTE 500k | LARGE {LARGE_PROMPT_CHARS} VERY_LARGE {VERY_LARGE_PROMPT_CHARS} TOKENS {LARGE_PROMPT_TOKENS}")
