"""
P8.3 Multi-Agent REAL router + P23 Builders quando construir app
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..services.multi_agent_service import multi_agent_service

router = APIRouter(prefix="/multi-agent", tags=["multi-agent"])

class MultiAgentChatRequest(BaseModel):
    prompt: str
    chat_history: Optional[List[Dict]] = []
    model: Optional[str] = "auto"
    run_pipeline: bool = True

class SingleAgentRequest(BaseModel):
    agent_id: str
    prompt: str
    context: Optional[Dict] = None
    model: Optional[str] = "auto"

@router.post("/chat")
async def multi_agent_chat(req: MultiAgentChatRequest):
    """Run full multi-agent pipeline: intent -> optimizer -> router -> main -> critic -> reviewer -> rigor + P23 builders quando construir app"""
    try:
        result = await multi_agent_service.run_multi_agent_pipeline(
            user_prompt=req.prompt,
            chat_history=req.chat_history or [],
            model=req.model or "auto"
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run-agent")
async def run_single_agent(req: SingleAgentRequest):
    """Run a single agent - REAL execution via orchestrator — P23 inclui frontend-builder-01 backend-builder-01 deploy-agent-01 brainstormer-01 memory-archiver-01"""
    try:
        result = await multi_agent_service.run_agent(
            agent_id=req.agent_id,
            user_prompt=req.prompt,
            context=req.context or {},
            model=req.model or "auto"
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents-status")
def agents_status():
    """Get all agents status with real metrics — 12 agents P23"""
    return multi_agent_service.get_agents_status()

@router.get("/pipeline-info")
def pipeline_info():
    return {
        "pipeline": "intent-analyzer-01 → prompt-optimizer-01 → router-01 → main_llm (orchestrator) → critic-01 → code-reviewer-01 → [SE construir_app: frontend-builder-01 → backend-builder-01 → deploy-agent-01] → rigor-checker-01",
        "description": "Multi-agent REAL P8.3 + P23 Builders no Pipeline quando construir app — cada agente executa via orchestrator, mede latency, registra resultado, evolui — builders escolhem template 20, geram código buildável, deploy real",
        "agents": [
            {"id": "intent-analyzer-01", "role": "INTENT_ANALYZER", "purpose": "Analisa intenção profunda, detecta ambiguidade, is_build_intent, terceiro olho"},
            {"id": "prompt-optimizer-01", "role": "PROMPT_ENGINEER", "purpose": "Otimiza prompts, adiciona contexto, edge cases, contesta 1ª tentativa"},
            {"id": "router-01", "role": "ROUTER", "purpose": "Seleciona provider/model por ranking medido, failover"},
            {"id": "critic-01", "role": "CRITIC", "purpose": "Critica resposta, funcional, coerente, precisa, rigorosa, terceiro olho aberto"},
            {"id": "code-reviewer-01", "role": "CODE_REVIEWER", "purpose": "Revisa código, segurança, performance, boas práticas"},
            {"id": "rigor-checker-01", "role": "AUDIT", "purpose": "Verifica rigor, marca UNKNOWN, 0% invenção"},
            # P23 builders
            {"id": "frontend-builder-01", "role": "FRONTEND_BUILDER", "purpose": "P23 Constrói frontend real Next.js 15.3.5 Tailwind 20 templates buildável npm run build OK", "conditional": "quando is_build_intent True — construir app, landing, dashboard, etc"},
            {"id": "backend-builder-01", "role": "BACKEND_BUILDER", "purpose": "P23 Constrói backend real FastAPI 201 providers gateway OpenAI-compatible 50 adapters", "conditional": "quando is_build_intent True"},
            {"id": "deploy-agent-01", "role": "DEPLOY", "purpose": "P23 Deploy real GitHub Vercel Docker verifica build env health", "conditional": "quando is_build_intent True"},
            {"id": "brainstormer-01", "role": "BRAINSTORM", "purpose": "Brainstorming 3-5 ideias antes construir, você no centro, terceiro olho", "optional": True},
            {"id": "memory-archiver-01", "role": "MEMORY_ARCHIVER", "purpose": "Arquiva sites apikeyless para acesso rápido análises rápidas", "optional": True},
        ],
        "build_pipeline": {
            "trigger": "is_build_intent = keywords ['cria app','construir app','build app','landing page','dashboard','ecommerce','portfolio','saas','chat app'] ou intent_type construir_app ou CODING com ```",
            "steps_when_build": ["frontend-builder-01: escolhe template 20, gera Next.js", "backend-builder-01: FastAPI 201 providers", "deploy-agent-01: Dockerfile docker-compose health"],
            "steps_always": ["intent-analyzer-01","prompt-optimizer-01","router-01","main_llm","critic-01","code-reviewer-01","rigor-checker-01"],
            "principle": "Quem cria app és tu orientando AI, agentes apoio terceiro olho otimizam para funcional coerente precisa rigorosa real profissional"
        },
        "principle": "Você cria orientando AI, agentes apoio chat otimizam respostas funcionais coerentes precisas rigorosas reais profissionais contestam criticam não ficam 1ª tentativa terceiro olho aberto — P23 builders no pipeline quando construir",
        "real": True,
        "simulated": False,
        "measures": ["latency_ms", "success_count", "failure_count", "rating", "evolution_level", "proficiency"],
        "total_agents": 11,
        "p23": True
    }
