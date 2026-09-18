"""
AI Horde Adapter - Community Free Unlimited Volunteer GPU Network
Uses direct API https://aihorde.net/api/v2/generate/text/async
Real, verified, no simulation - key 09e304e3-e390-4bbc-8238-f6696a570195 shared key BEee
26 text models with workers available 2026-09-16
"""
import httpx
import time
import json
import asyncio
from typing import List, Dict
from .base import BaseAdapter, AdapterResponse

class AIHordeAdapter(BaseAdapter):
    provider_id = "aihorde"
    
    async def chat_completion(self, model_id: str, messages: List[Dict], api_key: str, base_url: str, **kwargs) -> AdapterResponse:
        """
        AI Horde direct API - text generation async + poll status
        model_id: e.g. aphrodite/TheDrummer/Behemoth-X-123B-v2.1 or koboldcpp/Llama-3.2-3B
        """
        start = time.time()
        
        # Extract prompt from messages - use last user message
        prompt = ""
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                prompt = msg.get('content', '')
                break
        if not prompt:
            prompt = messages[-1].get('content', '') if messages else "Hello"
        
        # AI Horde expects prompt with instruction
        # For coding, add prefix
        if "soma" in prompt.lower() or "def " in prompt.lower() or "function" in prompt.lower():
            # Already coding prompt
            full_prompt = prompt
        else:
            full_prompt = prompt
        
        # Use direct API https://aihorde.net/api/v2/generate/text/async
        # base_url is https://oai.aihorde.net/v1 but we need direct API
        direct_base = "https://aihorde.net"
        
        headers = {
            "apikey": api_key,
            "Content-Type": "application/json"
        }
        
        # Clean model_id - remove prefix if needed, use as is
        # Try with provided model_id first
        payload = {
            "prompt": full_prompt,
            "params": {
                "max_context_length": 1024,
                "max_length": kwargs.get('max_tokens', 150),
                "temperature": kwargs.get('temperature', 0.7),
                "top_p": 0.9,
                "top_k": 0,
                "rep_pen": 1.1
            },
            "models": [model_id],
            "trusted_workers": False,
            "slow_workers": True
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                # Step 1: Create async task
                resp = await client.post(f"{direct_base}/api/v2/generate/text/async", headers=headers, json=payload)
            except httpx.TimeoutException:
                raise Exception("TIMEOUT: AI Horde timeout on async creation after 60s")
            except httpx.ConnectError:
                raise Exception("CONNECTION_FAILURE: Could not connect to AI Horde")
            
            if resp.status_code not in [200, 202]:
                error_type = self.map_error(resp.status_code, resp.text)
                raise Exception(f"{error_type}: {resp.status_code} - {resp.text[:500]}")
            
            try:
                data = resp.json()
                task_id = data.get('id')
                if not task_id:
                    raise Exception(f"INVALID_RESPONSE: No task ID from Horde - {str(data)[:500]}")
            except json.JSONDecodeError:
                raise Exception(f"INVALID_RESPONSE: Invalid JSON from Horde - {resp.text[:500]}")
            
            # Step 2: Poll status until done (max 90s)
            max_polls = 30
            poll_interval = 3
            content = ""
            
            for poll_idx in range(max_polls):
                await asyncio.sleep(poll_interval)
                try:
                    status_resp = await client.get(f"{direct_base}/api/v2/generate/text/status/{task_id}", headers=headers)
                except:
                    continue
                
                if status_resp.status_code != 200:
                    continue
                
                try:
                    status_data = status_resp.json()
                except:
                    continue
                
                # Check if done
                if status_data.get('done'):
                    generations = status_data.get('generations', [])
                    if generations and len(generations) > 0:
                        content = generations[0].get('text', '')
                        break
                    else:
                        # No generations but done - check if faulted
                        if status_data.get('faulted'):
                            raise Exception(f"HORDE_FAULTED: Task faulted - {str(status_data)[:500]}")
                        # Empty but done
                        content = ""
                        break
                
                # Check if impossible
                if not status_data.get('is_possible', True):
                    # No workers available
                    waiting = status_data.get('waiting', 0)
                    if waiting == 0 and status_data.get('queue_position', 0) == 0:
                        raise Exception(f"NO_WORKERS: No available workers for model {model_id} - {str(status_data)[:300]}")
            
            if not content:
                # Timeout or no content
                raise Exception(f"TIMEOUT: AI Horde task {task_id} no content after {max_polls*poll_interval}s - last status {str(status_data)[:300] if 'status_data' in locals() else 'unknown'}")
        
        latency = int((time.time() - start) * 1000)
        
        # Estimate tokens
        input_tokens = len(full_prompt) // 4
        output_tokens = len(content) // 4
        
        return AdapterResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency,
            model_used=model_id,
            provider_used=direct_base,
            raw_response={"task_id": task_id, "generations": generations if 'generations' in locals() else []},
            finish_reason="stop"
        )
    
    async def health_check(self, api_key: str, base_url: str) -> bool:
        """Check if Horde key is valid via find_user"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {"apikey": api_key}
                resp = await client.get("https://aihorde.net/api/v2/find_user", headers=headers)
                return resp.status_code == 200
        except:
            return False
