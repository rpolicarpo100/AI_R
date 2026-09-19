"""
AI Memory — Apikeyless Archive — Melhora memória da AI, arquivando sites apikeyless para acesso rápido e análises rápidas
- Repositório continuamente aumentado, auditado, rating e categoria
- 100% confiança com realismo — não inventar, medir real
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from ..core.database import Base
import uuid
from datetime import datetime

class ApikeylessMemory(Base):
    __tablename__ = "apikeyless_memory"
    
    id = Column(String, primary_key=True, default=lambda: f"mem-{uuid.uuid4().hex[:8]}")
    url = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    
    # Categoria e rating — auditado
    category = Column(String, nullable=False, index=True)  # llm_free_remote, llm_free_local, llm_free_no_card, image_free, video_free, audio_free, embedding_free, docs, code, etc
    subcategory = Column(String, default="")  # ex: eu_sovereign, gdpr, etc
    rating = Column(Float, default=0.0)  # 0-100 baseado em uptime, latency, free quality, GDPR, etc
    rating_breakdown = Column(JSON, default=dict)  # {uptime: 80, latency: 90, free_quality: 100, gdpr: 90, eu_sovereign: 100, etc}
    
    # Free type
    free_no_card = Column(Boolean, default=False)
    free_no_key = Column(Boolean, default=False)
    free_no_key_remote = Column(Boolean, default=False)
    free_no_key_local = Column(Boolean, default=False)
    free_type = Column(String, default="")  # remote, local, no_card, etc
    
    # Status auditado
    status = Column(String, default="UNKNOWN")  # ONLINE, OFFLINE, NEEDS_KEY, LOCAL_SETUP_REQUIRED, REACHABLE_BUT_ERROR, UNKNOWN, ARCHIVED
    last_checked = Column(DateTime, nullable=True)
    last_archived = Column(DateTime, nullable=True)
    latency_ms = Column(Integer, default=0)
    uptime_pct = Column(Float, default=0.0)
    
    # Conteúdo arquivado para acesso rápido
    content_markdown = Column(Text, default="")  # Conteúdo arquivado markdown para acesso rápido
    content_summary = Column(Text, default="")  # Resumo para análise rápida
    content_hash = Column(String, default="")  # Hash para detectar mudanças
    content_size = Column(Integer, default=0)
    
    # Tags e metadata
    tags = Column(JSON, default=list)  # ["free", "eu", "gdpr", "llm", "image", etc]
    capabilities = Column(JSON, default=dict)  # {models: 80, tokens_per_day: "10K", etc}
    meta = Column(JSON, default=dict)  # {source: "web_search 2026-09-18", discovered_at: timestamp, etc}
    
    # Auditoria contínua
    audit_count = Column(Integer, default=0)
    audit_history = Column(JSON, default=list)  # [{at: timestamp, status: ONLINE, latency: 100, rating: 80}, ...]
    deprecated = Column(Boolean, default=False)
    deprecated_reason = Column(Text, default="")
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

print("[MEMORY] ApikeylessMemory model loaded — arquiva sites apikeyless para acesso rápido e análises rápidas — continuamente aumentado, auditado, rating e categoria")
