"""
P8.3 Multi-Agent REAL - Agents actually execute tasks via orchestrator, not simulated
Real collaboration: intent -> prompt_optimizer -> router -> critic -> code_reviewer -> rigor_checker
Each agent calls LLM via orchestrator with specific role prompt, measures latency, records result
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from ..core.database import SessionLocal
from ..models.agent_models import AgentDB, AgentStatus
from .agent_manager import agent_manager
from .orchestrator import orchestrator_service

# Agent role prompts - real prompts that make agents behave as described
AGENT_PROMPTS = {
    "intent-analyzer-01": """Você é Intent Analyzer Agent, especialista em entender o que o usuário REALMENTE quer.
Analise o prompt do usuário:
- Intenção profunda (CODING, QUESTION, DEBUG, ARCHITECTURE, etc)
- Requisitos explícitos e implícitos
- Ambiguidades que precisam clarificação
- Edge cases que usuário não mencionou
- Terceiro olho: o que usuário não disse mas precisa?

Responda em JSON: {"intent_type": "...", "requirements": [...], "ambiguities": [...], "edge_cases": [...], "third_eye": "...", "clarification_needed": bool}
Seja rigoroso, não invente, marque UNKNOWN se não souber.""",

    "prompt-optimizer-01": """Você é Prompt Optimizer Agent, otimiza prompts para obter respostas funcionais, coerentes, precisas, rigorosas, reais, profissionais.
Recebe prompt original + análise de intenção.
Tarefas:
- Clarificar ambiguidade
- Adicionar contexto necessário
- Especificar requisitos técnicos (linguagem, framework, testes)
- Adicionar edge cases
- Terceiro olho: melhorar sem mudar intenção original
- Não fica na primeira tentativa, contesta e critica prompt original

Responda em JSON: {"optimized_prompt": "...", "improvements": [...], "enhanced_context": "...", "third_eye_checks": [...]}
Seja crítico, pragmático, orientado a evidência.""",

    "critic-01": """Você é Critic Agent, terceiro olho aberto, contesta, critica, não fica na primeira tentativa.
Recebe prompt otimizado + resposta AI + contexto.
Tarefas:
- Verificar funcionalidade: código funciona? resposta resolve?
- Coerência: lógica consistente?
- Precisão: sem alucinação?
- Rigor: dados medidos vs inventados?
- Profissionalismo: boas práticas?
- Contestar: o que pode melhorar? alternativas?
- Terceiro olho: o que ninguém viu?

Responda em JSON: {"score": 0-100, "is_functional": bool, "is_coherent": bool, "is_rigorous": bool, "is_professional": bool, "issues": [...], "improvements": [...], "third_eye": "...", "should_retry": bool}
Seja rigoroso, real, funcional, sem enganar, contesta, critica, eficiente.""",

    "code-reviewer-01": """Você é Code Reviewer Agent, revisa código gerado com rigor.
Recebe código + prompt + linguagem.
Tarefas:
- Segurança: secrets, injection, SSRF?
- Performance: complexidade, otimizações?
- Boas práticas: clean code, SOLID?
- Bugs: edge cases, null checks?
- Funcional: resolve requisito?
- Profissional: pronto para prod?

Responda em JSON: {"review_score": 0-100, "security_issues": [...], "performance": "...", "bugs": [...], "suggestions": [...], "improved_snippet": "..."}
Você cria orientando AI, não auto-geração.""",

    "rigor-checker-01": """Você é Rigor Checker Agent, verifica rigor, realidade, sem invenção, marca UNKNOWN.
Recebe resposta AI + contexto.
Tarefas:
- Marcar dados inventados vs medidos vs verificados vs UNKNOWN
- Validar APIs: endpoints reais?
- Model IDs reais?
- Preços/quotas reais ou UNKNOWN?
- Nunca inventar, marcar UNKNOWN quando não confirmado
- Distinguir fornecido vs verificado vs medido vs estimado

Responda em JSON: {"rigor_score": 0-100, "invented": [...], "verified": [...], "measured": [...], "unknown": [...], "hallucinations": [...], "honesty": bool}
Princípio: 0% invenção, tudo 0 até medição real.""",

    "router-01": """Você é Router Agent, roteia requests por ranking, failover automático.
Recebe classificação + providers disponíveis + models.
Tarefas:
- Calcular score por perfil (CODING, JSON, SPEED, etc)
- Selecionar provider/model por ranking medido
- Failover se quota acaba
- AUTO vs MANUAL

Responda em JSON: {"selected_provider": "...", "selected_model": "...", "reasoning": "...", "failover_chain": [...], "profile": "..."}
Provider-agnostic, autonomia auditável, modular, segura, cloud-ready, OpenAI-compatible."""
}

class MultiAgentService:
    def __init__(self):
        self.db = SessionLocal()

    async def run_agent(self, agent_id: str, user_prompt: str, context: Dict = None, model: str = "auto") -> Dict:
        """Run a single agent via orchestrator - REAL execution, not simulated"""
        from ..models.database_models import Provider, Model
        from ..services.routing_engine import Profile
        from ..services.classifier import classifier

        agent = self.db.query(AgentDB).filter(AgentDB.agent_id == agent_id).first()
        if not agent:
            return {"error": f"Agent {agent_id} not found", "success": False}

        role_prompt = AGENT_PROMPTS.get(agent_id, f"Você é {agent.name}, {agent.description}")
        
        # Build full prompt for agent
        full_prompt = f"""{role_prompt}

Contexto: {context or {}}
User prompt: {user_prompt}

Responda apenas em JSON válido, sem markdown, sem explicação extra. Seja rigoroso, real, funcional."""

        start = time.time()
        try:
            # Call orchestrator - REAL LLM call via execute_with_routing
            db = SessionLocal()
            providers = db.query(Provider).all()
            models = db.query(Model).all()
            classification = classifier.classify(full_prompt)
            orch_result = await orchestrator_service.execute_with_routing(
                prompt=full_prompt,
                providers=providers,
                models=models,
                profile=Profile.BEST,
                messages=[{"role": "user", "content": full_prompt}]
            )
            db.close()
            response_obj = orch_result["response"]
            content = response_obj.content
            latency_ms = int((time.time() - start) * 1000)
            
            # Try parse JSON
            import json
            try:
                # Extract JSON from markdown if needed
                if "```" in content:
                    # Find json block
                    start_idx = content.find("{")
                    end_idx = content.rfind("}") + 1
                    if start_idx != -1 and end_idx != -1:
                        content = content[start_idx:end_idx]
                parsed = json.loads(content)
            except:
                parsed = {"raw": content[:1000], "parse_error": True}

            # Record success
            agent_manager.record_task_result(agent_id, agent.skills[0].get("skill_id") if agent.skills else "general", True, latency_ms)
            
            return {
                "agent_id": agent_id,
                "agent_name": agent.name,
                "role": agent.role.value if hasattr(agent.role, 'value') else str(agent.role),
                "result": parsed,
                "raw_content": content[:2000],
                "latency_ms": latency_ms,
                "success": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            latency_ms = int((time.time() - start) * 1000)
            agent_manager.record_task_result(agent_id, "general", False, latency_ms)
            return {
                "agent_id": agent_id,
                "agent_name": agent.name if agent else agent_id,
                "error": str(e)[:500],
                "latency_ms": latency_ms,
                "success": False,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def run_multi_agent_pipeline(self, user_prompt: str, chat_history: List[Dict] = None, model: str = "auto") -> Dict:
        """Run full multi-agent pipeline: intent -> optimizer -> router -> critic -> reviewer -> rigor"""
        chat_history = chat_history or []
        pipeline_results = {}
        total_start = time.time()

        # Step 1: Intent Analysis
        print(f"[MultiAgent] Step 1: Intent Analysis for: {user_prompt[:50]}")
        intent_result = await self.run_agent("intent-analyzer-01", user_prompt, {"chat_history": chat_history[-3:]}, model)
        pipeline_results["intent_analysis"] = intent_result

        # Step 2: Prompt Optimization (uses intent result)
        print(f"[MultiAgent] Step 2: Prompt Optimization")
        optimizer_context = {"intent": intent_result.get("result", {}), "original_prompt": user_prompt}
        optimizer_result = await self.run_agent("prompt-optimizer-01", user_prompt, optimizer_context, model)
        pipeline_results["prompt_optimization"] = optimizer_result

        optimized_prompt = optimizer_result.get("result", {}).get("optimized_prompt", user_prompt)

        # Step 3: Router (selects best model)
        print(f"[MultiAgent] Step 3: Router")
        router_context = {"optimized_prompt": optimized_prompt, "intent": intent_result.get("result", {})}
        router_result = await self.run_agent("router-01", optimized_prompt, router_context, model)
        pipeline_results["routing"] = router_result

        # The actual LLM response would be generated here via orchestrator with optimized prompt
        print(f"[MultiAgent] Step 3.5: Main LLM Response with optimized prompt")
        main_start = time.time()
        try:
            from ..models.database_models import Provider, Model
            from ..services.routing_engine import Profile
            from ..services.classifier import classifier
            db = SessionLocal()
            providers = db.query(Provider).all()
            models_list = db.query(Model).all()
            orch_result_main = await orchestrator_service.execute_with_routing(
                prompt=optimized_prompt,
                providers=providers,
                models=models_list,
                profile=Profile.BEST,
                messages=[{"role": "user", "content": optimized_prompt}]
            )
            db.close()
            main_response_obj = orch_result_main["response"]
            main_content = main_response_obj.content
            routing_info = orch_result_main["routing"]
            main_latency = int((time.time() - main_start) * 1000)
            # Convert routing to dict
            routing_dict = {
                "selected": f"{routing_info.selected.model.display_name} / {routing_info.selected.provider.name}",
                "reason": routing_info.selected.reason,
                "profile": routing_info.profile.value,
                "confidence": routing_info.confidence
            }
            routing_info = routing_dict
        except Exception as e:
            main_content = f"Error generating main response: {e}"
            main_latency = int((time.time() - main_start) * 1000)
            routing_info = {}

        pipeline_results["main_response"] = {
            "content": main_content,
            "latency_ms": main_latency,
            "routing": routing_info,
            "optimized_prompt_used": optimized_prompt
        }

        # Step 4: Critic (evaluates main response)
        print(f"[MultiAgent] Step 4: Critic")
        critic_context = {"optimized_prompt": optimized_prompt, "main_response": main_content[:2000], "intent": intent_result.get("result", {})}
        critic_result = await self.run_agent("critic-01", main_content[:2000], critic_context, model)
        pipeline_results["critique"] = critic_result

        # Step 5: Code Reviewer (if coding intent)
        intent_type = intent_result.get("result", {}).get("intent_type", "")
        if "CODING" in str(intent_type).upper() or "```" in main_content:
            print(f"[MultiAgent] Step 5: Code Reviewer")
            reviewer_context = {"prompt": optimized_prompt, "code": main_content[:3000]}
            reviewer_result = await self.run_agent("code-reviewer-01", main_content[:2000], reviewer_context, model)
            pipeline_results["code_review"] = reviewer_result
        else:
            pipeline_results["code_review"] = {"skipped": True, "reason": "Not coding intent"}

        # Step 6: Rigor Checker
        print(f"[MultiAgent] Step 6: Rigor Checker")
        rigor_context = {"main_response": main_content[:2000], "intent": intent_result.get("result", {})}
        rigor_result = await self.run_agent("rigor-checker-01", main_content[:2000], rigor_context, model)
        pipeline_results["rigor_check"] = rigor_result

        total_latency = int((time.time() - total_start) * 1000)

        # Final summary
        should_retry = critic_result.get("result", {}).get("should_retry", False)
        critic_score = critic_result.get("result", {}).get("score", 0)

        return {
            "pipeline": "intent-analyzer → prompt-optimizer → router → main_llm → critic → code-reviewer → rigor-checker",
            "user_prompt": user_prompt,
            "optimized_prompt": optimized_prompt,
            "main_response": main_content,
            "main_latency_ms": main_latency,
            "routing": routing_info,
            "steps": pipeline_results,
            "total_latency_ms": total_latency,
            "critic_score": critic_score,
            "should_retry": should_retry,
            "third_eye": f"Critic: {critic_result.get('result', {}).get('third_eye', '')} | Rigor: {rigor_result.get('result', {}).get('hallucinations', [])}",
            "principle": "Você cria orientando AI, agentes apoio chat otimizam respostas funcionais coerentes precisas rigorosas reais profissionais contestam criticam não ficam 1ª tentativa terceiro olho aberto",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def get_agents_status(self) -> List[Dict]:
        agents = self.db.query(AgentDB).all()
        return [
            {
                "agent_id": a.agent_id,
                "name": a.name,
                "role": a.role.value if hasattr(a.role, 'value') else str(a.role),
                "status": a.status.value if hasattr(a.status, 'value') else str(a.status),
                "rating": a.rating,
                "success_count": a.success_count,
                "failure_count": a.failure_count,
                "total_tasks": a.total_tasks,
                "evolution_level": a.evolution_level,
                "avg_latency_ms": a.avg_latency_ms,
                "description": a.description
            }
            for a in agents
        ]

multi_agent_service = MultiAgentService()
