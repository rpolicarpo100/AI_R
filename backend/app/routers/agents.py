"""
AGENTS ROUTER - API para agentes, skills, competências e loop
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

from ..core.database import get_db
from ..models.agent_models import AgentDB, SkillDB, AgentCompetency, LoopTask, AgentStatus, LoopTaskType, LoopTaskStatus
from ..services.agent_manager import agent_manager
from ..services.loop_engine import loop_engine

router = APIRouter(prefix="/agents", tags=["agents"])

class AgentOut(BaseModel):
    agent_id: str
    name: str
    role: str
    status: str
    description: str
    skills: List[Dict]
    competencies: Dict
    tools: List[str]
    permissions: List[str]
    rating: float
    confidence: float
    success_count: int
    failure_count: int
    avg_latency_ms: float
    total_tasks: int
    evolution_level: int
    last_active: Optional[datetime]
    
    class Config:
        from_attributes = True

class SkillOut(BaseModel):
    skill_id: str
    name: str
    description: str
    category: str
    capabilities: List[str]
    security_level: str
    rating: float
    usage_count: int
    success_rate: float
    
    class Config:
        from_attributes = True

class CompetencyOut(BaseModel):
    agent_id: str
    skill_id: str
    proficiency: float
    experience_hours: float
    level: str
    success_count: int
    failure_count: int
    last_used: Optional[datetime]
    certified: bool
    
    class Config:
        from_attributes = True

class LoopTaskOut(BaseModel):
    task_id: str
    type: str
    status: str
    priority: str
    objective: str
    agent_id: Optional[str]
    skill_id: Optional[str]
    result: Dict
    error: Optional[str]
    latency_ms: int
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.get("", response_model=List[AgentOut])
def list_agents(db: Session = Depends(get_db)):
    agents = db.query(AgentDB).all()
    return [
        {
            "agent_id": a.agent_id,
            "name": a.name,
            "role": a.role.value if hasattr(a.role, 'value') else str(a.role),
            "status": a.status.value if hasattr(a.status, 'value') else str(a.status),
            "description": a.description,
            "skills": a.skills or [],
            "competencies": a.competencies or {},
            "tools": a.tools or [],
            "permissions": a.permissions or [],
            "rating": a.rating,
            "confidence": a.confidence,
            "success_count": a.success_count,
            "failure_count": a.failure_count,
            "avg_latency_ms": a.avg_latency_ms,
            "total_tasks": a.total_tasks,
            "evolution_level": a.evolution_level,
            "last_active": a.last_active,
        }
        for a in agents
    ]

@router.get("/skills", response_model=List[SkillOut])
def list_skills(db: Session = Depends(get_db)):
    skills = db.query(SkillDB).all()
    return [
        {
            "skill_id": s.skill_id,
            "name": s.name,
            "description": s.description,
            "category": s.category,
            "capabilities": s.capabilities or [],
            "security_level": s.security_level,
            "rating": s.rating,
            "usage_count": s.usage_count,
            "success_rate": s.success_rate,
        }
        for s in skills
    ]

@router.get("/competencies", response_model=List[CompetencyOut])
def list_competencies(db: Session = Depends(get_db)):
    comps = db.query(AgentCompetency).all()
    return [
        {
            "agent_id": c.agent_id,
            "skill_id": c.skill_id,
            "proficiency": c.proficiency,
            "experience_hours": c.experience_hours,
            "level": c.level.value if hasattr(c.level, 'value') else str(c.level),
            "success_count": c.success_count,
            "failure_count": c.failure_count,
            "last_used": c.last_used,
            "certified": c.certified,
        }
        for c in comps
    ]

@router.get("/tasks", response_model=List[LoopTaskOut])
def list_loop_tasks(db: Session = Depends(get_db), limit: int = 50):
    tasks = db.query(LoopTask).order_by(LoopTask.created_at.desc()).limit(limit).all()
    return [
        {
            "task_id": t.task_id,
            "type": t.type.value if hasattr(t.type, 'value') else str(t.type),
            "status": t.status.value if hasattr(t.status, 'value') else str(t.status),
            "priority": t.priority,
            "objective": t.objective,
            "agent_id": t.agent_id,
            "skill_id": t.skill_id,
            "result": t.result or {},
            "error": t.error,
            "latency_ms": t.latency_ms,
            "created_at": t.created_at,
        }
        for t in tasks
    ]

@router.post("/seed")
def seed_agents_and_skills(db: Session = Depends(get_db)):
    """Cria agentes e skills base - P0 foundation"""
    # Usar nova sessão para seed
    from ..core.database import SessionLocal
    local_db = SessionLocal()
    try:
        mgr = agent_manager
        mgr.db = local_db
        skills_created = mgr.seed_skills()
        agents_created = mgr.seed_agents()
        return {
            "skills_created": skills_created,
            "agents_created": agents_created,
            "message": f"Criados {skills_created} skills e {agents_created} agentes com competências medidas"
        }
    finally:
        local_db.close()

@router.post("/loop/run")
async def run_loop_cycle():
    """Executa um ciclo completo do loop: DISCOVERY -> HEALTH -> BENCHMARK -> RATING -> AUDIT -> EVOLUTION"""
    try:
        await loop_engine.run_single_loop()
        return {
            "status": "completed",
            "stats": loop_engine.stats,
            "message": "Loop cycle executado: discovery, health, benchmark, rating, audit, evolution"
        }
    except Exception as e:
        raise HTTPException(500, f"Loop failed: {str(e)[:1000]}")

@router.get("/loop/stats")
def get_loop_stats():
    return loop_engine.stats

@router.get("/{agent_id}", response_model=AgentOut)
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    a = db.query(AgentDB).filter(AgentDB.agent_id == agent_id).first()
    if not a:
        raise HTTPException(404, "Agent not found")
    return {
        "agent_id": a.agent_id,
        "name": a.name,
        "role": a.role.value if hasattr(a.role, 'value') else str(a.role),
        "status": a.status.value if hasattr(a.status, 'value') else str(a.status),
        "description": a.description,
        "skills": a.skills or [],
        "competencies": a.competencies or {},
        "tools": a.tools or [],
        "permissions": a.permissions or [],
        "rating": a.rating,
        "confidence": a.confidence,
        "success_count": a.success_count,
        "failure_count": a.failure_count,
        "avg_latency_ms": a.avg_latency_ms,
        "total_tasks": a.total_tasks,
        "evolution_level": a.evolution_level,
        "last_active": a.last_active,
    }
