"""
P7 — Novos Providers Poderosos Contínuos e Fluidos — sem cartão, free tier real 2026
Baseado em pesquisa real 2026-09-18:
- Google AI Studio (temos gemini mas DEGRADED fail 14)
- Groq (temos 100% medido)
- OpenRouter (100% medido)
- Cerebras (100% medido)
- Mistral (100% medido)
- Cohere (76% medido)
- Cloudflare Workers AI (temos mas 0% medido DEGRADED fail 13)
- GitHub Models (temos? não como provider separado, temos github_models? não listado, mas temos via openrouter?)
- NVIDIA NIM (temos nvidia 96% medido)
- HuggingFace (100% medido)
- Z.ai / Zhipu GLM-4.7-Flash free no card
- SiliconFlow — Qwen, DeepSeek, GLM free ¥14 signup
- LLM7.io — no registration needed
- Alibaba Qwen DashScope — 1M tokens/model free
- DeepInfra — $5 credits
- Together AI — $5 min purchase (não free puro)
- Fireworks — $1 credit (temos 0/8)
- SambaNova — $5 credits (temos DEGRADED)
- Venice.ai — tem mas 0/20
- Novita — tem mas 0/20
- Ollama Cloud — tem mas 0/20
- Nous Research — tem mas 0/30
- Pollinations — 93% medido free
- Chutes — 100% medido

Novos providers P7 para aumentar capacidade contínua fluida:
1. z_ai — Zhipu AI GLM-4.7-Flash free international endpoint no Chinese phone
2. siliconflow — SiliconFlow Qwen/DeepSeek/GLM free
3. llm7_io — LLM7.io no registration needed 20 req/min 200 req/day no card
4. alibaba_qwen — Alibaba DashScope Qwen 1M tokens/model free
5. deepinfra — DeepInfra $5 credits free
6. fireworks_fix — já existe mas vamos fixar medição
7. cloudflare_fix — já existe mas vamos fixar adapter

Todos com free_no_card=true para discovery incluir mesmo sem key
"""

NEW_PROVIDERS_P7 = [
    {
        "provider_id": "z_ai",
        "name": "Z.ai (Zhipu GLM)",
        "base_url": "https://api.z.ai/api/paas/v4",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "awesomeagents_2026_search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "vision": "UNKNOWN", "free_no_card": True, "free": True, "models": "GLM-4.7-Flash, GLM-4.5-Flash free"},
        "pricing_info": {"input_per_1m": "FREE GLM-4.7-Flash", "output_per_1m": "FREE", "free_no_card": True, "source": "search_2026_09_18"}
    },
    {
        "provider_id": "siliconflow",
        "name": "SiliconFlow",
        "base_url": "https://api.siliconflow.cn/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "awesomeagents_2026_search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "Qwen, DeepSeek, GLM"},
        "pricing_info": {"input_per_1m": "FREE ¥14 signup", "output_per_1m": "FREE", "free_no_card": True, "source": "search_2026_09_18"}
    },
    {
        "provider_id": "llm7_io",
        "name": "LLM7.io",
        "base_url": "https://api.llm7.io/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "awesomeagents_2026_search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "no_registration": True, "models": "bidara, codestral, deepseek-r1, gpt-4o-mini, grok-3-mini"},
        "pricing_info": {"input_per_1m": "FREE 20 RPM 200 RPD no card", "output_per_1m": "FREE", "free_no_card": True, "source": "search_2026_09_18"}
    },
    {
        "provider_id": "alibaba_qwen",
        "name": "Alibaba Qwen DashScope",
        "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "awesomeagents_2026_search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "provider_claim", "vision": "provider_claim", "free_no_card": False, "free": True, "models": "Qwen2.5, Qwen3, 1M tokens/model free"},
        "pricing_info": {"input_per_1m": "FREE 1M tokens/model 90 days", "output_per_1m": "FREE", "free_no_card": False, "source": "search_2026_09_18"}
    },
    {
        "provider_id": "deepinfra",
        "name": "DeepInfra",
        "base_url": "https://api.deepinfra.com/v1/openai",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "awesomeagents_2026_search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "provider_claim", "free_no_card": False, "free": True, "models": "Llama, Qwen, DeepSeek"},
        "pricing_info": {"input_per_1m": "$5 credits free", "output_per_1m": "$5 credits", "free_no_card": False, "source": "search_2026_09_18"}
    },
    {
        "provider_id": "together_ai",
        "name": "Together AI",
        "base_url": "https://api.together.xyz/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "awesomeagents_2026_search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "provider_claim", "free_no_card": False, "free": False, "models": "Llama 4, DeepSeek R1"},
        "pricing_info": {"input_per_1m": "$5 min purchase", "output_per_1m": "$5 min", "free_no_card": False, "source": "search_2026_09_18"}
    },
]

def seed_p7_providers(db):
    from ..models.database_models import Provider, ProviderStatus
    added = 0
    for p_data in NEW_PROVIDERS_P7:
        existing = db.query(Provider).filter(Provider.provider_id == p_data["provider_id"]).first()
        if existing:
            # Update capabilities to include free_no_card if missing
            caps = existing.capabilities or {}
            if "free_no_card" not in caps:
                caps["free_no_card"] = p_data["capabilities"].get("free_no_card", False)
                existing.capabilities = caps
                print(f"[P7] Updated existing {p_data['provider_id']} with free_no_card")
            continue
        provider = Provider(
            provider_id=p_data["provider_id"],
            name=p_data["name"],
            base_url=p_data["base_url"],
            auth_type=p_data["auth_type"],
            status=ProviderStatus.DISCOVERED,
            source=p_data["source"],
            source_confidence=p_data["source_confidence"],
            capabilities=p_data["capabilities"],
            pricing_info=p_data["pricing_info"]
        )
        db.add(provider)
        added += 1
        print(f"[P7] Added new provider {p_data['provider_id']} {p_data['name']} free_no_card={p_data['capabilities'].get('free_no_card')}")
    db.commit()
    return added

print(f"[P7] New providers module loaded — {len(NEW_PROVIDERS_P7)} providers to add")
