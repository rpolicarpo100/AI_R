import httpx
import time
import json
from typing import List, Dict
from .base import BaseAdapter, AdapterResponse

class OpenAICompatibleAdapter(BaseAdapter):
    provider_id = "openai_compat"
    
    async def chat_completion(self, model_id: str, messages: List[Dict], api_key: str, base_url: str, **kwargs) -> AdapterResponse:
        start = time.time()
        url = f"{base_url.rstrip('/')}/chat/completions"
        
        headers = {
            "Content-Type": "application/json"
        }
        if api_key and api_key.strip():
            headers["Authorization"] = f"Bearer {api_key}"
        if kwargs.get("extra_headers"):
            headers.update(kwargs["extra_headers"])
        
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2000),
        }
        
        if kwargs.get("tools"):
            payload["tools"] = kwargs["tools"]
        if kwargs.get("tool_choice"):
            payload["tool_choice"] = kwargs["tool_choice"]
        if kwargs.get("response_format"):
            payload["response_format"] = kwargs["response_format"]
        for extra_param in ["top_p", "top_k", "presence_penalty", "frequency_penalty", "stop", "seed", "user"]:
            if kwargs.get(extra_param) is not None:
                payload[extra_param] = kwargs[extra_param]
        
        timeout = kwargs.get("timeout", 60.0)
        if isinstance(timeout, (int, float)) and timeout > 0:
            timeout_val = float(timeout)
        else:
            timeout_val = 60.0
        timeout_val = min(timeout_val, 120.0)
        
        resp = None
        data = None
        use_pooled = True
        provider_id_for_quota = kwargs.get("provider_id") or self.provider_id
        
        try:
            from ..services.http_client import get_pooled_client
            provider_id = kwargs.get("provider_id") or self.provider_id
            client = await get_pooled_client(provider_id=provider_id, base_url=base_url, timeout=timeout_val, use_http2=True)
            try:
                resp = await client.post(url, headers=headers, json=payload, timeout=httpx.Timeout(timeout_val, read=timeout_val))
            except httpx.TimeoutException:
                raise Exception("TIMEOUT: Provider timeout after 60s")
            except httpx.ConnectError:
                raise Exception("CONNECTION_FAILURE: Could not connect to provider")
        except Exception as e:
            if resp is None:
                err_str = str(e)
                if "TIMEOUT" in err_str or "CONNECTION_FAILURE" in err_str or "HTTP_" in err_str or "RATE_LIMIT" in err_str or "AUTH_FAILED" in err_str:
                    raise
                print(f"[HTTP POOL] Fallback to non-pooled for {self.provider_id}/{model_id}: {e}")
                use_pooled = False
                async with httpx.AsyncClient(timeout=timeout_val) as fallback_client:
                    try:
                        resp = await fallback_client.post(url, headers=headers, json=payload)
                    except httpx.TimeoutException:
                        raise Exception("TIMEOUT: Provider timeout after 60s")
                    except httpx.ConnectError:
                        raise Exception("CONNECTION_FAILURE: Could not connect to provider")
        
        if resp is None:
            raise Exception("PROVIDER_ERROR: No response from provider")
        
        # P2.2 — Quota tracking
        try:
            from ..services.quota_tracker import quota_tracker
            quota_tracker.record_request(provider_id_for_quota, dict(resp.headers), resp.status_code)
        except Exception as e:
            print(f"[QUOTA P2.2] Record failed {e}")
        
        if resp.status_code != 200:
            retry_after = None
            try:
                from ..services.circuit_breaker import circuit_breaker
                retry_after = circuit_breaker.parse_retry_after(dict(resp.headers))
                if retry_after:
                    print(f"[RETRY_AFTER P0.5] {self.provider_id} 429 Retry-After {retry_after}s from headers {dict(resp.headers).get('Retry-After')}")
            except Exception as e:
                print(f"[RETRY_AFTER P0.5] Parse failed {e}")
            error_type = self.map_error(resp.status_code, resp.text)
            if retry_after:
                raise Exception(f"{error_type}: {resp.status_code} - {resp.text[:500]} - Retry-After: {retry_after}")
            else:
                raise Exception(f"{error_type}: {resp.status_code} - {resp.text[:500]}")
        
        try:
            data = resp.json()
        except json.JSONDecodeError:
            raise Exception(f"INVALID_RESPONSE: Invalid JSON from provider - {resp.text[:500]}")
        
        try:
            choice = data["choices"][0]
            message = choice.get("message", {})
            content = message.get("content") or ""
            tool_calls = message.get("tool_calls")
            finish_reason = choice.get("finish_reason", "stop")
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", len(str(messages))//4)
            output_tokens = usage.get("completion_tokens", len(content)//4)
        except (KeyError, IndexError) as e:
            raise Exception(f"INVALID_RESPONSE: Unexpected format {str(e)} - {str(data)[:500]}")
        
        latency = int((time.time() - start) * 1000)
        return AdapterResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency,
            model_used=model_id,
            provider_used=base_url,
            raw_response=data,
            finish_reason=finish_reason,
            tool_calls=tool_calls
        )
    
    async def chat_completion_stream(self, model_id: str, messages: List[Dict], api_key: str, base_url: str, **kwargs):
        """
        P21 TRUE STREAMING + P22 pooled client + P2.2 quota tracking
        """
        url = f"{base_url.rstrip('/')}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        if api_key and api_key.strip():
            headers["Authorization"] = f"Bearer {api_key}"
        if kwargs.get("extra_headers"):
            headers.update(kwargs["extra_headers"])
        
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2000),
            "stream": True,
        }
        
        if kwargs.get("tools"):
            payload["tools"] = kwargs["tools"]
        if kwargs.get("tool_choice"):
            payload["tool_choice"] = kwargs["tool_choice"]
        if kwargs.get("response_format"):
            payload["response_format"] = kwargs["response_format"]
        for extra_param in ["top_p", "top_k", "presence_penalty", "frequency_penalty", "stop", "seed", "user"]:
            if kwargs.get(extra_param) is not None:
                payload[extra_param] = kwargs[extra_param]
        
        timeout_val = min(float(kwargs.get("timeout", 60.0)), 120.0)
        provider_id_for_quota = kwargs.get("provider_id") or self.provider_id
        
        try:
            from ..services.http_client import get_pooled_client
            provider_id = kwargs.get("provider_id") or self.provider_id
            client = await get_pooled_client(provider_id=provider_id, base_url=base_url, timeout=timeout_val, use_http2=True)
            try:
                async with client.stream("POST", url, headers=headers, json=payload, timeout=httpx.Timeout(timeout_val, read=timeout_val)) as resp:
                    try:
                        from ..services.quota_tracker import quota_tracker
                        quota_tracker.record_request(provider_id_for_quota, dict(resp.headers), resp.status_code)
                    except:
                        pass
                    if resp.status_code != 200:
                        error_text = await resp.aread()
                        retry_after = None
                        try:
                            from ..services.circuit_breaker import circuit_breaker
                            retry_after = circuit_breaker.parse_retry_after(dict(resp.headers))
                        except:
                            pass
                        error_type = self.map_error(resp.status_code, error_text.decode()[:500] if isinstance(error_text, bytes) else str(error_text)[:500])
                        err_msg = f"{error_type}: {resp.status_code} - {error_text.decode()[:500] if isinstance(error_text, bytes) else str(error_text)[:500]}"
                        if retry_after:
                            err_msg += f" - Retry-After: {retry_after}"
                        raise Exception(err_msg)
                    
                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                yield {"type": "done"}
                                break
                            try:
                                chunk_data = json.loads(data_str)
                                yield {"type": "chunk", "data": chunk_data}
                            except json.JSONDecodeError:
                                continue
                return
            except httpx.TimeoutException:
                yield {"type": "error", "error": "TIMEOUT: Provider timeout during streaming"}
                raise Exception("TIMEOUT: Provider timeout during streaming")
            except httpx.ConnectError:
                yield {"type": "error", "error": "CONNECTION_FAILURE: Could not connect during streaming"}
                raise Exception("CONNECTION_FAILURE: Could not connect during streaming")
        except Exception as e:
            err_str = str(e)
            if any(x in err_str for x in ["TIMEOUT", "CONNECTION_FAILURE", "RATE_LIMIT", "AUTH_FAILED", "MODEL_NOT_FOUND", "HTTP_"]):
                if "TIMEOUT" not in err_str and "CONNECTION_FAILURE" not in err_str:
                    yield {"type": "error", "error": err_str[:500]}
                raise
            
            print(f"[HTTP POOL] Streaming fallback to non-pooled for {self.provider_id}/{model_id}: {e}")
            async with httpx.AsyncClient(timeout=httpx.Timeout(timeout_val, read=timeout_val)) as fallback_client:
                try:
                    async with fallback_client.stream("POST", url, headers=headers, json=payload) as resp:
                        try:
                            from ..services.quota_tracker import quota_tracker
                            quota_tracker.record_request(provider_id_for_quota, dict(resp.headers), resp.status_code)
                        except:
                            pass
                        if resp.status_code != 200:
                            error_text = await resp.aread()
                            retry_after = None
                            try:
                                from ..services.circuit_breaker import circuit_breaker
                                retry_after = circuit_breaker.parse_retry_after(dict(resp.headers))
                            except:
                                pass
                            error_type = self.map_error(resp.status_code, error_text.decode()[:500] if isinstance(error_text, bytes) else str(error_text)[:500])
                            err_msg = f"{error_type}: {resp.status_code} - {error_text.decode()[:500] if isinstance(error_text, bytes) else str(error_text)[:500]}"
                            if retry_after:
                                err_msg += f" - Retry-After: {retry_after}"
                            raise Exception(err_msg)
                        
                        async for line in resp.aiter_lines():
                            if not line:
                                continue
                            if line.startswith("data: "):
                                data_str = line[6:].strip()
                                if data_str == "[DONE]":
                                    yield {"type": "done"}
                                    break
                                try:
                                    chunk_data = json.loads(data_str)
                                    yield {"type": "chunk", "data": chunk_data}
                                except json.JSONDecodeError:
                                    continue
                except httpx.TimeoutException:
                    yield {"type": "error", "error": "TIMEOUT: Provider timeout during streaming"}
                    raise Exception("TIMEOUT: Provider timeout during streaming")
                except httpx.ConnectError:
                    yield {"type": "error", "error": "CONNECTION_FAILURE: Could not connect during streaming"}
                    raise Exception("CONNECTION_FAILURE: Could not connect during streaming")
    
    async def health_check(self, api_key: str, base_url: str) -> bool:
        url = f"{base_url.rstrip('/')}/models"
        headers = {}
        if api_key and api_key.strip():
            headers["Authorization"] = f"Bearer {api_key}"
        try:
            from ..services.http_client import get_shared_client
            client = await get_shared_client(timeout=10.0)
            resp = await client.get(url, headers=headers)
            return resp.status_code in [200, 401, 403]
        except:
            try:
                async with httpx.AsyncClient(timeout=10.0) as fallback_client:
                    resp = await fallback_client.get(url, headers=headers)
                    return resp.status_code in [200, 401, 403]
            except:
                return False

class GroqAdapter(OpenAICompatibleAdapter):
    provider_id = "groq"

class CerebrasAdapter(OpenAICompatibleAdapter):
    provider_id = "cerebras"

class OpenRouterAdapter(OpenAICompatibleAdapter):
    provider_id = "openrouter"
    
    async def chat_completion(self, model_id: str, messages: List[Dict], api_key: str, base_url: str, **kwargs) -> AdapterResponse:
        extra = {
            "HTTP-Referer": "https://ai-provider-os.local",
            "X-Title": "AI Provider OS"
        }
        if kwargs.get("extra_headers"):
            extra.update(kwargs["extra_headers"])
        kwargs["extra_headers"] = extra
        kwargs["provider_id"] = "openrouter"
        return await super().chat_completion(model_id, messages, api_key, base_url, **kwargs)
    
    async def chat_completion_stream(self, model_id: str, messages: List[Dict], api_key: str, base_url: str, **kwargs):
        extra = {
            "HTTP-Referer": "https://ai-provider-os.local",
            "X-Title": "AI Provider OS"
        }
        if kwargs.get("extra_headers"):
            extra.update(kwargs["extra_headers"])
        kwargs["extra_headers"] = extra
        kwargs["provider_id"] = "openrouter"
        async for chunk in super().chat_completion_stream(model_id, messages, api_key, base_url, **kwargs):
            yield chunk

class MistralAdapter(OpenAICompatibleAdapter):
    provider_id = "mistral"

class GitHubModelsAdapter(OpenAICompatibleAdapter):
    provider_id = "github_models"

class HuggingFaceAdapter(OpenAICompatibleAdapter):
    provider_id = "huggingface"
