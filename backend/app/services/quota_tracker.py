"""
P2.2 — Provider Quota Tracking Real-time
Rastreia rate limit hits, remaining, reset, quota awareness para routing
- Captura headers X-RateLimit-Remaining, X-RateLimit-Reset, Retry-After, etc.
- Tracking por provider: quota_used, quota_limit, remaining, reset_time, hits
- Integração com circuit breaker e routing_engine quota_score
- Observability para dashboard
"""

import time
from typing import Dict, Optional
from collections import defaultdict

class QuotaTracker:
    def __init__(self):
        # provider_id -> quota info
        self.quotas: Dict[str, Dict] = {}
        # Rate limit hits per provider last hour
        self.hits: Dict[str, list] = defaultdict(list)  # provider_id -> list[timestamp]
        print("[QUOTA P2.2] Initialized quota tracker")

    def record_request(self, provider_id: str, headers: Optional[Dict] = None, status_code: Optional[int] = None):
        """Record request and parse quota headers if available"""
        now = time.time()
        
        if provider_id not in self.quotas:
            self.quotas[provider_id] = {
                "remaining": None,
                "limit": None,
                "reset": None,
                "reset_seconds": None,
                "quota_used": 0,
                "last_update": now,
                "rate_limit_hits": 0,
                "last_429": None,
                "headers_seen": []
            }
        
        quota = self.quotas[provider_id]
        quota["quota_used"] += 1
        quota["last_update"] = now
        
        # Parse quota headers if provided
        if headers:
            # Common headers: X-RateLimit-Remaining, X-RateLimit-Limit, X-RateLimit-Reset, Retry-After
            # Also: ratelimit-remaining, ratelimit-limit, ratelimit-reset (RFC)
            headers_lower = {k.lower(): v for k, v in headers.items()}
            
            # Remaining
            for key in ["x-ratelimit-remaining", "ratelimit-remaining", "x-ratelimit-remaining-requests", "remaining"]:
                if key in headers_lower:
                    try:
                        quota["remaining"] = int(headers_lower[key])
                        quota["headers_seen"].append(key)
                    except:
                        pass
            
            # Limit
            for key in ["x-ratelimit-limit", "ratelimit-limit", "x-ratelimit-limit-requests", "limit"]:
                if key in headers_lower:
                    try:
                        quota["limit"] = int(headers_lower[key])
                        quota["headers_seen"].append(key)
                    except:
                        pass
            
            # Reset
            for key in ["x-ratelimit-reset", "ratelimit-reset", "x-ratelimit-reset-requests"]:
                if key in headers_lower:
                    try:
                        reset_val = headers_lower[key]
                        # Could be seconds or timestamp
                        if len(str(reset_val)) > 10:  # timestamp ms
                            reset_ts = int(reset_val) / 1000 if int(reset_val) > 1e10 else int(reset_val)
                            quota["reset"] = reset_ts
                            quota["reset_seconds"] = max(0, int(reset_ts - now))
                        else:
                            # seconds from now or timestamp seconds
                            try:
                                reset_int = int(reset_val)
                                if reset_int < 100000:  # seconds from now
                                    quota["reset_seconds"] = reset_int
                                    quota["reset"] = now + reset_int
                                else:  # timestamp
                                    quota["reset"] = reset_int
                                    quota["reset_seconds"] = max(0, int(reset_int - now))
                            except:
                                pass
                        quota["headers_seen"].append(key)
                    except:
                        pass
            
            # Retry-After
            if "retry-after" in headers_lower:
                try:
                    retry_after = int(headers_lower["retry-after"])
                    quota["reset_seconds"] = retry_after
                    quota["reset"] = now + retry_after
                except:
                    pass

        # Track 429 hits
        if status_code == 429:
            quota["rate_limit_hits"] += 1
            quota["last_429"] = now
            self.hits[provider_id].append(now)
            # Keep only last hour
            self.hits[provider_id] = [t for t in self.hits[provider_id] if now - t < 3600]
            print(f"[QUOTA P2.2] {provider_id} 429 hit #{quota['rate_limit_hits']} remaining={quota['remaining']} reset={quota['reset_seconds']}s")

    def get_quota(self, provider_id: str) -> Dict:
        """Get quota info for provider"""
        return self.quotas.get(provider_id, {
            "remaining": None,
            "limit": None,
            "reset": None,
            "reset_seconds": None,
            "quota_used": 0,
            "rate_limit_hits": 0,
            "last_429": None
        })

    def get_all_quotas(self) -> Dict:
        """Get all quotas"""
        return self.quotas

    def get_quota_score(self, provider_id: str) -> int:
        """Get quota score 0-100 for routing — higher is better (more quota available)"""
        quota = self.quotas.get(provider_id)
        if not quota:
            return 100  # No data, assume full quota
        
        # If recent 429 hits, penalize
        now = time.time()
        recent_hits = len([t for t in self.hits.get(provider_id, []) if now - t < 300])  # last 5 min
        if recent_hits > 0:
            # 1 hit in 5 min → 70, 2 hits → 40, 3+ → 10
            if recent_hits >= 3:
                return 10
            elif recent_hits == 2:
                return 40
            else:
                return 70
        
        # If remaining is low, penalize
        remaining = quota.get("remaining")
        limit = quota.get("limit")
        if remaining is not None and limit:
            pct_remaining = remaining / limit * 100 if limit > 0 else 100
            if pct_remaining < 10:
                return 20
            elif pct_remaining < 30:
                return 50
            elif pct_remaining < 50:
                return 75
        
        # If reset soon, but still has quota, moderate score
        reset_seconds = quota.get("reset_seconds")
        if reset_seconds and reset_seconds < 60 and remaining is not None and remaining < 10:
            return 30
        
        return 100

    def get_stats(self):
        """Stats for observability"""
        total_hits = sum(len(h) for h in self.hits.values())
        providers_with_quota = len([q for q in self.quotas.values() if q.get("remaining") is not None])
        return {
            "total_providers_tracked": len(self.quotas),
            "providers_with_quota_headers": providers_with_quota,
            "total_429_hits_last_hour": total_hits,
            "quotas": self.quotas
        }

quota_tracker = QuotaTracker()
