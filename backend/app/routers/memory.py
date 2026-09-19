"""
AI Memory Router — Apikeyless Archive — Melhora memória da AI
- Arquiva sites apikeyless para acesso rápido e análises rápidas
- Repositório continuamente aumentado, auditado, rating e categoria
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from ..core.database import get_db, SessionLocal
from ..models.memory_models import ApikeylessMemory
from ..services.apikeyless_memory_service import apikeyless_memory_service
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/memory", tags=["memory"])

@router.post("/seed")
async def seed_memory(db: Session = Depends(get_db)):
    """Seed inicial com 15 sites apikeyless reais verificados"""
    result = apikeyless_memory_service.seed_memory(db)
    return result

@router.get("/list")
async def list_memory(
    category: Optional[str] = None,
    min_rating: float = 0,
    free_type: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Lista memória com filtros — acesso rápido — rating desc"""
    memories = apikeyless_memory_service.list_memory(db, category=category, min_rating=min_rating, free_type=free_type, limit=limit)
    return {
        "total": len(memories),
        "filters": {"category": category, "min_rating": min_rating, "free_type": free_type, "limit": limit},
        "memories": memories,
        "version": "Apikeyless Memory — acesso rápido — rating desc"
    }

@router.get("/search")
async def search_memory(
    q: str,
    category: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Busca semântica simples — nome, descrição, tags, categoria — análises rápidas"""
    results = apikeyless_memory_service.search_memory(db, query=q, category=category, limit=limit)
    return {
        "query": q,
        "category": category,
        "total": len(results),
        "results": results,
        "version": "Search for fast analysis"
    }

@router.post("/archive")
@limiter.limit("10/minute")
async def archive_site(request: Request, url: str, db: Session = Depends(get_db)):
    """Arquiva site apikeyless — fetch conteúdo para acesso rápido"""
    result = await apikeyless_memory_service.archive_site(url, db, timeout=10.0)
    return result

@router.post("/audit")
@limiter.limit("5/minute")
async def audit_memory(request: Request, limit: int = 20, concurrency: int = 5, db: Session = Depends(get_db)):
    """Audita memória — health check + rating update — contínuo"""
    result = await apikeyless_memory_service.audit_all(db, limit=limit, concurrency=concurrency)
    return result

@router.post("/increase")
async def increase_memory(sites: List[dict], db: Session = Depends(get_db)):
    """
    Aumenta continuamente repositório — adiciona novos sites apikeyless
    Body: [{"url": "https://...", "name": "...", "category": "llm_free_remote", "rating": 80, "tags": ["free"], ...}]
    """
    result = apikeyless_memory_service.increase_continuously(db, new_sites=sites)
    return result

@router.get("/stats")
async def memory_stats(db: Session = Depends(get_db)):
    """Stats da memória — rating, categoria, free_type, status"""
    from collections import Counter
    all_mem = db.query(ApikeylessMemory).all()
    
    category_count = Counter([m.category for m in all_mem])
    free_type_count = Counter([m.free_type for m in all_mem])
    status_count = Counter([m.status for m in all_mem])
    
    ratings = [m.rating or 0 for m in all_mem]
    avg_rating = sum(ratings)/len(ratings) if ratings else 0
    
    return {
        "total": len(all_mem),
        "avg_rating": avg_rating,
        "rating_gte80": len([r for r in ratings if r>=80]),
        "rating_gte50": len([r for r in ratings if r>=50]),
        "category_count": dict(category_count),
        "free_type_count": dict(free_type_count),
        "status_count": dict(status_count),
        "version": "Memory stats — rating, categoria, free_type, status — continuamente auditado"
    }

@router.get("/categories")
async def memory_categories(db: Session = Depends(get_db)):
    """Lista categorias disponíveis"""
    from collections import Counter
    all_mem = db.query(ApikeylessMemory).all()
    categories = Counter([m.category for m in all_mem])
    return {
        "categories": [{"category": cat, "count": count} for cat, count in categories.most_common()],
        "total_categories": len(categories),
        "version": "Categories for fast analysis"
    }

@router.delete("/{memory_id}")
async def delete_memory(memory_id: str, db: Session = Depends(get_db)):
    """Deleta memória — se deprecated ou OFFLINE >7 days"""
    mem = db.query(ApikeylessMemory).filter(ApikeylessMemory.id == memory_id).first()
    if not mem:
        return {"status": "NOT_FOUND", "id": memory_id}
    
    db.delete(mem)
    db.commit()
    
    return {"status": "DELETED", "id": memory_id, "url": mem.url}

print("[MEMORY ROUTER] Apikeyless Memory router loaded — /api/memory — seed, list, search, archive, audit, increase, stats, categories")
