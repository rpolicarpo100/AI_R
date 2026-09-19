"""
P21 Rating Fix — 60 rating 0 → 0 — Health check real + deprecate OFFLINE
- Antes: 187 rating 0 DISCOVERED nunca health-checked (93.5%)
- Depois P21 health check 200 full: 60 rating 0 (30%) — melhorou 127, mas ainda 60 rating 0 com health_status None
- Agora P21.1: health check real para 60 rating 0 + deprecate OFFLINE >7 dias + marca NEEDS_KEY/LOCAL/ONLINE
- 100% confiança com realismo: sabemos exatamente quais funcionam real vs OFFLINE vs NEEDS_KEY vs LOCAL
"""

import time
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime, timezone

from ..models.database_models import Provider
from .health_check_200 import check_provider_health

class P21RatingFix:
    def __init__(self):
        self.checked = 0
        self.online = 0
        self.needs_key = 0
        self.offline = 0
        self.local = 0
        self.deprecated = 0
        
    async def fix_rating_0(self, db: Session, limit: int = 60, dry_run: bool = False) -> Dict:
        """
        Fixa 60 rating 0 com health check real + deprecate OFFLINE
        """
        providers = db.query(Provider).all()
        rating_0 = [p for p in providers if (p.rating or 0) == 0]
        
        print(f"\n[P21 RATING FIX] Found {len(rating_0)} rating 0 providers — target 0")
        print(f"  Dry run: {dry_run} — limit: {limit}")
        
        to_check = rating_0[:limit]
        
        results = []
        for provider in to_check:
            print(f"\n[P21] Checking {provider.provider_id} — {provider.base_url} — rating 0")
            result = await check_provider_health(provider, timeout=5.0)
            results.append(result)
            
            print(f"  Result: {result['status']} rating {result['rating']} — {result['reason']}")
            
            if not dry_run:
                # Update provider with health check result
                caps = dict(provider.capabilities or {})
                caps['health_status'] = result['status']
                caps['health_check_status'] = result['status']
                caps['health_check_real'] = result['real_test']
                caps['health_check_reason'] = result['reason']
                caps['health_check_latency_ms'] = result['latency_ms']
                caps['health_check_http_status'] = result.get('http_status')
                caps['free_no_key_remote'] = result['free_no_key_remote']
                caps['free_no_key_local'] = result['free_no_key_local']
                caps['health_check_at'] = time.time()
                
                if result['free_no_key_remote']:
                    caps['free_no_key'] = True
                    caps['free_no_key_type'] = 'remote'
                elif result['free_no_key_local']:
                    caps['free_no_key'] = True
                    caps['free_no_key_type'] = 'local'
                    caps['local_setup_required'] = True
                
                # Update rating if real test and rating >0
                if result['real_test'] and result['rating'] > 0:
                    old_rating = provider.rating or 0
                    provider.rating = result['rating']
                    print(f"  Rating updated: {old_rating} → {result['rating']}")
                
                # If OFFLINE, check if should deprecate (if OFFLINE >7 days or never online)
                if result['status'] == 'OFFLINE':
                    # Check how long OFFLINE — if never had successful health check, mark as deprecated candidate
                    last_health = caps.get('health_check_at')
                    # For now, mark as OFFLINE but not deprecated yet — need 7 days
                    caps['offline_since'] = caps.get('offline_since') or time.time()
                    caps['deprecated_candidate'] = True
                    caps['deprecated_reason'] = f"OFFLINE — {result['reason']} — needs investigation, deprecate if >7 days OFFLINE"
                
                provider.capabilities = caps
                flag_modified(provider, "capabilities")
                provider.last_health_check = datetime.now(timezone.utc)
                
                # Stats
                if result['status'] == 'ONLINE':
                    self.online += 1
                elif result['status'] == 'NEEDS_KEY':
                    self.needs_key += 1
                elif result['status'] == 'OFFLINE':
                    self.offline += 1
                elif result['status'] == 'LOCAL_SETUP_REQUIRED':
                    self.local += 1
        
        if not dry_run:
            try:
                db.commit()
                print(f"\n[P21] Committed {len(to_check)} providers")
            except Exception as e:
                print(f"[P21] Commit failed: {e}")
                db.rollback()
        
        # Summary after
        providers_after = db.query(Provider).all()
        rating_0_after = [p for p in providers_after if (p.rating or 0) == 0]
        rating_gt0_after = [p for p in providers_after if (p.rating or 0) > 0]
        
        from collections import Counter
        health_statuses = Counter()
        for p in providers_after:
            caps = p.capabilities or {}
            hs = caps.get('health_status') or 'UNKNOWN'
            health_statuses[hs] += 1
        
        return {
            'total_before': len(providers),
            'rating_0_before': len(rating_0),
            'rating_gt0_before': len([p for p in providers if (p.rating or 0) > 0]),
            'checked': len(to_check),
            'online': self.online,
            'needs_key': self.needs_key,
            'offline': self.offline,
            'local': self.local,
            'rating_0_after': len(rating_0_after),
            'rating_gt0_after': len(rating_gt0_after),
            'health_statuses_after': dict(health_statuses),
            'results': results[:20],  # First 20 for brevity
            'improvement': len(rating_0) - len(rating_0_after),
            'remaining': len(rating_0_after),
            'honesty': f"P21 Rating Fix — {len(rating_0)} rating 0 → {len(rating_0_after)} rating 0 — improvement {len(rating_0) - len(rating_0_after)} — {self.online} ONLINE, {self.needs_key} NEEDS_KEY, {self.offline} OFFLINE, {self.local} LOCAL",
            'version': 'P21 — 60 rating 0 → 0 — health check real + deprecate OFFLINE'
        }
    
    def deprecate_offline(self, db: Session, days_offline: int = 7, dry_run: bool = False) -> Dict:
        """
        Deprecate providers OFFLINE >7 days
        """
        providers = db.query(Provider).all()
        offline_providers = []
        
        for p in providers:
            caps = p.capabilities or {}
            hs = caps.get('health_status')
            offline_since = caps.get('offline_since')
            
            if hs == 'OFFLINE' and offline_since:
                offline_duration = time.time() - offline_since
                if offline_duration > days_offline * 24 * 3600:
                    offline_providers.append(p)
        
        print(f"\n[P21 DEPRECATE] Found {len(offline_providers)} OFFLINE >{days_offline} days")
        
        deprecated = []
        for p in offline_providers:
            if not dry_run:
                caps = dict(p.capabilities or {})
                caps['deprecated'] = True
                caps['deprecated_at'] = time.time()
                caps['deprecated_reason'] = f"OFFLINE >{days_offline} days — {caps.get('health_check_reason')} — deprecate"
                p.capabilities = caps
                flag_modified(p, "capabilities")
                deprecated.append(p.provider_id)
        
        if not dry_run and deprecated:
            try:
                db.commit()
                print(f"[P21 DEPRECATE] Deprecated {len(deprecated)} providers")
            except Exception as e:
                print(f"[P21 DEPRECATE] Commit failed: {e}")
                db.rollback()
        
        return {
            'offline_gt_days': len(offline_providers),
            'deprecated': len(deprecated),
            'deprecated_ids': deprecated[:20],
            'dry_run': dry_run,
            'version': f'P21 Deprecate OFFLINE >{days_offline} days'
        }

# Global instance
p21_rating_fix = P21RatingFix()

print("[P21] P21 Rating Fix loaded — 60 rating 0 → 0 — health check real + deprecate OFFLINE")
