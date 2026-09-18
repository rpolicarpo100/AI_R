"""
P4 - Auth Router - JWT + Roles + Human Override
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import timedelta
from typing import Optional

from ..services.auth import (
    authenticate_user, create_access_token, get_current_user,
    require_role, Role, human_override, ACCESS_TOKEN_EXPIRE_MINUTES,
    USERS_DB
)

router = APIRouter(prefix="/auth", tags=["auth"])

class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str
    permissions: list

class LoginRequest(BaseModel):
    username: str
    password: str

class OverrideRequest(BaseModel):
    task_id: str
    reason: str

class OverrideApprove(BaseModel):
    override_id: str

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        # P7 Audit Log Auto - login failed
        try:
            from ..services.audit_service import audit_service
            audit_service.log_action(action="login_failed", user_id=form_data.username, resource_type="auth", resource_id="login", details={"reason": "Incorrect username or password"}, status="failure", severity="warning")
        except: pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"], "permissions": user["permissions"]},
        expires_delta=access_token_expires
    )
    # P7 Audit Log Auto - login success
    try:
        from ..services.audit_service import audit_service
        audit_service.log_action(action="login", user_id=user["username"], resource_type="auth", resource_id="login", details={"role": user["role"], "permissions": user["permissions"]}, status="success", severity="info")
    except: pass
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user["username"],
        "role": user["role"],
        "permissions": user["permissions"]
    }

@router.post("/login/json", response_model=Token)
async def login_json(data: LoginRequest):
    user = authenticate_user(data.username, data.password)
    if not user:
        try:
            from ..services.audit_service import audit_service
            audit_service.log_action(action="login_failed", user_id=data.username, resource_type="auth", resource_id="login", details={"reason": "Incorrect username or password"}, status="failure", severity="warning")
        except: pass
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"], "permissions": user["permissions"]}
    )
    try:
        from ..services.audit_service import audit_service
        audit_service.log_action(action="login", user_id=user["username"], resource_type="auth", resource_id="login", details={"role": user["role"]}, status="success", severity="info")
    except: pass
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user["username"],
        "role": user["role"],
        "permissions": user["permissions"]
    }

@router.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user

@router.get("/users")
async def list_users(current_user: dict = Depends(require_role([Role.ADMIN]))):
    # Only admin can list users
    return [{"username": u["username"], "role": u["role"], "permissions": u["permissions"]} for u in USERS_DB.values()]

@router.post("/human-override/request")
async def request_human_override(data: OverrideRequest, current_user: dict = Depends(get_current_user)):
    override_id = human_override.request_override(data.task_id, data.reason, current_user["username"])
    return {"override_id": override_id, "status": "pending", "task_id": data.task_id, "reason": data.reason, "requested_by": current_user["username"]}

@router.post("/human-override/approve")
async def approve_human_override(data: OverrideApprove, current_user: dict = Depends(require_role([Role.ADMIN, Role.HUMAN_OVERRIDE]))):
    success = human_override.approve_override(data.override_id, current_user["username"])
    if not success:
        raise HTTPException(404, "Override not found")
    return {"override_id": data.override_id, "status": "approved", "approved_by": current_user["username"]}

@router.post("/human-override/reject")
async def reject_human_override(data: dict, current_user: dict = Depends(require_role([Role.ADMIN, Role.HUMAN_OVERRIDE]))):
    override_id = data.get("override_id")
    reason = data.get("reason", "No reason")
    success = human_override.reject_override(override_id, current_user["username"], reason)
    if not success:
        raise HTTPException(404, "Override not found")
    return {"override_id": override_id, "status": "rejected", "rejected_by": current_user["username"], "reason": reason}

@router.get("/human-override/list")
async def list_overrides(current_user: dict = Depends(get_current_user)):
    return human_override.pending_overrides

@router.get("/roles")
async def get_roles():
    return {
        "roles": [Role.ADMIN, Role.USER, Role.VIEWER, Role.HUMAN_OVERRIDE],
        "permissions": {
            Role.ADMIN: ["read", "write", "delete", "benchmark", "admin", "human_override"],
            Role.USER: ["read", "write", "benchmark"],
            Role.VIEWER: ["read"],
            Role.HUMAN_OVERRIDE: ["read", "human_override"]
        },
        "principle": "Você no centro - human override pode aprovar/rejeitar tasks críticas"
    }
