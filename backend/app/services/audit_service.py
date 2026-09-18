"""
P5.3 - Audit Log Service - Segurança 98%→99%
Loga todas ações críticas: login, human override, export, branches, task queue, provider test, benchmark, etc
Rigoroso, profissional, crítico
"""
from datetime import datetime
from typing import Optional, Dict
from sqlalchemy.orm import Session
from ..models.database_models import AuditLog

class AuditService:
    def __init__(self, db: Session = None):
        self.db = db
    
    def log_action(self, 
                   action: str,
                   user_id: Optional[str] = None,
                   resource_type: Optional[str] = None,
                   resource_id: Optional[str] = None,
                   details: Dict = None,
                   ip_address: Optional[str] = None,
                   user_agent: Optional[str] = None,
                   status: str = "success",
                   severity: str = "info",
                   db: Session = None):
        """Loga ação no audit log - P5"""
        db_session = db or self.db
        if not db_session:
            from ..core.database import SessionLocal
            db_session = SessionLocal()
            should_close = True
        else:
            should_close = False
        
        try:
            log = AuditLog(
                user_id=user_id or "anonymous",
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent,
                status=status,
                severity=severity
            )
            db_session.add(log)
            db_session.commit()
            print(f"[AUDIT] {action} by {user_id} on {resource_type}/{resource_id} - {status}")
            return log
        except Exception as e:
            print(f"[AUDIT] Failed to log {action}: {e}")
            return None
        finally:
            if should_close:
                db_session.close()

audit_service = AuditService()
