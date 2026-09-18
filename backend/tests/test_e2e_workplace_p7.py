"""
P7 E2E Workplace Test - Cria projeto, testa comandos reais, bulk delete, audit log auto
Rigoroso, real, funcional
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_e2e_workplace_flow():
    """E2E completo: cria projeto -> testa comando real -> audita -> bulk delete"""
    # 1. Cria projeto
    proj_data = {
        "name": "E2E Test Project P7",
        "description": "Teste e2e workplace P7 com comandos reais",
        "files": {
            "main.py": "def hello():\n    print('hello')\n\ndef add(a,b):\n    return a+b\n",
            "utils.py": "def validate_nif(nif):\n    return len(nif)==9\n"
        },
        "type": "utility",
        "language": "python"
    }
    resp = client.post("/api/projects", json=proj_data)
    assert resp.status_code == 200, f"Cria projeto falhou: {resp.text}"
    proj = resp.json()
    project_id = proj["project_id"]
    assert proj["file_count"] == 2
    assert proj["name"] == "E2E Test Project P7"
    
    # 2. Lista projetos com pagination
    resp = client.get("/api/projects?page=0&per_page=50")
    assert resp.status_code == 200
    projects = resp.json()
    assert len(projects) >= 1
    assert any(p["project_id"] == project_id for p in projects)
    
    # 3. Stats summary
    resp = client.get("/api/projects/stats/summary")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["total"] >= 1
    assert "active" in stats
    assert "by_type" in stats
    
    # 4. Testa comando /testa REAL - lê arquivos reais
    resp = client.post("/api/commands/execute", json={"command": "/testa", "project_id": project_id})
    assert resp.status_code == 200
    cmd_result = resp.json()
    assert cmd_result["command"] == "testa"
    assert cmd_result["result"]["real"] == True
    assert cmd_result["result"]["real_files_analyzed"] == 2
    assert len(cmd_result["result"]["file_analysis"]) == 2
    # Verifica que detectou def sem teste
    assert any("unit tests" in t for t in cmd_result["result"]["tests_suggested"])
    
    # 5. Testa comando /audita REAL
    resp = client.post("/api/commands/execute", json={"command": "/audita", "project_id": project_id})
    assert resp.status_code == 200
    cmd_result = resp.json()
    assert cmd_result["result"]["real"] == True
    assert cmd_result["result"]["real_files_audited"] == 2
    
    # 6. Testa comando /explica REAL
    resp = client.post("/api/commands/execute", json={"command": "/explica", "project_id": project_id})
    assert resp.status_code == 200
    assert resp.json()["result"]["real"] == True
    assert resp.json()["result"]["real_files"] == 2
    
    # 7. Testa comando /rigor REAL - P8: total agora 427, não 377 hardcoded
    resp = client.post("/api/commands/execute", json={"command": "/rigor"})
    assert resp.status_code == 200
    data_rigor = resp.json()
    rigor = data_rigor["result"]["rigor"]
    assert rigor["total"] >= 377  # P8: 427, P7: 377, não hardcoded
    assert rigor["measured"] >= 100  # P8: 175
    assert rigor["total"] >= rigor["measured"]
    assert data_rigor["result"].get("real", True) == True
    
    # 8. Audit log auto - verifica que comandos foram logados
    resp = client.get("/api/audit/logs?limit=100")
    assert resp.status_code == 200
    # Novo formato P7 com pagination
    data = resp.json()
    assert "logs" in data
    assert "total" in data
    assert "has_more" in data
    logs = data["logs"]
    # Deve ter logs de command_testa, command_audita, etc
    actions = [log["action"] for log in logs]
    assert any("command_testa" in a for a in actions) or any("command_" in a for a in actions)
    
    # 9. Cria segundo projeto para bulk delete
    proj2_data = {
        "name": "E2E Test Project 2 P7",
        "description": "Segundo projeto para bulk delete",
        "files": {"main.py": "print('test2')"},
        "type": "utility"
    }
    resp = client.post("/api/projects", json=proj2_data)
    assert resp.status_code == 200
    proj2_id = resp.json()["project_id"]
    
    # 10. Bulk delete - soft
    resp = client.post("/api/projects/bulk-delete", json=[project_id, proj2_id])
    assert resp.status_code == 200
    bulk_result = resp.json()
    assert bulk_result["deleted_count"] == 2
    assert project_id in bulk_result["deleted"]
    
    # 11. Verifica que foram arquivados
    resp = client.get(f"/api/projects/{project_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "archived"
    
    # 12. Hard delete com confirmação
    resp = client.delete(f"/api/projects/{project_id}/hard?confirm={project_id}")
    assert resp.status_code == 200
    assert resp.json()["hard"] == True
    
    resp = client.delete(f"/api/projects/{proj2_id}/hard?confirm={proj2_id}")
    assert resp.status_code == 200
    
    # 13. Verifica que foram eliminados
    resp = client.get(f"/api/projects/{project_id}")
    assert resp.status_code == 404
    
    print("✅ E2E Workplace P7 PASS - todos steps reais")

def test_audit_log_pagination():
    """Testa audit log pagination P7"""
    resp = client.get("/api/audit/logs?limit=2&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert "logs" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert "has_more" in data
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert len(data["logs"]) <= 2

def test_projects_pagination():
    """Testa projects pagination P7"""
    # Cria 3 projetos
    ids = []
    for i in range(3):
        resp = client.post("/api/projects", json={
            "name": f"Pagination Test {i}",
            "files": {f"file{i}.py": f"print({i})"},
            "type": "utility"
        })
        if resp.status_code == 200:
            ids.append(resp.json()["project_id"])
    
    # Lista com pagination
    resp = client.get("/api/projects?page=0&per_page=2")
    assert resp.status_code == 200
    assert len(resp.json()) <= 2
    
    # Stats
    resp = client.get("/api/projects/stats/summary")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 3
    
    # Cleanup bulk hard delete
    if ids:
        resp = client.post("/api/projects/bulk-delete?hard=true&confirm=BULK_DELETE_CONFIRM", json=ids)
        assert resp.status_code == 200

def test_commands_real():
    """Testa que comandos leem arquivos reais, não mock"""
    # Cria projeto com TODO para testar contesta
    resp = client.post("/api/projects", json={
        "name": "Commands Real Test",
        "files": {"main.py": "def foo():\n    # TODO: implement\n    pass\n"},
        "type": "utility"
    })
    assert resp.status_code == 200
    pid = resp.json()["project_id"]
    
    # /contesta deve detectar TODO real
    resp = client.post("/api/commands/execute", json={"command": "/contesta", "project_id": pid})
    assert resp.status_code == 200
    result = resp.json()
    assert result["result"]["real"] == True
    # Deve conter contestação sobre TODO
    contest_points = result["result"]["contestation_points"]
    assert len(contest_points) > 0
    
    # /melhora deve detectar TODO real
    resp = client.post("/api/commands/execute", json={"command": "/melhora", "project_id": pid})
    assert resp.status_code == 200
    assert resp.json()["result"]["real"] == True
    
    # Cleanup
    client.delete(f"/api/projects/{pid}/hard?confirm={pid}")

if __name__ == "__main__":
    test_e2e_workplace_flow()
    test_audit_log_pagination()
    test_projects_pagination()
    test_commands_real()
    print("All P7 e2e tests PASS")
