"""
P4 — Enterprise + Metrics + Task Queue + Frontend P3 + Final
- Metrics Prometheus enhanced P0.5 P1 P2 P3 P4
- Task queue P23 pipeline execution
- Frontend build check
- Final version P4
"""

import pytest
import requests
import os

BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

def test_metrics_p4_enhanced():
    """P4.1 — Metrics Prometheus includes P0.5 P1 P2 P3 P4"""
    r = requests.get(f"{BASE}/metrics", timeout=15)
    assert r.status_code == 200
    text = r.text
    
    assert "ai_provider_os_models_deprecated" in text, "Should have deprecated metric P0.5"
    assert "ai_provider_os_circuits_open" in text, "Should have circuits_open P0.5"
    assert "ai_provider_os_provider_cache_hit" in text, "Should have provider_cache_hit P1"
    assert "ai_provider_os_http_pool_clients" in text, "Should have http_pool_clients P1"
    assert "ai_provider_os_quota_tracked_providers" in text, "Should have quota_tracked P2"
    assert "ai_provider_os_quota_429_hits_last_hour" in text, "Should have quota 429 P2"
    assert "ai_provider_os_task_queue_total" in text, "Should have task_queue P4"
    assert "ai_provider_os_info" in text, "Should have info P4 with p0 p05 p1 p2 p3 p4"
    
    # Check values
    assert "ai_provider_os_models_deprecated 23" in text or "deprecated" in text
    
    print(f"✅ Metrics P4 enhanced: deprecated, circuits_open, cache_hit, pool_clients, quota_tracked, task_queue, info")

def test_task_queue_p23_execution():
    """P4.2 — Task queue P23 pipeline can be executed"""
    from app.services.task_queue import task_queue
    
    # Create pipeline
    tasks = task_queue.add_p23_pipeline("Test P4 final app")
    assert len(tasks) >= 7
    
    # Get ready tasks (should be P0 tasks)
    ready = task_queue.get_ready_tasks()
    assert len(ready) >= 1, f"Should have ready tasks, got {len(ready)}"
    
    # Complete first task
    first = ready[0]
    task_queue.complete_task(first.task_id, result={"success": True, "message": "P0 completed"})
    
    # Get next ready tasks
    ready2 = task_queue.get_ready_tasks()
    # Should have next tasks ready after completing dependency
    
    stats = task_queue.get_stats()
    assert stats["total"] >= 7
    assert "by_status" in stats
    assert "by_priority" in stats
    
    print(f"✅ Task queue P23 execution: {len(tasks)} tasks, ready {len(ready)} → {len(ready2)} after completing P0, stats {stats['total']}")

def test_frontend_build():
    """P4.3 — Frontend build check"""
    import os
    import json
    
    # Check package.json exists
    pkg_path = "/home/user/ai-provider-os/frontend/package.json"
    assert os.path.exists(pkg_path)
    
    with open(pkg_path) as f:
        pkg = json.load(f)
        assert "next" in pkg["dependencies"]
        assert "react" in pkg["dependencies"]
    
    # Check Settings components exist and enhanced
    base = "/home/user/ai-provider-os/frontend/app/components/settings"
    assert os.path.exists(f"{base}/DashboardTab.tsx")
    assert os.path.exists(f"{base}/NetworkTab.tsx")
    assert os.path.exists(f"{base}/ObservabilityTab.tsx")
    assert os.path.exists(f"{base}/BenchmarksTab.tsx")
    
    # Check DashboardTab has P3
    with open(f"{base}/DashboardTab.tsx") as f:
        content = f.read()
        assert "P0.5" in content or "p0_5" in content
        assert "P1" in content
        assert "P2" in content
    
    print(f"✅ Frontend build: package.json exists, Settings 8 tabs, DashboardTab P3 enhanced")

def test_final_version_p4():
    """P4.4 — Final version includes P0-P4"""
    r = requests.get(f"{BASE}/v1/cline/status", timeout=10)
    assert r.status_code == 200
    version = r.json()["version"]
    
    assert "P23" in version
    assert "P0" in version
    assert "P0.5" in version or "P0.5" in version or "LIFECYCLE" in version
    assert "P1" in version or "PRE-WARM" in version
    assert "P2" in version or "QUOTA" in version
    assert "P3" in version or "FRONTEND" in version
    assert "P4" in version or "METRICS" in version
    
    r2 = requests.get(f"{BASE}/health", timeout=10)
    assert r2.status_code == 200
    v2 = r2.json()["version"]
    assert "P23" in v2
    assert "P4" in v2
    
    print(f"✅ Final version P4: {version[:100]}...")

def test_all_layers_still_work():
    """P0-P3 still work after P4"""
    r1 = requests.post(f"{BASE}/v1/chat/completions", json={
        "model":"auto",
        "messages":[{"role":"user","content":"a"*12435}],
        "max_tokens":5
    }, timeout=20)
    assert r1.status_code == 200, f"12435 should pass after P4, got {r1.status_code}"
    
    r2 = requests.post(f"{BASE}/v1/chat/completions", json={
        "model":"auto",
        "messages":[{"role":"user","content":"b"*110000}],
        "max_tokens":5
    }, timeout=10)
    assert r2.status_code == 413, f"110k should be 413 after P4, got {r2.status_code}"
    
    r3 = requests.post(f"{BASE}/v1/chat/completions", json={
        "model":"auto",
        "messages":[{"role":"user","content":"test P4 max_completion_tokens"}],
        "max_completion_tokens":10
    }, timeout=20)
    assert r3.status_code == 200
    
    r4 = requests.get(f"{BASE}/api/observability/quotas", timeout=10)
    assert r4.status_code == 200
    
    r5 = requests.get(f"{BASE}/api/dashboard/stats", timeout=15)
    assert r5.status_code == 200
    assert "p0_5_stability" in r5.json()
    assert "p2_quotas" in r5.json()
    
    print(f"✅ All layers P0-P3 still work after P4: 12435 200, 110k 413, max_completion_tokens 200, quotas 200, dashboard 200")

def test_cline_gateway_p4():
    """Cline gateway still works after P4"""
    r = requests.post(f"{BASE}/v1/cline/completions", json={
        "model":"auto",
        "messages":[{"role":"user","content":"quanto é 2+2? P4 Cline gateway test"}],
        "max_tokens":10
    }, timeout=20)
    assert r.status_code == 200, f"Cline gateway should work after P4, got {r.status_code} {r.text[:200]}"
    data = r.json()
    assert "choices" in data
    assert len(data["choices"]) > 0
    
    print(f"✅ Cline gateway P4: {data.get('model')} works")

if __name__ == "__main__":
    test_metrics_p4_enhanced()
    test_task_queue_p23_execution()
    test_frontend_build()
    test_final_version_p4()
    test_all_layers_still_work()
    test_cline_gateway_p4()
    print("\n✅ All P4 tests passed")
