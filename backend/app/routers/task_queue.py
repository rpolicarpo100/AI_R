"""
P4 - Task Queue Router - Multi-Agent Orquestrado P0→P4
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from ..services.task_queue import task_queue, TaskPriority, TaskStatus
from ..services.auth import get_current_user, require_role, Role

router = APIRouter(prefix="/task-queue", tags=["task-queue"])

class TaskCreate(BaseModel):
    objective: str
    priority: str = "P1"
    dependencies: List[str] = []
    agent_id: Optional[str] = None
    skill_id: Optional[str] = None
    human_override_required: bool = False

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None

@router.get("")
async def list_tasks(current_user: dict = Depends(get_current_user)):
    tasks = task_queue.list_tasks()
    return [
        {
            "task_id": t.task_id,
            "objective": t.objective,
            "priority": t.priority,
            "status": t.status,
            "dependencies": t.dependencies,
            "agent_id": t.agent_id,
            "skill_id": t.skill_id,
            "result": t.result,
            "error": t.error,
            "created_at": t.created_at,
            "started_at": t.started_at,
            "completed_at": t.completed_at,
            "human_override_required": t.human_override_required,
            "human_override_id": t.human_override_id
        } for t in tasks
    ]

@router.get("/stats")
async def get_stats(current_user: dict = Depends(get_current_user)):
    return task_queue.get_stats()

@router.get("/ready")
async def get_ready_tasks(current_user: dict = Depends(get_current_user)):
    ready = task_queue.get_ready_tasks()
    return [
        {
            "task_id": t.task_id,
            "objective": t.objective,
            "priority": t.priority,
            "status": t.status,
            "dependencies": t.dependencies,
            "agent_id": t.agent_id,
            "skill_id": t.skill_id
        } for t in ready
    ]

@router.post("")
async def create_task(data: TaskCreate, current_user: dict = Depends(get_current_user)):
    try:
        priority = TaskPriority(data.priority)
    except:
        priority = TaskPriority.P1
    
    task = task_queue.add_task(
        objective=data.objective,
        priority=priority,
        dependencies=data.dependencies,
        agent_id=data.agent_id,
        skill_id=data.skill_id,
        human_override_required=data.human_override_required
    )
    return {
        "task_id": task.task_id,
        "objective": task.objective,
        "priority": task.priority,
        "status": task.status,
        "dependencies": task.dependencies
    }

@router.post("/pipeline")
async def create_pipeline(objective: str, current_user: dict = Depends(get_current_user)):
    """Create P4 pipeline: planner → arch → coding → testing → security → audit"""
    tasks = task_queue.add_p4_pipeline(objective)
    return {
        "main_objective": objective,
        "tasks_created": len(tasks),
        "tasks": [
            {
                "task_id": t.task_id,
                "objective": t.objective,
                "priority": t.priority,
                "status": t.status,
                "dependencies": t.dependencies,
                "agent_id": t.agent_id,
                "human_override_required": t.human_override_required
            } for t in tasks
        ],
        "principle": "Você no centro - P0→P4 com dependências, human override em P3/P4 críticos"
    }

@router.get("/{task_id}")
async def get_task(task_id: str, current_user: dict = Depends(get_current_user)):
    task = task_queue.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return {
        "task_id": task.task_id,
        "objective": task.objective,
        "priority": task.priority,
        "status": task.status,
        "dependencies": task.dependencies,
        "agent_id": task.agent_id,
        "skill_id": task.skill_id,
        "result": task.result,
        "error": task.error,
        "created_at": task.created_at,
        "completed_at": task.completed_at,
        "human_override_required": task.human_override_required
    }

@router.post("/{task_id}/complete")
async def complete_task(task_id: str, result: dict = None, current_user: dict = Depends(get_current_user)):
    task = task_queue.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    task_queue.complete_task(task_id, result)
    return {"task_id": task_id, "status": "COMPLETED", "result": result}

@router.post("/{task_id}/fail")
async def fail_task(task_id: str, error: dict = None, current_user: dict = Depends(get_current_user)):
    task = task_queue.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    error_msg = error.get("error", "Unknown") if error else "Unknown"
    task_queue.fail_task(task_id, error_msg)
    return {"task_id": task_id, "status": "FAILED", "error": error_msg}

@router.delete("/{task_id}")
async def delete_task(task_id: str, current_user: dict = Depends(require_role([Role.ADMIN]))):
    if task_id in task_queue.tasks:
        del task_queue.tasks[task_id]
        return {"deleted": task_id}
    raise HTTPException(404, "Task not found")
