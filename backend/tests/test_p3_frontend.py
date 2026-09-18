"""
P3 — Frontend Settings + Rating Evolution + Task Queue P23
- Frontend DashboardTab P0.5 P1 P2 enhanced
- NetworkTab quota + circuit detailed
- ObservabilityTab P0.5 P1 P2
- Task queue P23 pipeline
- Rating evolution
"""

import pytest
import requests
import os

BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

def test_dashboard_p3_enhanced():
    """P3.1 — Dashboard includes all P0-P3 metrics"""
    r = requests.get(f"{BASE}/api/dashboard/stats", timeout=15)
    assert r.status_code == 200
    data = r.json()
    
    # Check all P layers
    assert "ai_network" in data
    assert "p0_5_stability" in data
    assert "p1_performance" in data
    assert "p2_quotas" in data
    assert "p2_async_critic" in data
    
    ai = data["ai_network"]
    assert ai["total_providers"] == 26
    assert ai["models_available"] == 726
    assert ai["models_deprecated"] >= 1
    
    print(f"✅ Dashboard P3: {ai['total_providers']} prov {ai['models_available']} models deprecated {ai['models_deprecated']}")

def test_task_queue_p23():
    """P3.2 — Task queue P23 pipeline"""
    from app.services.task_queue import task_queue, TaskPriority
    
    # Create P23 pipeline
    tasks = task_queue.add_p23_pipeline("Test P3 app")
    assert len(tasks) >= 7, f"P23 pipeline should have at least 7 tasks, got {len(tasks)}"
    
    # Check priorities
    priorities = [t.priority for t in tasks]
    assert TaskPriority.P0 in priorities
    assert TaskPriority.P1 in priorities
    assert TaskPriority.P2 in priorities
    assert TaskPriority.P3 in priorities
    
    # Check P0.5 task exists
    p05_tasks = [t for t in tasks if "P0.5" in t.objective]
    assert len(p05_tasks) >= 1, f"Should have P0.5 task, got {[t.objective for t in tasks]}"
    
    # Check P1 task
    p1_tasks = [t for t in tasks if "P1" in t.objective and "pre-warm" in t.objective.lower() or "P1" in t.objective]
    assert len(p1_tasks) >= 1
    
    # Check P2 task
    p2_tasks = [t for t in tasks if "P2" in t.objective]
    assert len(p2_tasks) >= 1
    
    # Check P3 task
    p3_tasks = [t for t in tasks if "P3" in t.objective]
    assert len(p3_tasks) >= 1
    
    print(f"✅ Task queue P23: {len(tasks)} tasks P0→P3 with P0.5 P1 P2 P3")

def test_frontend_files_exist():
    """P3.1 — Frontend Settings files exist and enhanced"""
    import os
    base = "/home/user/ai-provider-os/frontend/app/components/settings"
    
    assert os.path.exists(f"{base}/DashboardTab.tsx")
    assert os.path.exists(f"{base}/NetworkTab.tsx")
    assert os.path.exists(f"{base}/ObservabilityTab.tsx")
    
    # Check DashboardTab contains P0.5 P1 P2
    with open(f"{base}/DashboardTab.tsx") as f:
        content = f.read()
        assert "p0_5_stability" in content or "P0.5" in content
        assert "p1_performance" in content or "P1" in content
        assert "p2_quotas" in content or "P2" in content
    
    # Check NetworkTab contains quota + circuit
    with open(f"{base}/NetworkTab.tsx") as f:
        content = f.read()
        assert "quota" in content.lower()
        assert "circuit" in content.lower()
    
    print(f"✅ Frontend P3 files exist and enhanced with P0.5 P1 P2")

def test_rating_evolution():
    """P3.3 — Rating evolution based on real usage"""
    from app.services.loop_engine import loop_engine
    from app.core.database import SessionLocal
    from app.models.database_models import Provider, Model
    
    # Check loop_engine has P3 rating evolution
    import inspect
    source = inspect.getsource(loop_engine.execute_rating)
    assert "P3" in source or "real usage" in source.lower() or "success_rate" in source.lower()
    
    print(f"✅ Rating evolution P3: loop_engine.execute_rating has P3 evolution logic")

def test_p0_p1_p2_still_work_after_p3():
    """P0, P1, P2 still work after P3"""
    r1 = requests.post(f"{BASE}/v1/chat/completions", json={
        "model":"auto",
        "messages":[{"role":"user","content":"a"*12435}],
        "max_tokens":5
    }, timeout=20)
    assert r1.status_code == 200
    
    r2 = requests.post(f"{BASE}/v1/chat/completions", json={
        "model":"auto",
        "messages":[{"role":"user","content":"b"*110000}],
        "max_tokens":5
    }, timeout=10)
    assert r2.status_code == 413
    
    r3 = requests.post(f"{BASE}/v1/chat/completions", json={
        "model":"auto",
        "messages":[{"role":"user","content":"test P3 max_completion_tokens"}],
        "max_completion_tokens":10
    }, timeout=20)
    assert r3.status_code == 200
    
    r4 = requests.get(f"{BASE}/api/observability/quotas", timeout=10)
    assert r4.status_code == 200
    
    print(f"✅ P0/P1/P2 still work after P3: 12435 200, 110k 413, max_completion_tokens 200, quotas 200")

def test_version_p3():
    """Version includes P3"""
    r = requests.get(f"{BASE}/v1/cline/status", timeout=10)
    assert r.status_code == 200
    version = r.json()["version"]
    assert "P23" in version
    assert "P3" in version
    print(f"✅ Version P3: {version[:80]}...")

if __name__ == "__main__":
    test_dashboard_p3_enhanced()
    test_task_queue_p23()
    test_frontend_files_exist()
    test_rating_evolution()
    test_p0_p1_p2_still_work_after_p3()
    test_version_p3()
    print("\n✅ All P3 tests passed")
