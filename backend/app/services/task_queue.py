"""
P4 - Multi-Agent Task Queue com Dependências P0→P3 + Human Override
Automação 85% -> 95% - planner → arch → coding → testing → security → audit
"""
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime, timezone
import uuid
from dataclasses import dataclass, field

class TaskPriority(str, Enum):
    P0 = "P0"  # Foundation - critical
    P1 = "P1"  # Router + Orchestrator
    P2 = "P2"  # Benchmark + Rating + Tests + UX + Performance
    P3 = "P3"  # Discovery + Observability + Security + Templates
    P4 = "P4"  # Enterprise + Multi-Agent + Grafana + Auth

class TaskStatus(str, Enum):
    QUEUED = "QUEUED"
    PLANNING = "PLANNING"
    WAITING_DEPENDENCY = "WAITING_DEPENDENCY"
    WAITING_HUMAN = "WAITING_HUMAN"
    RUNNING = "RUNNING"
    VALIDATING = "VALIDATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

@dataclass
class Task:
    task_id: str
    objective: str
    priority: TaskPriority
    status: TaskStatus
    dependencies: List[str] = field(default_factory=list)
    agent_id: Optional[str] = None
    skill_id: Optional[str] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    human_override_required: bool = False
    human_override_id: Optional[str] = None
    estimated_time: int = 30  # seconds
    cost: float = 0.0

class TaskQueue:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.execution_order = []
    
    def add_task(self, objective: str, priority: TaskPriority = TaskPriority.P1, 
                 dependencies: List[str] = None, agent_id: str = None, 
                 skill_id: str = None, human_override_required: bool = False) -> Task:
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        task = Task(
            task_id=task_id,
            objective=objective,
            priority=priority,
            status=TaskStatus.QUEUED,
            dependencies=dependencies or [],
            agent_id=agent_id,
            skill_id=skill_id,
            human_override_required=human_override_required
        )
        self.tasks[task_id] = task
        return task
    
    def add_p4_pipeline(self, main_objective: str) -> List[Task]:
        """P4 - Pipeline multi-agent: planner → arch → coding → testing → security → audit — P3 enhanced with P0.5 P1 P2"""
        tasks = []
        
        # P0 - Foundation + Central Policy
        t0 = self.add_task(
            objective=f"P0 - Analisar requisitos e definir arquitetura + central policy para: {main_objective}",
            priority=TaskPriority.P0,
            agent_id="planner-01",
            skill_id="provider_discovery"
        )
        tasks.append(t0)
        
        t0_5 = self.add_task(
            objective=f"P0.5 - Stability: model lifecycle DEPRECATED, cache key fix, circuit breaker backoff, Retry-After para: {main_objective}",
            priority=TaskPriority.P0,
            dependencies=[t0.task_id],
            agent_id="coding-01",
            skill_id="python"
        )
        tasks.append(t0_5)
        
        # P0 - DB schema
        t1 = self.add_task(
            objective=f"P0 - Desenhar database schema e modelos + WAL + indexes para: {main_objective}",
            priority=TaskPriority.P0,
            dependencies=[t0.task_id, t0_5.task_id],
            agent_id="planner-01",
            skill_id="model_discovery"
        )
        tasks.append(t1)
        
        # P1 - Backend API + Performance
        t2 = self.add_task(
            objective=f"P1 - Implementar backend API (FastAPI) + pre-warm 83% faster + max_completion_tokens + version sync para: {main_objective}",
            priority=TaskPriority.P1,
            dependencies=[t0.task_id, t1.task_id],
            agent_id="coding-01",
            skill_id="fastapi"
        )
        tasks.append(t2)
        
        # P1 - Frontend Settings
        t3 = self.add_task(
            objective=f"P1 - Implementar frontend (React/Next.js) Settings dashboard network benchmarks P15 virtual scroll para: {main_objective}",
            priority=TaskPriority.P1,
            dependencies=[t0.task_id],
            agent_id="coding-01",
            skill_id="react"
        )
        tasks.append(t3)
        
        # P2 - Testing + Observability + Quota + Async Critic
        t4 = self.add_task(
            objective=f"P2 - Criar testes automatizados + observability dashboard enhanced + quota tracking real-time + async critic 80% faster TTFB para: {main_objective}",
            priority=TaskPriority.P2,
            dependencies=[t2.task_id, t3.task_id],
            agent_id="coding-01",
            skill_id="python"
        )
        tasks.append(t4)
        
        # P3 - Security Audit + Frontend P3 + Rating Evolution
        t5 = self.add_task(
            objective=f"P3 - Auditoria segurança + frontend Settings P3 detailed quota circuit + rating evolution auto-update scores + task queue P23 para: {main_objective}",
            priority=TaskPriority.P3,
            dependencies=[t2.task_id, t3.task_id, t4.task_id],
            agent_id="security-01",
            skill_id="security_audit",
            human_override_required=True
        )
        tasks.append(t5)
        
        # P3 - Final + Docs
        t6 = self.add_task(
            objective=f"P3 - Auditoria final, Grafana dashboard, documentação P23 P0+P0.5+P1+P2+P3 para: {main_objective}",
            priority=TaskPriority.P4,
            dependencies=[t5.task_id],
            agent_id="audit-01",
            skill_id="rigor_audit",
            human_override_required=True
        )
        tasks.append(t6)
        
        return tasks

    def add_p23_pipeline(self, main_objective: str) -> List[Task]:
        """P23 — Pipeline completo P0→P3 com P0.5 P1 P2 P3 — 7 tasks com dependências rigorosas"""
        return self.add_p4_pipeline(main_objective)
    
    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to run (dependencies completed)"""
        ready = []
        for task in self.tasks.values():
            if task.status != TaskStatus.QUEUED and task.status != TaskStatus.WAITING_DEPENDENCY:
                continue
            
            # Check if dependencies are completed
            deps_completed = all(
                self.tasks.get(dep_id) and self.tasks[dep_id].status == TaskStatus.COMPLETED
                for dep_id in task.dependencies
            )
            
            if deps_completed or not task.dependencies:
                if task.human_override_required and not task.human_override_id:
                    task.status = TaskStatus.WAITING_HUMAN
                else:
                    task.status = TaskStatus.PLANNING
                    ready.append(task)
            else:
                task.status = TaskStatus.WAITING_DEPENDENCY
        
        # Sort by priority P0→P4
        priority_order = {TaskPriority.P0: 0, TaskPriority.P1: 1, TaskPriority.P2: 2, TaskPriority.P3: 3, TaskPriority.P4: 4}
        ready.sort(key=lambda t: priority_order.get(t.priority, 5))
        return ready
    
    def complete_task(self, task_id: str, result: Dict = None):
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now(timezone.utc).isoformat()
            self.execution_order.append(task_id)
    
    def fail_task(self, task_id: str, error: str):
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.FAILED
            task.error = error
            task.completed_at = datetime.now(timezone.utc).isoformat()
    
    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)
    
    def list_tasks(self) -> List[Task]:
        return list(self.tasks.values())
    
    def get_stats(self):
        total = len(self.tasks)
        by_status = {}
        by_priority = {}
        for task in self.tasks.values():
            by_status[task.status] = by_status.get(task.status, 0) + 1
            by_priority[task.priority] = by_priority.get(task.priority, 0) + 1
        
        return {
            "total": total,
            "by_status": by_status,
            "by_priority": by_priority,
            "execution_order": self.execution_order,
            "ready_count": len(self.get_ready_tasks())
        }

task_queue = TaskQueue()
