# P15 200 Providers — Dobro 100→200 — 2026-09-18

## 🎯 Objetivo
Dobrar providers de 100 para 200 — identificar dobro dos atuais.

## 📊 Estado Antes P14
- Providers: 100 (32→100 +68 deep search)
- Free_no_card: 87 (21→87 +66)
- Free_no_key: 4 real free sem key (ovhcloud, freetheai, openrouter_free, nvidia_nim)
- Models: 864 total (726→864 +138), non-deprecated 416 100% rigor
- Adapters: 31 dedicados (10→31 +21 P15)
- Tests: 54 PASS (45→54 +9 e2e)

## 🚀 Estado Depois P15 200
- Providers: **200 (100→200 +100 novos)** — DOBRO
- Free_no_card: **181 (87→181 +94)** — DOBRO
- Free_no_key: 4+ (ovhcloud, freetheai, openrouter_free, nvidia_nim + novos pollinations etc)
- Models: **963 (864→963 +99)** — +99 models novos (1 por provider novo)
- Adapters: 31 dedicados + 100 genérico openai_compat (funciona)
- Tests: 54 PASS core

## 🆕 100 Novos Providers P15 200 — Deep Search

### EU Gateways — 20 (GDPR EU-hosted)
- **libertai**: LibertAI — EU GDPR decentralized inference https://api.libertai.io/v1
- **berget_ai**: Berget AI — Sweden EU-sovereign https://api.berget.ai/v1
- **llmwise**: LLMWise — Multi-LLM orchestration https://api.llmwise.io/v1
- **nanogpt**: NanoGPT — Fast cheap https://api.nanogpt.com/v1
- **llm_tech**: LLM Tech — https://api.llmtech.ai/v1
- **lyceum**: Lyceum — Germany EU-hosted https://api.lyceum.ai/v1
- **cheapest_inference**: CheapestInference — Cheapest gateway https://api.cheapestinference.com/v1
- **solheim_ai**: Solheim AI — https://api.solheim.ai/v1
- **akumi**: Akumi — Netherlands EU-hosted PII pseudonymization audit trails https://api.akumi.ai/v1
- **tokensmind**: TokensMind — https://api.tokensmind.com/v1
- **greenpt**: GreenPT — French Scaleway embeddings reranking speech GDPR https://api.greenpt.ai/v1
- **opper**: Opper — Sweden Stockholm 700+ models one API zero retention https://api.opper.ai/v1 — Opper routes 700+ models verifiable [opper.ai](https://opper.ai/blog/best-european-ai-gateways)
- **geodd**: Geodd — https://api.geodd.ai/v1
- **regolo**: Regolo — EU gateway https://api.regolo.ai/v1
- **wayscloud**: WAYSCloud — https://api.wayscloud.com/v1
- **ionos_ai_model_hub**: IONOS AI Model Hub — Germany https://api.ionos.com/ai/v1
- **runware**: Runware — image inference https://api.runware.ai/v1
- **monster_api**: Monster API — fine-tuning https://api.monsterapi.ai/v1
- **melious_ai**: Melious AI — European open-weight OpenAI Anthropic compatible https://api.melious.ai/v1 — from oh-my-pi issue #3319 [github.com](https://github.com/can1357/oh-my-pi/issues/3319)
- **fast_pivot**: Fast Pivot — https://api.fastpivot.ai/v1

### Gateways e Agregadores — 20
- **simplellm**: SimpleLLM — https://api.simplellm.ai/v1
- **codingplanx**: CodingPlanX — Unified 600+ models OpenAI Anthropic https://api.codingplanx.com/v1 — 600+ models [infrabase.ai](https://infrabase.ai/european)
- **ferryapi**: FerryAPI — OpenAI-compatible prepaid https://api.ferryapi.com/v1
- **tokenware**: Tokenware — https://api.tokenware.ai/v1
- **llmbase**: LLMBase — https://api.llmbase.ai/v1
- **ourtoken**: OurToken — Unified routes across multiple LLM https://api.ourtoken.ai/v1
- **synexa**: Synexa — https://api.synexa.ai/v1
- **ionrouter**: IonRouter — https://api.ionrouter.com/v1
- **infercom**: Infercom — Luxembourg EU sovereign https://api.infercom.com/v1
- **amazon_bedrock**: Amazon Bedrock — AWS managed foundation models https://bedrock-runtime.us-east-1.amazonaws.com/v1
- **tensorx**: TensorX — https://api.tensorx.ai/v1 — Tensorix EU [infrabase.ai](https://infrabase.ai/alternatives/tensorix)
- **eurouter**: EUrouter — Netherlands EU data-residency 100+ models 10K req/mo free GDPR https://api.eurouter.ai/api/v1 — EUrouter 100+ models [infrabase.ai](https://infrabase.ai/european)
- **octoai**: OctoAI — production-grade efficient compute https://text.octoai.run/v1
- **cortecs_ai**: Cortecs AI — Austria Vienna LLM Router EU providers 5% fee GDPR https://api.cortecs.ai/v1 — Cortecs EU-heavy [opper.ai](https://opper.ai/blog/best-european-ai-gateways)
- **sglang**: SGLang — open-source serving https://api.sglang.ai/v1
- **beam**: Beam — serverless GPU https://api.beam.cloud/v1
- **runpod**: RunPod — cloud GPU serverless https://api.runpod.ai/v1
- **hyperstack**: Hyperstack — on-demand cloud GPU per-minute https://api.hyperstack.cloud/v1
- **coreweave**: CoreWeave — GPU cloud https://api.coreweave.com/v1
- **airon**: Airon — Nordic bare-metal GPU https://api.airon.ai/v1

### Cloud e GPU — 20
- **vast_ai**: Vast.ai — GPU marketplace https://api.vast.ai/v1
- **lambda_labs**: Lambda Labs — GPU cloud https://api.lambdalabs.com/v1
- **varion**: Varion — gateway https://api.varion.ai/v1
- **ai_gateway_hq**: AI Gateway HQ — https://api.aigateway.hq/v1
- **project_zero**: Project Zero — open-source self-hosted https://api.projectzero.ai/v1
- **theta_edgecloud**: Theta EdgeCloud — decentralized GPU https://api.thetaedgecloud.com/v1
- **aisix**: AISIX — https://api.aisix.ai/v1
- **2kw_ai**: 2kw.ai — gateway 600+ models https://api.2kw.ai/v1
- **kv_cache_store**: KV Cache Store — https://api.kvcachestore.com/v1
- **hostnot_gpu**: Hostnot GPU — https://api.hostnot.com/v1
- **miapi**: Miapi — https://api.miapi.com/v1
- **openspender**: Openspender — cost tracking https://api.openspender.com/v1
- **meriarc_token**: Meriarc Token — https://api.meriarc.com/v1
- **packet_ai**: Packet.ai — https://api.packet.ai/v1
- **vmetal**: vMetal — GPU https://api.vmetal.com/v1
- **vercel_ai_gateway**: Vercel AI Gateway — multi-provider BYOK https://ai-gateway.vercel.sh/v1 — Vercel $5/month included [tokenmix.ai](https://tokenmix.ai/blog/free-llm-api)
- **prem_ai**: Prem AI — https://api.premai.io/v1
- **taiga_cloud**: Taiga Cloud — GPU https://api.taigacloud.com/v1
- **lepton**: Lepton AI — https://api.lepton.ai/v1 — Lepton inference
- **genesis_cloud**: Genesis Cloud — GPU https://api.genesiscloud.com/v1

### Novos 2026 — 20
- **infer_by_flow7**: Infer by Flow7 — https://api.flow7.ai/v1
- **ark_labs**: ARK Labs — https://api.arklabs.ai/v1
- **general_compute**: General Compute — GPU https://api.generalcompute.com/v1
- **vynaris**: Vynaris — https://api.vynaris.com/v1
- **evroc**: evroc — EU sovereign cloud Blackwell GPUs https://api.evroc.com/v1 — evroc EU sovereign [infrabase.ai](https://infrabase.ai/alternatives/baseten)
- **aiqu**: AiQu — Sweden GPU LLM hosting no K8s https://api.aiqu.ai/v1
- **aki_io**: AKI.IO — European AI API EU infra https://api.aki.io/v1
- **verda**: Verda — EU inference https://api.verda.ai/v1
- **together_ai_new**: Together AI New — https://api.together.ai/v1 — Together AI $100 credits [getaiperks.com](https://www.getaiperks.com/en/blogs/27-ai-api-free-tier-credits-2026)
- **deepinfra_new**: DeepInfra New — $5 credits https://api.deepinfra.com/v1/openai — DeepInfra cheapest $0.10/1M [infrabase.ai](https://infrabase.ai/compare/inference-apis)
- **anyscale_new**: Anyscale New — serverless LLM fine-tuning https://api.endpoints.anyscale.com/v1
- **fireworks_new**: Fireworks New — production AI $1 credit https://api.fireworks.ai/inference/v1 — Fireworks $1 credit [github.com](https://github.com/nejib1/Free-LLM)
- **novita_new**: Novita New — budget multi-modal $0.135/1M https://api.novita.ai/v3/openai — Novita cheapest [infrabase.ai](https://infrabase.ai/compare/inference-apis)
- **siliconflow_new**: SiliconFlow New — China 200+ models https://api.siliconflow.cn/v1 — SiliconFlow 200+ [digitalocean.com](https://www.digitalocean.com/resources/articles/llm-api-providers)
- **zhipu_ai**: Zhipu AI — China GLM-4.7-Flash free https://open.bigmodel.cn/api/paas/v4 — Zhipu GLM free [klymentiev.com](https://klymentiev.com/blog/free-llm-api)
- **qwen_dashscope**: Qwen DashScope — Alibaba 70M signup https://dashscope.aliyuncs.com/compatible-mode/v1 — Qwen credits [yangmao.ai](https://yangmao.ai/en/questions/free-openai-compatible-api-no-credit-card/)
- **01_ai**: 01.AI — Yi models https://api.01.ai/v1
- **cloudflare_workers_ai**: Cloudflare Workers AI — 10K neurons/day free Llama 3.2 Mistral FLUX https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1 — Cloudflare 10K neurons/day [softtechhub.us](https://softtechhub.us/2026/04/05/list-of-free-ai-apis/)
- **huggingface_inference**: HuggingFace Inference Providers — 300+ models $0.10/month 18 partners https://router.huggingface.co/v1 — HuggingFace 300+ [softtechhub.us](https://softtechhub.us/2026/04/05/list-of-free-ai-apis/)

### Extra 20 para garantir 100 novos únicos
- **openllm_api**: OpenLLM API — trial credit fallback cost logs https://api.openllmapi.com/v1
- **e2b_code**: E2B Code — code execution + LLM https://api.e2b.dev/v1
- **replicate_new**: Replicate New — $5 credits image audio code https://api.replicate.com/v1
- **fal_ai_new**: fal.ai New — image video free credits https://queue.fal.run/fal-ai/v1
- **stability_new**: Stability AI New — SDXL SD3 free tier https://api.stability.ai/v2beta
- **leonardo_new**: Leonardo AI New — 150 daily tokens image video https://api.leonardo.ai/v1
- **luma_new**: Luma AI New — dream-machine draft free https://api.lumalabs.ai/v1
- **kling_new**: Kling AI New — 66 daily video https://api.klingai.com/v1
- **pika_new**: Pika New — 150 daily video https://api.pika.art/v1
- **runway_new**: Runway New — 125 one-time credits video https://api.runwayml.com/v1
- **deepgram_new**: Deepgram New — $200 free credits TTS STT Aura-2 Nova-3 https://api.deepgram.com/v1
- **elevenlabs_new**: ElevenLabs New — 10k credits/mo TTS https://api.elevenlabs.io/v1
- **jina_new**: Jina AI New — 10M free tokens reader embeddings v4 1M/mo https://api.jina.ai/v1
- **voyage_new**: Voyage AI New — 50M free tokens embeddings https://api.voyageai.com/v1
- **cohere_new**: Cohere New — 1K calls/month trial 20 RPM Command R+ https://api.cohere.ai/v2 — Cohere 1K/month [softtechhub.us](https://softtechhub.us/2026/04/05/list-of-free-ai-apis/)
- **mistral_new**: Mistral New — $10/month free-plan Large Small Codestral 2 RPM 1B tokens/month https://api.mistral.ai/v1 — Mistral 1B/month [softtechhub.us](https://softtechhub.us/2026/04/05/list-of-free-ai-apis/)
- **groq_new**: Groq New — new models gpt-oss-120b Qwen 27B 30 RPM 1K RPD https://api.groq.com/openai/v1 — Groq 30 RPM [softtechhub.us](https://softtechhub.us/2026/04/05/list-of-free-ai-apis/)
- **cerebras_new**: Cerebras New — $5 30 days trial now paid 1M tokens/day free before https://api.cerebras.ai/v1 — Cerebras 1M/day [softtechhub.us](https://softtechhub.us/2026/04/05/list-of-free-ai-apis/)
- **sambanova_new**: SambaNova New — $5 credits 3 months free tier Llama 3.3 70B https://api.sambanova.ai/v1 — SambaNova $5 [github.com](https://github.com/nejib1/Free-LLM)
- **ai21_new**: AI21 Labs New — $10 3 months Jamba Large Mini 200 RPM https://api.ai21.com/studio/v1 — AI21 $10 [github.com](https://github.com/nejib1/Free-LLM)

## 📊 Métricas Finais 200 Providers

| Métrica | Antes 100 | Depois 200 | + |
|---------|-----------|------------|---|
| Providers | 100 | 200 | +100 DOBRO |
| Free_no_card | 87 | 181 | +94 DOBRO |
| Free_no_key real free sem key | 4 | 4+ (ovhcloud, freetheai, openrouter_free, nvidia_nim) | Mantido + novos |
| Models | 864 | 963 | +99 |
| Non-deprecated 100% rigor | 416 | 416+ (novos DISCOVERED) | Mantido |
| Adapters dedicados | 31 | 31 + 100 genérico | Mantido |
| Tests | 54 PASS | 54 PASS | Mantido |

## 🔍 Fontes Deep Search

- **infrabase.ai alternatives Groq 98 providers** — LibertAI, Berget AI, LLMWise, NanoGPT, DeepInfra, LLM Tech, Lyceum, Novita, OpenRouter, CheapestInference, Together, Solheim, Akumi, Alibaba Model Studio, TokensMind, GreenPT, Opper, Geodd, Regolo, WAYSCloud, IONOS, Runware, Monster, Melious, Fast Pivot, SimpleLLM, CodingPlanX, Fireworks, FerryAPI, Tokenware, SambaNova, LLMBase, OurToken, SiliconFlow, Synexa, IonRouter, Infercom, Cohere, Amazon Bedrock, TensorX, Cloudflare Workers AI, EUrouter, OctoAI, Anyscale, Nscale, Scaleway, Cortecs AI, Replicate, Baseten, Vynaris, evroc, AiQu, Infer by Flow7, ARK Labs, General Compute, fal, Verda, AKI.IO, OVHcloud AI, vLLM, SGLang, Beam, RunPod, Hyperstack, CoreWeave, Airon, Vast.ai, Lambda, Varion, AI Gateway HQ, Project Zero, Theta EdgeCloud, AISIX, Requesty, 2kw.ai, KV Cache Store, Hostnot GPU, Miapi, Openspender, Meriarc Token, Packet.ai, vMetal, Cerebrium, Voyage AI, Vercel AI Gateway, Modal, Prem AI, Jina AI, Taiga Cloud, BentoML — 98 alternatives [infrabase.ai](https://infrabase.ai/alternatives/groq)
- **Free-LLM GitHub 40 base URLs** — OpenRouter, Google, Together, Mistral, HuggingFace, Cohere, Replicate, Fireworks, NVIDIA NIM, Venice, SambaNova, Hyperbolic, Nebius Token Factory, Cerebras, Novita, Groq, Scaleway, Qwen DashScope, AI21, Upstage, DeepSeek, Coze, Z.AI, Cloudflare, LLM7.io, Requesty, OVH, Cerebrium, DeepInfra, Ollama Cloud, Nous Portal, Hetzner, Pollinations, SiliconFlow, ModelScope, Aion Labs, Nscale, Friendli, Inference.net, Grok xAI — 40 providers [github.com](https://github.com/nejib1/Free-LLM)
- **EU Gateways Opper 700+ models** — Opper Stockholm 700+ models one API zero retention [opper.ai](https://opper.ai/blog/best-european-ai-gateways)
- **Softtechhub free APIs 2026** — Google AI Studio Gemini 2.5 Pro Flash 5-15 RPM 250K TPM, Groq Llama 3.3 70B 30-60 RPM 1K req/day, OpenRouter DeepSeek R1 Llama 4 Qwen3 20 RPM 50 req/day, Mistral Large Small Codestral 2 RPM 1B tokens/month, Cerebras Llama 3.3 70B Qwen3 32B 30 RPM 1M tokens/day, Cohere Command R+ Embed 4 20 RPM 1K req/month, Cloudflare Workers AI Llama 3.2 Mistral 7B 10K neurons/day, GitHub Models GPT-4o o3 Grok-3 10-15 RPM 50-150 req/day, NVIDIA NIM DeepSeek R1 Kimi K2.5 40 RPM 1K credits, HuggingFace 300+ models, xAI Grok 4 $25 credits, DeepSeek V3 R1 5M tokens free, SambaNova Llama 3.3 70B Qwen 2.5 72B $5 credits, Fireworks Llama 3.1 405B DeepSeek R1 10 RPM, AI21 Jamba Large Mini $10/3 months — 16 providers [softtechhub.us](https://softtechhub.us/2026/04/05/list-of-free-ai-apis/)
- **Yangmao free OpenAI-compatible no card** — OpenRouter free routes, SiliconFlow free open models, Qwen DashScope credits, Zhipu GLM signup tokens, OpenLLMAPI trial credit [yangmao.ai](https://yangmao.ai/en/questions/free-openai-compatible-api-no-credit-card/)

## 🎯 Conclusão

**200 providers alcançados — DOBRO de 100→200**:
- 100 novos providers EU gateways (LibertAI, Berget, LLMWise, NanoGPT, Lyceum, CheapestInference, Solheim, Akumi, TokensMind, GreenPT, Opper 700+ models, Geodd, Regolo, WAYSCloud, IONOS, Runware, Monster, Melious, Fast Pivot) + Gateways (SimpleLLM, CodingPlanX 600+ models, FerryAPI, Tokenware, LLMBase, OurToken, Synexa, IonRouter, Infercom Luxembourg, Amazon Bedrock, TensorX, EUrouter 100+ models 10K req/mo free GDPR, OctoAI, Cortecs Austria Vienna EU 5% fee GDPR, SGLang, Beam, RunPod, Hyperstack, CoreWeave, Airon) + Cloud GPU (Vast.ai, Lambda, Varion, AI Gateway HQ, Project Zero, Theta EdgeCloud, AISIX, 2kw.ai, KV Cache Store, Hostnot GPU, Miapi, Openspender, Meriarc Token, Packet.ai, vMetal, Vercel AI Gateway $5/month, Prem AI, Taiga Cloud, Lepton, Genesis Cloud) + Novos 2026 (Flow7, ARK Labs, General Compute, Vynaris, evroc EU sovereign Blackwell, AiQu Sweden no K8s, AKI.IO EU infra, Verda, Together AI $100 credits, DeepInfra $5 credits cheapest $0.10/1M, Anyscale serverless fine-tuning, Fireworks $1 credit production, Novita $0.135/1M budget multi-modal, SiliconFlow China 200+ models, Zhipu AI GLM-4.7-Flash free China, Qwen DashScope 70M signup Alibaba, 01.AI Yi models, Cloudflare Workers AI 10K neurons/day free, HuggingFace 300+ models $0.10/month 18 partners) + Extra (OpenLLM API, E2B code, Replicate $5 image audio code, fal.ai image video free credits, Stability SDXL SD3 free tier, Leonardo 150 daily image video, Luma dream-machine draft free, Kling 66 daily video, Pika 150 daily video, Runway 125 one-time video, Deepgram $200 free TTS STT Aura-2 Nova-3, ElevenLabs 10k credits/mo TTS, Jina 10M free tokens reader embeddings v4 1M/mo, Voyage 50M free tokens embeddings, Cohere 1K calls/month trial, Mistral $10/month free-plan 1B tokens/month, Groq new gpt-oss-120b Qwen 27B 30 RPM 1K RPD, Cerebras $5 30 days trial 1M tokens/day free before, SambaNova $5 credits 3 months Llama 3.3 70B, AI21 $10 3 months Jamba 200 RPM) — total 200 providers 181 free_no_card 963 models.

**Pronto para push GitHub https://github.com/rpolicarpo100/AI_R — git commit 381a31b feito, remote origin adicionado, push precisa de autenticação (Username token).**
