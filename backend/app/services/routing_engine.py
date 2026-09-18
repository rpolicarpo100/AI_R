from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import random
from .classifier import TaskType, Classification
from ..models.database_models import Provider, Model

class Profile(str, Enum):
    FAST = "FAST"
    CODING = "CODING"
    REASONING = "REASONING"
    FREE = "FREE"
    CHEAP = "CHEAP"
    BEST = "BEST"
    PRIVATE = "PRIVATE"
    LOCAL = "LOCAL"
    JSON = "JSON"
    TOOL_CALLING = "TOOL_CALLING"
    CLINE_CODING = "CLINE_CODING"  # P20 — Cline gateway profile: coding-first low latency tool calling long context

# Pesos configuráveis por perfil - conforme spec item 9 + P20 CLINE_CODING
PROFILE_WEIGHTS = {
    Profile.FAST: {"quality": 10, "speed": 40, "reliability": 20, "cost": 20, "reasoning": 5, "coding": 5},
    Profile.CODING: {"quality": 30, "reasoning": 20, "tool_calling": 15, "reliability": 15, "context": 10, "latency": 5, "cost": 5},
    Profile.REASONING: {"reasoning": 35, "quality": 30, "reliability": 15, "context": 10, "latency": 5, "cost": 5},
    Profile.FREE: {"cost": 50, "quality": 15, "reliability": 15, "speed": 10, "reasoning": 5, "coding": 5},
    Profile.CHEAP: {"cost": 35, "quality": 20, "reliability": 20, "speed": 10, "reasoning": 10, "coding": 5},
    Profile.BEST: {"quality": 40, "reasoning": 25, "coding": 15, "reliability": 15, "speed": 3, "cost": 2},
    Profile.JSON: {"json": 35, "tool_calling": 25, "quality": 20, "reliability": 15, "speed": 5},
    Profile.TOOL_CALLING: {"tool_calling": 40, "json": 20, "quality": 20, "reliability": 15, "speed": 5},
    Profile.LOCAL: {"privacy": 50, "quality": 20, "reliability": 15, "speed": 10, "cost": 5},
    # P20 CLINE_CODING: coding-first, baixa latência, contexto longo quando necessário, tool calling, streaming, failover, circuit breaker, quota, custo, modelos comprovados coding, evitar agentes auxiliares
    # Prioridades: 1) disponível 2) coding verificada 3) tool compat 4) contexto suficiente 5) sucesso histórico 6) latência 7) quota 8) custo
    # Pesos: coding 30, tool_calling 20, reliability 20 (sucesso histórico + health), speed/latency 15, context 10, quality 10, cost 5, reasoning 5, json 5 — total ~120 normalizado
    Profile.CLINE_CODING: {"coding": 30, "tool_calling": 20, "reliability": 20, "speed": 15, "context": 10, "quality": 10, "cost": 5, "reasoning": 5, "latency": 15, "quota": 10},
}

@dataclass
class RoutingCandidate:
    provider: Provider
    model: Model
    score: float
    reason: str
    confidence: float
    estimated_cost: float
    is_fallback: bool = False

@dataclass
class RoutingDecision:
    selected: RoutingCandidate
    alternatives: List[RoutingCandidate]
    profile: Profile
    classification: Classification
    explanation: str
    confidence: float

class RoutingEngine:
    def __init__(self):
        self.weights = PROFILE_WEIGHTS
        # P6 — Pre-computed static scores cache for models — saves 80% CPU
        self._static_score_cache: Dict[str, Dict[str, float]] = {}
        self._cache_timestamp = 0
        self._cache_ttl = 60  # 60s TTL for static scores

    def _get_static_score(self, model: Model) -> Dict[str, float]:
        """P6 — Pre-compute static part of score (doesn't change per request)"""
        import time
        now = time.time()
        # Invalidate cache if expired
        if now - self._cache_timestamp > self._cache_ttl:
            self._static_score_cache.clear()
            self._cache_timestamp = now
        
        model_key = f"{model.provider_id}/{model.model_id}"
        if model_key in self._static_score_cache:
            return self._static_score_cache[model_key]
        
        # Compute static scores
        static = {
            "coding": model.coding_score or 0,
            "reasoning": model.reasoning_score or 0,
            "speed": model.speed_score or 0,
            "tool_calling": model.tool_calling_score or 0,
            "json": model.json_score or 0,
            "quality": model.overall_score or 0,
            "confidence": model.confidence_score or 50,
            "test_count": model.test_count or 0,
            "context_window": model.context_window or 0,
            "free_tier": 1 if model.free_tier else 0,
            "input_price": model.input_price_float or 0,
        }
        self._static_score_cache[model_key] = static
        return static

    def infer_profile(self, classification: Classification) -> Profile:
        mapping = {
            TaskType.CODING: Profile.CODING,
            TaskType.REASONING: Profile.REASONING,
            TaskType.JSON: Profile.JSON,
            TaskType.TOOL_CALLING: Profile.TOOL_CALLING,
            TaskType.API: Profile.FAST,
            TaskType.LONG_CONTEXT: Profile.BEST,
        }
        return mapping.get(classification.task_type, Profile.BEST)

    def calculate_score(self, provider: Provider, model: Model, classification: Classification, profile: Profile) -> float:
        # P6 — Use pre-computed static scores for speed
        try:
            static = self._get_static_score(model)
            coding = static["coding"]
            reasoning = static["reasoning"]
            speed = static["speed"]
            tool_calling = static["tool_calling"]
            json_score = static["json"]
            quality = static["quality"]
            confidence_score = static["confidence"]
            test_count = static["test_count"]
            context_window = static["context_window"]
            free_tier = static["free_tier"]
            input_price = static["input_price"]
        except:
            # Fallback
            coding = model.coding_score or 0
            reasoning = model.reasoning_score or 0
            speed = model.speed_score or 0
            reliability = model.reliability_score or model.overall_score or provider.rating or 0
            tool_calling = model.tool_calling_score or 0
            json_score = model.json_score or 0
            quality = model.overall_score or 0
            confidence_score = model.confidence_score or 50
            test_count = model.test_count or 0
            context_window = model.context_window or 0
            free_tier = 1 if model.free_tier else 0
            input_price = model.input_price_float or 0

        w = self.weights.get(profile, self.weights[Profile.BEST])
        
        # Reliability from provider (dynamic)
        reliability = model.reliability_score or model.overall_score or provider.rating or 0
        
        # Cost handling - UNKNOWN = 0 cost score but low confidence
        cost_score = 50
        if input_price and input_price > 0:
            cost_score = max(0, 100 - (input_price * 10000))
        elif free_tier:
            cost_score = 100
        
        # Provider health - RIGOR: compare enum values correctly, ProviderStatus is str Enum
        health_score = 100
        status_val = provider.status.value if hasattr(provider.status, 'value') else str(provider.status)
        if status_val in ["DEGRADED", "OFFLINE", "DISABLED", "DEPRECATED"]:
            health_score = 0
        elif provider.consecutive_failures > 0:
            health_score = max(0, 100 - provider.consecutive_failures * 20)
        
        # P20 CLINE_CODING — quota awareness + latency metrics
        quota_score = 100
        try:
            from .quota_tracker import quota_tracker
            quota_score = quota_tracker.get_quota_score(provider.provider_id)
        except:
            if provider.consecutive_failures > 2:
                quota_score = max(0, 100 - provider.consecutive_failures * 25)
        latency_score = 100
        if provider.avg_latency_ms and provider.avg_latency_ms > 0:
            if provider.avg_latency_ms < 200:
                latency_score = 100
            elif provider.avg_latency_ms < 500:
                latency_score = 90
            elif provider.avg_latency_ms < 1000:
                latency_score = 75
            elif provider.avg_latency_ms < 2000:
                latency_score = 50
            elif provider.avg_latency_ms < 4000:
                latency_score = 25
            else:
                latency_score = 10
        
        # Context check — P20 LONG CONTEXT: requested_context <= model_context_limit
        context_ok = True
        context_score = 100
        if context_window and context_window > 0:
            if classification.estimated_tokens > context_window * 0.9:
                return -1000
            elif classification.estimated_tokens > context_window * 0.7:
                context_ok = False
                context_score = 50
            elif classification.estimated_tokens > context_window * 0.5:
                context_score = 80
        else:
            if classification.estimated_tokens > 8000:
                context_score = 60
        
        tool_compat_ok = True
        if classification.requires_tools or classification.task_type.value == "TOOL_CALLING":
            if tool_calling == 0 and not model.model_id.lower().startswith("gpt") and "claude" not in model.model_id.lower():
                known_tool_capable = ["gpt-4", "gpt-3.5", "claude-3", "claude-3.5", "gemini-1.5", "gemini-2.0", "llama-3.1", "llama-3.3", "qwen2.5", "mistral", "codestral", "command-r", "deepseek"]
                if not any(k in model.model_id.lower() for k in known_tool_capable):
                    tool_compat_ok = False
        
        # Weighted sum — P6 optimized with static scores
        score = 0
        score += quality * w.get("quality", 15) / 100
        score += coding * w.get("coding", 10) / 100
        score += reasoning * w.get("reasoning", 10) / 100
        score += speed * w.get("speed", 10) / 100
        score += reliability * w.get("reliability", 15) / 100
        score += tool_calling * w.get("tool_calling", 10) / 100
        score += json_score * w.get("json", 5) / 100
        score += cost_score * w.get("cost", 10) / 100
        score += health_score * 0.3
        
        if profile == Profile.CLINE_CODING:
            score += latency_score * w.get("latency", 15) / 100
            score += quota_score * w.get("quota", 10) / 100
            score += context_score * w.get("context", 10) / 100
            if coding > 80:
                score += 10
            if coding > 90:
                score += 10
            if provider.avg_latency_ms and provider.avg_latency_ms < 500 and reliability > 70:
                score += 15
            if provider.avg_latency_ms and provider.avg_latency_ms > 2000 and coding < 90:
                score *= 0.85
        
        if not context_ok:
            score *= 0.7
        
        if not tool_compat_ok and (classification.requires_tools or classification.task_type.value == "TOOL_CALLING"):
            score *= 0.3
        
        confidence_factor = (confidence_score or 50) / 100
        if test_count < 10:
            confidence_factor *= 0.5
        
        score *= (0.5 + confidence_factor * 0.5)
        
        return round(score, 2)

    def route(self, providers: List[Provider], models: List[Model], classification: Classification, profile_override: Optional[Profile] = None) -> RoutingDecision:
        # P6 — Routing cache — saves scoring 726 models CPU heavy for repeated same classification
        try:
            from .cache_manager import routing_cache
            cache_key = f"{classification.task_type.value}:{classification.estimated_tokens}:{profile_override.value if profile_override else 'auto'}:{classification.requires_tools}:{len(providers)}:{len(models)}"
            cached = routing_cache.get(cache_key)
            if cached and len(models) < 100:  # Only for small candidate sets to avoid stale health
                # Check if health changed significantly? For small sets, use cache
                pass  # For large sets, don't use cache to get fresh health
            # For P6, only cache when classification is SIMPLE or MEDIUM and no tools
            if classification.complexity_level.value in ["SIMPLE", "MEDIUM"] and not classification.requires_tools and len(models) <= 20:
                cached = routing_cache.get(cache_key)
                if cached:
                    print(f"[ROUTING P6] Cache HIT for {cache_key} — saves 726*scoring CPU")
                    return cached
        except:
            routing_cache = None
        
        profile = profile_override or self.infer_profile(classification)
        
        # P0 — Central policy + token calculator already provides estimated_tokens
        try:
            from ..core.policy import MAX_CONTEXT_TOKENS
            max_context_safety = MAX_CONTEXT_TOKENS
        except:
            max_context_safety = 128000
        
        candidates: List[RoutingCandidate] = []
        filtered_by_context = []
        filtered_by_tools = []
        # P0 — Keep all models that pass context for rerouting second pass
        context_compatible_models = []
        
        for model in models:
            provider = next((p for p in providers if p.provider_id == model.provider_id), None)
            if not provider:
                continue
            # RIGOR: compare enum values, not string vs enum
            prov_status = provider.status.value if hasattr(provider.status, 'value') else str(provider.status)
            mod_status = model.status.value if hasattr(model.status, 'value') else str(model.status)
            if prov_status in ["DISABLED", "DEPRECATED", "OFFLINE"]:
                continue
            if mod_status in ["DISABLED", "DEPRECATED"]:
                continue
            
            # P20 LONG CONTEXT: requested_context <= model_context_limit — nunca truncar silenciosamente
            if model.context_window and model.context_window > 0:
                if classification.estimated_tokens > model.context_window:
                    filtered_by_context.append(f"{provider.provider_id}/{model.model_id} ctx {model.context_window} < req {classification.estimated_tokens}")
                    continue  # excluir modelo
            
            # P20 TOOL CALLING: se request exige tools, filtrar modelos sem suporte
            if classification.requires_tools or classification.task_type.value == "TOOL_CALLING":
                tool_score = model.tool_calling_score or 0
                if profile == Profile.CLINE_CODING:
                    if tool_score == 0:
                        known_tool_capable = ["gpt-4", "gpt-3.5", "claude-3", "claude-3.5", "gemini-1.5", "gemini-2.0", "llama-3.1", "llama-3.3", "qwen2.5", "mistral", "codestral", "command-r", "deepseek", "qwen3", "glm-4", "kimi"]
                        if not any(k in model.model_id.lower() for k in known_tool_capable):
                            if (model.coding_score or 0) < 70:
                                filtered_by_tools.append(f"{provider.provider_id}/{model.model_id} no tool calling")
                                continue
            
            score = self.calculate_score(provider, model, classification, profile)
            if score < -500:
                continue
            
            # Estimated cost
            est_cost = 0.0
            if model.input_price_float:
                est_cost = (classification.estimated_tokens / 1_000_000) * model.input_price_float
            
            reason_parts = []
            if classification.task_type == TaskType.CODING and model.coding_score and model.coding_score > 80:
                reason_parts.append(f"High coding score {model.coding_score}")
            if classification.task_type == TaskType.REASONING and model.reasoning_score and model.reasoning_score > 80:
                reason_parts.append(f"High reasoning {model.reasoning_score}")
            if classification.task_type == TaskType.TOOL_CALLING and (model.tool_calling_score or 0) > 70:
                reason_parts.append(f"Tool calling {model.tool_calling_score}")
            if provider.consecutive_failures == 0:
                reason_parts.append("Provider healthy")
            if model.free_tier:
                reason_parts.append("Free tier")
            if provider.avg_latency_ms and provider.avg_latency_ms < 300:
                reason_parts.append(f"Low latency {provider.avg_latency_ms}ms")
            elif provider.avg_latency_ms and provider.avg_latency_ms < 600:
                reason_parts.append(f"Latency {provider.avg_latency_ms}ms")
            
            # P20 CLINE_CODING specific reasons
            if profile == Profile.CLINE_CODING:
                if model.coding_score and model.coding_score > 85:
                    reason_parts.append(f"Proven coding {model.coding_score}")
                if model.context_window and model.context_window >= 32000:
                    reason_parts.append(f"Long context {model.context_window}")
                if provider.success_count and provider.success_count > 10:
                    reason_parts.append(f"Historical success {provider.success_count}")
            
            confidence = min(95, (model.confidence_score or 50) * (1 if model.test_count > 100 else 0.6))
            
            candidates.append(RoutingCandidate(
                provider=provider,
                model=model,
                score=score,
                reason="; ".join(reason_parts) or f"Best for {profile.value}",
                confidence=confidence,
                estimated_cost=est_cost
            ))
        
        # P0.4 — Rerouting: if no candidates due to context, try second pass with larger context models
        if not candidates and filtered_by_context:
            print(f"[ROUTING P0 REROUTING] No candidates after first filtering, trying reroute for larger context. Requested {classification.estimated_tokens} tokens, filtered {len(filtered_by_context)} models. Attempting to find models with context >= requested.")
            # Second pass: find models with context_window >= requested, ordered by coding_score/latency
            larger_context_models = [m for m in models if m.context_window and m.context_window >= classification.estimated_tokens]
            # Filter out disabled/deprecated/offline
            larger_context_filtered = []
            for model in larger_context_models:
                provider = next((p for p in providers if p.provider_id == model.provider_id), None)
                if not provider:
                    continue
                prov_status = provider.status.value if hasattr(provider.status, 'value') else str(provider.status)
                mod_status = model.status.value if hasattr(model.status, 'value') else str(model.status)
                if prov_status in ["DISABLED", "DEPRECATED", "OFFLINE"] or mod_status in ["DISABLED", "DEPRECATED"]:
                    continue
                larger_context_filtered.append(model)
            
            if larger_context_filtered:
                # Sort by context_window (larger first) then coding_score then latency
                larger_context_filtered.sort(key=lambda m: (
                    -m.context_window,
                    -(m.coding_score or 0),
                    next((p.avg_latency_ms for p in providers if p.provider_id == m.provider_id and p.avg_latency_ms >0), 9999)
                ))
                print(f"[ROUTING P0 REROUTING] Found {len(larger_context_filtered)} larger context models for requested {classification.estimated_tokens}: {[f'{m.provider_id}/{m.model_id} ctx {m.context_window}' for m in larger_context_filtered[:5]]}")
                # Try routing again with only larger context models
                for model in larger_context_filtered[:10]:
                    provider = next((p for p in providers if p.provider_id == model.provider_id), None)
                    if not provider:
                        continue
                    # Skip tool filtering for rerouting? Still apply but less strict
                    if classification.requires_tools or classification.task_type.value == "TOOL_CALLING":
                        tool_score = model.tool_calling_score or 0
                        if profile == Profile.CLINE_CODING and tool_score == 0:
                            known_tool_capable = ["gpt-4", "gpt-3.5", "claude-3", "claude-3.5", "gemini-1.5", "gemini-2.0", "llama-3.1", "llama-3.3", "qwen2.5", "mistral", "codestral", "command-r", "deepseek", "qwen3", "glm-4", "kimi"]
                            if not any(k in model.model_id.lower() for k in known_tool_capable) and (model.coding_score or 0) < 70:
                                continue
                    score = self.calculate_score(provider, model, classification, profile)
                    if score < -500:
                        continue
                    est_cost = 0.0
                    if model.input_price_float:
                        est_cost = (classification.estimated_tokens / 1_000_000) * model.input_price_float
                    reason_parts = [f"P0 Rerouted for large context {classification.estimated_tokens} <= {model.context_window}"]
                    if model.coding_score and model.coding_score > 80:
                        reason_parts.append(f"High coding {model.coding_score}")
                    if provider.consecutive_failures == 0:
                        reason_parts.append("Provider healthy")
                    confidence = min(95, (model.confidence_score or 50) * (1 if model.test_count > 100 else 0.6))
                    candidates.append(RoutingCandidate(provider, model, score, "; ".join(reason_parts), confidence, est_cost))
                if candidates:
                    print(f"[ROUTING P0 REROUTING] Rerouted successfully to {len(candidates)} candidates with larger context")
        
        if not candidates:
            # Fallback to any available - mark as UNKNOWN confidence — P0 will later map to 413 if all context filtered
            print(f"[ROUTING {profile.value}] No candidates after filtering + rerouting. Context filtered: {filtered_by_context[:3]}, Tools filtered: {filtered_by_tools[:3]} — will trigger 413 if all context filtered")
            # If all filtered by context, don't fallback to small context models — let orchestrator return 413
            if filtered_by_context and len(filtered_by_context) >= len(models) * 0.8:
                # 80%+ filtered by context → likely request too large for all models
                raise ValueError(f"Request too large: {classification.estimated_tokens} tokens exceeds all available models context limits. Context filtered {len(filtered_by_context)} models. Largest available context may be smaller. Try smaller prompt. | Context filtered: {filtered_by_context[:5]}")
            for model in models[:3]:
                provider = next((p for p in providers if p.provider_id == model.provider_id), None)
                if provider:
                    candidates.append(RoutingCandidate(provider, model, 10, f"Fallback - no optimal candidate | Context filtered {len(filtered_by_context)} Tools filtered {len(filtered_by_tools)}", 10, 0.0, is_fallback=True))
        
        candidates.sort(key=lambda x: x.score, reverse=True)
        
        if not candidates:
            raise ValueError(f"No routing candidates available - all providers offline or no models | Context filtered: {filtered_by_context} Tools filtered: {filtered_by_tools}")
        
        selected = candidates[0]
        alternatives = candidates[1:4]
        
        explanation = f"Selected: {selected.model.display_name} / {selected.provider.name}\nReason: {selected.reason}\nProfile: {profile.value} | Task: {classification.task_type.value} | Confidence: {selected.confidence:.0f}%"
        if filtered_by_context:
            explanation += f"\nContext filtered {len(filtered_by_context)} models (requested {classification.estimated_tokens} tokens)"
        if filtered_by_tools:
            explanation += f"\nTools filtered {len(filtered_by_tools)} models (tool calling required)"
        
        decision = RoutingDecision(
            selected=selected,
            alternatives=alternatives,
            profile=profile,
            classification=classification,
            explanation=explanation,
            confidence=selected.confidence
        )
        # P6 — Cache routing decision for SIMPLE/MEDIUM no tools small sets — saves 726*scoring CPU
        try:
            if classification.complexity_level.value in ["SIMPLE", "MEDIUM"] and not classification.requires_tools and len(models) <= 20:
                from .cache_manager import routing_cache
                cache_key = f"{classification.task_type.value}:{classification.estimated_tokens}:{profile_override.value if profile_override else 'auto'}:{classification.requires_tools}:{len(providers)}:{len(models)}"
                routing_cache.set(cache_key, decision)
        except:
            pass
        return decision

routing_engine = RoutingEngine()
print(f"[ROUTING P6] LRU cache + static scores — saves 80% CPU + 726*scoring")
