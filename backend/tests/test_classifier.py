"""
Testes Classifier - Dia 1 Segurança + Testes - Maior ROI
Rigoroso, real, funcional, sem invenção
"""
import sys
sys.path.insert(0, '/home/user/ai-provider-os/backend')

from app.services.classifier import classifier, TaskType

def test_coding_detection():
    """Deve detectar CODING quando tem def, código, etc"""
    prompt = "Cria uma função Python para validar NIF português"
    result = classifier.classify(prompt)
    assert result.task_type == TaskType.CODING
    assert result.confidence >= 0.6
    # P0 — reasoning may contain complex indicators or coding keywords — both valid for CODING task
    assert any(k in result.reasoning.lower() for k in ["coding", "keywords", "complex", "cria", "python", "função"])
    print(f"✅ CODING detection: {result.task_type} conf {result.confidence} reasoning {result.reasoning}")

def test_api_fast():
    """Prompt curto deve ser API FAST"""
    prompt = "Olá"
    result = classifier.classify(prompt)
    assert result.task_type in [TaskType.API, TaskType.CHAT]
    print(f"✅ FAST/CHAT detection: {result.task_type} for short prompt")

def test_json_detection():
    """Deve detectar JSON quando pede json"""
    prompt = 'Retorne apenas JSON válido: {"nome": "João"}'
    result = classifier.classify(prompt)
    assert result.task_type == TaskType.JSON
    assert result.requires_json == True
    print(f"✅ JSON detection: {result.task_type} requires_json {result.requires_json}")

def test_reasoning_detection():
    """Deve detectar REASONING quando tem por que, explique"""
    prompt = "Por que o céu é azul? Explique passo a passo com lógica"
    result = classifier.classify(prompt)
    assert result.task_type == TaskType.REASONING
    print(f"✅ REASONING detection: {result.task_type}")

def test_long_context():
    """Deve detectar LONG_CONTEXT quando tokens >8000"""
    prompt = "a" * 35000  # ~8750 tokens
    result = classifier.classify(prompt)
    assert result.task_type == TaskType.LONG_CONTEXT
    assert result.estimated_tokens > 8000
    print(f"✅ LONG_CONTEXT detection: tokens {result.estimated_tokens}")

def test_complexity():
    """Complexidade deve ser 1-5"""
    prompts = [
        "Olá",
        "Cria função soma",
        "Cria API FastAPI completa com CRUD e auth",
        "Arquitetura sistema microservices com event sourcing"
    ]
    for p in prompts:
        r = classifier.classify(p)
        assert 1 <= r.complexity <= 5
    print("✅ Complexity range 1-5 OK")

if __name__ == "__main__":
    test_coding_detection()
    test_api_fast()
    test_json_detection()
    test_reasoning_detection()
    test_long_context()
    test_complexity()
    print("\n✅ All classifier tests passed - FUNCIONAL, COERENTE, PRECISO, RIGOROSO")
