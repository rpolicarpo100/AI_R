import httpx
import time
import json
from typing import List, Dict
from .base import BaseAdapter, AdapterResponse

class OllamaAdapter(BaseAdapter):
    provider_id = "ollama"
    
    async def chat_completion(self, model_id: str, messages: List[Dict], api_key: str, base_url: str, **kwargs) -> AdapterResponse:
        start = time.time()
        # Ollama: base_url like http://localhost:11434 or https://ollama.com/api
        # P8 - Handle both /api and without
        base = base_url.rstrip('/')
        if base.endswith('/api'):
            url = f"{base}/chat"
        else:
            url = f"{base}/api/chat"
        
        # Convert messages to Ollama format (same as OpenAI but without system special handling)
        payload = {
            "model": model_id,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
            }
        }
        
        headers = {"Content-Type": "application/json"}
        if api_key and api_key != "ollama":
            headers["Authorization"] = f"Bearer {api_key}"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                resp = await client.post(url, headers=headers, json=payload)
            except httpx.ConnectError:
                raise Exception("CONNECTION_FAILURE: Cannot connect to Ollama - is it running?")
            except httpx.TimeoutException:
                raise Exception("TIMEOUT: Ollama timeout after 120s")
            
            if resp.status_code != 200:
                raise Exception(f"{self.map_error(resp.status_code, resp.text)}: {resp.text[:500]}")
            
            try:
                data = resp.json()
                content = data.get("message", {}).get("content", "") or data.get("response", "")
            except Exception as e:
                raise Exception(f"INVALID_RESPONSE: {str(e)}")
        
        latency = int((time.time() - start) * 1000)
        return AdapterResponse(
            content=content,
            input_tokens=data.get("prompt_eval_count", len(str(messages))//4),
            output_tokens=data.get("eval_count", len(content)//4),
            latency_ms=latency,
            model_used=model_id,
            provider_used=base_url,
            raw_response=data,
            finish_reason="stop"
        )
    
    async def health_check(self, api_key: str, base_url: str) -> bool:
        base = base_url.rstrip('/')
        if base.endswith('/api'):
            url = f"{base}/tags"
        else:
            url = f"{base}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                return resp.status_code == 200
        except:
            return False
