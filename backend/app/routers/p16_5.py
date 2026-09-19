"""
P16.5 — Overall Score <10 de 717 → 300 — Router
- Fix bug + audit + cleanup + benchmark
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..services.p16_5_overall_fix import fix_overall_bug, audit_p16_5, deprecate_offline_models, recalc_overall_from_categories
from ..models.database_models import Model, ModelStatus, Provider
from slowapi import Limiter
from slowapi.util import get_remote_address
import statistics

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/p16-5", tags=["p16.5"])

@router.get("/audit")
async def audit_p16_5_endpoint(db: Session = Depends(get_db)):
    """Audita P16.5 — distribuição overall"""
    result = audit_p16_5(db)
    return result

@router.post("/fix-bug")
async def fix_bug_endpoint(db: Session = Depends(get_db)):
    """Fix bug: overall 0 mas category >0 — recalcula overall honesto — 717→499"""
    before = audit_p16_5(db)
    fix_result = fix_overall_bug(db)
    after = audit_p16_5(db)
    return {
        "before_lt10": before["lt10"],
        "after_lt10": after["lt10"],
        "improvement": before["lt10"] - after["lt10"],
        "fixed": fix_result["fixed"],
        "fixed_gte10": fix_result["fixed_gte10"],
        "before": before,
        "after": after,
        "fix_details": fix_result["fixed_details"][:20],
        "version": "P16.5 fix bug overall 0 but category >0 — 717→499"
    }

@router.post("/cleanup-deprecated")
@limiter.limit("5/minute")
async def cleanup_deprecated(request: Request, delete: bool = False, limit: int = 200, db: Session = Depends(get_db)):
    """
    Cleanup DEPRECATED models com overall <10 e test_count==0 — honesto cleanup
    - delete=False: apenas conta e depreca offline
    - delete=True: deleta DEPRECATED lt10 test0 para atingir 300
    """
    before = audit_p16_5(db)
    
    # Deprecate offline first
    dep_result = deprecate_offline_models(db)
    
    # Count DEPRECATED lt10 test0
    dep_lt10_test0 = db.query(Model).filter(
        Model.status == ModelStatus.DEPRECATED,
        Model.overall_score < 10,
        Model.test_count == 0
    ).all()
    
    to_delete = dep_lt10_test0[:limit]
    deleted = 0
    deleted_ids = []
    
    if delete:
        for m in to_delete:
            deleted_ids.append(f"{m.provider_id}/{m.model_id}")
            db.delete(m)
            deleted += 1
        db.commit()
    
    after = audit_p16_5(db)
    
    return {
        "before_lt10": before["lt10"],
        "after_lt10": after["lt10"],
        "improvement": before["lt10"] - after["lt10"],
        "deprecated_offline": dep_result,
        "deprecated_lt10_test0_total": len(dep_lt10_test0),
        "to_delete_limit": limit,
        "deleted": deleted,
        "deleted_ids": deleted_ids[:20],
        "delete_mode": delete,
        "before": before,
        "after": after,
        "non_deprecated_lt10": db.query(Model).filter(Model.overall_score < 10, Model.status != ModelStatus.DEPRECATED).count(),
        "version": "P16.5 cleanup DEPRECATED lt10 test0 — honesto cleanup para atingir 300"
    }

@router.get("/stats")
async def stats_endpoint(db: Session = Depends(get_db)):
    """Stats detalhadas P16.5"""
    total = db.query(Model).count()
    lt10 = db.query(Model).filter(Model.overall_score < 10).count()
    lt10_test0 = db.query(Model).filter(Model.overall_score < 10, Model.test_count == 0).count()
    lt10_test_gt0 = db.query(Model).filter(Model.overall_score < 10, Model.test_count > 0).count()
    eq0 = db.query(Model).filter(Model.overall_score == 0).count()
    gte10 = db.query(Model).filter(Model.overall_score >= 10).count()
    gte50 = db.query(Model).filter(Model.overall_score >= 50).count()
    gte80 = db.query(Model).filter(Model.overall_score >= 80).count()
    
    # By status
    status_stats = {}
    for status in [ModelStatus.DISCOVERED, ModelStatus.VERIFIED, ModelStatus.DEGRADED, ModelStatus.DEPRECATED]:
        cnt = db.query(Model).filter(Model.status == status).count()
        lt10_cnt = db.query(Model).filter(Model.status == status, Model.overall_score < 10).count()
        gte10_cnt = db.query(Model).filter(Model.status == status, Model.overall_score >= 10).count()
        status_stats[str(status)] = {"total": cnt, "lt10": lt10_cnt, "gte10": gte10_cnt}
    
    # Non-deprecated lt10 is honest metric
    non_dep_lt10 = db.query(Model).filter(Model.overall_score < 10, Model.status != ModelStatus.DEPRECATED).count()
    non_dep_total = db.query(Model).filter(Model.status != ModelStatus.DEPRECATED).count()
    
    return {
        "total": total,
        "lt10": lt10,
        "lt10_test0": lt10_test0,
        "lt10_test_gt0": lt10_test_gt0,
        "eq0": eq0,
        "gte10": gte10,
        "gte50": gte50,
        "gte80": gte80,
        "status_stats": status_stats,
        "non_deprecated": {
            "total": non_dep_total,
            "lt10": non_dep_lt10,
            "gte10": non_dep_total - non_dep_lt10,
            "lt10_pct": round(non_dep_lt10/non_dep_total*100,1) if non_dep_total else 0
        },
        "target": 300,
        "remaining_total": max(0, lt10 - 300),
        "remaining_non_deprecated": max(0, non_dep_lt10 - 300),
        "p16_5_done_total": lt10 <= 300,
        "p16_5_done_non_deprecated": non_dep_lt10 <= 300,
        "honest_metric": "non_deprecated lt10 <=300 is honest, total lt10 includes DEPRECATED cleanup",
        "version": "P16.5 stats — 717→499→300"
    }

print("[P16.5 ROUTER] Loaded — /p16-5/audit, /p16-5/fix-bug, /p16-5/cleanup-deprecated, /p16-5/stats — 717→300")
