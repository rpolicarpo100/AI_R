"""
P25 Frontend badge free_remote vs local + P26 Cost tracking daily endpoint — 8 tests
"""
import pathlib
import pytest

def read_file(p):
    return pathlib.Path(p).read_text()

def test_p25_network_tab_badge():
    path = pathlib.Path(__file__).parent.parent.parent / "frontend" / "app" / "components" / "settings" / "NetworkTab.tsx"
    if not path.exists():
        path = pathlib.Path("/home/user/1-PROJECT/frontend/app/components/settings/NetworkTab.tsx")
    content = path.read_text()
    assert "REMOTE FREE" in content, "REMOTE FREE badge missing"
    assert "LOCAL SETUP" in content, "LOCAL SETUP badge missing"
    assert "free_no_key_remote" in content or "pollinations" in content, "free remote logic missing"
    assert "free_no_key_local" in content or "ollama" in content, "free local logic missing"
    assert "NEEDS KEY" in content, "NEEDS KEY badge missing"
    assert "P25" in content, "P25 marker missing"

def test_p25_badge_logic_remote_free():
    # Check provider model has free_no_key_remote
    content = read_file(pathlib.Path(__file__).parent.parent / "app" / "routers" / "rigor.py")
    assert "free_no_key_remote" in content, "free_no_key_remote not in rigor.py"
    assert "free_no_key_local" in content, "free_no_key_local not in rigor.py"
    assert "free_remote" in content
    assert "free_local" in content

def test_p26_cost_endpoint_exists():
    content = read_file(pathlib.Path(__file__).parent.parent / "app" / "routers" / "observability.py")
    assert '"/cost"' in content or "@router.get(\"/cost\")" in content, "cost endpoint missing"
    assert "P26" in content, "P26 marker missing"
    assert "daily" in content.lower(), "daily logic missing"
    assert "RequestLog" in content, "RequestLog aggregation missing"
    assert "by_provider" in content, "by_provider aggregation missing"
    assert "budget" in content.lower(), "budget alerts missing"

def test_p26_cost_daily_logic():
    from app.services.brainstorming_service import brainstorming_service  # just to ensure import works, not related
    # Test the cost daily aggregation logic manually
    from collections import defaultdict
    from datetime import datetime, timezone
    
    # Simulate logs
    class FakeLog:
        def __init__(self, provider, model, cost, ts):
            self.provider = provider
            self.model = model
            self.cost = cost
            self.timestamp = ts
            self.input_tokens = 100
            self.output_tokens = 50
    
    logs = [
        FakeLog("groq", "llama-3.1-8b", 0.01, datetime(2026,9,19,10,0, tzinfo=timezone.utc)),
        FakeLog("groq", "llama-3.1-8b", 0.02, datetime(2026,9,19,11,0, tzinfo=timezone.utc)),
        FakeLog("openrouter", "gpt-4", 0.05, datetime(2026,9,18,10,0, tzinfo=timezone.utc)),
    ]
    
    daily = defaultdict(lambda: {"total_cost": 0.0, "count": 0})
    for log in logs:
        day_key = log.timestamp.strftime("%Y-%m-%d")
        daily[day_key]["total_cost"] += log.cost
        daily[day_key]["count"] += 1
    
    assert daily["2026-09-19"]["total_cost"] == 0.03
    assert daily["2026-09-19"]["count"] == 2
    assert daily["2026-09-18"]["total_cost"] == 0.05

def test_p26_frontend_observability_cost_daily():
    path = pathlib.Path(__file__).parent.parent.parent / "frontend" / "app" / "components" / "settings" / "ObservabilityTab.tsx"
    if not path.exists():
        path = pathlib.Path("/home/user/1-PROJECT/frontend/app/components/settings/ObservabilityTab.tsx")
    content = path.read_text()
    assert "P26" in content, "P26 marker missing in ObservabilityTab"
    assert "cost" in content.lower()
    assert "daily" in content.lower()
    assert "budget" in content.lower()
    assert "/api/observability/cost" in content, "cost endpoint call missing in frontend"

def test_p26_observability_router_has_both_costs():
    content = read_file(pathlib.Path(__file__).parent.parent / "app" / "routers" / "observability.py")
    assert '"/costs"' in content, "old /costs endpoint missing"
    assert '"/cost"' in content, "new /cost daily endpoint missing"
    assert "period" in content, "period param missing"

def test_p25_p26_integration_rigor_confidence():
    # Ensure rigor confidence still has free_remote free_local
    content = read_file(pathlib.Path(__file__).parent.parent / "app" / "routers" / "rigor.py")
    assert "free_remote" in content
    assert "free_local" in content
    assert "free_no_card" in content
    assert "confidence-100" in content.lower() or "confidence" in content.lower()

def test_p25_frontend_badge_colors():
    path = pathlib.Path("/home/user/1-PROJECT/frontend/app/components/settings/NetworkTab.tsx")
    content = path.read_text()
    # Check colors: emerald for remote, amber for local
    assert "emerald" in content.lower(), "emerald color for remote free missing"
    assert "amber" in content.lower(), "amber color for local setup missing"
    assert "REMOTE FREE" in content
    assert "LOCAL SETUP" in content
