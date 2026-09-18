"""
P17 Lean - Response Critic Simples Heuristics 10ms - sem LLM, sem hallucination detection até dataset
Rigoroso, real, funcional, sem invenção - heuristics simples: vazia? incompleta? off-topic keyword? PII leak regex?
"""
import re
from typing import Dict, List

class ResponseCritic:
    """P17 Lean - Critic simples heuristics, não LLM, 10ms target"""
    
    def __init__(self):
        self.pii_patterns = {
            "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "phone": r"\b9\d{8}\b",
            "nif": r"\b\d{9}\b",
            "credit_card": r"\b\d{16}\b",
            "api_key": r"sk-[a-zA-Z0-9]{20,}"
        }
    
    def critique(self, prompt: str, response: str, provider: str = None, model: str = None) -> Dict:
        """
        Critica resposta com heuristics simples P17 Lean:
        - vazia? incompleta? off-topic keyword? PII leak regex?
        - score 0-100 simples, não LLM
        - sem hallucination detection até dataset
        """
        issues = []
        score = 100
        
        # Check vazia
        if not response or len(response.strip()) < 10:
            issues.append("Resposta vazia ou muito curta <10 chars")
            score -= 60  # P17 Lean fix: vazia deve ser <50 para fallback, 100-60=40
        
        # Check incompleta - não respondeu pergunta?
        # Heurística simples: se prompt tem "?" e resposta não tem conteúdo relevante
        if "?" in prompt and len(response) < 20:
            issues.append("Prompt tem pergunta mas resposta muito curta, possível incompleta")
            score -= 20
        
        # Check off-topic via keyword simples
        # Se prompt menciona "Python" e resposta não menciona "python" nem "code" nem "def" etc
        prompt_lower = prompt.lower()
        response_lower = response.lower()
        if "python" in prompt_lower and not any(k in response_lower for k in ["python", "def ", "import ", "print", "code"]):
            issues.append("Prompt menciona Python mas resposta não contém código Python, possível off-topic")
            score -= 15
        
        if "nif" in prompt_lower and not any(k in response_lower for k in ["nif", "valida", "9 dígitos"]):
            issues.append("Prompt menciona NIF mas resposta não contém NIF, possível off-topic")
            score -= 15
        
        # Check PII leak via regex
        for pii_type, pattern in self.pii_patterns.items():
            if pii_type in ["credit_card", "api_key"]:  # Só block para cc e api_key
                matches = re.findall(pattern, response)
                if matches:
                    issues.append(f"PII leak detectado: {pii_type} {len(matches)} matches - deve bloquear")
                    score -= 40
        
        # Check tamanho - muito curta vs prompt longo
        if len(prompt) > 100 and len(response) < 30:
            issues.append(f"Prompt longo {len(prompt)} chars mas resposta curta {len(response)} chars, possível incompleta")
            score -= 20
        
        # Check se resposta é só repetição do prompt
        if prompt.strip().lower() in response_lower and len(response) < len(prompt) * 1.5:
            issues.append("Resposta parece repetição do prompt, possível incompleta")
            score -= 20
        
        # Score final 0-100
        score = max(0, min(100, score))
        
        # Should fallback? P17 Lean: só se score <50 (mais conservador que 70) e não por quality subjetivo, só se vazia ou PII leak
        should_fallback = score < 50
        
        return {
            "score": score,
            "issues": issues,
            "should_fallback": should_fallback,
            "should_fallback_reason": "score <50 vazia ou PII leak - P17 Lean conservador" if should_fallback else "score >=50 OK",
            "prompt_length": len(prompt),
            "response_length": len(response),
            "provider": provider,
            "model": model,
            "checks": {
                "empty": len(response.strip()) < 10,
                "incomplete": len(prompt) > 100 and len(response) < 30,
                "off_topic": len(issues) > 0 and any("off-topic" in i for i in issues),
                "pii_leak": any("PII leak" in i for i in issues)
            },
            "method": "heuristics simples 10ms, sem LLM, sem hallucination detection até dataset 100+",
            "p17_lean": True,
            "confidence": "heuristics - ESTIMATIVA, não LLM",
            "hallucination": "UNKNOWN - precisa dataset + LLM critic, não implementado P17 Lean",
            "quality_rubric": "vazia? incompleta? off-topic keyword? PII leak regex? - simples, não LLM"
        }

# Singleton
response_critic = ResponseCritic()
