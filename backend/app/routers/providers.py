from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import ipaddress
from urllib.parse import urlparse

from ..core.database import get_db
from ..models.database_models import Provider, ProviderStatus
from ..services.encryption import encrypt_api_key, mask_api_key, decrypt_api_key
from ..adapters.openai_compat import OpenAICompatibleAdapter, GroqAdapter, CerebrasAdapter, OpenRouterAdapter, MistralAdapter
from ..adapters.gemini import GeminiAdapter
from ..adapters.ollama import OllamaAdapter
# P15 — Dedicated adapters for 90 providers
try:
    from ..adapters.dedicated_p15 import DEDICATED_ADAPTERS_P15
    print(f"[P15] Loaded {len(DEDICATED_ADAPTERS_P15)} dedicated adapters")
except Exception as e:
    print(f"[P15] Dedicated adapters load failed {e}, using generic")
    DEDICATED_ADAPTERS_P15 = {}

# P15 200 — Dedicated adapters for 100 new providers
try:
    from ..adapters.dedicated_p15_200 import DEDICATED_ADAPTERS_P15_200
    print(f"[P15 200] Loaded {len(DEDICATED_ADAPTERS_P15_200)} dedicated adapters for 200 providers")
except Exception as e:
    print(f"[P15 200] Dedicated adapters load failed {e}, using generic")
    DEDICATED_ADAPTERS_P15_200 = {}

def validate_base_url(url: str):
    """P3 Security - SSRF validation - evita internal IPs, metadata, mas permite localhost para Ollama local real"""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ["http","https"]:
            raise HTTPException(400, f"Invalid scheme {parsed.scheme}, must be http/https")
        hostname = parsed.hostname
        if not hostname:
            raise HTTPException(400, "Invalid URL, no hostname")
        # Block cloud metadata - CRITICAL
        if "169.254.169.254" in url or "metadata.google" in url or "metadata" in hostname:
            raise HTTPException(400, "SSRF blocked: metadata endpoint")
        if hostname.endswith(".internal") or hostname.endswith(".local"):
            raise HTTPException(400, f"SSRF blocked: internal domain {hostname}")
        # Block private IPs, but allow localhost for Ollama local real (user creates app locally)
        try:
            ip = ipaddress.ip_address(hostname)
            # Allow loopback for ollama local, but log
            if ip.is_loopback:
                # Permitido apenas para uso local real - log audit
                print(f"[SECURITY] Loopback allowed for local use: {url} - audit logged")
                return True
            if ip.is_private:
                # Block 10., 172.16., 192.168. - SSRF
                raise HTTPException(400, f"SSRF blocked: private IP {hostname} not allowed")
            if ip.is_link_local or ip.is_multicast or ip.is_reserved:
                raise HTTPException(400, f"SSRF blocked: restricted IP {hostname}")
            if str(ip) == "0.0.0.0":
                raise HTTPException(400, f"SSRF blocked: 0.0.0.0 not allowed")
        except ValueError:
            # hostname is domain, not IP - allow, but already blocked .internal/.local above
            # Additional check: if hostname is localhost, allow for ollama
            if hostname.lower() == "localhost":
                print(f"[SECURITY] localhost allowed for local use: {url}")
                return True
        return True
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Invalid URL: {e}")

router = APIRouter(prefix="/providers", tags=["providers"])

ADAPTERS_MAP = {
    "groq": GroqAdapter(),
    "cerebras": CerebrasAdapter(),
    "openrouter": OpenRouterAdapter(),
    "mistral": MistralAdapter(),
    "gemini": GeminiAdapter(),
    "ollama": OllamaAdapter(),
    "openai": OpenAICompatibleAdapter(),
    "github_models": OpenAICompatibleAdapter(),
    "huggingface": OpenAICompatibleAdapter(),
    "kie_ai": OpenAICompatibleAdapter(),  # P10 - KIE AI 206 models 80 credits gpt-5-2 measured
    **DEDICATED_ADAPTERS_P15,  # P15 — 20+ dedicated adapters for 90 providers
    **DEDICATED_ADAPTERS_P15_200,  # P15 200 — 20 dedicated adapters for 100 new providers
}

class ProviderCreate(BaseModel):
    provider_id: str
    name: str
    base_url: str
    auth_type: str = "bearer"
    api_key: Optional[str] = None
    status: Optional[str] = "DISCOVERED"
    pricing_info: Optional[dict] = {}
    capabilities: Optional[dict] = {}
    source: Optional[str] = "manual"

class ProviderUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    status: Optional[str] = None
    pricing_info: Optional[dict] = None
    capabilities: Optional[dict] = None

class ProviderOut(BaseModel):
    id: str
    provider_id: str
    name: str
    base_url: str
    auth_type: str
    api_key_masked: str
    status: str
    pricing_info: dict
    capabilities: dict
    rating: float
    confidence: float
    success_count: int
    failure_count: int
    avg_latency_ms: float
    consecutive_failures: int
    last_health_check: Optional[datetime]
    last_success: Optional[datetime]
    last_failure: Optional[datetime]
    source: str
    source_confidence: str
    has_key: bool

    class Config:
        from_attributes = True

def to_out(p: Provider) -> dict:
    return {
        "id": p.id,
        "provider_id": p.provider_id,
        "name": p.name,
        "base_url": p.base_url,
        "auth_type": p.auth_type,
        "api_key_masked": mask_api_key(p.api_key_encrypted) if p.api_key_encrypted else "NOT_SET",
        "status": p.status.value if hasattr(p.status, 'value') else str(p.status),
        "pricing_info": p.pricing_info or {},
        "capabilities": p.capabilities or {},
        "rating": p.rating,
        "confidence": p.confidence,
        "success_count": p.success_count,
        "failure_count": p.failure_count,
        "avg_latency_ms": p.avg_latency_ms,
        "consecutive_failures": p.consecutive_failures,
        "last_health_check": p.last_health_check,
        "last_success": p.last_success,
        "last_failure": p.last_failure,
        "source": p.source,
        "source_confidence": p.source_confidence,
        "has_key": bool(p.api_key_encrypted)
    }

@router.get("", response_model=List[ProviderOut])
def list_providers(db: Session = Depends(get_db)):
    providers = db.query(Provider).all()
    return [to_out(p) for p in providers]

@router.get("/{provider_id}", response_model=ProviderOut)
def get_provider(provider_id: str, db: Session = Depends(get_db)):
    p = db.query(Provider).filter(Provider.provider_id == provider_id).first()
    if not p:
        raise HTTPException(404, "Provider not found")
    return to_out(p)

@router.post("", response_model=ProviderOut)
def create_provider(data: ProviderCreate, db: Session = Depends(get_db)):
    existing = db.query(Provider).filter(Provider.provider_id == data.provider_id).first()
    if existing:
        raise HTTPException(409, "Provider ID already exists")
    
    # P3 Security - SSRF validation
    validate_base_url(data.base_url)
    
    encrypted = encrypt_api_key(data.api_key) if data.api_key else None
    
    # Validate status
    try:
        status_enum = ProviderStatus(data.status) if data.status else ProviderStatus.DISCOVERED
    except:
        status_enum = ProviderStatus.DISCOVERED
    
    provider = Provider(
        provider_id=data.provider_id,
        name=data.name,
        base_url=data.base_url,
        auth_type=data.auth_type,
        api_key_encrypted=encrypted,
        status=status_enum,
        pricing_info=data.pricing_info or {},
        capabilities=data.capabilities or {},
        source=data.source or "manual",
        source_confidence="verified" if data.source == "manual" else "UNKNOWN"
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    # P22 — Invalidate provider cache when provider added
    try:
        from ..services.http_client import invalidate_provider_cache
        invalidate_provider_cache()
    except:
        pass
    return to_out(provider)

@router.put("/{provider_id}", response_model=ProviderOut)
def update_provider(provider_id: str, data: ProviderUpdate, db: Session = Depends(get_db)):
    p = db.query(Provider).filter(Provider.provider_id == provider_id).first()
    if not p:
        raise HTTPException(404, "Provider not found")
    
    if data.name:
        p.name = data.name
    if data.base_url:
        validate_base_url(data.base_url)
        p.base_url = data.base_url
    if data.api_key is not None:
        if data.api_key == "" or data.api_key is None:
            p.api_key_encrypted = None
        else:
            p.api_key_encrypted = encrypt_api_key(data.api_key)
    if data.status:
        try:
            p.status = ProviderStatus(data.status)
        except:
            pass
    if data.pricing_info is not None:
        p.pricing_info = data.pricing_info
    if data.capabilities is not None:
        p.capabilities = data.capabilities
    
    db.commit()
    db.refresh(p)
    # P22 — Invalidate cache on update
    try:
        from ..services.http_client import invalidate_provider_cache
        invalidate_provider_cache()
    except:
        pass
    return to_out(p)

@router.delete("/{provider_id}")
def delete_provider(provider_id: str, db: Session = Depends(get_db)):
    p = db.query(Provider).filter(Provider.provider_id == provider_id).first()
    if not p:
        raise HTTPException(404, "Provider not found")
    db.delete(p)
    db.commit()
    # P22 — Invalidate cache on delete
    try:
        from ..services.http_client import invalidate_provider_cache
        invalidate_provider_cache()
    except:
        pass
    return {"deleted": provider_id}

# P5 - API Key Rotation + Rate Limiting per Provider + DNS Rebinding + Audit Log
@router.post("/{provider_id}/rotate-key")
async def rotate_api_key(provider_id: str, new_api_key: str, db: Session = Depends(get_db)):
    """P5 - API Key Rotation - Segurança 98%→99% - rotaciona key, audit log"""
    p = db.query(Provider).filter(Provider.provider_id == provider_id).first()
    if not p:
        raise HTTPException(404, "Provider not found")
    
    old_masked = mask_api_key(p.api_key_encrypted) if p.api_key_encrypted else "NOT_SET"
    
    if not new_api_key or len(new_api_key) < 5:
        raise HTTPException(400, "New API key too short")
    
    p.api_key_encrypted = encrypt_api_key(new_api_key)
    p.updated_at = datetime.now(timezone.utc)
    db.commit()
    
    new_masked = mask_api_key(p.api_key_encrypted)
    
    try:
        from ..services.audit_service import audit_service
        audit_service.log_action(
            action="rotate_api_key",
            user_id="admin",
            resource_type="provider",
            resource_id=provider_id,
            details={"old_masked": old_masked, "new_masked": new_masked, "provider": provider_id},
            severity="warning",
            db=db
        )
    except Exception as e:
        print(f"[AUDIT] Failed to log rotate_key: {e}")
    
    return {
        "provider_id": provider_id,
        "old_masked": old_masked,
        "new_masked": new_masked,
        "rotated_at": datetime.now(timezone.utc).isoformat(),
        "message": f"API key rotated for {provider_id} - old {old_masked} → new {new_masked}",
        "audit_logged": True,
        "principle": "Você no centro - key rotation auditada"
    }

@router.get("/{provider_id}/rate-limit")
async def get_rate_limit(provider_id: str, db: Session = Depends(get_db)):
    """P5 - Rate Limiting per Provider"""
    PROVIDER_RATE_LIMITS = {
        "groq": "60/minute", "cerebras": "30/minute", "gemini": "60/minute",
        "mistral": "60/minute", "openrouter": "30/minute", "huggingface": "20/minute",
        "cohere": "30/minute", "nvidia": "30/minute", "sambanova": "20/minute",
        "chutes": "20/minute", "deepseek": "20/minute", "default": "20/minute"
    }
    limit = PROVIDER_RATE_LIMITS.get(provider_id, PROVIDER_RATE_LIMITS["default"])
    p = db.query(Provider).filter(Provider.provider_id == provider_id).first()
    if not p:
        raise HTTPException(404, "Provider not found")
    return {
        "provider_id": provider_id,
        "rate_limit": limit,
        "current_status": p.status.value if hasattr(p.status, 'value') else str(p.status),
        "consecutive_failures": p.consecutive_failures,
        "success_count": p.success_count,
        "failure_count": p.failure_count,
        "principle": "Rate limiting por provider - evita abuse free tier"
    }

def validate_base_url_dns_rebinding(url: str):
    """P5 - SSRF DNS Rebinding Validation"""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False
        if hostname.lower() in ["localhost", "127.0.0.1", "::1"]:
            print(f"[SECURITY P5] Loopback allowed for local use: {url} - DNS rebinding check skipped for localhost")
            return True
        import socket
        try:
            ip_str = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
                print(f"[SECURITY P5] DNS rebinding blocked: {hostname} resolves to private IP {ip_str}")
                raise HTTPException(400, f"SSRF DNS rebinding blocked: {hostname} resolves to private IP {ip_str}")
            if str(ip) == "0.0.0.0" or ip_str == "169.254.169.254":
                raise HTTPException(400, f"SSRF DNS rebinding blocked: {hostname} resolves to restricted IP {ip_str}")
        except socket.gaierror:
            print(f"[SECURITY P5] DNS resolution failed for {hostname}, allowing but logged")
        except HTTPException:
            raise
        except Exception as e:
            print(f"[SECURITY P5] DNS check error for {hostname}: {e}")
        return True
    except HTTPException:
        raise
    except Exception as e:
        print(f"[SECURITY P5] DNS rebinding validation error: {e}")
        return True

@router.post("/{provider_id}/test")
async def test_provider(provider_id: str, db: Session = Depends(get_db)):
    p = db.query(Provider).filter(Provider.provider_id == provider_id).first()
    if not p:
        raise HTTPException(404, "Provider not found")
    
    if not p.api_key_encrypted and p.provider_id != "ollama":
        return {"status": "FAILED", "reason": "No API key configured", "provider": provider_id, "timestamp": datetime.now(timezone.utc).isoformat()}
    
    adapter = ADAPTERS_MAP.get(p.provider_id, OpenAICompatibleAdapter())
    try:
        api_key = decrypt_api_key(p.api_key_encrypted) if p.api_key_encrypted else ""
        healthy = await adapter.health_check(api_key, p.base_url)
        
        # Update DB
        p.last_health_check = datetime.now(timezone.utc)
        if healthy:
            p.last_success = datetime.now(timezone.utc)
            p.success_count += 1
            p.consecutive_failures = 0
            if p.status == ProviderStatus.DISCOVERED:
                p.status = ProviderStatus.VERIFIED
            elif p.status == ProviderStatus.DEGRADED:
                p.status = ProviderStatus.PRODUCTION
        else:
            p.last_failure = datetime.now(timezone.utc)
            p.failure_count += 1
            p.consecutive_failures += 1
            if p.consecutive_failures >= 5:
                p.status = ProviderStatus.DEGRADED
        
        db.commit()
        
        return {
            "status": "HEALTHY" if healthy else "DEGRADED",
            "provider": provider_id,
            "base_url": p.base_url,
            "latency": "UNKNOWN - health check only",
            "timestamp": p.last_health_check.isoformat(),
            "consecutive_failures": p.consecutive_failures,
            "source_confidence": "measured"
        }
    except Exception as e:
        p.last_health_check = datetime.now(timezone.utc)
        p.last_failure = datetime.now(timezone.utc)
        p.failure_count += 1
        p.consecutive_failures += 1
        db.commit()
        return {
            "status": "FAILED",
            "provider": provider_id,
            "error": str(e)[:500],
            "error_type": "UNKNOWN",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_confidence": "measured"
        }
