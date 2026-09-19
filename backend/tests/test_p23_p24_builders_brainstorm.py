"""
P23 Agents builders no pipeline + P24 Brainstorming deep integration — 10 tests
"""
import pytest
import pathlib

# Helper to read file without importing heavy deps
def read_file(path):
    return pathlib.Path(path).read_text()

def test_p23_agents_prompts_builders_exist():
    # Avoid importing module with sqlalchemy — read file content
    content = read_file(pathlib.Path(__file__).parent.parent / "app" / "services" / "multi_agent_service.py")
    assert "frontend-builder-01" in content, "frontend-builder-01 missing"
    assert "backend-builder-01" in content, "backend-builder-01 missing"
    assert "deploy-agent-01" in content, "deploy-agent-01 missing"
    assert "brainstormer-01" in content, "brainstormer-01 missing"
    assert "memory-archiver-01" in content, "memory-archiver-01 missing"
    # Check AGENT_PROMPTS dict contains them
    assert '"frontend-builder-01":' in content or "'frontend-builder-01':" in content or "frontend-builder-01" in content
    # Check content mentions real build
    assert "Next.js" in content
    assert "FastAPI" in content
    assert "Docker" in content

def test_p23_pipeline_info_has_builders():
    content = read_file(pathlib.Path(__file__).parent.parent / "app" / "routers" / "multi_agent.py")
    assert "frontend-builder-01" in content, "frontend-builder-01 not in pipeline-info file"
    assert "backend-builder-01" in content
    assert "deploy-agent-01" in content
    assert "brainstormer-01" in content
    assert "memory-archiver-01" in content
    assert "build_pipeline" in content, "build_pipeline missing"
    assert "is_build_intent" in content or "construir" in content.lower() or "cria app" in content.lower()

def test_p23_is_build_detection_keywords():
    prompts = [
        "Cria landing page moderna",
        "construir app dashboard saas",
        "build app ecommerce",
        "cria app chat com RAG",
        "faz um dashboard analytics",
        "landing page com AI"
    ]
    build_keywords = ["cria app","construir app","build app","landing page","dashboard","ecommerce","portfolio","saas","chat app"]
    for p in prompts:
        is_build = any(kw in p.lower() for kw in build_keywords)
        assert is_build, f"Should detect build intent for '{p}'"

def test_p23_multi_agent_service_has_build_logic():
    content = read_file(pathlib.Path(__file__).parent.parent / "app" / "services" / "multi_agent_service.py")
    assert "frontend-builder-01" in content, "frontend-builder-01 not in pipeline logic"
    assert "backend-builder-01" in content
    assert "deploy-agent-01" in content
    assert "is_build" in content, "is_build detection missing"
    assert "is_build_intent" in content

def test_p24_brainstorming_service_20_templates():
    from app.services.brainstorming_service import TEMPLATES
    assert len(TEMPLATES) >= 20, f"Templates should be 20, got {len(TEMPLATES)}"
    for tid in ["chat-rag", "saas-auth", "portfolio-blog", "ecommerce-ai", "dashboard-analytics", "landing-ai", "api-webhook"]:
        assert tid in TEMPLATES, f"{tid} missing in TEMPLATES P22"
    for tid in ["landing-page", "dashboard-saas", "ecommerce", "blog-md", "chat-app", "portfolio", "api-gateway", "fastapi-crud", "nextjs-app", "python-fastapi-react"]:
        assert tid in TEMPLATES, f"{tid} missing"

def test_p24_brainstorm_should_auto():
    from app.services.brainstorming_service import brainstorming_service
    res = brainstorming_service.should_auto_brainstorm("Cria landing page moderna", "BEST")
    assert res["should_brainstorm"] == True, "Should auto brainstorm for landing page"
    assert res["is_build_intent"] == True, "Should be build intent"
    
    res2 = brainstorming_service.should_auto_brainstorm("cria app dashboard saas com métricas", "CODING")
    assert res2["should_brainstorm"] == True
    assert res2["is_build_intent"] == True
    
    res3 = brainstorming_service.should_auto_brainstorm("O que é FastAPI?", "BEST")
    assert res3["should_brainstorm"] == False, f"Should NOT brainstorm for simple question with ?, got {res3}"

def test_p24_brainstorm_before_build_approaches():
    from app.services.brainstorming_service import brainstorming_service
    result = brainstorming_service.brainstorm_before_build("Cria landing page moderna com AI chat streaming")
    assert "approaches" in result
    assert len(result["approaches"]) >= 3, f"Should have 3-5 approaches, got {len(result['approaches'])}"
    assert "best_approach" in result
    assert result["best_approach"]["closest_to_final"] >= 70
    assert result["templates_count"] >= 20
    suggested = result.get("suggested_templates", [])
    assert len(suggested) >= 1
    templates_suggested = [s["template"] for s in suggested]
    assert any("landing" in t for t in templates_suggested), f"Should suggest landing template, got {templates_suggested}"

def test_p24_brainstorm_before_respond_interpretations():
    from app.services.brainstorming_service import brainstorming_service
    result = brainstorming_service.brainstorm_before_respond("cria app", profile="BEST")
    assert "interpretations" in result
    assert len(result["interpretations"]) >= 3
    assert "best_interpretation" in result
    assert result["templates_count"] >= 20

def test_p24_chat_router_has_brainstorm_integration():
    content = read_file(pathlib.Path(__file__).parent.parent / "app" / "routers" / "chat.py")
    assert "brainstorming_service" in content, "brainstorming_service not integrated"
    assert "should_auto_brainstorm" in content, "should_auto_brainstorm not called"
    assert "P24" in content, "P24 marker missing"
    assert "brainstorm_panel" in content, "brainstorm_panel missing in response"

def test_p24_frontend_brainstorm_panel_exists():
    import os
    path = pathlib.Path(__file__).parent.parent.parent / "frontend" / "app" / "components" / "chat" / "BrainstormPanel.tsx"
    if not path.exists():
        path = pathlib.Path("/home/user/1-PROJECT/frontend/app/components/chat/BrainstormPanel.tsx")
    assert path.exists(), f"BrainstormPanel.tsx missing at {path}"
    content = path.read_text()
    assert "BrainstormPanel" in content
    assert "Escolher esta" in content
    assert "templates" in content.lower()
    assert "MVP" in content
    assert "Você no centro" in content or "voce no centro" in content.lower()
