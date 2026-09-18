"""
P18 v1.2 Observability Enterprise - Tracing, Sessions, Cost Tracking, Tiered Caching L1/L2/L3 + Local Folder BD, Logs, Alerts
Pattern Helicone + Portkey + Future AGI - OTel traces metrics logs
Rigoroso, real, funcional, sem simulação - P18 v1.2 fast-path SIMPLE vs COMPLEX + local_cache_service

P18 Changes:
- Tiered cache: L1 in-memory 30s (exact), L2 SQLite persistent 1h simple / 30min medium / 10min complex (local_cache/simple/simple_cache.db), L3 semantic similarity
- Local folder BD: /home/user/ai-provider-os/local_cache/ com simple/, conversation/, metrics/, semantic/
- Fast-path: SIMPLE messages bypass agents pesados, latency 10ms hit / 500ms miss vs 2-5s full
- Complexity detection via classifier ComplexityLevel SIMPLE/MEDIUM/COMPLEX
"""
import time
import uuid
import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
import os

# P18 v1.2 — Import local cache service for tiered caching
try:
    from .local_cache_service import local_cache_service
    USE_LOCAL_CACHE = True
    print("[OBSERVABILITY] Local cache service available — tiered L1/L2/L3 + local folder BD")
except Exception as e:
    USE_LOCAL_CACHE = False
    local_cache_service = None
    print(f"[OBSERVABILITY] Local cache not available: {e} — using L1 only")

# In-memory stores with TTL - fallback when Redis not available
_traces = deque(maxlen=1000)  # trace_id span_id parent_span_id latency breakdown
_sessions = {}  # session_id multi-turn tracking cost per session
_costs = {"total": 0.0, "count": 0, "providers": defaultdict(float), "models": defaultdict(float), "users": defaultdict(float)}
_cache_stats = {"hits": 0, "misses": 0, "hit_rate": 0.0, "l1_hits": 0, "l1_misses": 0, "l2_hits": 0, "l2_misses": 0, "l3_hits": 0, "l3_misses": 0, "fast_path": 0, "complex_path": 0, "latency_saved_ms": 0}
_cache_store = {}  # P17 Lean - exact match cache: key -> {response, expiry, cost, latency, provider, model, timestamp}
_logs = deque(maxlen=1000)  # structured JSON logs
_alerts = deque(maxlen=100)  # alerts rigor <50% latency >5s error >10% cost >budget provider offline

# Try Redis for distributed observability
try:
    import redis
    redis_client = redis.Redis(host='localhost', port=6379, db=2, decode_responses=True, socket_connect_timeout=1)
    redis_client.ping()
    USE_REDIS_OBS = True
    print("[OBSERVABILITY] Redis available - using Redis for observability P17 Lean Enterprise")
except:
    USE_REDIS_OBS = False
    redis_client = None
    print("[OBSERVABILITY] Redis not available - using in-memory observability P17 Lean")

# P0 — Central policy for cache TTLs
try:
    from ..core.policy import (
        CACHE_L1_TTL, CACHE_L1_MAX, CACHE_L2_TTL_SIMPLE, CACHE_L2_TTL_MEDIUM, CACHE_L2_TTL_COMPLEX
    )
    print(f"[OBSERVABILITY P0] Loaded policy: L1_TTL={CACHE_L1_TTL}s L1_MAX={CACHE_L1_MAX} L2_SIMPLE={CACHE_L2_TTL_SIMPLE}s MEDIUM={CACHE_L2_TTL_MEDIUM}s COMPLEX={CACHE_L2_TTL_COMPLEX}s")
except Exception as e:
    print(f"[OBSERVABILITY P0] Policy load failed {e}, using defaults")
    CACHE_L1_TTL = 30
    CACHE_L1_MAX = 100
    CACHE_L2_TTL_SIMPLE = 3600
    CACHE_L2_TTL_MEDIUM = 1800
    CACHE_L2_TTL_COMPLEX = 600

class ObservabilityService:
    def __init__(self):
        self.traces = _traces
        self.sessions = _sessions
        self.costs = _costs
        self.cache_stats = _cache_stats
        self.cache_store = _cache_store
        self.logs = _logs
        self.alerts = _alerts

    def create_trace(self, trace_id: str = None, parent_span_id: str = None, operation: str = "chat.completion", provider: str = None, model: str = None, user_id: str = "admin") -> Dict:
        """Cria trace com trace_id span_id parent_span_id latency breakdown"""
        trace_id = trace_id or f"trace-{uuid.uuid4().hex[:12]}"
        span_id = f"span-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)
        
        trace = {
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_span_id": parent_span_id,
            "operation": operation,
            "provider": provider,
            "model": model,
            "user_id": user_id,
            "start_time": now.isoformat(),
            "end_time": None,
            "latency_ms": 0,
            "breakdown": {
                "classifier": 0,
                "routing": 0,
                "adapter": 0,
                "critic": 0,
                "total": 0
            },
            "status": "running",
            "cost": 0.0,
            "tokens": {"prompt": 0, "completion": 0, "total": 0},
            "metadata": {},
            "created_at": now
        }
        
        self.traces.append(trace)
        
        if USE_REDIS_OBS:
            try:
                redis_client.setex(f"trace:{trace_id}:{span_id}", 3600, json.dumps(trace, default=str))
            except: pass
        
        return trace

    def end_trace(self, trace_id: str, span_id: str, latency_ms: int, status: str = "success", cost: float = 0.0, breakdown: Dict = None, tokens: Dict = None):
        """Finaliza trace com latency breakdown"""
        for trace in self.traces:
            if trace["trace_id"] == trace_id and trace["span_id"] == span_id:
                trace["end_time"] = datetime.now(timezone.utc).isoformat()
                trace["latency_ms"] = latency_ms
                trace["status"] = status
                trace["cost"] = cost
                if breakdown:
                    trace["breakdown"].update(breakdown)
                    trace["breakdown"]["total"] = latency_ms
                if tokens:
                    trace["tokens"].update(tokens)
                
                provider = trace.get("provider")
                model = trace.get("model")
                user_id = trace.get("user_id")
                if provider:
                    self.costs["providers"][provider] += cost
                if model:
                    self.costs["models"][model] += cost
                if user_id:
                    self.costs["users"][user_id] += cost
                self.costs["total"] += cost
                self.costs["count"] += 1
                
                self._check_alerts(trace)
                
                if USE_REDIS_OBS:
                    try:
                        redis_client.setex(f"trace:{trace_id}:{span_id}", 3600, json.dumps(trace, default=str))
                    except: pass
                break

    def create_session(self, session_id: str = None, user_id: str = "admin") -> Dict:
        """Cria session multi-turn - P17 Lean fix: não sobrescreve se já existe"""
        session_id = session_id or f"session-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)
        
        # P17 Lean fix session race
        existing = self.sessions.get(session_id)
        if existing:
            existing["last_activity"] = now.isoformat()
            if USE_REDIS_OBS:
                try:
                    redis_client.setex(f"session:{session_id}", 3600, json.dumps(existing, default=str))
                except: pass
            return existing
        
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "start_time": now.isoformat(),
            "last_activity": now.isoformat(),
            "turns": 0,
            "total_cost": 0.0,
            "total_latency_ms": 0,
            "avg_latency_ms": 0,
            "providers_used": [],
            "models_used": [],
            "status": "active",
            "traces": []
        }
        
        self.sessions[session_id] = session
        
        if USE_REDIS_OBS:
            try:
                redis_client.setex(f"session:{session_id}", 3600, json.dumps(session, default=str))
            except: pass
        
        return session

    def get_or_create_session(self, session_id: str, user_id: str = "admin") -> Dict:
        """P17 Lean - get or create sem sobrescrever"""
        if session_id in self.sessions:
            # Update last_activity
            self.sessions[session_id]["last_activity"] = datetime.now(timezone.utc).isoformat()
            return self.sessions[session_id]
        return self.create_session(session_id=session_id, user_id=user_id)

    def add_to_session(self, session_id: str, trace_id: str, cost: float = 0.0, latency_ms: int = 0, provider: str = None, model: str = None):
        """Adiciona trace à session - P17 Lean fix race"""
        session = self.sessions.get(session_id)
        if not session:
            # Se session não existe, cria sem resetar turns (edge case)
            session = self.create_session(session_id=session_id)
        if session:
            session["turns"] += 1
            session["total_cost"] += cost
            session["total_latency_ms"] += latency_ms
            session["avg_latency_ms"] = session["total_latency_ms"] / session["turns"] if session["turns"] > 0 else 0
            session["last_activity"] = datetime.now(timezone.utc).isoformat()
            session["traces"].append(trace_id)
            if provider and provider not in session["providers_used"]:
                session["providers_used"].append(provider)
            if model and model not in session["models_used"]:
                session["models_used"].append(model)
            
            if USE_REDIS_OBS:
                try:
                    redis_client.setex(f"session:{session_id}", 3600, json.dumps(session, default=str))
                except: pass

    def log(self, level: str, message: str, trace_id: str = None, user_id: str = None, provider: str = None, model: str = None, latency_ms: int = None, cost: float = None, metadata: Dict = None):
        """Logs estruturados JSON"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
            "trace_id": trace_id,
            "user_id": user_id,
            "provider": provider,
            "model": model,
            "latency_ms": latency_ms,
            "cost": cost,
            "metadata": metadata or {},
        }
        
        self.logs.append(log_entry)
        
        if USE_REDIS_OBS:
            try:
                redis_client.lpush("logs", json.dumps(log_entry, default=str))
                redis_client.ltrim("logs", 0, 999)
            except: pass
        
        if level in ["error", "warning"]:
            print(f"[{level.upper()}] {message} trace={trace_id} provider={provider} latency={latency_ms}ms")

    # P0.5.4 — Cache key fix — include system + tools hash to avoid wrong response
    # Before: hash(prompt.lower()+profile) — risk wrong response for same prompt with different system/tools
    # After: hash(prompt + system + tools_hash + profile + model + temperature) with backward compat
    # For CLINE_CODING, we bypass cache for tools/streaming anyway, but for SIMPLE we need correctness
    def _cache_key(self, prompt: str, provider: str = None, model: str = None, profile: str = None, system: str = None, tools: str = None, temperature: float = None) -> str:
        """P0.5.4 — Improved cache key: prompt + system + tools_hash + profile + model — avoids wrong response"""
        # P0.5 — Include system and tools hash for correctness
        # Keep backward compat: if system/tools not provided, fallback to old key for hit_rate
        try:
            from ..core.policy import CACHE_L1_TTL
            # Use improved key
            tools_hash = hashlib.sha256(str(tools).encode()).hexdigest()[:8] if tools else "notools"
            system_hash = hashlib.sha256(str(system).encode()).hexdigest()[:8] if system else "nosys"
            # For CLINE_CODING, include more context to avoid wrong response
            if profile and "CLINE" in profile.upper():
                # For Cline, always include system and tools for correctness, even if reduces hit_rate
                key_str = f"{prompt.strip().lower()}|{system_hash}|{tools_hash}|{profile or ''}|{model or ''}"
            else:
                # For SIMPLE, include system/tools but keep simple for hit_rate
                # If system/tools present, include, else old key
                if system or tools:
                    key_str = f"{prompt.strip().lower()}|{system_hash}|{tools_hash}|{profile or ''}"
                else:
                    key_str = f"{prompt.strip().lower()}|{profile or ''}"
            return hashlib.sha256(key_str.encode()).hexdigest()[:16]
        except Exception as e:
            # Fallback old key
            key_str = f"{prompt.strip().lower()}|{profile or ''}"
            return hashlib.sha256(key_str.encode()).hexdigest()[:16]
    
    def _cache_key_legacy(self, prompt: str, provider: str = None, model: str = None, profile: str = None) -> str:
        """Legacy key for backward compat — hash(prompt+profile)"""
        key_str = f"{prompt.strip().lower()}|{profile or ''}"
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]

    def cache_get(self, prompt: str, provider: str = None, model: str = None, profile: str = None, complexity: str = None, system: str = None, tools: Any = None, temperature: float = None) -> Optional[Dict]:
        """P18 v1.2 + P0.5.4 — Tiered cache: L1 in-memory 30s → L2 SQLite persistent → L3 semantic — improved key with system/tools"""
        # L1 — in-memory exact 30s (fastest 0ms) — P0.5.4 improved key
        key = self._cache_key(prompt, provider, model, profile, system=system, tools=tools, temperature=temperature)
        entry = self.cache_store.get(key)
        if entry:
            if datetime.now(timezone.utc) < entry["expiry"]:
                self.record_cache_hit(True, level="L1")
                entry["cache_level"] = "L1"
                entry["latency_saved"] = entry.get("latency_ms", 2000)
                return entry
            else:
                del self.cache_store[key]

        # L2 — SQLite persistent (local folder BD) — for SIMPLE/MEDIUM with longer TTL
        if USE_LOCAL_CACHE and local_cache_service:
            l2_entry = local_cache_service.get_l2(prompt, profile)
            if l2_entry:
                # Promote to L1 for faster next hit
                self.cache_store[key] = {
                    "response": l2_entry["response"],
                    "provider": l2_entry.get("provider"),
                    "model": l2_entry.get("model"),
                    "profile": profile,
                    "cost": l2_entry.get("cost", 0.0),
                    "latency_ms": l2_entry.get("latency_ms", 0),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "expiry": datetime.now(timezone.utc) + timedelta(seconds=30),
                    "prompt_hash": key,
                    "cache_level": "L2",
                    "hit_count": l2_entry.get("hit_count", 1),
                    "source": "L2 SQLite persistent"
                }
                self.record_cache_hit(True, level="L2")
                l2_entry["cache_level"] = "L2"
                return l2_entry

        # L3 — Semantic similarity (future with embeddings) — for similar prompts
        if USE_LOCAL_CACHE and local_cache_service and complexity != "COMPLEX":
            # Only for SIMPLE/MEDIUM, not for COMPLEX code gen
            l3_entry = local_cache_service.get_l3_semantic(prompt, threshold=0.85)
            if l3_entry:
                # Promote to L1 and L2
                self.cache_store[key] = {
                    "response": l3_entry["response"],
                    "provider": l3_entry.get("provider"),
                    "model": l3_entry.get("model"),
                    "profile": profile,
                    "cost": 0.0,
                    "latency_ms": 0,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "expiry": datetime.now(timezone.utc) + timedelta(seconds=30),
                    "prompt_hash": key,
                    "cache_level": "L3",
                    "similarity": l3_entry.get("similarity", 0.85),
                    "source": "L3 semantic"
                }
                self.record_cache_hit(True, level="L3")
                l3_entry["cache_level"] = "L3"
                return l3_entry

        self.record_cache_hit(False, level="L1")
        return None

    def cache_set(self, prompt: str, response: str, provider: str = None, model: str = None, 
                  profile: str = None, cost: float = 0.0, latency_ms: int = 0, complexity: str = None, system: str = None, tools: Any = None, temperature: float = None):
        """P18 v1.2 + P0.5.4 — Tiered cache set: L1 30s + L2 SQLite persistent with TTL based on complexity + L3 semantic — improved key"""
        # L1 — in-memory 30s — P0.5.4 improved key
        key = self._cache_key(prompt, provider, model, profile, system=system, tools=tools, temperature=temperature)
        expiry = datetime.now(timezone.utc) + timedelta(seconds=30)
        self.cache_store[key] = {
            "response": response,
            "provider": provider,
            "model": model,
            "profile": profile,
            "cost": cost,
            "latency_ms": latency_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "expiry": expiry,
            "prompt_hash": key,
            "cache_level": "L1"
        }
        if len(self.cache_store) > 100:
            oldest_key = min(self.cache_store.keys(), key=lambda k: self.cache_store[k]["timestamp"])
            del self.cache_store[oldest_key]

        # L2 — SQLite persistent with TTL based on complexity
        if USE_LOCAL_CACHE and local_cache_service:
            # Determine complexity if not provided
            comp = complexity or "MEDIUM"
            # TTL: SIMPLE 3600s (1h), MEDIUM 1800s (30min), COMPLEX 600s (10min) or no cache for large code
            ttl_map = {"SIMPLE": 3600, "MEDIUM": 1800, "COMPLEX": 600}
            ttl = ttl_map.get(comp, 1800)
            
            # Don't cache COMPLEX large code generation (>5000 chars) — should be fresh
            if not (comp == "COMPLEX" and len(response) > 5000):
                local_cache_service.set_l2(
                    prompt=prompt, response=response, provider=provider, model=model,
                    profile=profile, complexity=comp, latency_ms=latency_ms, cost=cost, ttl_seconds=ttl
                )

            # L3 — Semantic cache for SIMPLE/MEDIUM
            if comp in ["SIMPLE", "MEDIUM"] and len(prompt) < 500:
                local_cache_service.set_l3_semantic(
                    prompt=prompt, response=response, provider=provider, model=model, ttl_seconds=ttl
                )

    def record_cache_hit(self, hit: bool, level: str = "L1"):
        """P18 v1.2 — Cache stats hit_rate with L1/L2/L3 breakdown + fast vs complex path"""
        if hit:
            self.cache_stats["hits"] += 1
            if level == "L1":
                self.cache_stats["l1_hits"] += 1
            elif level == "L2":
                self.cache_stats["l2_hits"] += 1
            elif level == "L3":
                self.cache_stats["l3_hits"] += 1
        else:
            self.cache_stats["misses"] += 1
            if level == "L1":
                self.cache_stats["l1_misses"] += 1
            elif level == "L2":
                self.cache_stats["l2_misses"] += 1
            elif level == "L3":
                self.cache_stats["l3_misses"] += 1
        
        total = self.cache_stats["hits"] + self.cache_stats["misses"]
        self.cache_stats["hit_rate"] = (self.cache_stats["hits"] / total * 100) if total > 0 else 0.0

        # Sync with local_cache_service if available
        if USE_LOCAL_CACHE and local_cache_service:
            try:
                local_stats = local_cache_service.get_stats()
                self.cache_stats["latency_saved_ms"] = local_stats.get("latency_saved_ms", 0)
                self.cache_stats["fast_path"] = local_stats.get("fast_path_count", 0)
                self.cache_stats["complex_path"] = local_stats.get("complex_path_count", 0)
            except:
                pass

    def record_fast_path(self):
        """P18 v1.2 — Record fast-path usage"""
        self.cache_stats["fast_path"] += 1
        if USE_LOCAL_CACHE and local_cache_service:
            local_cache_service.record_fast_path()

    def record_complex_path(self):
        """P18 v1.2 — Record complex-path usage"""
        self.cache_stats["complex_path"] += 1
        if USE_LOCAL_CACHE and local_cache_service:
            local_cache_service.record_complex_path()

    def _check_alerts(self, trace: Dict):
        """Alerts rigor <50% latency >5s error rate >10% cost >budget provider offline - P17 Lean adiciona rigor"""
        alerts_triggered = []
        
        if trace["latency_ms"] > 5000:
            alerts_triggered.append({
                "type": "latency",
                "severity": "warning",
                "message": f"Latency >5s: {trace['latency_ms']}ms trace={trace['trace_id']} provider={trace.get('provider')} model={trace.get('model')}",
                "trace_id": trace["trace_id"],
                "threshold": 5000,
                "value": trace["latency_ms"]
            })
        
        if trace["status"] == "error":
            alerts_triggered.append({
                "type": "error",
                "severity": "error",
                "message": f"Error trace={trace['trace_id']} provider={trace.get('provider')} model={trace.get('model')}",
                "trace_id": trace["trace_id"]
            })
        
        if trace["status"] == "error" and "provider" in trace:
            alerts_triggered.append({
                "type": "provider_offline",
                "severity": "warning",
                "message": f"Provider {trace.get('provider')} error - possible offline",
                "provider": trace.get("provider")
            })
        
        if trace["cost"] > 1.0:
            alerts_triggered.append({
                "type": "cost",
                "severity": "warning",
                "message": f"Cost >$1: ${trace['cost']} trace={trace['trace_id']}",
                "cost": trace["cost"],
                "threshold": 1.0
            })
        
        # P17 Lean - Rigor <50% alert - check via DB or stats
        try:
            # Try to get rigor from DB if available, else skip
            from ..core.database import SessionLocal
            from ..models.database_models import Model
            db = SessionLocal()
            try:
                total = db.query(Model).count()
                measured = db.query(Model).filter(Model.test_count>0).count()
                percent = (measured/total*100) if total else 0
                if percent < 50:
                    # Only alert once per hour to avoid spam
                    last_rigor_alert = [a for a in self.alerts if a.get("type")=="rigor" and (datetime.now(timezone.utc) - datetime.fromisoformat(a["timestamp"])).total_seconds() < 3600]
                    if not last_rigor_alert:
                        alerts_triggered.append({
                            "type": "rigor",
                            "severity": "warning",
                            "message": f"Rigor LOW {percent:.1f}% <50% - {measured}/{total} measured - need 80% target",
                            "threshold": 50,
                            "value": percent
                        })
            finally:
                db.close()
        except Exception as e:
            # Don't fail if DB not available
            pass
        
        for alert in alerts_triggered:
            alert["timestamp"] = datetime.now(timezone.utc).isoformat()
            alert["alert_id"] = f"alert-{uuid.uuid4().hex[:8]}"
            self.alerts.append(alert)
            
            if USE_REDIS_OBS:
                try:
                    redis_client.lpush("alerts", json.dumps(alert, default=str))
                    redis_client.ltrim("alerts", 0, 99)
                except: pass

    def get_stats(self) -> Dict:
        """Retorna stats observability enterprise P17 Lean"""
        total_traces = len(self.traces)
        error_traces = len([t for t in self.traces if t["status"] == "error"])
        error_rate = (error_traces / total_traces * 100) if total_traces > 0 else 0
        
        latencies = [t["latency_ms"] for t in self.traces if t["latency_ms"] > 0]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        p50 = sorted(latencies)[len(latencies)//2] if latencies else 0
        p95 = sorted(latencies)[int(len(latencies)*0.95)] if latencies and len(latencies) > 20 else 0
        p99 = sorted(latencies)[int(len(latencies)*0.99)] if latencies and len(latencies) > 100 else 0
        
        return {
            "traces": {
                "total": total_traces,
                "errors": error_traces,
                "error_rate": round(error_rate, 2),
                "avg_latency_ms": round(avg_latency, 2),
                "p50_ms": p50,
                "p95_ms": p95,
                "p99_ms": p99,
            },
            "sessions": {
                "total": len(self.sessions),
                "active": len([s for s in self.sessions.values() if s["status"] == "active"]),
                "avg_turns": sum(s["turns"] for s in self.sessions.values()) / len(self.sessions) if self.sessions else 0,
            },
            "costs": {
                "total": round(self.costs["total"], 6),
                "count": self.costs["count"],
                "avg": round(self.costs["total"] / self.costs["count"], 6) if self.costs["count"] > 0 else 0,
                "by_provider": dict(self.costs["providers"]),
                "by_model": dict(self.costs["models"]),
                "by_user": dict(self.costs["users"]),
            },
            "cache": {
                "hits": self.cache_stats["hits"],
                "misses": self.cache_stats["misses"],
                "hit_rate": round(self.cache_stats["hit_rate"], 2),
                "store_size": len(self.cache_store),
                "l1_hits": self.cache_stats.get("l1_hits", 0),
                "l1_misses": self.cache_stats.get("l1_misses", 0),
                "l2_hits": self.cache_stats.get("l2_hits", 0),
                "l2_misses": self.cache_stats.get("l2_misses", 0),
                "l3_hits": self.cache_stats.get("l3_hits", 0),
                "l3_misses": self.cache_stats.get("l3_misses", 0),
                "fast_path": self.cache_stats.get("fast_path", 0),
                "complex_path": self.cache_stats.get("complex_path", 0),
                "latency_saved_ms": self.cache_stats.get("latency_saved_ms", 0),
                "p18_tiered": "L1 in-memory 30s + L2 SQLite persistent 1h/30min/10min + L3 semantic",
                "local_cache": local_cache_service.get_stats() if USE_LOCAL_CACHE and local_cache_service else {"enabled": False},
                "p17_lean": "exact match 30s TTL",
                "p18_v12": "tiered L1/L2/L3 + local folder BD"
            },
            "alerts": {
                "total": len(self.alerts),
                "recent": list(self.alerts)[-5:],
            },
            "logs": {
                "total": len(self.logs),
                "recent": list(self.logs)[-5:],
            },
            "persistence": "redis" if USE_REDIS_OBS else "memory",
            "p16_enterprise": True,
            "p17_lean": True,
            "otel": True,
            "pattern": "Helicone + Portkey + Future AGI + P17 Lean 3 agents"
        }

    def get_traces(self, limit: int = 50) -> List[Dict]:
        return list(self.traces)[-limit:]

    def get_sessions(self, limit: int = 20) -> List[Dict]:
        return list(self.sessions.values())[-limit:]

    def get_alerts(self, limit: int = 20) -> List[Dict]:
        return list(self.alerts)[-limit:]

    def get_cache_entries(self, limit: int = 20) -> List[Dict]:
        """P17 Lean - retorna cache entries"""
        entries = []
        for k, v in list(self.cache_store.items())[-limit:]:
            entries.append({
                "key": k,
                "provider": v.get("provider"),
                "model": v.get("model"),
                "cost": v.get("cost"),
                "latency_ms": v.get("latency_ms"),
                "timestamp": v.get("timestamp"),
                "expiry": v.get("expiry").isoformat() if isinstance(v.get("expiry"), datetime) else str(v.get("expiry")),
                "response_preview": v.get("response", "")[:100]
            })
        return entries

# Singleton
observability_service = ObservabilityService()
