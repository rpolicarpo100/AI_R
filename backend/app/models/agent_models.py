"""
AGENT MODELS - Agentes com Skills e Competências
Rigoroso, real, sem simulação. Agentes aprendem com evidência medida.
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from ..core.database import Base
import enum
import uuid
from datetime import datetime

class AgentStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    LEARNING = "LEARNING"
    OFFLINE = "OFFLINE"
    DISABLED = "DISABLED"

class AgentRole(str, enum.Enum):
    PLANNER = "PLANNER"
    RESEARCH = "RESEARCH"
    ARCHITECTURE = "ARCHITECTURE"
    CODING = "CODING"
    TESTING = "TESTING"
    SECURITY = "SECURITY"
    AUDIT = "AUDIT"
    DISCOVERY = "DISCOVERY"
    BENCHMARK = "BENCHMARK"
    RATING = "RATING"
    EVOLUTION = "EVOLUTION"
    ROUTER = "ROUTER"
    ORCHESTRATOR = "ORCHESTRATOR"
    PROMPT_ENGINEER = "PROMPT_ENGINEER"
    CRITIC = "CRITIC"
    CODE_REVIEWER = "CODE_REVIEWER"
    INTENT_ANALYZER = "INTENT_ANALYZER"

class SkillLevel(str, enum.Enum):
    NOVICE = "NOVICE"      # 0-25
    INTERMEDIATE = "INTERMEDIATE"  # 25-50
    ADVANCED = "ADVANCED"  # 50-75
    EXPERT = "EXPERT"      # 75-90
    MASTER = "MASTER"      # 90-100

class LoopTaskType(str, enum.Enum):
    DISCOVERY = "DISCOVERY"
    HEALTH_CHECK = "HEALTH_CHECK"
    BENCHMARK = "BENCHMARK"
    RATING = "RATING"
    AUDIT = "AUDIT"
    EVOLUTION = "EVOLUTION"
    CLEANUP = "CLEANUP"
    SECURITY_SCAN = "SECURITY_SCAN"

class LoopTaskStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class AgentDB(Base):
    __tablename__ = "agents"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, unique=True, nullable=False)  # slug
    name = Column(String, nullable=False)
    role = Column(SQLEnum(AgentRole), nullable=False)
    status = Column(SQLEnum(AgentStatus), default=AgentStatus.AVAILABLE)
    description = Column(Text, default="")
    
    # Skills e competências - JSON para flexibilidade mas com estrutura rigorosa
    # skills: [{"skill_id": "python", "proficiency": 85, "experience_hours": 120, "last_used": "...", "certified": false}]
    skills = Column(JSON, default=list)
    # competencies: {"coding": 90, "security": 70, "research": 85} - agregado por categoria
    competencies = Column(JSON, default=dict)
    tools = Column(JSON, default=list)  # ["web_search", "benchmark", "health_check", ...]
    permissions = Column(JSON, default=list)
    
    # Métricas medidas, não inventadas
    rating = Column(Float, default=50.0)  # 0-100, baseado em success_rate medido
    confidence = Column(Float, default=0.0)  # 0-100, baseado em test_count
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    avg_latency_ms = Column(Float, default=0.0)
    total_tasks = Column(Integer, default=0)
    
    # Aprendizado
    learning_history = Column(JSON, default=list)  # [{"task": "...", "result": "...", "improvement": 5}]
    evolution_level = Column(Integer, default=1)  # nível de evolução
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())
    last_active = Column(DateTime, nullable=True)

class SkillDB(Base):
    __tablename__ = "skills"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    skill_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    version = Column(String, default="1.0")
    category = Column(String, default="general")  # coding, security, research, etc.
    
    capabilities = Column(JSON, default=list)
    inputs = Column(JSON, default=list)
    outputs = Column(JSON, default=list)
    requirements = Column(JSON, default=list)
    
    preferred_models = Column(JSON, default=list)
    fallback_models = Column(JSON, default=list)
    
    security_level = Column(String, default="LOW")  # LOW, MEDIUM, HIGH
    status = Column(String, default="AVAILABLE")
    
    # Métricas medidas
    rating = Column(Float, default=50.0)
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    avg_latency_ms = Column(Float, default=0.0)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())

class AgentCompetency(Base):
    __tablename__ = "agent_competencies"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, nullable=False)  # FK to AgentDB.agent_id
    skill_id = Column(String, nullable=False)  # FK to SkillDB.skill_id
    
    proficiency = Column(Float, default=0.0)  # 0-100 medido
    experience_hours = Column(Float, default=0.0)
    level = Column(SQLEnum(SkillLevel), default=SkillLevel.NOVICE)
    
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)
    certified = Column(Boolean, default=False)
    
    # Evidência
    evidence = Column(JSON, default=dict)  # {"benchmarks": [...], "tasks": [...]}
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())

class LoopTask(Base):
    __tablename__ = "loop_tasks"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, unique=True, nullable=False)
    type = Column(SQLEnum(LoopTaskType), nullable=False)
    status = Column(SQLEnum(LoopTaskStatus), default=LoopTaskStatus.QUEUED)
    priority = Column(String, default="P1")  # P0-P3
    
    objective = Column(Text, nullable=False)
    agent_id = Column(String, nullable=True)  # assigned agent
    skill_id = Column(String, nullable=True)
    
    # Execução
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    result = Column(JSON, default=dict)
    error = Column(Text, nullable=True)
    latency_ms = Column(Integer, default=0)
    
    # Dependências e contexto
    dependencies = Column(JSON, default=list)
    context = Column(JSON, default=dict)
    
    scheduled_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
