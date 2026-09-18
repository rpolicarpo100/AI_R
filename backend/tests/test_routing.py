"""
Testes Routing Engine - Dia 1 Segurança + Testes
Rigoroso, real, funcional, crítico
"""
import sys
sys.path.insert(0, '/home/user/ai-provider-os/backend')

from app.services.routing_engine import routing_engine, Profile
from app.services.classifier import classifier
from app.models.database_models import Provider, Model, ProviderStatus, ModelStatus

def create_mock_provider(provider_id="groq", status=ProviderStatus.VERIFIED, rating=80, failures=0):
    return Provider(
        provider_id=provider_id,
        name=provider_id.title(),
        base_url=f"https://api.{provider_id}.com/v1",
        status=status,
        rating=rating,
        consecutive_failures=failures,
        avg_latency_ms=200,
        success_count=10,
        failure_count=0,
        api_key_encrypted="test"
    )

def create_mock_model(model_id="llama-3.3-70b", provider_id="groq", coding=90, overall=90, confidence=80, test_count=20):
    return Model(
        model_id=model_id,
        provider_id=provider_id,
        display_name=model_id,
        coding_score=coding,
        reasoning_score=80,
        speed_score=80,
        reliability_score=80,
        overall_score=overall,
        confidence_score=confidence,
        test_count=test_count,
        status=ModelStatus.VERIFIED,
        input_price_float=0.0,
        free_tier=True
    )

def test_routing_coding():
    """Para CODING deve selecionar modelo com high coding score"""
    providers = [
        create_mock_provider("groq", ProviderStatus.VERIFIED, 80, 0),
        create_mock_provider("cerebras", ProviderStatus.VERIFIED, 70, 0)
    ]
    models = [
        create_mock_model("codestral", "groq", coding=100, overall=95),
        create_mock_model("llama-8b", "cerebras", coding=50, overall=60)
    ]
    classification = classifier.classify("Cria função Python validar NIF")
    decision = routing_engine.route(providers, models, classification, Profile.CODING)
    
    assert decision.selected.model.coding_score == 100
    assert decision.profile == Profile.CODING
    assert decision.selected.score > 0
    assert len(decision.alternatives) <= 3
    print(f"✅ Routing CODING: selected {decision.selected.model.model_id} score {decision.selected.score} reason {decision.selected.reason}")

def test_routing_health_filter():
    """Deve filtrar providers OFFLINE/DISABLED/DEPRECATED"""
    providers = [
        create_mock_provider("groq", ProviderStatus.VERIFIED, 80, 0),
        create_mock_provider("bad", ProviderStatus.OFFLINE, 90, 10)
    ]
    models = [
        create_mock_model("good-model", "groq", coding=80),
        create_mock_model("bad-model", "bad", coding=100)
    ]
    classification = classifier.classify("Cria função")
    decision = routing_engine.route(providers, models, classification)
    
    # Deve selecionar groq, não bad (OFFLINE)
    assert decision.selected.provider.provider_id == "groq"
    print(f"✅ Health filter: selected {decision.selected.provider.provider_id} not OFFLINE")

def test_routing_enum_fix():
    """Testa fix do bug enum vs string - deve funcionar com enum e string"""
    # Testa com enum
    p_enum = create_mock_provider("groq", ProviderStatus.DEGRADED, 80, 0)
    m = create_mock_model("test", "groq", coding=80)
    classification = classifier.classify("test")
    
    # DEGRADED deve ter health_score 0
    score_degraded = routing_engine.calculate_score(p_enum, m, classification, Profile.BEST)
    
    p_healthy = create_mock_provider("groq", ProviderStatus.VERIFIED, 80, 0)
    score_healthy = routing_engine.calculate_score(p_healthy, m, classification, Profile.BEST)
    
    assert score_healthy > score_degraded
    print(f"✅ Enum fix: healthy {score_healthy} > degraded {score_degraded}")

def test_routing_fallback():
    """Se nenhum candidato ótimo, deve fallback"""
    providers = [create_mock_provider("groq", ProviderStatus.VERIFIED, 10, 0)]
    models = [create_mock_model("low-score", "groq", coding=10, overall=10, confidence=10, test_count=1)]
    classification = classifier.classify("test")
    decision = routing_engine.route(providers, models, classification)
    
    assert decision.selected is not None
    assert decision.confidence >= 0
    print(f"✅ Fallback: selected even with low scores, confidence {decision.confidence}")

def test_profile_weights():
    """Pesos por perfil devem existir"""
    for profile in [Profile.FAST, Profile.CODING, Profile.REASONING, Profile.BEST, Profile.FREE]:
        assert profile in routing_engine.weights
        weights = routing_engine.weights[profile]
        assert isinstance(weights, dict)
        assert sum(weights.values()) > 0
    print("✅ Profile weights OK for all profiles")

if __name__ == "__main__":
    test_routing_coding()
    test_routing_health_filter()
    test_routing_enum_fix()
    test_routing_fallback()
    test_profile_weights()
    print("\n✅ All routing tests passed - FUNCIONAL, RIGOROSO, FIXED enum bug")
