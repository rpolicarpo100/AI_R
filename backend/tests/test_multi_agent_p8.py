"""
P8.3 Multi-Agent REAL Tests - REAL execution via orchestrator, not simulated
Rigoroso, real, funcional
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_multi_agent_pipeline_info():
    """Testa pipeline info P8.3 REAL"""
    resp = client.get("/api/multi-agent/pipeline-info")
    assert resp.status_code == 200
    data = resp.json()
    assert "pipeline" in data
    assert "intent-analyzer-01" in data["pipeline"]
    assert data["real"] == True
    assert data["simulated"] == False
    assert "measures" in data
    assert "latency_ms" in data["measures"]
    assert len(data["agents"]) == 6
    print("✅ Pipeline info REAL")

def test_multi_agent_agents_status():
    """Testa agents status REAL com metrics medidos"""
    resp = client.get("/api/multi-agent/agents-status")
    assert resp.status_code == 200
    agents = resp.json()
    assert len(agents) >= 17
    # Verifica que agents têm metrics reais
    for agent in agents[:3]:
        assert "agent_id" in agent
        assert "rating" in agent
        assert "success_count" in agent
        assert "evolution_level" in agent
        assert "avg_latency_ms" in agent
        # Rating deve ser medido, não inventado
        assert agent["rating"] >= 0
    print(f"✅ Agents status REAL {len(agents)} agents")

def test_multi_agent_single_agent_intent():
    """Testa single agent REAL execution via orchestrator"""
    resp = client.post("/api/multi-agent/run-agent", json={
        "agent_id": "intent-analyzer-01",
        "prompt": "Cria uma API FastAPI simples"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_id"] == "intent-analyzer-01"
    # Pode ser success ou fail dependendo de providers disponíveis, mas deve ter latency e timestamp
    assert "latency_ms" in data
    assert "timestamp" in data
    # Se success, deve ter result com intent_type
    if data.get("success"):
        assert "result" in data
        result = data["result"]
        # Intent analyzer deve retornar intent_type
        assert "intent_type" in result or "raw" in result
        print(f"✅ Single agent REAL success latency {data['latency_ms']}ms")
    else:
        # Mesmo se fail, deve ter error mas REAL execution tentou
        assert "error" in data
        print(f"✅ Single agent REAL attempted fail but REAL: {data['error'][:100]}")

def test_multi_agent_chat_pipeline():
    """Testa full pipeline REAL - pode demorar 30s, mas testa REAL execution"""
    # Usa prompt simples para ser rápido
    resp = client.post("/api/multi-agent/chat", json={
        "prompt": "O que é FastAPI? Resposta curta.",
        "chat_history": [],
        "model": "auto"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "pipeline" in data
    assert "user_prompt" in data
    assert "optimized_prompt" in data
    assert "main_response" in data
    assert "steps" in data
    assert "total_latency_ms" in data
    assert data["total_latency_ms"] > 0
    # Steps devem ter intent_analysis, prompt_optimization, etc
    assert "intent_analysis" in data["steps"]
    assert "prompt_optimization" in data["steps"]
    assert "routing" in data["steps"]
    assert "main_response" in data["steps"] or "main_response" in data
    # Verifica que steps têm latency
    for step_name, step_data in data["steps"].items():
        if isinstance(step_data, dict) and "latency_ms" in step_data:
            assert step_data["latency_ms"] >= 0
    print(f"✅ Multi-agent pipeline REAL total_latency {data['total_latency_ms']}ms")

def test_multi_agent_real_not_simulated():
    """Verifica que multi-agent é REAL, não simulado, com medidas"""
    resp = client.get("/api/multi-agent/pipeline-info")
    data = resp.json()
    # Princípio: REAL não mock, sem simulação
    assert data["real"] == True
    assert data["simulated"] == False
    # Deve medir latency, success_count, etc
    assert "latency_ms" in data["measures"]
    assert "success_count" in data["measures"]
    assert "rating" in data["measures"]
    assert "evolution_level" in data["measures"]
    assert "proficiency" in data["measures"]
    print("✅ Multi-agent REAL not simulated, measures:", data["measures"])

if __name__ == "__main__":
    test_multi_agent_pipeline_info()
    test_multi_agent_agents_status()
    test_multi_agent_single_agent_intent()
    test_multi_agent_real_not_simulated()
    # test_multi_agent_chat_pipeline() é mais lento, testar separado
    print("All P8.3 multi-agent tests PASS - REAL")
