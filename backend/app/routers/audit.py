"""
P5.3 - Audit Log Router - GET /api/audit/logs
"""
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from ..core.database import get_db
from ..models.database_models import AuditLog
from ..services.auth import get_current_user, require_role, Role

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/logs")
async def list_audit_logs(
    request: Request,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """P5 - Lista audit logs - P7 pagination com total count"""
    query = db.query(AuditLog).order_by(AuditLog.timestamp.desc())
    
    if action:
        query = query.filter(AuditLog.action == action)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if severity:
        query = query.filter(AuditLog.severity == severity)
    
    total = query.count()
    logs = query.offset(offset).limit(limit).all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "timestamp": log.timestamp,
                "user_id": log.user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": log.details,
                "ip_address": log.ip_address,
                "status": log.status,
                "severity": log.severity
            } for log in logs
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }

@router.get("/stats")
async def audit_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """P5 - Estatísticas audit log"""
    from sqlalchemy import func
    total = db.query(AuditLog).count()
    by_action = db.query(AuditLog.action, func.count(AuditLog.id)).group_by(AuditLog.action).all()
    by_user = db.query(AuditLog.user_id, func.count(AuditLog.id)).group_by(AuditLog.user_id).all()
    by_severity = db.query(AuditLog.severity, func.count(AuditLog.id)).group_by(AuditLog.severity).all()
    
    return {
        "total": total,
        "by_action": dict(by_action),
        "by_user": dict(by_user),
        "by_severity": dict(by_severity),
        "principle": "Você no centro - todas ações auditadas, human override logado"
    }

@router.delete("/logs")
async def clear_audit_logs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role([Role.ADMIN]))
):
    """P5 - Limpa audit logs - admin only"""
    count = db.query(AuditLog).count()
    db.query(AuditLog).delete()
    db.commit()
    
    # Log this action itself
    from ..services.audit_service import audit_service
    audit_service.log_action(
        action="clear_audit_logs",
        user_id=current_user.get("username"),
        details={"cleared_count": count},
        severity="warning",
        db=db
    )
    
    return {"cleared": count, "message": f"Cleared {count} audit logs"}
