from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    APP_NAME: str = "AI Provider OS"
    VERSION: str = "1.2.0-P23 P0 + P0.5 + P1 + P2 + P3 + P4 + P5 — CENTRAL POLICY + TOKEN + ERROR 413/429 + REROUTING + LIFECYCLE + CACHE KEY + BACKOFF + RETRY-AFTER + PRE-WARM 83% + MAX_COMPLETION_TOKENS + QUOTA TRACKING + ASYNC CRITIC + DASHBOARD ENHANCED + FRONTEND P3 + RATING EVOLUTION + TASK QUEUE P23 + METRICS P4 + LARGE PROMPT FASEADO P5 ENTERPRISE++"
    API_PREFIX: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod-32chars-min-32")
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")  # Fernet key base64
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./ai_provider_os.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "")  # P6 — Redis for shared cache multi-worker: redis://localhost:6379/0
    # CORS - env var for prod: CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"]
    # Security P4 - JWT + Auth
    ENCRYPT_API_KEYS: bool = True
    LOG_SENSITIVE: bool = False
    JWT_EXPIRE_MINUTES: int = 60*24
    # P4 - Enterprise
    ENABLE_HUMAN_OVERRIDE: bool = True
    ENABLE_TASK_QUEUE: bool = True
    ENABLE_BRANCHES: bool = True
    # P5 - Enterprise++ Rigoroso Profissional Crítico
    ENABLE_AUDIT_LOG: bool = True
    ENABLE_KEY_ROTATION: bool = True
    ENABLE_RATE_LIMIT_PER_PROVIDER: bool = True
    ENABLE_VIRTUAL_SCROLL: bool = True
    RIGOR_TARGET: int = 60  # Target 60% rigor
    # P6 — Speed + Capacity
    ENABLE_GZIP: bool = True  # 70% bandwidth reduction
    ENABLE_LRU_CACHE: bool = True  # LRU caches classifier 200/60s token 500/60s routing 100/30s
    ENABLE_REQUEST_COALESCING: bool = True  # Coalesce identical prompts
    CACHE_TTL_CLASSIFIER: int = 60
    CACHE_TTL_TOKEN: int = 60
    CACHE_TTL_ROUTING: int = 30
    CACHE_TTL_DASHBOARD: int = 5
    RATE_LIMIT_GLOBAL: int = 100  # req/min global
    RATE_LIMIT_CHAT: int = 30  # req/min chat
    RATE_LIMIT_CLINE: int = 60  # req/min cline

    class Config:
        env_file = ".env"

# Security warning for default SECRET_KEY — critical improvement
settings = Settings()
if settings.SECRET_KEY in ["dev-secret-key-change-in-prod-32chars-min-32", "change-me-32chars-minimum-secret-key-prod", "auto-generated-dev-key-32-chars-minimum-change-prod"]:
    print(f"[SECURITY WARNING] SECRET_KEY is default/dev — change in prod! Current: {settings.SECRET_KEY[:16]}... — Set SECRET_KEY env var with 32+ chars random")
if settings.CORS_ORIGINS == ["*"]:
    print(f"[SECURITY WARNING] CORS_ORIGINS=* — insecure for prod — set CORS_ORIGINS env var to your domains, e.g. https://yourdomain.com")
# Docker volume bug warning
if "ai_provider_os.db" in settings.DATABASE_URL and "/app/data/" not in settings.DATABASE_URL and settings.DATABASE_URL.startswith("sqlite:////app/"):
    print(f"[DOCKER WARNING] DATABASE_URL {settings.DATABASE_URL} may be file mount bug — use sqlite:////app/data/ai_provider_os.db with volume backend_db:/app/data")
