"""
P8.3 Multi-Agent REAL router
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
    """Run full multi-agent pipeline: intent -> optimizer -> router -> main -> critic -> reviewer -> rigor"""
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
    """Run a single agent - REAL execution via orchestrator"""
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
    """Get all agents status with real metrics"""
    return multi_agent_service.get_agents_status()

@router.get("/pipeline-info")
def pipeline_info():
    return {
        "pipeline": "intent-analyzer-01 → prompt-optimizer-01 → router-01 → main_llm (orchestrator) → critic-01 → code-reviewer-01 → rigor-checker-01",
        "description": "Multi-agent REAL P8.3 - cada agente executa via orchestrator, mede latency, registra resultado, evolui",
        "agents": [
            {"id": "intent-analyzer-01", "role": "INTENT_ANALYZER", "purpose": "Analisa intenção profunda, detecta ambiguidade, terceiro olho"},
            {"id": "prompt-optimizer-01", "role": "PROMPT_ENGINEER", "purpose": "Otimiza prompts, adiciona contexto, edge cases, contesta 1ª tentativa"},
            {"id": "router-01", "role": "ROUTER", "purpose": "Seleciona provider/model por ranking medido, failover"},
            {"id": "critic-01", "role": "CRITIC", "purpose": "Critica resposta, funcional, coerente, precisa, rigorosa, terceiro olho aberto"},
            {"id": "code-reviewer-01", "role": "CODE_REVIEWER", "purpose": "Revisa código, segurança, performance, boas práticas"},
            {"id": "rigor-checker-01", "role": "AUDIT", "purpose": "Verifica rigor, marca UNKNOWN, 0% invenção"},
        ],
        "principle": "Você cria orientando AI, agentes apoio chat otimizam respostas funcionais coerentes precisas rigorosas reais profissionais contestam criticam não ficam 1ª tentativa terceiro olho aberto",
        "real": True,
        "simulated": False,
        "measures": ["latency_ms", "success_count", "failure_count", "rating", "evolution_level", "proficiency"]
    }
