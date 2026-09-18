import time
from typing import Dict
from datetime import datetime, timezone, timedelta
from enum import Enum
import json

class CircuitState(str, Enum):
    CLOSED = "CLOSED"  # normal
    OPEN = "OPEN"      # failing, don't send traffic
    HALF_OPEN = "HALF_OPEN"  # testing recovery

# P4 - Try Redis for persistent circuit breaker
try:
    import redis
    redis_client = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True, socket_connect_timeout=1)
    redis_client.ping()
    USE_REDIS_CB = True
    print("[CIRCUIT] Redis available - using Redis persistent circuit breaker P4")
except:
    USE_REDIS_CB = False
    redis_client = None
    print("[CIRCUIT] Redis not available - using in-memory circuit breaker")

# P0.5 — Exponential backoff + Retry-After parsing
# P0 policy for circuit breaker thresholds
try:
    from ..core.policy import CIRCUIT_FAILURE_THRESHOLD, CIRCUIT_RECOVERY_TIMEOUT
    DEFAULT_FAILURE_THRESHOLD = CIRCUIT_FAILURE_THRESHOLD
    DEFAULT_RECOVERY_TIMEOUT = CIRCUIT_RECOVERY_TIMEOUT
    print(f"[CIRCUIT P0.5] Loaded policy: failure_threshold={DEFAULT_FAILURE_THRESHOLD} recovery_timeout={DEFAULT_RECOVERY_TIMEOUT}s + exponential backoff + Retry-After")
except:
    DEFAULT_FAILURE_THRESHOLD = 5
    DEFAULT_RECOVERY_TIMEOUT = 60
    print(f"[CIRCUIT P0.5] Policy load failed, using defaults + exponential backoff + Retry-After")

class CircuitBreaker:
    def __init__(self, failure_threshold: int = None, recovery_timeout: int = None, half_open_max: int = 3):
        self.failure_threshold = failure_threshold or DEFAULT_FAILURE_THRESHOLD
        self.recovery_timeout = recovery_timeout or DEFAULT_RECOVERY_TIMEOUT
        self.half_open_max = half_open_max
        self.circuits: Dict[str, dict] = {}  # provider_id -> state
        # P0.5 — In-memory model failure tracking for DEPRECATED marking
        self.model_failures: Dict[str, int] = {}  # model_key provider_id/model_id -> count
        self.retry_after: Dict[str, float] = {}  # provider_id -> timestamp when retry allowed (from Retry-After header)

    def _get(self, provider_id: str):
        # P4 - Try Redis first for persistence
        if USE_REDIS_CB:
            try:
                data = redis_client.get(f"circuit:{provider_id}")
                if data:
                    c = json.loads(data)
                    if c.get("last_failure"):
                        c["last_failure"] = datetime.fromisoformat(c["last_failure"])
                    if c.get("opened_at"):
                        c["opened_at"] = datetime.fromisoformat(c["opened_at"])
                    # P0.5 — Check Retry-After from Redis if stored
                    if c.get("retry_after"):
                        self.retry_after[provider_id] = c["retry_after"]
                    return c
            except:
                pass
        
        if provider_id not in self.circuits:
            self.circuits[provider_id] = {
                "state": CircuitState.CLOSED,
                "failures": 0,
                "successes": 0,
                "last_failure": None,
                "opened_at": None,
                "half_open_attempts": 0,
                "retry_after": None,  # P0.5 — timestamp when retry allowed from Retry-After header
                "backoff_seconds": self.recovery_timeout  # P0.5 — exponential backoff
            }
        return self.circuits[provider_id]
    
    def _save(self, provider_id: str, circuit: dict):
        # Save to memory
        self.circuits[provider_id] = circuit
        # P4 - Save to Redis for persistence
        if USE_REDIS_CB:
            try:
                # Convert datetime to iso for json
                to_save = circuit.copy()
                if to_save.get("last_failure") and isinstance(to_save["last_failure"], datetime):
                    to_save["last_failure"] = to_save["last_failure"].isoformat()
                if to_save.get("opened_at") and isinstance(to_save["opened_at"], datetime):
                    to_save["opened_at"] = to_save["opened_at"].isoformat()
                redis_client.setex(f"circuit:{provider_id}", 3600, json.dumps(to_save))
            except:
                pass

    def can_execute(self, provider_id: str) -> bool:
        c = self._get(provider_id)
        now = datetime.now(timezone.utc)
        
        # P0.5 — Check Retry-After header — if set, don't execute before timestamp
        retry_after_ts = self.retry_after.get(provider_id)
        if retry_after_ts:
            if time.time() < retry_after_ts:
                # Still in Retry-After cooldown
                return False
            else:
                # Retry-After expired, clear
                self.retry_after.pop(provider_id, None)
                c["retry_after"] = None
        
        if c["state"] == CircuitState.CLOSED:
            return True
        if c["state"] == CircuitState.OPEN:
            # P0.5 — Exponential backoff: use backoff_seconds, not fixed recovery_timeout
            backoff = c.get("backoff_seconds", self.recovery_timeout)
            if c["opened_at"] and now > c["opened_at"] + timedelta(seconds=backoff):
                c["state"] = CircuitState.HALF_OPEN
                c["half_open_attempts"] = 0
                self._save(provider_id, c)
                print(f"[CIRCUIT P0.5] {provider_id} OPEN→HALF_OPEN after backoff {backoff}s (failures {c['failures']})")
                return True
            return False
        if c["state"] == CircuitState.HALF_OPEN:
            return c["half_open_attempts"] < self.half_open_max
        return False

    def record_success(self, provider_id: str):
        c = self._get(provider_id)
        c["successes"] += 1
        c["failures"] = 0
        c["backoff_seconds"] = self.recovery_timeout  # Reset backoff on success
        c["retry_after"] = None
        self.retry_after.pop(provider_id, None)
        if c["state"] == CircuitState.HALF_OPEN:
            c["half_open_attempts"] += 1
            if c["half_open_attempts"] >= 2:
                c["state"] = CircuitState.CLOSED
                c["opened_at"] = None
                print(f"[CIRCUIT P0.5] {provider_id} HALF_OPEN→CLOSED after 2 successes — recovery OK")
        elif c["state"] == CircuitState.OPEN:
            c["state"] = CircuitState.HALF_OPEN
        self._save(provider_id, c)

    def record_failure(self, provider_id: str, retry_after_seconds: int = None):
        c = self._get(provider_id)
        c["failures"] += 1
        c["last_failure"] = datetime.now(timezone.utc)
        c["successes"] = 0
        
        # P0.5 — Exponential backoff: 60s, 120s, 240s cap 300s
        # failures 1→60s, 2→120s, 3→240s, 4+→300s cap
        if c["failures"] == 1:
            c["backoff_seconds"] = self.recovery_timeout
        elif c["failures"] == 2:
            c["backoff_seconds"] = min(self.recovery_timeout * 2, 300)
        elif c["failures"] >= 3:
            c["backoff_seconds"] = min(self.recovery_timeout * (2 ** (c["failures"]-1)), 300)
        
        # P0.5 — Retry-After header handling
        if retry_after_seconds:
            retry_ts = time.time() + retry_after_seconds
            c["retry_after"] = retry_ts
            self.retry_after[provider_id] = retry_ts
            # Use max of backoff and Retry-After
            c["backoff_seconds"] = max(c["backoff_seconds"], retry_after_seconds)
            print(f"[CIRCUIT P0.5] {provider_id} Retry-After {retry_after_seconds}s → backoff {c['backoff_seconds']}s (failures {c['failures']})")
        
        if c["state"] == CircuitState.HALF_OPEN:
            c["state"] = CircuitState.OPEN
            c["opened_at"] = datetime.now(timezone.utc)
            print(f"[CIRCUIT P0.5] {provider_id} HALF_OPEN→OPEN after failure — backoff {c['backoff_seconds']}s")
        elif c["failures"] >= self.failure_threshold:
            c["state"] = CircuitState.OPEN
            c["opened_at"] = datetime.now(timezone.utc)
            print(f"[CIRCUIT P0.5] {provider_id} CLOSED→OPEN after {c['failures']} failures threshold {self.failure_threshold} — backoff {c['backoff_seconds']}s")
        self._save(provider_id, c)
    
    # P0.5.1 — Model lifecycle DEPRECATED after 3x MODEL_NOT_FOUND
    def record_model_failure(self, provider_id: str, model_id: str, error_type: str):
        """Track model failures — if MODEL_NOT_FOUND 3x, mark DEPRECATED"""
        if "MODEL_NOT_FOUND" not in error_type:
            return False
        key = f"{provider_id}/{model_id}"
        self.model_failures[key] = self.model_failures.get(key, 0) + 1
        print(f"[MODEL_LIFECYCLE P0.5.1] {key} MODEL_NOT_FOUND count {self.model_failures[key]}/3")
        if self.model_failures[key] >= 3:
            print(f"[MODEL_LIFECYCLE P0.5.1] {key} → DEPRECATED after 3x MODEL_NOT_FOUND — will skip in routing")
            # Try to update DB status to DEPRECATED
            try:
                from ..core.database import SessionLocal
                from ..models.database_models import Model, ModelStatus
                db = SessionLocal()
                try:
                    m = db.query(Model).filter(Model.provider_id==provider_id, Model.model_id==model_id).first()
                    if m and str(m.status) != "DEPRECATED" and getattr(m.status, 'value', str(m.status)) != "DEPRECATED":
                        m.status = ModelStatus.DEPRECATED
                        db.commit()
                        print(f"[MODEL_LIFECYCLE P0.5.1] DB marked {key} DEPRECATED")
                        # P0.5 — Invalidate provider cache to ensure DEPRECATED skipped immediately
                        try:
                            from .http_client import invalidate_provider_cache
                            invalidate_provider_cache()
                            print(f"[MODEL_LIFECYCLE P0.5.1] Invalidated provider cache after DEPRECATED {key}")
                        except Exception as e:
                            print(f"[MODEL_LIFECYCLE P0.5.1] Cache invalidate failed {e}")
                finally:
                    db.close()
            except Exception as e:
                print(f"[MODEL_LIFECYCLE P0.5.1] DB update failed {e}")
            return True
        return False
    
    def get_model_failures(self):
        return dict(self.model_failures)
    
    def parse_retry_after(self, headers: dict) -> int:
        """Parse Retry-After header — seconds or HTTP date"""
        if not headers:
            return None
        # Case-insensitive lookup
        retry_after = None
        for k,v in headers.items():
            if k.lower() == "retry-after":
                retry_after = v
                break
        if not retry_after:
            return None
        try:
            # Try seconds
            return int(str(retry_after).strip())
        except:
            try:
                # Try HTTP date
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(str(retry_after))
                now = datetime.now(timezone.utc)
                delta = (dt - now).total_seconds()
                return max(0, int(delta))
            except:
                return None

    def get_state(self, provider_id: str) -> dict:
        c = self._get(provider_id)
        # Convert datetime to string for API
        result = c.copy()
        if result.get("last_failure") and isinstance(result["last_failure"], datetime):
            result["last_failure"] = result["last_failure"].isoformat()
        if result.get("opened_at") and isinstance(result["opened_at"], datetime):
            result["opened_at"] = result["opened_at"].isoformat()
        result["persistence"] = "redis" if USE_REDIS_CB else "memory"
        return result

circuit_breaker = CircuitBreaker()
