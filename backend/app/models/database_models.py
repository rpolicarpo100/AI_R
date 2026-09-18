from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from ..core.database import Base
import enum
import uuid
from datetime import datetime

class ProviderStatus(str, enum.Enum):
    DISCOVERED = "DISCOVERED"
    UNVERIFIED = "UNVERIFIED"
    TESTING = "TESTING"
    VERIFIED = "VERIFIED"
    PRODUCTION = "PRODUCTION"
    DEGRADED = "DEGRADED"
    DISABLED = "DISABLED"
    DEPRECATED = "DEPRECATED"
    OFFLINE = "OFFLINE"

class ModelStatus(str, enum.Enum):
    DISCOVERED = "DISCOVERED"
    UNVERIFIED = "UNVERIFIED"
    TESTING = "TESTING"
    VERIFIED = "VERIFIED"
    PRODUCTION = "PRODUCTION"
    DEGRADED = "DEGRADED"
    DISABLED = "DISABLED"
    DEPRECATED = "DEPRECATED"

class Provider(Base):
    __tablename__ = "providers"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(String, unique=True, nullable=False)  # slug: openai, groq...
    name = Column(String, nullable=False)
    base_url = Column(String, nullable=False)
    auth_type = Column(String, default="bearer")  # bearer, api_key, x-api-key
    api_key_encrypted = Column(Text, nullable=True)  # encrypted
    status = Column(SQLEnum(ProviderStatus), default=ProviderStatus.DISCOVERED)
    # Pricing & limits - UNKNOWN if not confirmed
    pricing_info = Column(JSON, default=dict)  # {input_per_1m: UNKNOWN, ...}
    limits = Column(JSON, default=dict)
    capabilities = Column(JSON, default=dict)  # {tool_calling: true, vision: false...}
    last_health_check = Column(DateTime, nullable=True)
    last_success = Column(DateTime, nullable=True)
    last_failure = Column(DateTime, nullable=True)
    consecutive_failures = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)  # 0-100
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    avg_latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())
    # Verification tracking
    source = Column(String, default="manual")  # manual, discovery, official_docs
    source_confidence = Column(String, default="UNKNOWN")  # verified, measured, provider_claim, estimate, UNKNOWN

class Model(Base):
    __tablename__ = "models"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id = Column(String, nullable=False)  # e.g., llama-3.3-70b-versatile
    provider_id = Column(String, nullable=False)  # FK to Provider.provider_id
    display_name = Column(String, nullable=False)
    context_window = Column(Integer, default=0)  # 0 = UNKNOWN
    input_price = Column(String, default="UNKNOWN")  # Keep as string to allow UNKNOWN, or float
    output_price = Column(String, default="UNKNOWN")
    input_price_float = Column(Float, nullable=True)
    output_price_float = Column(Float, nullable=True)
    free_tier = Column(Boolean, default=False)
    rate_limits = Column(JSON, default=dict)
    # Scores 0-100
    coding_score = Column(Float, default=0.0)
    reasoning_score = Column(Float, default=0.0)
    speed_score = Column(Float, default=0.0)
    reliability_score = Column(Float, default=0.0)
    tool_calling_score = Column(Float, default=0.0)
    json_score = Column(Float, default=0.0)
    overall_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    test_count = Column(Integer, default=0)
    status = Column(SQLEnum(ModelStatus), default=ModelStatus.DISCOVERED)
    last_verified = Column(DateTime, nullable=True)
    capabilities = Column(JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now())

class RequestLog(Base):
    __tablename__ = "request_logs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String, unique=True, default=lambda: str(uuid.uuid4()))
    provider = Column(String, nullable=True)
    model = Column(String, nullable=True)
    task_type = Column(String, nullable=True)
    profile = Column(String, nullable=True)  # FAST, CODING...
    latency_ms = Column(Integer, default=0)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    cost_status = Column(String, default="UNKNOWN")  # measured, estimate, UNKNOWN
    status = Column(String, default="UNKNOWN")  # success, error
    error_code = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    fallback_used = Column(Boolean, default=False)
    fallback_chain = Column(JSON, default=list)
    rating_at_time = Column(Float, nullable=True)
    timestamp = Column(DateTime, server_default=func.now())
    # Never store sensitive content unless consent - we store hash only
    prompt_hash = Column(String, nullable=True)

class BenchmarkResult(Base):
    __tablename__ = "benchmark_results"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id = Column(String, nullable=False)
    provider_id = Column(String, nullable=False)
    category = Column(String, nullable=False)  # CODING, REASONING, JSON...
    test_name = Column(String, nullable=False)
    score = Column(Float, default=0.0)
    latency_ms = Column(Integer, default=0)
    success = Column(Boolean, default=False)
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime, server_default=func.now())

# P5 - Audit Log Persistente DB - Segurança 98%→99%
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, server_default=func.now())
    user_id = Column(String, nullable=True)  # username or anonymous
    action = Column(String, nullable=False)  # login, logout, create_project, delete_project, rotate_key, human_override_request, etc
    resource_type = Column(String, nullable=True)  # provider, model, project, task, branch, etc
    resource_id = Column(String, nullable=True)  # id of resource
    details = Column(JSON, default=dict)  # extra details
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    status = Column(String, default="success")  # success, failure
    severity = Column(String, default="info")  # info, warning, critical
