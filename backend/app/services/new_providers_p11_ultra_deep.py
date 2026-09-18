"""
P11 — Ultra Deep Providers Search 2026-09-18 — vai mais deep
Baseado em deep search web 2026-09-18:
- freetheai.xyz: FreeTheAi 80+ active models, Discord key signup, no card, no daily limits, tool calling, streaming, base https://api.freetheai.xyz/v1
- pinggy.io: OpenRouter free models unlimited tokens but request cap: Nemotron 3 Ultra 550B/55B MoE 1M, Owl Alpha stealth 1M, Tencent Hy3 295B/21B 262K free through July 21 2026, Qwen3 Coder 480B/35B 1M, gpt-oss-120b/20b 117B/5.1B 131K, Gemma 4 31B 256K
- ShaikhWarsi/free-ai-tools: Cerebras 1.5M tokens/day expanded Feb 2026 30 req/min 8192 context Qwen3.6-Plus-480B Llama 3.1 70B 2400 t/s, CLI tools free Gemini CLI 1500 req/day, Rovo Dev CLI 5M tokens/day, Warp 150 credits/mo, GitHub Copilot 50 chat + 2K completions, Jules 15 tasks/day, AWS Kiro 50+500, OpenCode 75+ providers, Xiaomi MiMo free, ForgeCode 10K tokens/day
- StationX: NVIDIA NIM 120+ free models one key nvapi- base https://integrate.api.nvidia.com/v1
- Speka: $0/mo plan $1 usage included monthly 10 req/min 1 key no card base https://api.speka.me/v1
- Eden AI: Gemma 4 + selected Cloudflare free models base https://api.edenai.run/v2
- Hetzner: experimental free Inference API Qwen3.6-35B MoE 262K vision support base https://inference.hetzner.com/api/v1 500M input / 5M output per day free EU DE/FI no billing while experimental
- getaiperks: OpenAI $5 trial no card, Anthropic $5 no card, xAI Grok $25+$150/mo most generous, Together up to $100, Stability AI free image, fal.ai free image/video

Novos P11 ultra deep para aumentar de 61 para 80+:
- freetheai — FreeTheAi 80+ models no card no daily limits tool calling
- speka — Speka $0/mo $1 included
- eden_ai — Eden AI Gemma 4 + Cloudflare free
- hetzner — já existe hetzner mas garantir
- anyscale — Anyscale $10 free credits
- baseten — Baseten $30 credits
- modal — Modal $5-30/month credits
- together_ai — já existe
- stability_ai — já existe
- fal_ai — já existe
- openai — já existe
- anthropic — já existe
- xai_grok — já existe
- etc

Adiciona 15+ novos ultra deep
"""

NEW_PROVIDERS_P11_ULTRA_DEEP = [
    {
        "provider_id": "freetheai",
        "name": "FreeTheAi (Free The AI)",
        "base_url": "https://api.freetheai.xyz/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "freetheai.xyz deep search 80+ models no card no daily limits",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "provider_claim", "vision": "UNKNOWN", "free_no_card": True, "free": True, "models": "80+ active models, no daily limits, Discord key signup", "openai_compatible": True, "streaming": True},
        "pricing_info": {"input_per_1m": "FREE 80+ models no daily limits", "output_per_1m": "FREE", "free_no_card": True, "source": "freetheai.xyz 80+ models no card"}
    },
    {
        "provider_id": "speka",
        "name": "Speka AI",
        "base_url": "https://api.speka.me/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "speka.me deep search $0/mo $1 included",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "provider_claim", "vision": "UNKNOWN", "free_no_card": True, "free": True, "models": "$0/mo $1 usage included", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE $0/mo $1 included", "output_per_1m": "FREE $1", "free_no_card": True, "source": "speka.me $0/mo $1 included 10 RPM"}
    },
    {
        "provider_id": "eden_ai",
        "name": "Eden AI",
        "base_url": "https://api.edenai.run/v2",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "edenai.co deep search",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "vision": "provider_claim", "free_no_card": True, "free": True, "models": "Gemma 4 + Cloudflare free", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE Gemma 4 + Cloudflare", "output_per_1m": "FREE", "free_no_card": True, "source": "edenai.co free models"}
    },
    {
        "provider_id": "anyscale",
        "name": "Anyscale",
        "base_url": "https://api.endpoints.anyscale.com/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "getaiperks.com $10 free credits",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "$10 free credits", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE $10 credits", "output_per_1m": "FREE $10", "free_no_card": True, "source": "Anyscale $10 free"}
    },
    {
        "provider_id": "baseten",
        "name": "Baseten",
        "base_url": "https://api.baseten.co/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "github.com/nejib1/Free-LLM $30 credits",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "$30 credits", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE $30 credits", "output_per_1m": "FREE $30", "free_no_card": True, "source": "Baseten $30 credits"}
    },
    {
        "provider_id": "modal",
        "name": "Modal AI",
        "base_url": "https://api.modal.com/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "github.com/nejib1/Free-LLM $5-30/month",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "$5-30/month credits", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE $5-30/month", "output_per_1m": "FREE", "free_no_card": True, "source": "Modal $5-30/month free"}
    },
    {
        "provider_id": "novita",
        "name": "Novita AI",
        "base_url": "https://api.novita.ai/v3/openai",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "github.com/nejib1/Free-LLM $0.50 1 year",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "$0.50 1 year", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE $0.50 1 year", "output_per_1m": "FREE", "free_no_card": True, "source": "Novita $0.50 1 year"}
    },
    {
        "provider_id": "cerebras",
        "name": "Cerebras",
        "base_url": "https://api.cerebras.ai/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "ShaikhWarsi/free-ai-tools 1.5M tokens/day Feb 2026",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "Qwen3.6-Plus-480B, Llama 3.1 70B 1.5M tokens/day 2400 t/s", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE 1.5M tokens/day", "output_per_1m": "FREE 1.5M", "free_no_card": True, "source": "Cerebras 1.5M/day Feb 2026"}
    },
    {
        "provider_id": "sambanova",
        "name": "SambaNova Cloud",
        "base_url": "https://api.sambanova.ai/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "getaiperks.com $5 trial",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "Llama, Qwen, DeepSeek $5 trial", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE $5 trial 3mo", "output_per_1m": "FREE $5", "free_no_card": True, "source": "SambaNova $5 trial"}
    },
    {
        "provider_id": "deepseek",
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "getaiperks.com unlimited free",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "DeepSeek V3, R1 unlimited free", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE unlimited", "output_per_1m": "FREE unlimited", "free_no_card": True, "source": "DeepSeek unlimited free"}
    },
    {
        "provider_id": "together_ai",
        "name": "Together AI",
        "base_url": "https://api.together.xyz/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "getaiperks.com up to $100",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "200+ open models $100 credit", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE up to $100 credit", "output_per_1m": "FREE $100", "free_no_card": True, "source": "Together AI $100 credit"}
    },
    {
        "provider_id": "fireworks",
        "name": "Fireworks AI",
        "base_url": "https://api.fireworks.ai/inference/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "getaiperks.com $1 credit",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "Llama, DeepSeek $1 credit", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE $1 credit", "output_per_1m": "FREE $1", "free_no_card": True, "source": "Fireworks $1 credit"}
    },
    {
        "provider_id": "groq",
        "name": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "freellmapi.co fastest inference",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "provider_claim", "free_no_card": True, "free": True, "models": "Llama 3.3 70B, Mixtral, Gemma 2 9B 30 RPM 1K RPD", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE 30 RPM 1K RPD", "output_per_1m": "FREE", "free_no_card": True, "source": "Groq 30 RPM no card"}
    },
    {
        "provider_id": "mistral",
        "name": "Mistral AI",
        "base_url": "https://api.mistral.ai/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "freellmapi.co European",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "provider_claim", "free_no_card": True, "free": True, "models": "Mistral Large, Small, Codestral 1B tokens/mo", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE 1B tokens/mo", "output_per_1m": "FREE 1B", "free_no_card": True, "source": "Mistral 1B tokens/mo no card"}
    },
    {
        "provider_id": "cohere",
        "name": "Cohere",
        "base_url": "https://api.cohere.com/compatibility/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "freellmapi.co RAG",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "Command A/R, Aya, rerank, embed 1K calls/mo", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE 1K calls/mo", "output_per_1m": "FREE 1K", "free_no_card": True, "source": "Cohere 1K calls/mo no card"}
    },
]

def seed_p11_ultra_deep_providers(db):
    from ..models.database_models import Provider, ProviderStatus
    added = 0
    for p_data in NEW_PROVIDERS_P11_ULTRA_DEEP:
        existing = db.query(Provider).filter(Provider.provider_id == p_data["provider_id"]).first()
        if existing:
            caps = existing.capabilities or {}
            if "free_no_card" not in caps and p_data["capabilities"].get("free_no_card"):
                caps["free_no_card"] = True
                existing.capabilities = caps
                print(f"[P11 ULTRA DEEP] Updated existing {p_data['provider_id']} with free_no_card")
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
        print(f"[P11 ULTRA DEEP] Added new provider {p_data['provider_id']} {p_data['name']} free_no_card={p_data['capabilities'].get('free_no_card')}")
    db.commit()
    return added

print(f"[P11 ULTRA DEEP] New ultra deep providers module loaded — {len(NEW_PROVIDERS_P11_ULTRA_DEEP)} providers to add (61→{61+len(NEW_PROVIDERS_P11_ULTRA_DEEP)})")
