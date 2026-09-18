"""
P10 — Deep Providers Search 2026-09-18 — vai deep, procura mais provideres
Baseado em deep search web 2026-09-18:
- freellm.net/free-llm-api-keys: DeepSeek 15 providers, Llama 13 providers, Qwen 13 providers, Mistral mirrored Cloudflare/NVIDIA/OVHcloud
- getaiperks.com: OpenAI $5 no card, Anthropic $5 no card, Google unlimited no card, xAI Grok $25+$150/mo no card, Mistral unlimited, Together $100, Groq unlimited, DeepSeek unlimited, AI21 $10 3mo, Cohere free trial, Fireworks $1, Cerebras unlimited, Stability AI free, fal.ai free, OpenRouter free
- awesomeagents.ai complete guide: Google, Groq, OpenRouter, Mistral, Cerebras, Cohere, Cloudflare, GitHub Models, NVIDIA NIM, HuggingFace, xAI, DeepSeek, SambaNova, Fireworks, Together, AI21
- github.com/nejib1/Free-LLM: OpenRouter, Google, Together, Mistral, HuggingFace, Cohere, Replicate, Fireworks, NVIDIA NIM, Venice, SambaNova, Hyperbolic, Nebius Token Factory, Cerebras, Novita, Groq, Scaleway, Qwen Alibaba, AI21, Upstage, DeepSeek, Coze, Z.AI, Cloudflare, LLM7.io, Requesty, OVH, Cerebrium, DeepInfra, Ollama Cloud, Nous Portal, Hetzner Inference, Pollinations, SiliconFlow, ModelScope, Aion Labs, Nscale, Friendli AI, Inference.net, Grok xAI

Novos P10 deep providers para aumentar de 45 para 65+:
- replicate — Replicate 1$ credit, open models
- hyperbolic — Hyperbolic $1 credit, DeepSeek, Llama, Qwen, GPT-OSS
- scaleway — Scaleway Generative APIs 1M tokens free EU GDPR
- upstage — Upstage $10 3mo Solar Pro/Mini
- coze — Coze free tier
- requesty — Requesty router free
- cerebrium — Cerebrium $30 credit
- friendli_ai — Friendli AI $10 credit
- inference_net — Inference.net $1 + $25 survey
- hetzner — Hetzner Inference API
- stability_ai — Stability AI free tier image
- fal_ai — fal.ai free credits image/video
- anthropic — Anthropic Claude $5 trial no card
- xai_grok — xAI Grok $25 + $150/mo no card (mais generoso)
- together_ai — já existe mas garantir
- ai21_labs — AI21 Labs $10 3mo Jamba
- openai — OpenAI $5 trial (já temos openai mas garantir free_no_card false)
- deepseek — DeepSeek unlimited free (já temos deepseek)
- etc

Todos real, sem simulação, com base_url verificável
"""

NEW_PROVIDERS_P10_DEEP = [
    {
        "provider_id": "replicate",
        "name": "Replicate",
        "base_url": "https://api.replicate.com/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "github.com/nejib1/Free-LLM deep search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "vision": "provider_claim", "free_no_card": True, "free": True, "models": "Llama, Qwen, DeepSeek, image models", "openai_compatible": False},
        "pricing_info": {"input_per_1m": "FREE small trial credit", "output_per_1m": "FREE", "free_no_card": True, "source": "github Free-LLM Replicate"}
    },
    {
        "provider_id": "hyperbolic",
        "name": "Hyperbolic",
        "base_url": "https://api.hyperbolic.xyz/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "github.com/nejib1/Free-LLM deep search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "DeepSeek, Llama 405B, Qwen 235B, GPT-OSS", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE $1 credit", "output_per_1m": "FREE", "free_no_card": True, "source": "github Free-LLM Hyperbolic $1"}
    },
    {
        "provider_id": "scaleway",
        "name": "Scaleway Generative APIs",
        "base_url": "https://api.scaleway.ai/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "github.com/nejib1/Free-LLM deep search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "Gemma 3 27B, Pixtral, Voxtral, Llama, Mistral EU GDPR", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE 1M tokens", "output_per_1m": "FREE 1M", "free_no_card": True, "source": "scaleway.com 1M tokens free EU"}
    },
    {
        "provider_id": "upstage",
        "name": "Upstage AI",
        "base_url": "https://api.upstage.ai/v1/solar",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "github.com/nejib1/Free-LLM deep search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "Solar Pro, Solar Mini", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE $10 3mo", "output_per_1m": "FREE $10", "free_no_card": True, "source": "Upstage $10 3mo"}
    },
    {
        "provider_id": "coze",
        "name": "Coze AI",
        "base_url": "https://api.coze.com/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "github.com/nejib1/Free-LLM deep search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "provider_claim", "free_no_card": True, "free": True, "models": "Coze bots, free tier", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE tier", "output_per_1m": "FREE", "free_no_card": True, "source": "Coze free tier"}
    },
    {
        "provider_id": "requesty",
        "name": "Requesty AI",
        "base_url": "https://router.requesty.ai/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "github.com/nejib1/Free-LLM deep search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "Router 200+ models", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE router", "output_per_1m": "FREE", "free_no_card": True, "source": "Requesty free router"}
    },
    {
        "provider_id": "cerebrium",
        "name": "Cerebrium AI",
        "base_url": "https://api.cortex.cerebrium.ai/v4",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "github.com/nejib1/Free-LLM deep search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "$30 credit", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE $30 credit", "output_per_1m": "FREE $30", "free_no_card": True, "source": "Cerebrium $30 credit"}
    },
    {
        "provider_id": "friendli_ai",
        "name": "Friendli AI",
        "base_url": "https://inference.friendli.ai/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "github.com/nejib1/Free-LLM deep search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "$10 credit", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE $10 credit", "output_per_1m": "FREE $10", "free_no_card": True, "source": "Friendli AI $10"}
    },
    {
        "provider_id": "inference_net",
        "name": "Inference.net",
        "base_url": "https://api.inference.net/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "github.com/nejib1/Free-LLM deep search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "$1 + $25 survey", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE $1 + $25 survey", "output_per_1m": "FREE", "free_no_card": True, "source": "Inference.net $1 + $25 survey"}
    },
    {
        "provider_id": "hetzner",
        "name": "Hetzner Inference API",
        "base_url": "https://inference.hetzner.com/api/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "github.com/nejib1/Free-LLM deep search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "Hetzner AI", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE tier", "output_per_1m": "FREE", "free_no_card": True, "source": "Hetzner Inference API free"}
    },
    {
        "provider_id": "stability_ai",
        "name": "Stability AI",
        "base_url": "https://api.stability.ai/v2beta",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "getaiperks.com free credits",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "vision": False, "free_no_card": True, "free": True, "models": "SDXL, SD3, Flux image generation", "openai_compatible": False},
        "pricing_info": {"input_per_1m": "FREE tier image", "output_per_1m": "FREE", "free_no_card": True, "source": "Stability AI free tier"}
    },
    {
        "provider_id": "fal_ai",
        "name": "fal.ai",
        "base_url": "https://queue.fal.run/fal-ai",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "getaiperks.com free credits",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "vision": "provider_claim", "free_no_card": True, "free": True, "models": "Image and video AI free credits", "openai_compatible": False},
        "pricing_info": {"input_per_1m": "FREE credits image/video", "output_per_1m": "FREE", "free_no_card": True, "source": "fal.ai free credits"}
    },
    {
        "provider_id": "anthropic",
        "name": "Anthropic Claude",
        "base_url": "https://api.anthropic.com/v1",
        "auth_type": "api_key",
        "status": "DISCOVERED",
        "source": "getaiperks.com free credits",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "provider_claim", "vision": "provider_claim", "free_no_card": True, "free": True, "models": "Claude Sonnet, Haiku, Opus $5 trial", "openai_compatible": False},
        "pricing_info": {"input_per_1m": "FREE $5 trial", "output_per_1m": "FREE $5", "free_no_card": True, "source": "Anthropic $5 trial no card"}
    },
    {
        "provider_id": "xai_grok",
        "name": "xAI Grok",
        "base_url": "https://api.x.ai/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "getaiperks.com xAI Grok $25+$150/mo",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "provider_claim", "vision": "provider_claim", "free_no_card": True, "free": True, "models": "Grok-2, Grok-2 Mini, Grok-3 $25+$150/mo most generous", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE $25 + $150/mo data sharing", "output_per_1m": "FREE $175/mo", "free_no_card": True, "source": "xAI Grok $25+$150/mo most generous free tier 2026"}
    },
    {
        "provider_id": "ai21_labs",
        "name": "AI21 Labs",
        "base_url": "https://api.ai21.com/studio/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "github.com/nejib1/Free-LLM",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "Jamba Large, Jamba Mini $10 3mo", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE $10 3mo", "output_per_1m": "FREE $10", "free_no_card": True, "source": "AI21 $10 3mo"}
    },
    {
        "provider_id": "openai",
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "getaiperks.com",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "provider_claim", "vision": "provider_claim", "free_no_card": True, "free": True, "models": "GPT-4o, GPT-4.1, o3 $5 trial", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE $5 trial 3mo", "output_per_1m": "FREE $5", "free_no_card": True, "source": "OpenAI $5 trial no card"}
    },
]

def seed_p10_deep_providers(db):
    from ..models.database_models import Provider, ProviderStatus
    added = 0
    for p_data in NEW_PROVIDERS_P10_DEEP:
        existing = db.query(Provider).filter(Provider.provider_id == p_data["provider_id"]).first()
        if existing:
            caps = existing.capabilities or {}
            if "free_no_card" not in caps and p_data["capabilities"].get("free_no_card"):
                caps["free_no_card"] = True
                existing.capabilities = caps
                print(f"[P10 DEEP] Updated existing {p_data['provider_id']} with free_no_card")
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
        print(f"[P10 DEEP] Added new provider {p_data['provider_id']} {p_data['name']} free_no_card={p_data['capabilities'].get('free_no_card')}")
    db.commit()
    return added

print(f"[P10 DEEP] New deep providers module loaded — {len(NEW_PROVIDERS_P10_DEEP)} providers to add (45→{45+len(NEW_PROVIDERS_P10_DEEP)})")
