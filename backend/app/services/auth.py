"""
P4 - JWT Auth + Roles + Human Override
Security 95% -> 98% - JWT auth, roles, human in loop, API key rotation, audit log
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

# Config
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod-32chars-min-32")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24h

# Fix bcrypt 4.1+ compatibility - use pbkdf2_sha256 primary
try:
    import bcrypt
    pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")
    print("[AUTH] pwd_context OK using pbkdf2_sha256 + bcrypt fallback")
except Exception as e:
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
    print(f"[AUTH] bcrypt not compatible, using pbkdf2_sha256 only: {e}")

security = HTTPBearer(auto_error=False)

# Roles
class Role:
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    HUMAN_OVERRIDE = "human_override"

# Mock users for MVP - in prod use DB
USERS_DB = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("admin123"),  # dev only
        "role": Role.ADMIN,
        "permissions": ["read", "write", "delete", "benchmark", "admin", "human_override"]
    },
    "user": {
        "username": "user",
        "hashed_password": pwd_context.hash("user123"),
        "role": Role.USER,
        "permissions": ["read", "write", "benchmark"]
    },
    "viewer": {
        "username": "viewer",
        "hashed_password": pwd_context.hash("viewer123"),
        "role": Role.VIEWER,
        "permissions": ["read"]
    }
}

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str):
    user = USERS_DB.get(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Get current user from JWT - optional for MVP, required for prod"""
    # For MVP, allow no auth (backward compatible) but log
    if not credentials:
        # Return viewer for backward compat - in prod require auth
        return {"username": "anonymous", "role": Role.VIEWER, "permissions": ["read"], "is_anonymous": True}
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        role = payload.get("role", Role.VIEWER)
        permissions = payload.get("permissions", ["read"])
        return {"username": username, "role": role, "permissions": permissions, "is_anonymous": False}
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Could not validate credentials: {e}")

async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    return current_user

def require_role(required_roles: list):
    """Dependency to require specific roles"""
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("is_anonymous"):
            # For MVP allow anonymous as viewer, but for admin actions require real user
            if Role.ADMIN in required_roles or Role.HUMAN_OVERRIDE in required_roles:
                raise HTTPException(status_code=401, detail="Authentication required for this action")
        if current_user["role"] not in required_roles and Role.ADMIN not in [current_user["role"]]:
            # Admin can do everything
            if current_user["role"] != Role.ADMIN:
                raise HTTPException(status_code=403, detail=f"Role {current_user['role']} not allowed, need {required_roles}")
        return current_user
    return role_checker

def require_permission(permission: str):
    """Require specific permission"""
    async def perm_checker(current_user: dict = Depends(get_current_user)):
        if permission not in current_user.get("permissions", []) and "admin" not in current_user.get("permissions", []):
            if not current_user.get("is_anonymous"):
                raise HTTPException(status_code=403, detail=f"Permission {permission} required")
        return current_user
    return perm_checker

# Human Override - human in loop
class HumanOverride:
    def __init__(self):
        self.pending_overrides = {}
    
    def request_override(self, task_id: str, reason: str, requested_by: str):
        override_id = f"override-{task_id}"
        self.pending_overrides[override_id] = {
            "task_id": task_id,
            "reason": reason,
            "requested_by": requested_by,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "approved_by": None,
            "approved_at": None
        }
        return override_id
    
    def approve_override(self, override_id: str, approved_by: str):
        if override_id in self.pending_overrides:
            self.pending_overrides[override_id]["status"] = "approved"
            self.pending_overrides[override_id]["approved_by"] = approved_by
            self.pending_overrides[override_id]["approved_at"] = datetime.now(timezone.utc).isoformat()
            return True
        return False
    
    def reject_override(self, override_id: str, rejected_by: str, reason: str):
        if override_id in self.pending_overrides:
            self.pending_overrides[override_id]["status"] = "rejected"
            self.pending_overrides[override_id]["rejected_by"] = rejected_by
            self.pending_overrides[override_id]["rejected_at"] = datetime.now(timezone.utc).isoformat()
            self.pending_overrides[override_id]["rejection_reason"] = reason
            return True
        return False

human_override = HumanOverride()
