"""
P17 Lean - Prompt Engineer Provider-Specific - templates com source docs + measured, marca provider_claim vs measured vs UNKNOWN
Rigoroso, real, funcional, sem invenção
"""

PROVIDER_TEMPLATES = {
    "groq": {
        "template": "Concise, direct, no fluff. Answer in same language as user. Use markdown for code.",
        "source": "provider_claim - Groq docs recommend concise, fast, direct",
        "confidence": "provider_claim",
        "best_for": ["SPEED", "CHAT", "CODING"],
        "measured": False
    },
    "groq2": {
        "template": "Concise, direct, no fluff. Answer in same language as user.",
        "source": "provider_claim - Groq2 same as Groq",
        "confidence": "provider_claim",
        "best_for": ["SPEED", "CHAT"],
        "measured": False
    },
    "groq3": {
        "template": "Concise, direct, no fluff.",
        "source": "provider_claim - Groq3",
        "confidence": "provider_claim",
        "best_for": ["SPEED"],
        "measured": False
    },
    "gemini": {
        "template": "System instruction separate from user. Safety settings default. Use thinking for reasoning. Answer in user language PT if user writes PT.",
        "source": "provider_claim - Gemini docs system instruction separate, safety",
        "confidence": "provider_claim",
        "best_for": ["REASONING", "CHAT"],
        "measured": False
    },
    "openrouter": {
        "template": "Model-specific: Claude needs XML tags <thinking> etc, GPT needs system role, Llama needs concise. Check model_id for best practice.",
        "source": "provider_claim - OpenRouter docs model-specific",
        "confidence": "provider_claim",
        "best_for": ["BEST", "REASONING"],
        "measured": False,
        "model_specific": {
            "anthropic": "Use XML tags <thinking> for reasoning, concise",
            "openai": "Use system role for instructions",
            "meta-llama": "Concise, direct",
            "google": "System instruction separate"
        }
    },
    "kie_ai": {
        "template": "Reasoning effort high for gpt-5-2, verbosity medium. Use chain-of-thought for complex tasks.",
        "source": "measured - KIE gpt-5-2 tested 100% 5 tests, reasoning effort high works",
        "confidence": "measured",
        "best_for": ["REASONING", "CODING"],
        "measured": True,
        "evidence": "gpt-5-2 100% 5 tests"
    },
    "pollinations": {
        "template": "Simple, no system, direct prompt. No complex instructions.",
        "source": "provider_claim - Pollinations free, simple",
        "confidence": "provider_claim",
        "best_for": ["CHAT", "SPEED"],
        "measured": False
    },
    "typhoon": {
        "template": "Thai + English, concise, direct. Supports Thai language.",
        "source": "provider_claim - Typhoon Thai",
        "confidence": "provider_claim",
        "best_for": ["CHAT"],
        "measured": False
    },
    "cerebras": {
        "template": "Concise, direct, fast. Similar to Groq.",
        "source": "measured - cerebras/gpt-oss-120b tested 605ms 283ms 296ms",
        "confidence": "measured",
        "best_for": ["SPEED", "CHAT"],
        "measured": True,
        "evidence": "cerebras/gpt-oss-120b 605ms 283ms 296ms traces"
    },
    "default": {
        "template": "Answer in same language as user. Use markdown for code. Be concise but thorough.",
        "source": "default - generic best practice",
        "confidence": "default",
        "best_for": ["CHAT"],
        "measured": False
    }
}

class PromptEngineerProvider:
    """P17 Lean - Prompt Engineer Provider-Specific com source tracking"""
    
    def get_template(self, provider_id: str, model_id: str = None) -> dict:
        """Retorna template provider-specific com source"""
        # Exact match
        if provider_id in PROVIDER_TEMPLATES:
            return PROVIDER_TEMPLATES[provider_id]
        
        # Model-specific for openrouter
        if provider_id == "openrouter" and model_id:
            base = PROVIDER_TEMPLATES["openrouter"].copy()
            for key, tmpl in PROVIDER_TEMPLATES["openrouter"].get("model_specific", {}).items():
                if key in model_id.lower():
                    base["template"] = tmpl
                    base["source"] = f"provider_claim - OpenRouter {key} specific"
                    return base
            return base
        
        # Fallback default
        return PROVIDER_TEMPLATES["default"]
    
    def optimize(self, prompt: str, provider_id: str, model_id: str = None, intent: str = "CHAT") -> dict:
        """Otimiza prompt por provider - P17 Lean"""
        template_info = self.get_template(provider_id, model_id)
        
        # Simple optimization: prepend template if intent matches best_for
        if intent in template_info.get("best_for", []):
            optimized = f"{template_info['template']}\n\nUser: {prompt}"
            should_use = True
        else:
            optimized = prompt
            should_use = False
        
        return {
            "original": prompt,
            "optimized": optimized,
            "should_use_optimized": should_use,
            "provider_id": provider_id,
            "model_id": model_id,
            "template": template_info["template"],
            "source": template_info["source"],
            "confidence": template_info["confidence"],
            "measured": template_info.get("measured", False),
            "evidence": template_info.get("evidence", "UNKNOWN"),
            "intent": intent,
            "best_for": template_info.get("best_for", []),
            "p17_lean": True
        }

# Singleton
prompt_engineer_provider = PromptEngineerProvider()
