"""
PROJECT WORKPLACE - Espaço para projetos criados a partir de pedidos no chat
Rigoroso, real, funcional. Você cria orientando a AI.
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean
from sqlalchemy.sql import func
from ..core.database import Base
import uuid
from datetime import datetime

class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, unique=True, nullable=False)  # slug
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    type = Column(String, default="generic")  # python, fastapi, react, nextjs, generic
    status = Column(String, default="active")  # active, archived, draft
    
    # Origem - de qual request veio
    created_from_request_id = Column(String, nullable=True)
    created_from_prompt = Column(Text, nullable=True)
    provider_used = Column(String, nullable=True)
    model_used = Column(String, nullable=True)
    
    # Files - {path: content} - essencial para workplace
    files = Column(JSON, default=dict)  # {"main.py": "code...", "README.md": "..."}
    file_count = Column(Integer, default=0)
    
    # Metadata
    tags = Column(JSON, default=list)  # ["nif", "validation", "python"]
    language = Column(String, default="python")  # python, typescript, javascript
    framework = Column(String, default="")  # fastapi, react, nextjs
    
    # Stats
    total_generations = Column(Integer, default=1)  # quantas vezes AI gerou/atualizou
    last_generation_at = Column(DateTime, server_default=func.now())
    
    # Workplace
    is_favorite = Column(Boolean, default=False)
    is_template = Column(Boolean, default=False)
    
    # P4 - Branches, merge, enterprise
    branches = Column(JSON, default=dict)  # {"main": {"files": {...}, "created_at": "..."}, "feature-x": {...}}
    current_branch = Column(String, default="main")
    export_targets = Column(JSON, default=list)  # ["github", "vercel", "docker"]
    github_repo = Column(String, nullable=True)
    vercel_url = Column(String, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())

class ProjectBranch(Base):
    __tablename__ = "project_branches"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, nullable=False)
    branch_name = Column(String, nullable=False)
    files = Column(JSON, default=dict)
    created_from = Column(String, default="main")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())
    is_merged = Column(Boolean, default=False)
    merged_at = Column(DateTime, nullable=True)
    merge_conflicts = Column(JSON, default=list)

class ProjectGeneration(Base):
    __tablename__ = "project_generations"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, nullable=False)  # FK to Project.project_id
    request_id = Column(String, nullable=True)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)  # raw AI response
    files_changed = Column(JSON, default=list)  # ["main.py", "utils.py"]
    provider = Column(String, nullable=True)
    model = Column(String, nullable=True)
    latency_ms = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
