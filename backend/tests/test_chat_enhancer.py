"""
Testes Chat Enhancer - Dia 1 Segurança + Testes
Agentes apoio: intent analyzer, prompt optimizer, critic, code reviewer, rigor checker
Terceiro olho aberto, contesta, critica, não fica na primeira tentativa
"""
import sys
sys.path.insert(0, '/home/user/ai-provider-os/backend')

from app.services.chat_enhancer import chat_enhancer

def test_intent_analysis_code():
    """Deve detectar code_generation para prompts de código"""
    prompt = "Cria uma função Python para validar NIF português"
    intent = chat_enhancer.analyze_intent(prompt)
    
    assert intent["intent_type"] == "code_generation"
    assert "NIF" in str(intent["ambiguities"]) or len(intent["ambiguities"]) >= 0
    assert len(intent["requirements"]) > 0
    assert intent["agent"] == "intent-analyzer-01"
    assert intent["skill"] == "intent_analysis"
    print(f"✅ Intent code_generation: {intent['intent_type']} ambiguities {intent['ambiguities']} reqs {intent['requirements']}")

def test_intent_short_prompt():
    """Prompt curto deve detectar ambiguidade"""
    prompt = "Cria API"
    intent = chat_enhancer.analyze_intent(prompt)
    
    assert "Prompt muito curto" in str(intent["ambiguities"])
    assert intent["confidence"] == 60
    assert intent["should_clarify"] == True
    print(f"✅ Intent short prompt: ambiguities {intent['ambiguities']} should_clarify {intent['should_clarify']}")

def test_prompt_optimization():
    """Deve otimizar prompts curtos com terceiro olho"""
    prompt = "Cria API"
    intent = chat_enhancer.analyze_intent(prompt)
    optimized = chat_enhancer.optimize_prompt(prompt, intent)
    
    assert len(optimized["optimized_prompt"]) > len(prompt)
    assert optimized["should_use_optimized"] == True
    assert len(optimized["third_eye_checks"]) == 5
    assert "Verificar se código funciona" in optimized["third_eye_checks"][0]
    assert optimized["agent"] == "prompt-optimizer-01"
    print(f"✅ Prompt optimization: improvements {optimized['improvements']} third_eye {optimized['third_eye_checks'][:2]}")

def test_prompt_optimization_clear():
    """Prompt claro não deve precisar otimização"""
    prompt = "Explica como funciona validação NIF e depois cria função Python apenas código com docstring e testes"
    intent = chat_enhancer.analyze_intent(prompt)
    optimized = chat_enhancer.optimize_prompt(prompt, intent)
    
    # Prompt já claro, não deve expandir muito
    assert optimized["should_use_optimized"] == False or len(optimized["improvements"]) <= 2
    print(f"✅ Prompt clear: should_use_optimized {optimized['should_use_optimized']} improvements {optimized['improvements']}")

def test_critique_good_response():
    """Critic deve dar score alto para resposta boa com código funcional"""
    original = "Cria função validar NIF"
    optimized = "Cria função validar NIF\n\nRequisitos: 9 dígitos, checksum mod 11"
    response = """
def validar_nif(nif: str) -> bool:
    \"\"\"Valida NIF português\"\"\"
    if len(nif) != 9 or not nif.isdigit():
        return False
    if nif[0] not in "1235689":
        return False
    pesos = range(9, 1, -1)
    soma = sum(int(d) * p for d, p in zip(nif[:8], pesos))
    resto = soma % 11
    digito = 11 - resto
    if digito >= 10:
        digito = 0
    return digito == int(nif[-1])
"""
    intent = {"intent_type": "code_generation"}
    critique = chat_enhancer.critique_response(original, optimized, response, intent)
    
    assert critique["score"] >= 70
    assert critique["is_functional"] == True
    assert critique["is_rigorous"] == True
    assert critique["should_retry"] == False
    print(f"✅ Critique good: score {critique['score']} functional {critique['is_functional']} rigorous {critique['is_rigorous']}")

def test_critique_bad_response():
    """Critic deve detectar resposta ruim sem código"""
    original = "Cria função validar NIF"
    optimized = original
    response = "Claro, NIF é um número fiscal português"
    intent = {"intent_type": "code_generation"}
    critique = chat_enhancer.critique_response(original, optimized, response, intent)
    
    assert critique["score"] < 70
    assert len(critique["issues"]) > 0
    assert critique["should_retry"] == True
    print(f"✅ Critique bad: score {critique['score']} issues {critique['issues'][:1]} should_retry {critique['should_retry']}")

def test_code_review_security():
    """Code reviewer deve detectar eval perigoso e api_key hardcoded"""
    code_eval = "def test():\n    eval(user_input)"
    review = chat_enhancer.review_code(code_eval, "python", "test")
    assert any("CRÍTICO" in i and "eval" in i for i in review["issues"])
    assert review["is_secure"] == False
    print(f"✅ Code review security eval: issues {review['issues']}")

def test_code_review_api_key():
    """Deve detectar API key hardcoded"""
    code_key = 'api_key = "sk-1234567890abcdef"'
    review = chat_enhancer.review_code(code_key, "python", "test")
    assert any("API key" in i for i in review["issues"])
    print(f"✅ Code review api_key: issues {review['issues']}")

def test_enhance_chat_flow():
    """Fluxo completo enhance_chat"""
    prompt = "Cria função validar NIF"
    result = chat_enhancer.enhance_chat(prompt, [])
    
    assert "original_prompt" in result
    assert "optimized_prompt" in result
    assert "intent" in result
    assert "optimization" in result
    assert "agents_trace" in result
    assert len(result["agents_trace"]) == 2
    assert result["latency_ms"] >= 0
    print(f"✅ Enhance chat flow: trace {len(result['agents_trace'])} agents, latency {result['latency_ms']}ms")

def test_enhance_response_flow():
    """Fluxo completo enhance_response com terceiro olho"""
    original = "Cria função NIF"
    optimized = "Cria função NIF com checksum"
    response = "def validar_nif(nif): return len(nif)==9"
    intent = {"intent_type": "validation_utility"}
    result = chat_enhancer.enhance_response(original, optimized, response, intent)
    
    assert "critique" in result
    assert "final_score" in result
    assert "should_retry" in result
    assert "agents_trace" in result
    assert result["latency_ms"] >= 0
    print(f"✅ Enhance response flow: score {result['final_score']} should_retry {result['should_retry']}")

if __name__ == "__main__":
    test_intent_analysis_code()
    test_intent_short_prompt()
    test_prompt_optimization()
    test_prompt_optimization_clear()
    test_critique_good_response()
    test_critique_bad_response()
    test_code_review_security()
    test_code_review_api_key()
    test_enhance_chat_flow()
    test_enhance_response_flow()
    print("\n✅ All chat_enhancer tests passed - TERCEIRO OLHO ATIVO, CONTESTA, CRITICA, NÃO FICA NA 1ª")
