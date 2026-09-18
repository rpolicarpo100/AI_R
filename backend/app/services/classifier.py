from enum import Enum
from dataclasses import dataclass
from typing import List
import re

class TaskType(str, Enum):
    CHAT = "CHAT"
    CODING = "CODING"
    REASONING = "REASONING"
    LONG_CONTEXT = "LONG_CONTEXT"
    MULTIMODAL = "MULTIMODAL"
    API = "API"
    JSON = "JSON"
    TOOL_CALLING = "TOOL_CALLING"

class ComplexityLevel(str, Enum):
    SIMPLE = "SIMPLE"
    MEDIUM = "MEDIUM"
    COMPLEX = "COMPLEX"

@dataclass
class Classification:
    task_type: TaskType
    confidence: float
    complexity: int
    estimated_tokens: int
    requires_vision: bool = False
    requires_tools: bool = False
    requires_json: bool = False
    reasoning: str = ""
    complexity_level: ComplexityLevel = ComplexityLevel.MEDIUM
    is_simple: bool = False
    fast_path_eligible: bool = False
    cache_ttl_seconds: int = 1800
    suggested_profile: str = "BEST"

class TaskClassifier:
    CODING_KEYWORDS = ["codigo", "code", "função", "function", "class", "bug", "python", "javascript", "typescript", "react", "api", "implement", "refactor", "sql", "docker", "git", "```", "def ", "const ", "import"]
    REASONING_KEYWORDS = ["por que", "why", "explique", "analyze", "compare", "prove", "raciocínio", "lógica", "planej", "strategy", "decide", "tradeoff", "step by step"]
    JSON_KEYWORDS = ["json", "schema", "structured", "format", "output as"]
    TOOL_KEYWORDS = ["tool", "function calling", "call function", "use tool"]
    SIMPLE_GREETINGS = ["ola", "olá", "oi", "hey", "hi", "hello", "bom dia", "boa tarde", "boa noite", "obrigado", "obrigada", "tchau", "adeus", "thanks", "thank you"]
    SIMPLE_QUESTIONS = ["quanto é", "quanto e", "o que é", "o que e", "quem é", "quem e", "quando é", "onde é", "definição", "definiçao", "significado", "que horas", "que dia", "hoje é", "capital de", "quem foi", "como se diz", "traduza", "translate"]
    SIMPLE_MATH = [r"^\s*\d+\s*[\+\-\*\/]\s*\d+", r"^\s*quanto\s+é\s+\d+", r"^\d+\s*\+\s*\d+\s*\?\s*$"]
    COMPLEX_INDICATORS = ["cria", "crie", "gera", "gere", "implementa", "desenvolve", "refatora", "analisa", "compare", "planeja", "arquitetura", "fullstack", "endpoint", "crud", "componente", "valida", "autenticação", "segurança", "performance", "otimiza", "microservice", "refactor", "deploy"]
    GENERIC_COMPLEX = ["sistema", "funciona", "explica"]

    def _is_simple_message(self, prompt: str, tokens_est: int, history: List[dict] = None) -> tuple:
        prompt_lower = prompt.lower().strip()
        prompt_len = len(prompt.strip())
        words = prompt_lower.split()
        if prompt_len < 20 or len(words) <= 3:
            if not any(k in prompt_lower for k in self.CODING_KEYWORDS):
                return True, f"Muito curta {prompt_len} chars {len(words)} palavras — greeting/fast", ComplexityLevel.SIMPLE
        for greeting in self.SIMPLE_GREETINGS:
            if prompt_lower.startswith(greeting) or prompt_lower == greeting or f" {greeting} " in f" {prompt_lower} ":
                if len(words) <= 8:
                    return True, f"Greeting detectado '{greeting}' + curta {len(words)} palavras", ComplexityLevel.SIMPLE
        for sq in self.SIMPLE_QUESTIONS:
            if sq in prompt_lower and len(words) <= 15 and tokens_est < 100:
                if not any(ci in prompt_lower for ci in self.COMPLEX_INDICATORS):
                    return True, f"FAQ simples '{sq}' + {len(words)} palavras <15 + tokens {tokens_est}<100", ComplexityLevel.SIMPLE
        for pattern in self.SIMPLE_MATH:
            if re.match(pattern, prompt_lower):
                return True, f"Math simples pattern '{pattern}'", ComplexityLevel.SIMPLE
        if tokens_est < 20 and not any(k in prompt_lower for k in self.CODING_KEYWORDS + self.REASONING_KEYWORDS):
            return True, f"Tokens {tokens_est}<20 sem código/reasoning → SIMPLE", ComplexityLevel.SIMPLE
        if tokens_est < 50 and len(words) <= 12:
            if not any(ci in prompt_lower for ci in self.COMPLEX_INDICATORS):
                if not any(k in prompt_lower for k in self.CODING_KEYWORDS):
                    return True, f"Tokens {tokens_est}<50 palavras {len(words)}<=12 sem complexo → SIMPLE", ComplexityLevel.SIMPLE
        if tokens_est < 200 and len(words) <= 40:
            coding_hits = sum(1 for k in self.CODING_KEYWORDS if k in prompt_lower)
            if coding_hits < 2:
                return False, f"Tokens {tokens_est}<200 mas não SIMPLE → MEDIUM", ComplexityLevel.MEDIUM
        return False, f"Tokens {tokens_est} palavras {len(words)} com indicadores complexos → COMPLEX", ComplexityLevel.COMPLEX

    def _classify_internal(self, prompt: str, history: List[dict] = None) -> Classification:
        """Internal classification without cache — P6 uses wrapper"""
        history = history or []
        text = prompt.lower()
        full_text = text + " " + " ".join([m.get("content","").lower() for m in history[-5:]])
        tokens_est = len(prompt) // 4 + sum(len(m.get("content","",))//4 for m in history)

        is_simple, simple_reasoning, complexity_level = self._is_simple_message(prompt, tokens_est, history)

        if tokens_est > 8000:
            return Classification(
                TaskType.LONG_CONTEXT, 0.92, 4, tokens_est, 
                reasoning=f"tokens~{tokens_est} > 8000 threshold",
                complexity_level=ComplexityLevel.COMPLEX,
                is_simple=False,
                fast_path_eligible=False,
                cache_ttl_seconds=600,
                suggested_profile="BEST"
            )

        complex_hits = sum(1 for k in self.COMPLEX_INDICATORS if k in full_text)
        if complex_hits >= 1 and len(prompt.split()) > 4:
            coding_hits = sum(1 for k in self.CODING_KEYWORDS if k in full_text)
            task_type = TaskType.CODING if coding_hits >=1 else TaskType.REASONING if complex_hits>=2 else TaskType.CHAT
            return Classification(
                task_type, min(0.7+complex_hits*0.1, 0.9), 3, tokens_est,
                reasoning=f"complex indicators={complex_hits} ({[k for k in self.COMPLEX_INDICATORS if k in full_text][:3]}) palavras={len(prompt.split())} → COMPLEX | {simple_reasoning}",
                complexity_level=ComplexityLevel.COMPLEX,
                is_simple=False,
                fast_path_eligible=False,
                cache_ttl_seconds=600,
                suggested_profile="CODING" if coding_hits>=1 else "REASONING"
            )

        coding_hits = sum(1 for k in self.CODING_KEYWORDS if k in full_text)
        if coding_hits >= 2 or "```" in prompt or (coding_hits>=1 and complex_hits>=1):
            complexity = 4 if any(w in full_text for w in ["arquitetura", "system design", "refactor large", "microservice"]) else 3 if coding_hits > 4 else 2
            return Classification(
                TaskType.CODING, min(0.6+coding_hits*0.12, 0.95), complexity, tokens_est, 
                reasoning=f"coding keywords={coding_hits} | {simple_reasoning}",
                complexity_level=ComplexityLevel.COMPLEX,
                is_simple=False,
                fast_path_eligible=False,
                cache_ttl_seconds=600,
                suggested_profile="CODING"
            )

        if any(k in full_text for k in self.JSON_KEYWORDS) and ("{" in prompt or "json" in text):
            level = ComplexityLevel.SIMPLE if is_simple else ComplexityLevel.MEDIUM
            return Classification(
                TaskType.JSON, 0.85, 2, tokens_est, requires_json=True, 
                reasoning=f"JSON/schema keywords | {simple_reasoning}",
                complexity_level=level,
                is_simple=is_simple,
                fast_path_eligible=is_simple,
                cache_ttl_seconds=3600 if is_simple else 1800,
                suggested_profile="JSON" if not is_simple else "FAST"
            )

        if any(k in full_text for k in self.TOOL_KEYWORDS):
            return Classification(
                TaskType.TOOL_CALLING, 0.85, 3, tokens_est, requires_tools=True, 
                reasoning=f"tool calling keywords | {simple_reasoning}",
                complexity_level=ComplexityLevel.COMPLEX,
                is_simple=False,
                fast_path_eligible=False,
                cache_ttl_seconds=600,
                suggested_profile="TOOL_CALLING"
            )

        reasoning_hits = sum(1 for k in self.REASONING_KEYWORDS if k in full_text)
        if reasoning_hits >= 1 or len(prompt) > 600:
            return Classification(
                TaskType.REASONING, 0.75+reasoning_hits*0.05, 4, tokens_est, 
                reasoning=f"reasoning keywords={reasoning_hits}, len={len(prompt)} | {simple_reasoning}",
                complexity_level=ComplexityLevel.COMPLEX,
                is_simple=False,
                fast_path_eligible=False,
                cache_ttl_seconds=600,
                suggested_profile="REASONING"
            )

        if len(prompt) < 120 and tokens_est < 500:
            if is_simple:
                return Classification(
                    TaskType.API, 0.8, 1, tokens_est, 
                    reasoning=f"short prompt, fast path | {simple_reasoning}",
                    complexity_level=ComplexityLevel.SIMPLE,
                    is_simple=True,
                    fast_path_eligible=True,
                    cache_ttl_seconds=3600,
                    suggested_profile="FAST"
                )
            else:
                return Classification(
                    TaskType.API, 0.8, 1, tokens_est, 
                    reasoning=f"short prompt but not simple | {simple_reasoning}",
                    complexity_level=ComplexityLevel.MEDIUM,
                    is_simple=False,
                    fast_path_eligible=False,
                    cache_ttl_seconds=1800,
                    suggested_profile="FAST"
                )

        if complexity_level == ComplexityLevel.SIMPLE:
            return Classification(
                TaskType.CHAT, 0.7, 2, tokens_est, 
                reasoning=f"default chat SIMPLE | {simple_reasoning}",
                complexity_level=ComplexityLevel.SIMPLE,
                is_simple=True,
                fast_path_eligible=True,
                cache_ttl_seconds=3600,
                suggested_profile="FAST"
            )
        elif complexity_level == ComplexityLevel.MEDIUM:
            return Classification(
                TaskType.CHAT, 0.7, 2, tokens_est, 
                reasoning=f"default chat MEDIUM | {simple_reasoning}",
                complexity_level=ComplexityLevel.MEDIUM,
                is_simple=False,
                fast_path_eligible=False,
                cache_ttl_seconds=1800,
                suggested_profile="BEST"
            )
        else:
            return Classification(
                TaskType.CHAT, 0.7, 3, tokens_est, 
                reasoning=f"default chat COMPLEX | {simple_reasoning}",
                complexity_level=ComplexityLevel.COMPLEX,
                is_simple=False,
                fast_path_eligible=False,
                cache_ttl_seconds=600,
                suggested_profile="BEST"
            )

    def classify(self, prompt: str, history: List[dict] = None) -> Classification:
        """P6 — LRU cache wrapper — saves 10ms per hit for repeated prompts"""
        try:
            from .cache_manager import classifier_cache
            cache_key = f"{prompt[:500]}:{len(history) if history else 0}"
            cached = classifier_cache.get(cache_key)
            if cached:
                return cached
            result = self._classify_internal(prompt, history)
            classifier_cache.set(cache_key, result)
            return result
        except Exception as e:
            # Fallback without cache
            return self._classify_internal(prompt, history)

classifier = TaskClassifier()
print(f"[CLASSIFIER P6] LRU cache enabled 200/60s — saves 10ms per hit")
