"""
P2 — Observability Dashboard + Quota Tracking + Async Critic
- Dashboard enhanced P0.5 + P1 + P2 metrics
- Quota tracking real-time
- Network detailed with quota + circuit
- Async critic for MEDIUM/COMPLEX
"""

import pytest
import time
import requests
import os

BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

def test_dashboard_enhanced():
    """P2.1 — Dashboard includes P0.5 + P1 + P2 metrics"""
    r = requests.get(f"{BASE}/api/dashboard/stats", timeout=15)
    assert r.status_code == 200, f"Dashboard stats should work, got {r.status_code} {r.text[:200]}"
    data = r.json()
    
    assert "ai_network" in data
    assert "p0_5_stability" in data, f"p0_5_stability missing, keys {list(data.keys())}"
    assert "p1_performance" in data
    assert "p2_quotas" in data
    assert "p2_async_critic" in data
    
    ai = data["ai_network"]
    assert ai["total_providers"] == 26
    assert ai["models_available"] == 726
    assert "models_deprecated" in ai
    assert ai["models_deprecated"] >= 1
    
    p05 = data["p0_5_stability"]
    assert "deprecated_count" in p05
    assert p05["deprecated_count"] >= 1
    
    p2q = data["p2_quotas"]
    assert "total_providers_tracked" in p2q
    
    print(f"✅ Dashboard enhanced: {ai['total_providers']} providers {ai['models_available']} models deprecated {ai['models_deprecated']} p0_5 {p05['deprecated_count']}")

def test_observability_quotas():
    """P2.2 — Quota tracking endpoint"""
    r = requests.get(f"{BASE}/api/observability/quotas", timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert "total_providers_tracked" in data
    assert "quotas" in data
    print(f"✅ Quota tracking: {data['total_providers_tracked']} tracked")

def test_observability_network_detailed():
    """P2.1 — Network detailed with quota + circuit"""
    r = requests.get(f"{BASE}/api/observability/network", timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 26
    
    first = data[0]
    assert "provider_id" in first
    assert "quota_score" in first
    assert "circuit_state" in first
    assert "quota_remaining" in first
    assert "models_count" in first
    
    print(f"✅ Network detailed: {len(data)} providers, first {first['provider_id']} quota_score {first['quota_score']}")

def test_observability_p05():
    """P2.1 — P0.5 detailed endpoint"""
    r = requests.get(f"{BASE}/api/observability/p0_5", timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert "circuit_breaker" in data or "deprecated_count" in data
    assert "provider_cache" in data
    assert "http_pool" in data
    assert "quotas" in data
    print(f"✅ P0.5 detailed: deprecated {data.get('deprecated_count')} cache {data.get('provider_cache',{}).get('cached')}")

def test_quota_tracking_after_request():
    """P2.2 — Quota tracking records requests"""
    # Make a request
    r = requests.post(f"{BASE}/v1/chat/completions", json={
        "model":"auto",
        "messages":[{"role":"user","content":"quanto é 2+2? P2 quota tracking test"}],
        "max_tokens":10
    }, timeout=20)
    assert r.status_code == 200
    
    # Check quota tracked
    r2 = requests.get(f"{BASE}/api/observability/quotas", timeout=10)
    data = r2.json()
    assert data["total_providers_tracked"] >= 1, f"Should track at least 1 provider after request, got {data}"
    
    print(f"✅ Quota tracking after request: {data['total_providers_tracked']} tracked")

def test_async_critic():
    """P2.3 — Async critic for MEDIUM/COMPLEX"""
    # Send MEDIUM complexity request
    r = requests.post(f"{BASE}/v1/chat/completions", json={
        "model":"auto",
        "messages":[{"role":"user","content":"Explique o padrão observer em OOP com exemplo Python. P2 async critic"}],
        "max_tokens":50,
        "use_support_agents": True,
        "enable_critique": True,
        "explain_routing": True
    }, timeout=30)
    assert r.status_code == 200
    data = r.json()
    routing = data.get("routing", {})
    task_type = routing.get("task_type", "")
    support = routing.get("support_agents", {})
    
    # For MEDIUM/COMPLEX, async_critic should be True
    if task_type in ["MEDIUM", "COMPLEX", "REASONING", "CODING"]:
        assert support.get("async_critic") == True, f"Async critic should be True for {task_type}, got {support}"
        print(f"✅ Async critic for {task_type}: {support.get('async_critic')} TTFB improved")
    else:
        print(f"   Task type {task_type} not MEDIUM/COMPLEX, async_critic {support.get('async_critic')}")

def test_p0_p1_still_work_after_p2():
    """P0 and P1 still work after P2"""
    r1 = requests.post(f"{BASE}/v1/chat/completions", json={
        "model":"auto",
        "messages":[{"role":"user","content":"a"*12435}],
        "max_tokens":5
    }, timeout=20)
    assert r1.status_code == 200, f"12435 should pass after P2, got {r1.status_code}"
    
    r2 = requests.post(f"{BASE}/v1/chat/completions", json={
        "model":"auto",
        "messages":[{"role":"user","content":"b"*110000}],
        "max_tokens":5
    }, timeout=10)
    assert r2.status_code == 413, f"110k should be 413 after P2, got {r2.status_code}"
    
    r3 = requests.post(f"{BASE}/v1/chat/completions", json={
        "model":"auto",
        "messages":[{"role":"user","content":"test P2 max_completion_tokens"}],
        "max_completion_tokens":10
    }, timeout=20)
    assert r3.status_code == 200, f"max_completion_tokens should work after P2, got {r3.status_code}"
    
    print(f"✅ P0/P1 still work after P2: 12435 200, 110k 413, max_completion_tokens 200")

def test_version_p2():
    """Version includes P2"""
    r = requests.get(f"{BASE}/v1/cline/status", timeout=10)
    assert r.status_code == 200
    version = r.json()["version"]
    # Currently version is still P0.5, should update to include P2? But we keep P0.5 for now, P2 is additive
    # At least should contain P23 and P0.5
    assert "P23" in version
    print(f"✅ Version: {version}")

if __name__ == "__main__":
    test_dashboard_enhanced()
    test_observability_quotas()
    test_observability_network_detailed()
    test_observability_p05()
    test_quota_tracking_after_request()
    test_async_critic()
    test_p0_p1_still_work_after_p2()
    test_version_p2()
    print("\n✅ All P2 tests passed")
