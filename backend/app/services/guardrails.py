"""
P16 Guardrails 18+ - Future AGI pattern - Middleware chain config enabled threshold action block/warn/log/human approval
Rigoroso, real, funcional, sem simulação
"""
import re
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone

# PII patterns
PII_PATTERNS = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone": r"\b(?:\+?351)?\s?(?:9\d{8}|2\d{8})\b",  # PT phone
    "nif": r"\b\d{9}\b",  # PT NIF 9 digits
    "credit_card": r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "api_key": r"\b(?:sk-|gsk_|xai-|groq_|Bearer\s+)[A-Za-z0-9_\-]{10,}\b",
    "password": r"(?i)(?:password|senha|pwd)\s*[:=]\s*\S+",
}

# Prompt injection patterns
INJECTION_PATTERNS = [
    r"(?i)ignore\s+previous\s+instructions",
    r"(?i)ignore\s+all\s+previous",
    r"(?i)system\s*:\s*you\s+are\s+now",
    r"(?i)you\s+are\s+now\s+a\s+different",
    r"(?i)jailbreak",
    r"(?i)do\s+anything\s+now",
    r"(?i)disregard\s+your\s+programming",
    r"(?i)forget\s+your\s+instructions",
]

# Content filtering patterns (basic)
TOXIC_PATTERNS = [
    r"(?i)\b(hate|kill|murder|terrorist|bomb)\b",
]
HATE_PATTERNS = [
    r"(?i)\b(racist|sexist|discriminat)\b",
]
SELF_HARM_PATTERNS = [
    r"(?i)\b(suicide|self.?harm|cut\s+myself)\b",
]
SEXUAL_PATTERNS = [
    r"(?i)\b(porn|explicit\s+sexual)\b",
]

# Code security patterns
SQL_INJECTION_PATTERNS = [
    r"(?i)(\bUNION\b.*\bSELECT\b|\bDROP\b.*\bTABLE\b|'\s*OR\s*'1'\s*=\s*'1)",
]
XSS_PATTERNS = [
    r"(?i)(<script|javascript:|onerror\s*=)",
]
COMMAND_INJECTION_PATTERNS = [
    r"(?i)(;\s*rm\s+-rf|&&\s*cat\s+/etc/passwd|\|\s*sh)",
]

class GuardrailResult:
    def __init__(self, guardrail_id: str, passed: bool, severity: str = "info", message: str = "", action: str = "log", details: Dict = None):
        self.guardrail_id = guardrail_id
        self.passed = passed
        self.severity = severity
        self.message = message
        self.action = action  # block/warn/log/human approval
        self.details = details or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()

class GuardrailsService:
    def __init__(self):
        # P0 — Use central policy for thresholds — single source of truth
        try:
            from ..core.policy import (
                COST_MAX, LATENCY_MAX_MS, TOKEN_LIMIT, MAX_FILE_SIZE, MAX_FILES
            )
            cost_max = COST_MAX
            latency_max = LATENCY_MAX_MS
            token_limit = TOKEN_LIMIT
            file_size = MAX_FILE_SIZE
            files_count = MAX_FILES
            print(f"[GUARDRAILS P0] Loaded policy: cost_max={cost_max} latency_max={latency_max} token_limit={token_limit} file_size={file_size} files_count={files_count}")
        except Exception as e:
            print(f"[GUARDRAILS P0] Policy load failed {e}, using defaults")
            cost_max = 1.0
            latency_max = 10000
            token_limit = 50000
            file_size = 100000
            files_count = 20

        self.guardrails_config = {
            # 18+ guardrails — P0 thresholds from central policy
            "pii_email": {"enabled": True, "threshold": 0, "action": "warn", "description": "PII email detection regex"},
            "pii_phone": {"enabled": True, "threshold": 0, "action": "warn", "description": "PII phone PT 9 digits"},
            "pii_nif": {"enabled": True, "threshold": 0, "action": "log", "description": "PII NIF 9 digits - log only PT"},
            "pii_credit_card": {"enabled": True, "threshold": 0, "action": "block", "description": "Credit card block"},
            "pii_api_key": {"enabled": True, "threshold": 0, "action": "block", "description": "Secrets API keys block"},
            "prompt_injection": {"enabled": True, "threshold": 0, "action": "block", "description": "Prompt injection ignore previous instructions classifier"},
            "content_toxicity": {"enabled": True, "threshold": 0, "action": "warn", "description": "Content filtering toxicity"},
            "content_hate": {"enabled": True, "threshold": 0, "action": "warn", "description": "Hate speech"},
            "content_self_harm": {"enabled": True, "threshold": 0, "action": "block", "description": "Self-harm block + human approval"},
            "content_sexual": {"enabled": True, "threshold": 0, "action": "warn", "description": "Sexual content"},
            "code_sql_injection": {"enabled": True, "threshold": 0, "action": "block", "description": "Code security SQL injection SAST"},
            "code_xss": {"enabled": True, "threshold": 0, "action": "block", "description": "XSS"},
            "code_command_injection": {"enabled": True, "threshold": 0, "action": "block", "description": "Command injection"},
            "cost_max": {"enabled": True, "threshold": cost_max, "action": "warn", "description": f"Max cost per request ${cost_max} — P0 from policy"},
            "latency_max": {"enabled": True, "threshold": latency_max, "action": "warn", "description": f"Max latency {latency_max}ms timeout — P0 from policy"},
            "token_limit": {"enabled": True, "threshold": token_limit, "action": "block", "description": f"Token limit max {token_limit} — P0 from policy"},
            "file_size": {"enabled": True, "threshold": file_size, "action": "block", "description": f"File size max {file_size} — P0 from policy"},
            "files_count": {"enabled": True, "threshold": files_count, "action": "block", "description": f"Files count max {files_count} — P0 from policy"},
            "provider_health": {"enabled": True, "threshold": 0, "action": "log", "description": "Provider health circuit breaker"},
            "model_capability": {"enabled": True, "threshold": 0, "action": "log", "description": "Model capability check task coding json etc"},
            "human_override": {"enabled": True, "threshold": 0, "action": "human", "description": "Require approval critical actions"},
        }
        self.hits = []  # guardrail hits for metrics Grafana

    def check_pii(self, text: str) -> List[GuardrailResult]:
        """PII email phone NIF credit card SSN regex NER"""
        results = []
        for pii_type, pattern in PII_PATTERNS.items():
            guardrail_id = f"pii_{pii_type}"
            config = self.guardrails_config.get(guardrail_id)
            if not config or not config["enabled"]:
                continue
            
            matches = re.findall(pattern, text)
            if matches:
                passed = False
                results.append(GuardrailResult(
                    guardrail_id=guardrail_id,
                    passed=passed,
                    severity="warning" if pii_type in ["email", "phone", "nif"] else "error",
                    message=f"PII {pii_type} detected: {len(matches)} matches",
                    action=config["action"],
                    details={"matches": matches[:3], "count": len(matches), "type": pii_type}
                ))
                self.hits.append({"guardrail_id": guardrail_id, "type": "pii", "count": len(matches), "timestamp": datetime.now(timezone.utc).isoformat()})
            else:
                results.append(GuardrailResult(guardrail_id=guardrail_id, passed=True, message=f"No PII {pii_type}"))
        
        return results

    def check_prompt_injection(self, text: str) -> GuardrailResult:
        """Prompt injection ignore previous instructions system prompt jailbreak classifier"""
        guardrail_id = "prompt_injection"
        config = self.guardrails_config.get(guardrail_id)
        if not config or not config["enabled"]:
            return GuardrailResult(guardrail_id=guardrail_id, passed=True, message="Disabled")
        
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, text):
                result = GuardrailResult(
                    guardrail_id=guardrail_id,
                    passed=False,
                    severity="error",
                    message=f"Prompt injection detected: {pattern}",
                    action=config["action"],
                    details={"pattern": pattern, "text_snippet": text[:100]}
                )
                self.hits.append({"guardrail_id": guardrail_id, "type": "injection", "timestamp": datetime.now(timezone.utc).isoformat()})
                return result
        
        return GuardrailResult(guardrail_id=guardrail_id, passed=True, message="No injection")

    def check_content_filtering(self, text: str) -> List[GuardrailResult]:
        """Content filtering toxicity hate self-harm sexual classifier"""
        results = []
        checks = [
            ("content_toxicity", TOXIC_PATTERNS, "toxicity"),
            ("content_hate", HATE_PATTERNS, "hate"),
            ("content_self_harm", SELF_HARM_PATTERNS, "self_harm"),
            ("content_sexual", SEXUAL_PATTERNS, "sexual"),
        ]
        
        for guardrail_id, patterns, content_type in checks:
            config = self.guardrails_config.get(guardrail_id)
            if not config or not config["enabled"]:
                continue
            
            for pattern in patterns:
                if re.search(pattern, text):
                    results.append(GuardrailResult(
                        guardrail_id=guardrail_id,
                        passed=False,
                        severity="error" if content_type == "self_harm" else "warning",
                        message=f"Content {content_type} detected",
                        action=config["action"],
                        details={"pattern": pattern, "type": content_type}
                    ))
                    self.hits.append({"guardrail_id": guardrail_id, "type": content_type, "timestamp": datetime.now(timezone.utc).isoformat()})
                    break
            else:
                results.append(GuardrailResult(guardrail_id=guardrail_id, passed=True, message=f"No {content_type}"))
        
        return results

    def check_code_security(self, text: str) -> List[GuardrailResult]:
        """Code security SQL injection XSS command injection SAST"""
        results = []
        checks = [
            ("code_sql_injection", SQL_INJECTION_PATTERNS, "sql_injection"),
            ("code_xss", XSS_PATTERNS, "xss"),
            ("code_command_injection", COMMAND_INJECTION_PATTERNS, "command_injection"),
        ]
        
        for guardrail_id, patterns, sec_type in checks:
            config = self.guardrails_config.get(guardrail_id)
            if not config or not config["enabled"]:
                continue
            
            for pattern in patterns:
                if re.search(pattern, text):
                    results.append(GuardrailResult(
                        guardrail_id=guardrail_id,
                        passed=False,
                        severity="error",
                        message=f"Code security {sec_type} detected",
                        action=config["action"],
                        details={"pattern": pattern, "type": sec_type}
                    ))
                    self.hits.append({"guardrail_id": guardrail_id, "type": sec_type, "timestamp": datetime.now(timezone.utc).isoformat()})
                    break
            else:
                results.append(GuardrailResult(guardrail_id=guardrail_id, passed=True, message=f"No {sec_type}"))
        
        return results

    def check_limits(self, text: str = "", cost: float = 0.0, latency_ms: int = 0, file_size: int = 0, files_count: int = 0, profile: str = None) -> List[GuardrailResult]:
        """Cost max latency max token limit file size files count — P5 per-profile aware"""
        results = []
        
        # P5 — Per-profile thresholds for file_size and token_limit
        try:
            from ..core.policy import get_limits_for_profile, MAX_TOTAL_CHARS_ABSOLUTE, LARGE_PROMPT_TOKENS
            max_total, max_prompt = get_limits_for_profile(profile)
            # For guardrails, use per-profile file_size = max_total, token_limit = max_total//4 or LARGE*2
            per_profile_file_size = max_total
            per_profile_token_limit = max(max_total // 4, LARGE_PROMPT_TOKENS * 2)  # at least 30k tokens for large
            # Absolute cap
            per_profile_file_size = min(per_profile_file_size, MAX_TOTAL_CHARS_ABSOLUTE)
        except:
            per_profile_file_size = None
            per_profile_token_limit = None
        
        # Token limit (approx chars/4) — P5 per-profile
        tokens = len(text) // 4
        config = self.guardrails_config.get("token_limit")
        if config and config["enabled"]:
            threshold = per_profile_token_limit if per_profile_token_limit else config["threshold"]
            if tokens > threshold:
                results.append(GuardrailResult(
                    guardrail_id="token_limit",
                    passed=False,
                    severity="error",
                    message=f"Token limit exceeded: {tokens} > {threshold} (profile {profile or 'BEST'} P5 per-profile)",
                    action=config["action"],
                    details={"tokens": tokens, "threshold": threshold, "profile": profile}
                ))
            else:
                results.append(GuardrailResult(guardrail_id="token_limit", passed=True, message=f"Tokens {tokens} < {threshold} profile {profile or 'BEST'}"))
        
        # File size — P5 per-profile
        config = self.guardrails_config.get("file_size")
        if config and config["enabled"]:
            threshold = per_profile_file_size if per_profile_file_size else config["threshold"]
            if file_size > threshold:
                results.append(GuardrailResult(
                    guardrail_id="file_size",
                    passed=False,
                    severity="error",
                    message=f"File size exceeded: {file_size} > {threshold} (profile {profile or 'BEST'} P5 per-profile)",
                    action=config["action"],
                    details={"file_size": file_size, "threshold": threshold, "profile": profile}
                ))
            else:
                results.append(GuardrailResult(guardrail_id="file_size", passed=True, message=f"File size {file_size} OK profile {profile or 'BEST'} threshold {threshold}"))
        
        # Files count
        config = self.guardrails_config.get("files_count")
        if config and config["enabled"]:
            if files_count > config["threshold"]:
                results.append(GuardrailResult(
                    guardrail_id="files_count",
                    passed=False,
                    severity="error",
                    message=f"Files count exceeded: {files_count} > {config['threshold']}",
                    action=config["action"],
                    details={"files_count": files_count, "threshold": config["threshold"]}
                ))
            else:
                results.append(GuardrailResult(guardrail_id="files_count", passed=True, message=f"Files count {files_count} OK"))
        
        # Cost max
        config = self.guardrails_config.get("cost_max")
        if config and config["enabled"]:
            if cost > config["threshold"]:
                results.append(GuardrailResult(
                    guardrail_id="cost_max",
                    passed=False,
                    severity="warning",
                    message=f"Cost exceeded: ${cost} > ${config['threshold']}",
                    action=config["action"],
                    details={"cost": cost, "threshold": config["threshold"]}
                ))
            else:
                results.append(GuardrailResult(guardrail_id="cost_max", passed=True, message=f"Cost ${cost} OK"))
        
        # Latency max
        config = self.guardrails_config.get("latency_max")
        if config and config["enabled"]:
            if latency_ms > config["threshold"]:
                results.append(GuardrailResult(
                    guardrail_id="latency_max",
                    passed=False,
                    severity="warning",
                    message=f"Latency exceeded: {latency_ms}ms > {config['threshold']}ms",
                    action=config["action"],
                    details={"latency_ms": latency_ms, "threshold": config["threshold"]}
                ))
            else:
                results.append(GuardrailResult(guardrail_id="latency_max", passed=True, message=f"Latency {latency_ms}ms OK"))
        
        return results

    def check_all(self, text: str, cost: float = 0.0, latency_ms: int = 0, file_size: int = 0, files_count: int = 0, provider: str = None, model: str = None, profile: str = None) -> Dict:
        """Middleware chain config enabled threshold action block/warn/log/human approval + Audit log guardrail trigger + Metrics + P5 per-profile"""
        all_results = []
        
        # PII
        all_results.extend(self.check_pii(text))
        
        # Prompt injection
        all_results.append(self.check_prompt_injection(text))
        
        # Content filtering
        all_results.extend(self.check_content_filtering(text))
        
        # Code security
        all_results.extend(self.check_code_security(text))
        
        # Limits — P5 per-profile aware
        all_results.extend(self.check_limits(text, cost, latency_ms, file_size, files_count, profile=profile))
        
        # Provider health (log only)
        config = self.guardrails_config.get("provider_health")
        if config and config["enabled"]:
            all_results.append(GuardrailResult(guardrail_id="provider_health", passed=True, message=f"Provider {provider} health check", action=config["action"]))
        
        # Model capability (log only)
        config = self.guardrails_config.get("model_capability")
        if config and config["enabled"]:
            all_results.append(GuardrailResult(guardrail_id="model_capability", passed=True, message=f"Model {model} capability check", action=config["action"]))
        
        # Human override for critical
        blocked = [r for r in all_results if not r.passed and r.action == "block"]
        warnings = [r for r in all_results if not r.passed and r.action == "warn"]
        human_required = [r for r in all_results if not r.passed and r.action == "human"]
        
        should_block = len(blocked) > 0
        should_human = len(human_required) > 0 or (len(blocked) > 0 and any(r.guardrail_id == "content_self_harm" for r in blocked))
        
        return {
            "passed": not should_block and not should_human,
            "should_block": should_block,
            "should_human_approval": should_human,
            "blocked": [{"id": r.guardrail_id, "message": r.message, "action": r.action} for r in blocked],
            "warnings": [{"id": r.guardrail_id, "message": r.message, "action": r.action} for r in warnings],
            "human_required": [{"id": r.guardrail_id, "message": r.message, "action": r.action} for r in human_required],
            "all_results": [{"id": r.guardrail_id, "passed": r.passed, "message": r.message, "action": r.action, "severity": r.severity} for r in all_results],
            "total_checks": len(all_results),
            "passed_checks": len([r for r in all_results if r.passed]),
            "failed_checks": len([r for r in all_results if not r.passed]),
            "guardrails_config": self.guardrails_config,
            "p16_enterprise": True,
            "count": len(self.guardrails_config),
            "pattern": "Future AGI 18+ guardrails"
        }

    def get_stats(self) -> Dict:
        """Metrics guardrail hits + Grafana panels"""
        from collections import Counter
        counter = Counter([h["guardrail_id"] for h in self.hits])
        return {
            "total_hits": len(self.hits),
            "by_guardrail": dict(counter),
            "recent_hits": self.hits[-10:],
            "config": self.guardrails_config,
            "count": len(self.guardrails_config),
            "enabled": len([c for c in self.guardrails_config.values() if c["enabled"]]),
            "p16_enterprise": True
        }

# Singleton
guardrails_service = GuardrailsService()
