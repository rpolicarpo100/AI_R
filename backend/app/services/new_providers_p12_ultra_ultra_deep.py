"""
P12 — Ultra Ultra Deep Providers Search 2026-09-18 — vai ainda mais deep
Baseado em deep search web 2026-09-18:
- freetheai.xyz: FreeTheAi 80+ models no card no daily limits tool calling streaming base https://api.freetheai.xyz/v1 (já temos freetheai)
- Speka $0/mo $1 included base https://api.speka.me/v1 (já temos speka)
- Eden AI Gemma 4 + Cloudflare free base https://api.edenai.run/v2 (já temos eden_ai)
- Hetzner experimental free Qwen3.6-35B 262K 500M input /5M output per day EU DE/FI base https://inference.hetzner.com/api/v1 (já temos hetzner)
- Voyage AI 50M free tokens embeddings base https://api.voyageai.com/v1
- Jina AI 10M free tokens reader + embeddings + reranker base https://api.jina.ai/v1
- Deepgram $200 free credits no expiry TTS/STT base https://api.deepgram.com/v1
- ElevenLabs 10k credits/month TTS/STT base https://api.elevenlabs.io/v1
- Puter free LLM API in browser no signup base https://api.puter.com/v1
- AIML API 200+ models unified API free tier base https://api.aimlapi.com/v1
- Stability AI 25 free credits image base https://api.stability.ai/v2beta (já temos stability_ai)
- fal.ai free credits image/video base https://queue.fal.run/fal-ai (já temos fal_ai)
- Runway 125 one-time credits video base https://api.runwayml.com/v1
- Pika 150 daily credits video base https://api.pika.art/v1
- Luma AI limited draft video base https://api.lumalabs.ai/v1
- Kling AI 66 daily credits video base https://api.klingai.com/v1
- Kensa 15 credits one-time video base https://api.kensa.ai/v1
- Leonardo AI 150 daily tokens image+video base https://api.leonardo.ai/v1
- Perchance unlimited no signup image base https://api.perchance.org/v1
- Pollinations free API no signup image base https://gen.pollinations.ai/v1 (já temos pollinations)
- DeepSeek unlimited free base https://api.deepseek.com/v1 (já temos deepseek)
- etc

Novos P12 ultra ultra deep para aumentar de 67 para 80+:
- voyage_ai — Voyage AI 50M free embeddings
- jina_ai — Jina AI 10M free reader+embeddings
- deepgram — Deepgram $200 free TTS/STT
- elevenlabs — ElevenLabs 10k credits TTS/STT
- puter — Puter free LLM API no signup
- aiml_api — AIML API 200+ models free tier
- runway — Runway 125 credits video
- pika — Pika 150 daily video
- luma_ai — Luma AI limited video
- kling_ai — Kling AI 66 daily video
- kensa — Kensa 15 credits video
- leonardo_ai — Leonardo AI 150 daily image+video
- perchance — Perchance unlimited image no signup
"""

NEW_PROVIDERS_P12_ULTRA_ULTRA_DEEP = [
    {
        "provider_id": "voyage_ai",
        "name": "Voyage AI",
        "base_url": "https://api.voyageai.com/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "edenai.co embeddings 50M free",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "voyage-4-lite, embeddings 50M free", "openai_compatible": True, "embeddings": True},
        "pricing_info": {"input_per_1m": "FREE 50M tokens embeddings", "output_per_1m": "FREE 50M", "free_no_card": True, "source": "Voyage AI 50M free"}
    },
    {
        "provider_id": "jina_ai",
        "name": "Jina AI",
        "base_url": "https://api.jina.ai/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "edenai.co embeddings 1M free",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "jina-embeddings-v4 1M tokens/mo free, reader 10M free", "openai_compatible": True, "embeddings": True, "rerank": True},
        "pricing_info": {"input_per_1m": "FREE 1M tokens/mo embeddings + 10M reader", "output_per_1m": "FREE 1M", "free_no_card": True, "source": "Jina AI 1M embeddings + 10M reader free"}
    },
    {
        "provider_id": "deepgram",
        "name": "Deepgram",
        "base_url": "https://api.deepgram.com/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "texttolab.com $200 free credits",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "Aura-2 TTS, Nova-3 STT $200 free no expiry", "openai_compatible": False, "tts": True, "stt": True},
        "pricing_info": {"input_per_1m": "FREE $200 credits TTS/STT no expiry", "output_per_1m": "FREE $200", "free_no_card": True, "source": "Deepgram $200 free no card no expiry"}
    },
    {
        "provider_id": "elevenlabs",
        "name": "ElevenLabs",
        "base_url": "https://api.elevenlabs.io/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "elevenlabs.io 10k credits/month",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "Scribe v2 STT, TTS 10k credits/mo", "openai_compatible": False, "tts": True, "stt": True},
        "pricing_info": {"input_per_1m": "FREE 10k credits/mo TTS/STT", "output_per_1m": "FREE 10k", "free_no_card": True, "source": "ElevenLabs 10k credits/mo free"}
    },
    {
        "provider_id": "puter",
        "name": "Puter.com",
        "base_url": "https://api.puter.com/v1",
        "auth_type": "none",
        "status": "DISCOVERED",
        "source": "github.com/OuterSpacee/free-ai-apis",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "Free LLM API in browser no signup", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE no signup browser", "output_per_1m": "FREE", "free_no_card": True, "source": "Puter free no signup"}
    },
    {
        "provider_id": "aiml_api",
        "name": "AIML API",
        "base_url": "https://api.aimlapi.com/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "github.com/OuterSpacee/free-ai-apis",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "200+ models unified API free tier", "openai_compatible": True},
        "pricing_info": {"input_per_1m": "FREE 200+ models unified", "output_per_1m": "FREE", "free_no_card": True, "source": "AIML API 200+ models free tier"}
    },
    {
        "provider_id": "runway",
        "name": "Runway ML",
        "base_url": "https://api.runwayml.com/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "kensa.cc free video credits",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "Gen-3 Alpha video 125 one-time credits", "openai_compatible": False, "video": True},
        "pricing_info": {"input_per_1m": "FREE 125 credits one-time video", "output_per_1m": "FREE 125", "free_no_card": True, "source": "Runway 125 credits free video"}
    },
    {
        "provider_id": "pika",
        "name": "Pika Labs",
        "base_url": "https://api.pika.art/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "kensa.cc free video credits",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "Pika 2.2 video 150 daily credits", "openai_compatible": False, "video": True},
        "pricing_info": {"input_per_1m": "FREE 150 daily credits video", "output_per_1m": "FREE 150", "free_no_card": True, "source": "Pika 150 daily free video"}
    },
    {
        "provider_id": "luma_ai",
        "name": "Luma AI",
        "base_url": "https://api.lumalabs.ai/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "kensa.cc free video credits",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "Dream Machine video limited draft", "openai_compatible": False, "video": True},
        "pricing_info": {"input_per_1m": "FREE limited draft video", "output_per_1m": "FREE", "free_no_card": True, "source": "Luma AI free limited video"}
    },
    {
        "provider_id": "kling_ai",
        "name": "Kling AI",
        "base_url": "https://api.klingai.com/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "kensa.cc free video credits",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "Kling 2.1 video 66 daily credits", "openai_compatible": False, "video": True},
        "pricing_info": {"input_per_1m": "FREE 66 daily credits video", "output_per_1m": "FREE 66", "free_no_card": True, "source": "Kling AI 66 daily free video"}
    },
    {
        "provider_id": "kensa",
        "name": "Kensa AI",
        "base_url": "https://api.kensa.ai/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "kensa.cc free video credits",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "Veo 3.1, Kling 3, Seedance 15 credits one-time", "openai_compatible": False, "video": True},
        "pricing_info": {"input_per_1m": "FREE 15 credits one-time video", "output_per_1m": "FREE 15", "free_no_card": True, "source": "Kensa 15 credits free video"}
    },
    {
        "provider_id": "leonardo_ai",
        "name": "Leonardo AI",
        "base_url": "https://api.leonardo.ai/v1",
        "auth_type": "bearer",
        "status": "DISCOVERED",
        "source": "kensa.cc free video credits",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "Proprietary image+video 150 daily tokens", "openai_compatible": False, "video": True, "image": True},
        "pricing_info": {"input_per_1m": "FREE 150 daily tokens image+video", "output_per_1m": "FREE 150", "free_no_card": True, "source": "Leonardo AI 150 daily free"}
    },
    {
        "provider_id": "perchance",
        "name": "Perchance AI",
        "base_url": "https://api.perchance.org/v1",
        "auth_type": "none",
        "status": "DISCOVERED",
        "source": "zplatform.ai 61 free image generators",
        "source_confidence": "provider_claim",
        "capabilities": {"tool_calling": "UNKNOWN", "free_no_card": True, "free": True, "models": "Unlimited image no signup", "openai_compatible": False, "image": True},
        "pricing_info": {"input_per_1m": "FREE unlimited image no signup", "output_per_1m": "FREE unlimited", "free_no_card": True, "source": "Perchance unlimited free no signup"}
    },
]

def seed_p12_ultra_ultra_deep_providers(db):
    from ..models.database_models import Provider, ProviderStatus
    added = 0
    for p_data in NEW_PROVIDERS_P12_ULTRA_ULTRA_DEEP:
        existing = db.query(Provider).filter(Provider.provider_id == p_data["provider_id"]).first()
        if existing:
            caps = existing.capabilities or {}
            if "free_no_card" not in caps and p_data["capabilities"].get("free_no_card"):
                caps["free_no_card"] = True
                existing.capabilities = caps
                print(f"[P12 ULTRA ULTRA DEEP] Updated existing {p_data['provider_id']} with free_no_card")
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
        print(f"[P12 ULTRA ULTRA DEEP] Added new provider {p_data['provider_id']} {p_data['name']} free_no_card={p_data['capabilities'].get('free_no_card')}")
    db.commit()
    return added

print(f"[P12 ULTRA ULTRA DEEP] New ultra ultra deep providers module loaded — {len(NEW_PROVIDERS_P12_ULTRA_ULTRA_DEEP)} providers to add (67→{67+len(NEW_PROVIDERS_P12_ULTRA_ULTRA_DEEP)})")
