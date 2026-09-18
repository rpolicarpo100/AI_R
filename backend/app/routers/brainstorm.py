"""
Brainstorm Router — Vertente de brainstorming antes de construir ou responder
POST /api/brainstorm — brainstorm antes de responder
POST /api/brainstorm/build — brainstorm antes de construir app/site
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from ..services.brainstorming_service import brainstorming_service

router = APIRouter(prefix="/brainstorm", tags=["brainstorm"])

class BrainstormRequest(BaseModel):
    prompt: str
    chat_history: Optional[List[Dict[str, Any]]] = None
    profile: Optional[str] = "BEST"
    available_templates: Optional[List[str]] = None

@router.post("/")
async def brainstorm_before_respond(req: BrainstormRequest):
    """
    Brainstorm antes de responder — 3-5 interpretações possíveis
    Para ficar mais perto do objetivo final, não ficar na 1ª tentativa
    """
    result = brainstorming_service.brainstorm_before_respond(
        user_prompt=req.prompt,
        chat_history=req.chat_history,
        profile=req.profile
    )
    return {
        "status": "SUCCESS",
        "brainstorm": result,
        "version": "Brainstorming antes de responder — mais perto do objetivo final"
    }

@router.post("/build")
async def brainstorm_before_build(req: BrainstormRequest):
    """
    Brainstorm antes de construir app/site — 3-5 abordagens arquiteturais
    MVP vs full vs custom, template mais próximo, effort, pros/cons
    """
    result = brainstorming_service.brainstorm_before_build(
        user_prompt=req.prompt,
        available_templates=req.available_templates
    )
    return {
        "status": "SUCCESS",
        "brainstorm": result,
        "version": "Brainstorming antes de construir — mais perto do objetivo final"
    }

@router.get("/templates")
async def list_templates_for_brainstorm():
    """Lista templates disponíveis para brainstorming"""
    from ..services.brainstorming_service import TEMPLATES
    return {
        "templates": TEMPLATES,
        "count": len(TEMPLATES),
        "version": "13 templates — 6→13 com chat-app, portfolio, api-gateway"
    }
