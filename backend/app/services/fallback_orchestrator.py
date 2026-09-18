"""
P17 Lean - Fallback Orchestrator Simples 1x Erro Técnico - não fallback por quality até rubric validado
Rigoroso, real, funcional, sem invenção - só fallback se erro técnico timeout 5xx rate limit, não quality subjetivo
"""
from typing import Dict, List, Optional

class FallbackOrchestrator:
    """P17 Lean - Fallback simples 1x técnico, circuit breaker já existe"""
    
    def should_fallback(self, error: str = None, status_code: int = None, critic_score: int = None) -> Dict:
        """
        Decide se deve fallback - P17 Lean conservador:
        - Só fallback se erro técnico: timeout, 5xx, rate limit, connection error
        - Não fallback por quality score até rubric validado (quality subjetivo)
        - Max 1 fallback para não aumentar latency muito 402ms*2=804ms
        """
        if error:
            error_lower = error.lower()
            # Erros técnicos que justificam fallback
            technical_errors = ["timeout", "timed out", "connection", "5xx", "500", "502", "503", "504", "rate limit", "429", "overloaded", "unavailable"]
            if any(e in error_lower for e in technical_errors):
                return {
                    "should_fallback": True,
                    "reason": f"Erro técnico detectado: {error[:100]} - justifica fallback",
                    "type": "technical",
                    "max_fallbacks": 1,
                    "p17_lean": True
                }
        
        if status_code:
            if status_code >= 500 or status_code == 429:
                return {
                    "should_fallback": True,
                    "reason": f"Status code {status_code} >=500 ou 429 rate limit - justifica fallback",
                    "type": "technical",
                    "max_fallbacks": 1,
                    "p17_lean": True
                }
        
        # P17 Lean: não fallback por critic_score até rubric validado
        # Quality subjetivo, não justifica fallback automático
        if critic_score is not None and critic_score < 50:
            return {
                "should_fallback": False,
                "reason": f"Critic score {critic_score} <50 mas P17 Lean não faz fallback por quality subjetivo até rubric validado - só técnico",
                "type": "quality",
                "should_fallback": False,
                "p17_lean": True,
                "note": "Quality fallback desabilitado P17 Lean, só técnico"
            }
        
        return {
            "should_fallback": False,
            "reason": "Sem erro técnico, sem fallback - P17 Lean conservador",
            "type": "none",
            "p17_lean": True
        }
    
    def get_next_provider(self, failed_provider_id: str, ranked_providers: List[Dict]) -> Optional[Dict]:
        """Retorna próximo provider ranking após falha"""
        for i, prov in enumerate(ranked_providers):
            if prov["provider_id"] == failed_provider_id and i+1 < len(ranked_providers):
                return ranked_providers[i+1]
        # Se failed é último ou não encontrado, retorna primeiro diferente
        for prov in ranked_providers:
            if prov["provider_id"] != failed_provider_id:
                return prov
        return None

# Singleton
fallback_orchestrator = FallbackOrchestrator()
