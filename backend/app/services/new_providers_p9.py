"""
P9 — Novos Providers 2026-09-18 — busca web real free no card
Baseado em pesquisa web 2026-09-18:
- freellmapi.co best-free-llm-apis-2026: Google, Groq, Cerebras, OpenRouter, NVIDIA NIM, Cloudflare, Mistral, Cohere, Z.ai, Reka $10/mo
- freellm.net 31+ providers: OpenRouter 34, NVIDIA 131, Groq 12, Ollama Cloud 17, Kilo Code 15, Cloudflare 40, ModelScope 61, LLM7.io 19, OVHcloud 14, Chutes 2, Google 19, GitHub 16, Agnes 5, Mistral 15, Glhf 2, Z AI 8, Cohere 12, HuggingFace 8, SiliconFlow 3, Aion Labs 11, OpenCode Zen 13, DeepSeek 2, SambaNova 4, Nscale 2, Nebius 1, Alibaba 5, AI21 2
- tokenmix.ai 15 best: Google, Groq, OpenRouter, GitHub Models, Cloudflare, Cerebras, Mistral, Cohere, Vercel $5/mo, HuggingFace $0.10/mo, NVIDIA, SambaNova $5 30d, AI21 $10 3mo, Fireworks $1, DeepSeek conditional

Novos providers P9 para aumentar de 32 para 50+:
- kilo_code — 15 models no card
- modelscope — 61 models no card (ModelScope)
- ovhcloud — 14 models no card OVHcloud AI Endpoints
- agnes_ai — 5 models no card
- glhf_chat — 2 models no card Glhf.chat
- aion_labs — 11 models no card
- opencode_zen — 13 models no card OpenCode Zen
- nscale — 2 models no card
- nebius — 1 model no card Nebius
- reka — $10/month recurring Reka
- vercel_ai — $5/month Vercel AI Gateway
- bazaarlink — free gateway BazaarLink auto:free
- github_models — já existe? temos github_models mas vamos garantir
- ovhcloud, etc

Todos com free_no_card=true quando aplicável
"""

NEW_PROVIDERS_P9 = [
    {
        "provider_id": "kilo_code",
        "name": "Kilo Code",
        "base_url": "https://api.kilocode.ai/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "freellm.net_2026_09_18_search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "15 models free", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE 15 models", "output_per_1m": "FREE", "free_no_card": True, "source": "freellm.net 15 models no card"}
    },
    {
        "provider_id": "modelscope",
        "name": "ModelScope",
        "base_url": "https://api-inference.modelscope.cn/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "freellm.net_2026_09_18_search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "vision": "provider_claim", "free_no_card": True, "free": True, "models": "61 models free", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE 61 models", "output_per_1m": "FREE", "free_no_card": True, "source": "freellm.net 61 models no card"}
    },
    {
        "provider_id": "ovhcloud",
        "name": "OVHcloud AI Endpoints",
        "base_url": "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "freellm.net_2026_09_18_search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "14 models free", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE 14 models", "output_per_1m": "FREE", "free_no_card": True, "source": "freellm.net 14 models no card"}
    },
    {
        "provider_id": "agnes_ai",
        "name": "Agnes AI",
        "base_url": "https://api.agnes.ai/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "freellm.net_2026_09_18_search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "vision": "provider_claim", "free_no_card": True, "free": True, "models": "5 models free", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE 5 models", "output_per_1m": "FREE", "free_no_card": True, "source": "freellm.net 5 models no card"}
    },
    {
        "provider_id": "glhf_chat",
        "name": "Glhf.chat",
        "base_url": "https://glhf.chat/api/openai/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "freellm.net_2026_09_18_search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "2 models free", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE 2 models", "output_per_1m": "FREE", "free_no_card": True, "source": "freellm.net 2 models no card"}
    },
    {
        "provider_id": "aion_labs",
        "name": "Aion Labs",
        "base_url": "https://api.aionlabs.ai/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "freellm.net_2026_09_18_search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "11 models free", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE 11 models", "output_per_1m": "FREE", "free_no_card": True, "source": "freellm.net 11 models no card"}
    },
    {
        "provider_id": "opencode_zen",
        "name": "OpenCode Zen",
        "base_url": "https://api.opencodezen.com/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "freellm.net_2026_09_18_search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "13 models free", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE 13 models", "output_per_1m": "FREE", "free_no_card": True, "source": "freellm.net 13 models no card"}
    },
    {
        "provider_id": "nscale",
        "name": "Nscale",
        "base_url": "https://api.nscale.ai/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "freellm.net_2026_09_18_search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "2 models free", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE 2 models", "output_per_1m": "FREE", "free_no_card": True, "source": "freellm.net 2 models no card"}
    },
    {
        "provider_id": "nebius",
        "name": "Nebius",
        "base_url": "https://api.studio.nebius.com/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "freellm.net_2026_09_18_search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "1 model free", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE 1 model", "output_per_1m": "FREE", "free_no_card": True, "source": "freellm.net 1 model no card"}
    },
    {
        "provider_id": "reka",
        "name": "Reka AI",
        "base_url": "https://api.reka.ai/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "freellmapi.co_2026_09_18_search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": False, "free": True, "models": "$10/month recurring", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "$10/month recurring free", "output_per_1m": "$10/month", "free_no_card": False, "source": "freellmapi.co Reka $10/mo"}
    },
    {
        "provider_id": "vercel_ai",
        "name": "Vercel AI Gateway",
        "base_url": "https://ai-gateway.vercel.sh/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "tokenmix.ai_2026_09_18_search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "provider_claim", "free_no_card": True, "free": True, "models": "$5/month included", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE $5/month included", "output_per_1m": "FREE $5/mo", "free_no_card": True, "source": "tokenmix.ai Vercel $5/mo"}
    },
    {
        "provider_id": "bazaarlink",
        "name": "BazaarLink",
        "base_url": "https://api.bazaarlink.ai/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "freellm.net_2026_09_18_search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "auto:free zero-cost inference", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE auto:free", "output_per_1m": "FREE", "free_no_card": True, "source": "bazaarlink.ai free gateway"}
    },
    {
        "provider_id": "github_models",
        "name": "GitHub Models",
        "base_url": "https://models.inference.ai.azure.com",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "freellm.net_2026_09_18_search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "16 models free GitHub", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE GitHub Models 150 RPD", "output_per_1m": "FREE", "free_no_card": True, "source": "freellm.net GitHub Models"}
    },
]

def seed_p9_providers(db):
    from ..models.database_models import Provider, ProviderStatus
    added = 0
    for p_data in NEW_PROVIDERS_P9:
        existing = db.query(Provider).filter(Provider.provider_id == p_data["provider_id"]).first()
        if existing:
            # Update capabilities to include free_no_card if missing
            caps = existing.capabilities or {}
            if "free_no_card" not in caps and p_data["capabilities"].get("free_no_card"):
                caps["free_no_card"] = True
                existing.capabilities = caps
                print(f"[P9] Updated existing {p_data['provider_id']} with free_no_card")
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
        print(f"[P9] Added new provider {p_data['provider_id']} {p_data['name']} free_no_card={p_data['capabilities'].get('free_no_card')}")
    db.commit()
    return added

print(f"[P9] New providers module loaded — {len(NEW_PROVIDERS_P9)} providers to add (32→{32+len(NEW_PROVIDERS_P9)})")
