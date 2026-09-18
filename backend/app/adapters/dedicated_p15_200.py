
"""
P15 200 — Dedicated Adapters for 100 new providers — EU gateways + China + novos
"""

from .openai_compat import OpenAICompatibleAdapter

class OpperAdapter(OpenAICompatibleAdapter):
    """Opper Sweden 700+ models one API zero retention"""
    provider_id = "opper"

class EUrouterAdapter(OpenAICompatibleAdapter):
    """EUrouter Netherlands 100+ models 10K req/mo free GDPR"""
    provider_id = "eurouter"

class CodingPlanXAdapter(OpenAICompatibleAdapter):
    """CodingPlanX 600+ models OpenAI Anthropic"""
    provider_id = "codingplanx"

class DeepInfraNewAdapter(OpenAICompatibleAdapter):
    """DeepInfra New $5 credits cheapest $0.10/1M"""
    provider_id = "deepinfra_new"

class NovitaNewAdapter(OpenAICompatibleAdapter):
    """Novita New $0.135/1M budget multi-modal"""
    provider_id = "novita_new"

class SiliconFlowNewAdapter(OpenAICompatibleAdapter):
    """SiliconFlow New China 200+ models"""
    provider_id = "siliconflow_new"

class ZhipuAIAdapter(OpenAICompatibleAdapter):
    """Zhipu AI China GLM-4.7-Flash free"""
    provider_id = "zhipu_ai"

class QwenDashScopeAdapter(OpenAICompatibleAdapter):
    """Qwen DashScope Alibaba 70M signup"""
    provider_id = "qwen_dashscope"

class CloudflareWorkersAIAdapter(OpenAICompatibleAdapter):
    """Cloudflare Workers AI 10K neurons/day free"""
    provider_id = "cloudflare_workers_ai"

class HuggingFaceInferenceAdapter(OpenAICompatibleAdapter):
    """HuggingFace Inference 300+ models $0.10/month 18 partners"""
    provider_id = "huggingface_inference"

class LibertAIAdapter(OpenAICompatibleAdapter):
    provider_id = "libertai"

class BergetAIAdapter(OpenAICompatibleAdapter):
    provider_id = "berget_ai"

class LLMWiseAdapter(OpenAICompatibleAdapter):
    provider_id = "llmwise"

class CortecsAIAdapter(OpenAICompatibleAdapter):
    """Cortecs Austria Vienna LLM Router EU 5% fee GDPR"""
    provider_id = "cortecs_ai"

class TogetherAINewAdapter(OpenAICompatibleAdapter):
    provider_id = "together_ai_new"

class FireworksNewAdapter(OpenAICompatibleAdapter):
    provider_id = "fireworks_new"

class AnyscaleNewAdapter(OpenAICompatibleAdapter):
    provider_id = "anyscale_new"

class EvrocAdapter(OpenAICompatibleAdapter):
    """evroc EU sovereign Blackwell GPUs"""
    provider_id = "evroc"

class AkumiAdapter(OpenAICompatibleAdapter):
    """Akumi Netherlands PII pseudonymization"""
    provider_id = "akumi"

class GreenPTAdapter(OpenAICompatibleAdapter):
    """GreenPT French Scaleway GDPR"""
    provider_id = "greenpt"

DEDICATED_ADAPTERS_P15_200 = {
    "opper": OpperAdapter(),
    "eurouter": EUrouterAdapter(),
    "codingplanx": CodingPlanXAdapter(),
    "deepinfra_new": DeepInfraNewAdapter(),
    "novita_new": NovitaNewAdapter(),
    "siliconflow_new": SiliconFlowNewAdapter(),
    "zhipu_ai": ZhipuAIAdapter(),
    "qwen_dashscope": QwenDashScopeAdapter(),
    "cloudflare_workers_ai": CloudflareWorkersAIAdapter(),
    "huggingface_inference": HuggingFaceInferenceAdapter(),
    "libertai": LibertAIAdapter(),
    "berget_ai": BergetAIAdapter(),
    "llmwise": LLMWiseAdapter(),
    "cortecs_ai": CortecsAIAdapter(),
    "together_ai_new": TogetherAINewAdapter(),
    "fireworks_new": FireworksNewAdapter(),
    "anyscale_new": AnyscaleNewAdapter(),
    "evroc": EvrocAdapter(),
    "akumi": AkumiAdapter(),
    "greenpt": GreenPTAdapter(),
}

print(f"[P15 200] Dedicated adapters loaded — {len(DEDICATED_ADAPTERS_P15_200)} new for 200 providers")
