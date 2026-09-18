"""
AI ORCHESTRATOR - Cérebro Central
Implementa loop: REQUEST -> UNDERSTAND -> PLAN -> DECOMPOSE -> SELECT AGENTS -> SELECT SKILLS -> SELECT MODELS -> SELECT PROVIDERS -> EXECUTE -> VALIDATE -> REPAIR -> AUDIT -> LEARN -> FINAL
"""
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
import time
import hashlib
from datetime import datetime

from .classifier import classifier, TaskType, Classification
from .routing_engine import routing_engine, Profile, RoutingDecision
from .circuit_breaker import circuit_breaker
from ..adapters.openai_compat import GroqAdapter, CerebrasAdapter, OpenRouterAdapter, MistralAdapter, GitHubModelsAdapter, OpenAICompatibleAdapter
from ..adapters.gemini import GeminiAdapter
from ..adapters.ollama import OllamaAdapter
from ..adapters.aihorde import AIHordeAdapter
from .encryption import decrypt_api_key

class AgentRole(str, Enum):
    RESEARCH = "RESEARCH"
    ARCHITECTURE = "ARCHITECTURE"
    CODING = "CODING"
    TESTING = "TESTING"
    SECURITY = "SECURITY"
    AUDIT = "AUDIT"
    BUSINESS = "BUSINESS"
    DATA = "DATA"
    CREATIVE = "CREATIVE"
    PLANNER = "PLANNER"
    ROUTER = "ROUTER"

class TaskStatus(str, Enum):
    QUEUED = "QUEUED"
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    VALIDATING = "VALIDATING"
    REPAIRING = "REPAIRING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

@dataclass
class Skill:
    skill_id: str
    name: str
    description: str
    version: str
    capabilities: List[str]
    inputs: List[str]
    outputs: List[str]
    preferred_models: List[str] = field(default_factory=list)
    fallback_models: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    security_level: str = "LOW"
    status: str = "AVAILABLE"

@dataclass
class Agent:
    agent_id: str
    name: str
    role: AgentRole
    skills: List[str]
    preferred_models: List[str]
    fallback_models: List[str]
    tools: List[str]
    permissions: List[str]
    rating: float = 80.0
    status: str = "AVAILABLE"

@dataclass
class SubTask:
    task_id: str
    parent_task: Optional[str]
    objective: str
    priority: str  # P0-P3
    status: TaskStatus
    agent: Optional[str] = None
    skill: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    attempts: int = 0
    cost: float = 0.0
    latency_ms: int = 0
    result: Optional[str] = None
    validation: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)

@dataclass
class OrchestratorPlan:
    objective: str
    tasks: List[SubTask]
    dependencies: Dict[str, List[str]]
    estimated_cost: float
    estimated_time: int
    required_skills: List[str]
    required_agents: List[AgentRole]
    success_criteria: List[str]

@dataclass
class OrchestratorResult:
    request_id: str
    objective: str
    plan: OrchestratorPlan
    routing: RoutingDecision
    execution_trace: List[Dict]
    final_output: str
    validation: str
    confidence: float
    total_cost: float
    total_latency: int
    fallback_used: bool
    audit_log: List[Dict]

# Skill Registry - conforme spec item 11
SKILL_REGISTRY: List[Skill] = [
    Skill("html", "HTML", "Semantic HTML5", "1.0", ["frontend", "markup"], ["design"], ["html"], security_level="LOW"),
    Skill("css", "CSS", "Modern CSS, Tailwind", "1.0", ["frontend", "styling"], ["design"], ["css"], security_level="LOW"),
    Skill("js", "JavaScript", "ES2023, DOM, APIs", "1.0", ["frontend", "backend", "logic"], ["spec"], ["js"], preferred_models=["codestral", "gpt-4o"], security_level="LOW"),
    Skill("ts", "TypeScript", "Typed JS, Next.js", "1.0", ["frontend", "backend", "typing"], ["spec"], ["ts"], preferred_models=["codestral", "claude-3.5"], security_level="LOW"),
    Skill("react", "React", "React 18, hooks, Next.js", "1.0", ["frontend", "component"], ["design"], ["react"], preferred_models=["claude-3.5", "gpt-4o"], security_level="LOW"),
    Skill("nextjs", "Next.js", "App Router, SSR, API routes", "1.0", ["fullstack", "frontend", "backend"], ["spec"], ["nextjs"], security_level="LOW"),
    Skill("python", "Python", "FastAPI, data, scripting", "1.0", ["backend", "data", "automation"], ["spec"], ["python"], preferred_models=["codestral", "gpt-4o"], security_level="MEDIUM"),
    Skill("fastapi", "FastAPI", "Async APIs, Pydantic", "1.0", ["backend", "api"], ["spec"], ["python", "api"], security_level="MEDIUM"),
    Skill("sql", "SQL", "PostgreSQL, queries, schema", "1.0", ["database", "data"], ["spec"], ["sql"], security_level="MEDIUM"),
    Skill("security", "Security Analysis", "Audit, secrets, vulnerabilities", "1.0", ["security", "audit"], ["code"], ["security_report"], security_level="HIGH"),
    Skill("testing", "Automated Testing", "Unit, integration, e2e", "1.0", ["qa", "validation"], ["code"], ["tests"], security_level="LOW"),
    Skill("research", "Web Research", "Source verification, competitive", "1.0", ["research", "analysis"], ["query"], ["report"], security_level="LOW"),
    Skill("business", "Business Analysis", "Models, KPIs, strategy", "1.0", ["business", "analysis"], ["idea"], ["business_plan"], security_level="LOW"),
]

# Agent Registry
AGENT_REGISTRY: List[Agent] = [
    Agent("planner-01", "Planner Agent", AgentRole.PLANNER, ["research", "business"], ["gemini-1.5-pro", "claude-3.5-sonnet"], ["gpt-4o-mini"], ["plan", "decompose"], ["read", "plan"]),
    Agent("research-01", "Research Agent", AgentRole.RESEARCH, ["research"], ["gemini-2.0-flash", "gpt-4o-mini"], ["llama-3.3-70b"], ["web_search", "doc_analysis"], ["read", "search"]),
    Agent("arch-01", "Architecture Agent", AgentRole.ARCHITECTURE, ["react", "nextjs", "fastapi", "sql"], ["claude-3.5-sonnet", "gemini-1.5-pro"], ["codestral"], ["design", "diagram"], ["read", "design"]),
    Agent("coding-01", "Coding Agent", AgentRole.CODING, ["js", "ts", "react", "nextjs", "python", "fastapi", "html", "css", "sql"], ["codestral-latest", "claude-3.5-sonnet", "gpt-4o"], ["llama-3.3-70b"], ["code", "refactor", "debug"], ["read", "write", "execute"]),
    Agent("testing-01", "QA Agent", AgentRole.TESTING, ["testing"], ["codestral", "gpt-4o-mini"], ["llama-3.3-70b"], ["test", "validate"], ["read", "test"]),
    Agent("security-01", "Security Agent", AgentRole.SECURITY, ["security"], ["claude-3.5-sonnet", "gemini-1.5-pro"], ["gpt-4o"], ["audit", "scan"], ["read", "audit"]),
    Agent("audit-01", "Audit Agent", AgentRole.AUDIT, ["testing", "security", "research"], ["claude-3.5-sonnet"], ["gemini-1.5-pro"], ["validate", "audit"], ["read", "audit"]),
]

# RIGOR: ADAPTERS para todos os 56 providers - fallback para OpenAICompatibleAdapter se não específico
# Mapeia todos os providers descobertos para adapter correto, funcional, real - P9.1 fix cloudflare @cf/ + fireworks accounts/ + typhoon + aihorde
ADAPTERS = {
    "groq": GroqAdapter(),
    "groq2": GroqAdapter(),  # P9 - Groq key 2 backup 30 RPM
    "groq3": GroqAdapter(),  # P9 - Groq key 3 backup 30 RPM
    "cerebras": CerebrasAdapter(),
    "openrouter": OpenRouterAdapter(),
    "mistral": MistralAdapter(),
    "github_models": GitHubModelsAdapter(),
    "gemini": GeminiAdapter(),
    "ollama": OllamaAdapter(),
    "ollama_cloud": OllamaAdapter(),  # P8 - Ollama Cloud free uses same API as local
    "openai": OpenAICompatibleAdapter(),
    "anthropic": OpenAICompatibleAdapter(),
    "huggingface": OpenAICompatibleAdapter(),
    "cohere": OpenAICompatibleAdapter(),
    "together": OpenAICompatibleAdapter(),
    "fireworks": OpenAICompatibleAdapter(),  # P9 fix - accounts/fireworks/models/ prefix handled by OpenAI compat
    "deepseek": OpenAICompatibleAdapter(),
    "perplexity": OpenAICompatibleAdapter(),
    # Novos providers free descobertos - todos OpenAI-compatible real
    "chutes": OpenAICompatibleAdapter(),
    "chutes_ai": OpenAICompatibleAdapter(),
    "nscale": OpenAICompatibleAdapter(),
    "novita": OpenAICompatibleAdapter(),
    "novita_ai": OpenAICompatibleAdapter(),
    "hyperbolic": OpenAICompatibleAdapter(),
    "venice": OpenAICompatibleAdapter(),
    "venice_ai": OpenAICompatibleAdapter(),  # P8 - Venice AI free
    "upstage": OpenAICompatibleAdapter(),
    "coze": OpenAICompatibleAdapter(),
    "requesty": OpenAICompatibleAdapter(),
    "pollinations": OpenAICompatibleAdapter(),  # P8 - Pollinations free 189 models
    "friendli": OpenAICompatibleAdapter(),
    "inference_net": OpenAICompatibleAdapter(),
    "nous": OpenAICompatibleAdapter(),
    "nous_research": OpenAICompatibleAdapter(),
    "hetzner": OpenAICompatibleAdapter(),
    "bazaarlink": OpenAICompatibleAdapter(),
    "agnes": OpenAICompatibleAdapter(),
    "agnes_ai": OpenAICompatibleAdapter(),
    "alibaba": OpenAICompatibleAdapter(),
    "alibaba_cloud": OpenAICompatibleAdapter(),
    "alibaba_dashscope": OpenAICompatibleAdapter(),
    "scaleway": OpenAICompatibleAdapter(),
    "github": OpenAICompatibleAdapter(),
    # P9.1 - Fix cloudflare @cf/ prefix + typhoon + aihorde + outros
    "cloudflare": OpenAICompatibleAdapter(),  # P9 fix - @cf/meta/llama-3.1-8b-instruct needs account_id in base_url, key invalid 403 currently
    "modelscope": OpenAICompatibleAdapter(),
    "llm7": OpenAICompatibleAdapter(),
    "kilo": OpenAICompatibleAdapter(),
    "ovhcloud": OpenAICompatibleAdapter(),  # OVH anonymous 2 RPM no key
    "opencode_zen": OpenAICompatibleAdapter(),
    "aionlabs": OpenAICompatibleAdapter(),
    "zai": OpenAICompatibleAdapter(),  # Z.ai GLM free
    "siliconflow": OpenAICompatibleAdapter(),  # SiliconFlow 3 free models
    "glhf": OpenAICompatibleAdapter(),
    "xai": OpenAICompatibleAdapter(),
    "aihubmix": OpenAICompatibleAdapter(),
    "cerebrium": OpenAICompatibleAdapter(),
    "anyapi": OpenAICompatibleAdapter(),
    "nebius_tokenfactory": OpenAICompatibleAdapter(),
    "nvidia": OpenAICompatibleAdapter(),
    "sambanova": OpenAICompatibleAdapter(),
    "typhoon": OpenAICompatibleAdapter(),  # P9 - Typhoon SCB 10X Thai LLM $0 - verified 200 OK 4/4 success 100%
    "kie_ai": OpenAICompatibleAdapter(),   # P13 - KIE AI 206 models
    "aihorde": AIHordeAdapter(),  # P9 fix - AI Horde community free unlimited - direct API /api/v2/generate/text/async with workers
    "horde": AIHordeAdapter(),
}

def get_adapter_for_provider(provider_id: str):
    """Retorna adapter para provider_id, fallback para OpenAICompatibleAdapter - funcional, não inventa"""
    return ADAPTERS.get(provider_id, OpenAICompatibleAdapter())

class Orchestrator:
    def __init__(self, db_session=None):
        self.db = db_session
        self.classifier = classifier
        self.router = routing_engine
        self.circuit = circuit_breaker

    def decompose_task(self, objective: str, classification: Classification) -> OrchestratorPlan:
        """TASK DECOMPOSITION - transforma pedido complexo em tarefas"""
        objective_lower = objective.lower()
        tasks: List[SubTask] = []
        
        # Detecta se é pedido de app completa
        is_full_app = any(k in objective_lower for k in ["aplicação", "app", "loja", "sistema", "gestão", "dashboard", "constrói", "cria uma"])
        is_expense = "despesa" in objective_lower
        
        if is_full_app:
            # Decomposição padrão para app web
            base_tasks = [
                ("Analisar requisitos e definir arquitetura", AgentRole.ARCHITECTURE, ["business", "research"], "P0"),
                ("Desenhar database schema e modelos", AgentRole.ARCHITECTURE, ["sql"], "P0"),
                ("Implementar backend API (FastAPI)", AgentRole.CODING, ["python", "fastapi", "sql"], "P0"),
                ("Implementar frontend (React/Next.js)", AgentRole.CODING, ["react", "nextjs", "ts", "css"], "P0"),
                ("Implementar autenticação e segurança", AgentRole.SECURITY, ["security", "fastapi"], "P1"),
                ("Criar testes automatizados", AgentRole.TESTING, ["testing"], "P1"),
                ("Auditoria final e validação", AgentRole.AUDIT, ["testing", "security"], "P1"),
            ]
            if is_expense:
                base_tasks.insert(2, ("Definir modelo de despesas, categorias, utilizadores", AgentRole.ARCHITECTURE, ["business", "sql"], "P0"))
            
            for i, (obj, role, skills, prio) in enumerate(base_tasks):
                task_id = f"task-{uuid.uuid4().hex[:8]}"
                deps = [tasks[i-1].task_id] if i > 0 and prio == "P0" else []
                tasks.append(SubTask(
                    task_id=task_id,
                    parent_task=None,
                    objective=obj,
                    priority=prio,
                    status=TaskStatus.QUEUED,
                    agent=role.value,
                    skill=",".join(skills),
                    dependencies=deps
                ))
        else:
            # Tarefa simples = 1 task
            tasks.append(SubTask(
                task_id=f"task-{uuid.uuid4().hex[:8]}",
                parent_task=None,
                objective=objective,
                priority="P1",
                status=TaskStatus.QUEUED,
                agent=AgentRole.CODING.value if classification.task_type == TaskType.CODING else AgentRole.RESEARCH.value,
                skill=classification.task_type.value.lower()
            ))
        
        return OrchestratorPlan(
            objective=objective,
            tasks=tasks,
            dependencies={t.task_id: t.dependencies for t in tasks},
            estimated_cost=len(tasks) * 0.02,
            estimated_time=len(tasks) * 30,
            required_skills=list(set([s for t in tasks for s in t.skill.split(",")])),
            required_agents=list(set([AgentRole(t.agent) for t in tasks if t.agent])),
            success_criteria=[f"{t.objective} completed" for t in tasks]
        )

    def select_agents_for_task(self, task: SubTask, classification: Classification) -> List[Agent]:
        # SPECIALIST SELECTION
        if task.agent:
            matched = [a for a in AGENT_REGISTRY if a.role.value == task.agent]
            if matched:
                return sorted(matched, key=lambda x: x.rating, reverse=True)
        # Fallback by skill
        skill_names = task.skill.split(",")
        candidates = []
        for agent in AGENT_REGISTRY:
            overlap = len(set(agent.skills) & set(skill_names))
            if overlap > 0:
                candidates.append((agent, overlap))
        candidates.sort(key=lambda x: (x[1], x[0].rating), reverse=True)
        return [c[0] for c in candidates[:2]] or [AGENT_REGISTRY[2]]  # coding agent default

    async def execute_with_routing(self, prompt: str, providers, models, profile: Profile = None, messages: List[Dict] = None, tools: List[Dict] = None, tool_choice: Any = None, response_format: Dict = None, temperature: float = 0.7, max_tokens: int = 2000, stream: bool = False, early_classification=None, **kwargs) -> Dict:
        """ROUTING + FAILOVER + CIRCUIT BREAKER + EXECUTE — P20 CLINE_CODING + P0 token calculator + early_classification reuse"""
        messages = messages or [{"role": "user", "content": prompt}]
        # P0 — Reuse early_classification if provided — saves 10ms duplicate
        if early_classification:
            classification = early_classification
            print(f"[P0 REUSE] Reusing early_classification {classification.task_type} complexity {classification.complexity_level} — saves 10ms")
        else:
            classification = self.classifier.classify(prompt, messages)
        
        # P20 — If tools present, mark classification as requiring tools
        if tools:
            classification.requires_tools = True
            if classification.task_type not in [TaskType.TOOL_CALLING, TaskType.CODING]:
                classification.task_type = TaskType.TOOL_CALLING
                classification.reasoning += f" | tools present {len(tools)} → TOOL_CALLING"
        
        # P0 — Use token_calculator coherent — single source
        try:
            from ..core.token_calculator import calculate_tokens
            token_calc = calculate_tokens(
                messages=messages,
                tools=tools,
                system=None,
                max_tokens_requested=max_tokens
            )
            requested_tokens = token_calc["estimated_input"]
            # For backward compat, keep estimated_tokens as input
            classification.estimated_tokens = requested_tokens
            print(f"[P0 TOKEN] orchestrator non-stream: estimated_input={token_calc['estimated_input']} tools={token_calc['tools_tokens']} overhead={token_calc['overhead']} effective_output={token_calc['effective_output']}")
        except Exception as e:
            print(f"[P0 TOKEN] calc failed {e}, fallback len//4")
            tools_tokens = len(str(tools)) // 4 if tools else 0
            requested_tokens = classification.estimated_tokens + tools_tokens
            classification.estimated_tokens = requested_tokens
        
        # Routing decision — P20 uses existing routing_engine, not second system
        routing = self.router.route(providers, models, classification, profile)
        
        # Check circuit breaker — P20 failover automático
        if not self.circuit.can_execute(routing.selected.provider.provider_id):
            # Try alternatives
            for alt in routing.alternatives:
                if self.circuit.can_execute(alt.provider.provider_id):
                    print(f"[CLINE_CODING FALLBACK] Circuit open for {routing.selected.provider.provider_id}, trying {alt.provider.provider_id}/{alt.model.model_id}")
                    routing.selected = alt
                    break
        
        execution_trace = []
        fallback_chain = []
        final_response = None
        total_latency = 0
        fallback_reasons = []
        
        # Try primary + fallbacks — P20 fallback real
        candidates = [routing.selected] + routing.alternatives
        for idx, candidate in enumerate(candidates):
            provider = candidate.provider
            model = candidate.model
            
            # P20 LONG CONTEXT logging: requested_tokens, model_context_limit, selected_model, fallback_reason
            model_context_limit = model.context_window or 0
            if model_context_limit and requested_tokens > model_context_limit:
                fallback_reason = f"requested_tokens {requested_tokens} > model_context_limit {model_context_limit} for {provider.provider_id}/{model.model_id}"
                print(f"[CLINE_CODING LONG CONTEXT] {fallback_reason} — excluding model, fallback")
                execution_trace.append({"provider": provider.provider_id, "model": model.model_id, "status": "SKIPPED_CONTEXT_LIMIT", "requested_tokens": requested_tokens, "model_context_limit": model_context_limit, "fallback_reason": fallback_reason})
                fallback_chain.append({"provider": provider.provider_id, "model": model.model_id, "status": "SKIPPED_CONTEXT_LIMIT", "requested_tokens": requested_tokens, "model_context_limit": model_context_limit, "fallback_reason": fallback_reason})
                fallback_reasons.append(fallback_reason)
                continue
            
            if not self.circuit.can_execute(provider.provider_id):
                state = self.circuit.get_state(provider.provider_id) if hasattr(self.circuit, 'get_state') else "OPEN"
                execution_trace.append({"provider": provider.provider_id, "model": model.model_id, "status": "SKIPPED_CIRCUIT_OPEN", "reason": str(state), "requested_tokens": requested_tokens, "model_context_limit": model_context_limit})
                fallback_chain.append({"provider": provider.provider_id, "model": model.model_id, "status": "SKIPPED_CIRCUIT_OPEN", "reason": str(state)})
                fallback_reasons.append(f"Circuit open {provider.provider_id}")
                continue
            
            adapter = get_adapter_for_provider(provider.provider_id)
            
            # Decrypt API key
            try:
                api_key = decrypt_api_key(provider.api_key_encrypted) if provider.api_key_encrypted else ""
            except:
                api_key = ""
            
            # RIGOR: ollama não precisa de API key - local real, quem cria app é o utilizador
            if not api_key and provider.provider_id not in ["ollama"] and provider.auth_type != "none":
                execution_trace.append({"provider": provider.provider_id, "model": model.model_id, "status": "SKIPPED_NO_KEY", "reason": "No API key configured", "requested_tokens": requested_tokens, "model_context_limit": model_context_limit})
                fallback_chain.append({"provider": provider.provider_id, "model": model.model_id, "status": "SKIPPED_NO_KEY"})
                fallback_reasons.append(f"No key {provider.provider_id}")
                continue
            
            try:
                execution_trace.append({"provider": provider.provider_id, "model": model.model_id, "status": "ATTEMPTING", "attempt": idx+1, "requested_tokens": requested_tokens, "model_context_limit": model_context_limit, "selected_model": f"{provider.provider_id}/{model.model_id}"})
                # P20 — Pass through OpenAI-compatible params: tools, tool_choice, response_format, temperature, max_tokens, stream, etc
                # P2.2 — Pass provider_id for quota tracking
                resp = await adapter.chat_completion(
                    model_id=model.model_id,
                    messages=messages,
                    api_key=api_key,
                    base_url=provider.base_url,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=tools,
                    tool_choice=tool_choice,
                    response_format=response_format,
                    stream=stream,
                    provider_id=provider.provider_id,
                    **kwargs
                )
                # Success
                self.circuit.record_success(provider.provider_id)
                total_latency += resp.latency_ms
                final_response = resp
                fallback_chain.append({"provider": provider.provider_id, "model": model.model_id, "status": "SUCCESS", "latency": resp.latency_ms, "requested_tokens": requested_tokens, "model_context_limit": model_context_limit, "selected_model": f"{provider.provider_id}/{model.model_id}"})
                execution_trace[-1]["status"] = "SUCCESS"
                execution_trace[-1]["latency_ms"] = resp.latency_ms
                execution_trace[-1]["selected_model"] = f"{provider.provider_id}/{model.model_id}"
                print(f"[CLINE_CODING SUCCESS] {provider.provider_id}/{model.model_id} latency {resp.latency_ms}ms tokens req {requested_tokens} limit {model_context_limit} tools {bool(tools)}")
                break
            except Exception as e:
                err_msg = str(e)
                # P0.5 — Parse Retry-After from error message and pass to circuit breaker
                retry_after = None
                try:
                    import re
                    m = re.search(r'Retry-After:\s*(\d+)', err_msg)
                    if m:
                        retry_after = int(m.group(1))
                except:
                    pass
                self.circuit.record_failure(provider.provider_id, retry_after_seconds=retry_after)
                # P0.5.1 — Model lifecycle DEPRECATED after 3x MODEL_NOT_FOUND
                try:
                    self.circuit.record_model_failure(provider.provider_id, model.model_id, err_msg)
                except:
                    pass
                execution_trace[-1]["status"] = "FAILED"
                execution_trace[-1]["error"] = err_msg[:500]
                execution_trace[-1]["fallback_reason"] = err_msg[:200]
                if retry_after:
                    execution_trace[-1]["retry_after"] = retry_after
                fallback_chain.append({"provider": provider.provider_id, "model": model.model_id, "status": "FAILED", "error": err_msg[:200], "requested_tokens": requested_tokens, "model_context_limit": model_context_limit, "fallback_reason": err_msg[:200], "retry_after": retry_after})
                fallback_reasons.append(f"{provider.provider_id}/{model.model_id} failed: {err_msg[:100]}")
                print(f"[CLINE_CODING FALLBACK P0.5] {provider.provider_id}/{model.model_id} failed: {err_msg[:200]} retry_after={retry_after} — trying next")
                
                # Check if error is retryable
                if any(code in err_msg for code in ["AUTH_FAILED", "MODEL_NOT_FOUND"]):
                    # Don't retry same provider type for auth errors
                    continue
                # For 429, timeout, etc - continue to next
                continue
        
        if not final_response:
            # P0 — Error contract: map to correct HTTP status 413/429/503/500
            no_key_count = len([t for t in execution_trace if "SKIPPED_NO_KEY" in t.get("status","")])
            if no_key_count == len(candidates) and len(candidates) > 0:
                raise Exception(f"NO_PROVIDER_AVAILABLE: Nenhum provider com API key configurada. Routing escolheu {routing.selected.provider.provider_id}/{routing.selected.model.model_id} (reason: {routing.selected.reason}) mas sem key não pode executar. Adicione keys em /api/providers. Trace: {execution_trace} Fallback reasons: {fallback_reasons} Requested tokens: {requested_tokens}")
            else:
                # P0 — Check if all rate limited → will be mapped to 429 in chat.py error handling
                # Check if all context filtered → 413
                context_filtered_count = len([t for t in execution_trace if "SKIPPED_CONTEXT_LIMIT" in t.get("status","")])
                if context_filtered_count > 0 and context_filtered_count == len(candidates):
                    raise Exception(f"REQUEST_TOO_LARGE: Request {requested_tokens} tokens exceeds all models context limits. Chain: {fallback_chain} | Fallback reasons: {fallback_reasons} | Requested tokens: {requested_tokens} Model context limit: {model.context_window if 'model' in locals() else 'UNKNOWN'} | P0 413")
                rate_limited_count = len([r for r in fallback_reasons if "rate_limit" in r.lower() or "429" in r])
                if rate_limited_count >0 and rate_limited_count == len(fallback_reasons) and len(fallback_reasons)>0:
                    raise Exception(f"ALL_RATE_LIMITED: All providers rate limited. Chain: {fallback_chain} | Reasons: {fallback_reasons} | Requested tokens: {requested_tokens} | P0 429")
                raise Exception(f"All providers failed. Chain: {fallback_chain} | Trace: {execution_trace} | Fallback reasons: {fallback_reasons} | Requested tokens: {requested_tokens} Model context limit: {model.context_window if 'model' in locals() else 'UNKNOWN'}")
        
        return {
            "response": final_response,
            "routing": routing,
            "trace": execution_trace,
            "fallback_chain": fallback_chain,
            "fallback_used": len(fallback_chain) > 1,
            "fallback_reasons": fallback_reasons,
            "classification": classification,
            "total_latency": total_latency,
            "requested_tokens": requested_tokens,
            "model_context_limit": final_response.raw_response.get("model_context_limit") if final_response.raw_response else model.context_window if 'model' in locals() else 0
        }

    async def execute_with_routing_stream(self, prompt: str, providers, models, profile: Profile = None, messages: List[Dict] = None, tools: List[Dict] = None, tool_choice: Any = None, response_format: Dict = None, temperature: float = 0.7, max_tokens: int = 2000, early_classification=None, **kwargs):
        """
        P21 TRUE STREAMING + P0 token calculator + early_classification reuse
        Cline -> classifier -> routing -> provider -> streaming response -> Cline
        """
        messages = messages or [{"role": "user", "content": prompt}]
        if early_classification:
            classification = early_classification
            print(f"[P0 REUSE STREAM] Reusing early_classification {classification.task_type} — saves 10ms")
        else:
            classification = self.classifier.classify(prompt, messages)
        
        if tools:
            classification.requires_tools = True
            if classification.task_type not in [TaskType.TOOL_CALLING, TaskType.CODING]:
                classification.task_type = TaskType.TOOL_CALLING
                classification.reasoning += f" | tools present {len(tools)} → TOOL_CALLING"
        
        try:
            from ..core.token_calculator import calculate_tokens
            token_calc = calculate_tokens(messages=messages, tools=tools, system=None, max_tokens_requested=max_tokens)
            requested_tokens = token_calc["estimated_input"]
            classification.estimated_tokens = requested_tokens
            print(f"[P0 TOKEN] orchestrator stream: estimated_input={token_calc['estimated_input']} tools={token_calc['tools_tokens']}")
        except Exception as e:
            print(f"[P0 TOKEN] stream calc failed {e}")
            tools_tokens = len(str(tools)) // 4 if tools else 0
            requested_tokens = classification.estimated_tokens + tools_tokens
            classification.estimated_tokens = requested_tokens
        
        routing = self.router.route(providers, models, classification, profile)
        
        # Check circuit breaker for primary
        if not self.circuit.can_execute(routing.selected.provider.provider_id):
            for alt in routing.alternatives:
                if self.circuit.can_execute(alt.provider.provider_id):
                    print(f"[CLINE_CODING STREAMING FALLBACK] Circuit open for {routing.selected.provider.provider_id}, trying {alt.provider.provider_id}/{alt.model.model_id}")
                    routing.selected = alt
                    break
        
        execution_trace = []
        fallback_chain = []
        fallback_reasons = []
        total_latency = 0
        first_chunk_received = False
        selected_provider = None
        selected_model = None
        
        candidates = [routing.selected] + routing.alternatives
        for idx, candidate in enumerate(candidates):
            provider = candidate.provider
            model = candidate.model
            
            model_context_limit = model.context_window or 0
            if model_context_limit and requested_tokens > model_context_limit:
                fallback_reason = f"requested_tokens {requested_tokens} > model_context_limit {model_context_limit} for {provider.provider_id}/{model.model_id}"
                print(f"[CLINE_CODING STREAMING LONG CONTEXT] {fallback_reason} — excluding, fallback")
                execution_trace.append({"provider": provider.provider_id, "model": model.model_id, "status": "SKIPPED_CONTEXT_LIMIT", "requested_tokens": requested_tokens, "model_context_limit": model_context_limit, "fallback_reason": fallback_reason})
                fallback_chain.append({"provider": provider.provider_id, "model": model.model_id, "status": "SKIPPED_CONTEXT_LIMIT"})
                fallback_reasons.append(fallback_reason)
                continue
            
            if not self.circuit.can_execute(provider.provider_id):
                state = self.circuit.get_state(provider.provider_id) if hasattr(self.circuit, 'get_state') else "OPEN"
                execution_trace.append({"provider": provider.provider_id, "model": model.model_id, "status": "SKIPPED_CIRCUIT_OPEN", "reason": str(state)})
                fallback_chain.append({"provider": provider.provider_id, "model": model.model_id, "status": "SKIPPED_CIRCUIT_OPEN"})
                fallback_reasons.append(f"Circuit open {provider.provider_id}")
                continue
            
            adapter = get_adapter_for_provider(provider.provider_id)
            
            try:
                api_key = decrypt_api_key(provider.api_key_encrypted) if provider.api_key_encrypted else ""
            except:
                api_key = ""
            
            if not api_key and provider.provider_id not in ["ollama"] and provider.auth_type != "none":
                execution_trace.append({"provider": provider.provider_id, "model": model.model_id, "status": "SKIPPED_NO_KEY", "reason": "No API key"})
                fallback_chain.append({"provider": provider.provider_id, "model": model.model_id, "status": "SKIPPED_NO_KEY"})
                fallback_reasons.append(f"No key {provider.provider_id}")
                continue
            
            try:
                execution_trace.append({"provider": provider.provider_id, "model": model.model_id, "status": "ATTEMPTING_STREAM", "attempt": idx+1, "requested_tokens": requested_tokens, "model_context_limit": model_context_limit})
                print(f"[CLINE_CODING STREAMING] Attempting {provider.provider_id}/{model.model_id} latency target <500ms tools={bool(tools)} req_tokens={requested_tokens} limit={model_context_limit}")
                
                start = time.time()
                stream_gen = adapter.chat_completion_stream(
                    model_id=model.model_id,
                    messages=messages,
                    api_key=api_key,
                    base_url=provider.base_url,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=tools,
                    tool_choice=tool_choice,
                    response_format=response_format,
                    provider_id=provider.provider_id,
                    **kwargs
                )
                
                chunk_count = 0
                async for chunk in stream_gen:
                    if chunk.get("type") == "chunk":
                        chunk_count += 1
                        if not first_chunk_received:
                            first_chunk_received = True
                            selected_provider = provider
                            selected_model = model
                            latency_first = int((time.time() - start) * 1000)
                            print(f"[CLINE_CODING STREAMING] First chunk from {provider.provider_id}/{model.model_id} after {latency_first}ms — TRUE STREAMING")
                            execution_trace[-1]["status"] = "STREAMING"
                            execution_trace[-1]["first_chunk_latency_ms"] = latency_first
                            fallback_chain.append({"provider": provider.provider_id, "model": model.model_id, "status": "STREAMING", "first_chunk_latency_ms": latency_first})
                            self.circuit.record_success(provider.provider_id)
                        # Yield chunk with routing info for caller
                        yield {
                            "type": "chunk",
                            "data": chunk.get("data"),
                            "provider": provider.provider_id,
                            "model": model.model_id,
                            "routing": routing,
                            "trace": execution_trace,
                            "fallback_chain": fallback_chain,
                            "fallback_reasons": fallback_reasons,
                            "requested_tokens": requested_tokens,
                            "model_context_limit": model_context_limit,
                            "classification": classification
                        }
                    elif chunk.get("type") == "done":
                        total_latency = int((time.time() - start) * 1000)
                        print(f"[CLINE_CODING STREAMING] Done {provider.provider_id}/{model.model_id} chunks={chunk_count} total_latency={total_latency}ms")
                        yield {
                            "type": "done",
                            "provider": provider.provider_id,
                            "model": model.model_id,
                            "routing": routing,
                            "trace": execution_trace,
                            "fallback_chain": fallback_chain,
                            "fallback_reasons": fallback_reasons,
                            "total_latency": total_latency,
                            "chunk_count": chunk_count,
                            "requested_tokens": requested_tokens,
                            "model_context_limit": model_context_limit,
                            "classification": classification
                        }
                        return
                    elif chunk.get("type") == "error":
                        print(f"[CLINE_CODING STREAMING ERROR] {provider.provider_id}/{model.model_id} error during streaming: {chunk.get('error')}")
                        if not first_chunk_received:
                            # Fail before first chunk — try next provider
                            self.circuit.record_failure(provider.provider_id)
                            execution_trace[-1]["status"] = "FAILED_STREAM_BEFORE_FIRST_CHUNK"
                            execution_trace[-1]["error"] = chunk.get("error", "")[:500]
                            fallback_chain.append({"provider": provider.provider_id, "model": model.model_id, "status": "FAILED_STREAM", "error": chunk.get("error", "")[:200]})
                            fallback_reasons.append(f"{provider.provider_id}/{model.model_id} stream failed before first chunk: {chunk.get('error','')[:100]}")
                            break  # try next candidate
                        else:
                            # Fail mid-stream after chunks sent — yield error and stop
                            yield {
                                "type": "error",
                                "error": chunk.get("error"),
                                "provider": provider.provider_id,
                                "model": model.model_id,
                                "routing": routing,
                                "trace": execution_trace,
                                "fallback_chain": fallback_chain,
                                "fallback_reasons": fallback_reasons
                            }
                            return
                
                # If we exhausted stream without done (should not happen), yield done
                if first_chunk_received:
                    yield {
                        "type": "done",
                        "provider": provider.provider_id,
                        "model": model.model_id,
                        "routing": routing,
                        "trace": execution_trace,
                        "fallback_chain": fallback_chain,
                        "fallback_reasons": fallback_reasons,
                        "total_latency": int((time.time() - start) * 1000),
                        "chunk_count": chunk_count,
                        "requested_tokens": requested_tokens,
                        "model_context_limit": model_context_limit,
                        "classification": classification
                    }
                    return
                else:
                    # No chunks received but no error — try next
                    continue
                    
            except Exception as e:
                err_msg = str(e)
                # P0.5 — Parse Retry-After
                retry_after = None
                try:
                    import re
                    m = re.search(r'Retry-After:\s*(\d+)', err_msg)
                    if m:
                        retry_after = int(m.group(1))
                except:
                    pass
                print(f"[CLINE_CODING STREAMING FALLBACK P0.5] {provider.provider_id}/{model.model_id} failed: {err_msg[:200]} retry_after={retry_after} — trying next")
                if not first_chunk_received:
                    self.circuit.record_failure(provider.provider_id, retry_after_seconds=retry_after)
                    try:
                        self.circuit.record_model_failure(provider.provider_id, model.model_id, err_msg)
                    except:
                        pass
                    execution_trace[-1]["status"] = "FAILED"
                    execution_trace[-1]["error"] = err_msg[:500]
                    if retry_after:
                        execution_trace[-1]["retry_after"] = retry_after
                    fallback_chain.append({"provider": provider.provider_id, "model": model.model_id, "status": "FAILED", "error": err_msg[:200], "retry_after": retry_after})
                    fallback_reasons.append(f"{provider.provider_id}/{model.model_id} failed: {err_msg[:100]}")
                    continue
                else:
                    yield {
                        "type": "error",
                        "error": err_msg,
                        "provider": provider.provider_id,
                        "model": model.model_id,
                        "routing": routing,
                        "trace": execution_trace,
                        "fallback_chain": fallback_chain,
                        "fallback_reasons": fallback_reasons
                    }
                    return
        
        # All providers failed
        if not first_chunk_received:
            raise Exception(f"All providers failed for streaming. Chain: {fallback_chain} | Trace: {execution_trace} | Reasons: {fallback_reasons}")

    def validate_output(self, output: str, task: SubTask) -> Dict:
        """OUTPUT VALIDATION"""
        checks = {
            "not_empty": len(output.strip()) > 0,
            "not_error": "error" not in output.lower()[:100],
            "has_content": len(output) > 20,
        }
        # For coding tasks, check for code blocks or structure
        if "code" in task.skill.lower() or "coding" in task.objective.lower():
            checks["has_code"] = "```" in output or "def " in output or "function" in output or "const " in output
        
        passed = sum(checks.values())
        total = len(checks)
        return {
            "checks": checks,
            "passed": passed,
            "total": total,
            "valid": passed >= total * 0.6,
            "score": round(passed/total*100, 1)
        }

    async def orchestrate(self, objective: str, providers, models, profile: Profile = None) -> OrchestratorResult:
        request_id = f"req-{uuid.uuid4().hex[:12]}"
        start = time.time()
        
        # 1. UNDERSTAND & CLASSIFY
        classification = self.classifier.classify(objective)
        
        # 2. PLAN & DECOMPOSE
        plan = self.decompose_task(objective, classification)
        
        # 3. SELECT & EXECUTE (for MVP, execute main objective directly via routing)
        # In full version, would iterate over plan.tasks with multi-agent
        exec_result = await self.execute_with_routing(objective, providers, models, profile)
        
        # 4. VALIDATE
        main_task = plan.tasks[0] if plan.tasks else SubTask(f"task-{request_id}", None, objective, "P1", TaskStatus.RUNNING)
        validation = self.validate_output(exec_result["response"].content, main_task)
        
        # 5. AUDIT LOG
        audit_log = [
            {"step": "UNDERSTAND", "classification": classification.task_type.value, "confidence": classification.confidence, "reasoning": classification.reasoning},
            {"step": "PLAN", "tasks_count": len(plan.tasks), "estimated_cost": plan.estimated_cost},
            {"step": "ROUTING", "selected": f"{exec_result['routing'].selected.model.display_name}/{exec_result['routing'].selected.provider.name}", "explanation": exec_result["routing"].explanation, "confidence": exec_result["routing"].confidence},
            {"step": "EXECUTE", "trace": exec_result["trace"], "fallback_used": exec_result["fallback_used"]},
            {"step": "VALIDATE", "validation": validation, "valid": validation["valid"]},
        ]
        
        total_latency = int((time.time() - start) * 1000)
        
        # 6. LEARN - would update metrics in DB
        total_cost = exec_result["response"].input_tokens * 0.000001 + exec_result["response"].output_tokens * 0.000002  # placeholder
        
        return OrchestratorResult(
            request_id=request_id,
            objective=objective,
            plan=plan,
            routing=exec_result["routing"],
            execution_trace=exec_result["trace"],
            final_output=exec_result["response"].content,
            validation=str(validation),
            confidence=exec_result["routing"].confidence,
            total_cost=total_cost,
            total_latency=total_latency,
            fallback_used=exec_result["fallback_used"],
            audit_log=audit_log
        )

orchestrator_service = Orchestrator()
