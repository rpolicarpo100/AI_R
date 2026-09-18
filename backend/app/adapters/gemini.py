import time
from typing import List, Dict
from .base import BaseAdapter, AdapterResponse

class GeminiAdapter(BaseAdapter):
    provider_id = "gemini"
    
    async def chat_completion(self, model_id: str, messages: List[Dict], api_key: str, base_url: str, **kwargs) -> AdapterResponse:
        start = time.time()
        try:
            import google.generativeai as genai
        except ImportError:
            raise Exception("PROVIDER_ERROR: google-generativeai not installed")
        
        genai.configure(api_key=api_key)
        
        # Convert OpenAI messages to Gemini format
        # Gemini uses system instruction + history
        system_prompt = ""
        gemini_history = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                system_prompt += content + "\n"
            elif role == "user":
                gemini_history.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                gemini_history.append({"role": "model", "parts": [content]})
        
        if not gemini_history:
            raise Exception("INVALID_REQUEST: No user message")
        
        # Last message is the prompt
        last = gemini_history[-1]
        history = gemini_history[:-1]
        
        try:
            model = genai.GenerativeModel(
                model_name=model_id,
                system_instruction=system_prompt if system_prompt else None
            )
            chat = model.start_chat(history=history)
            response = await chat.send_message_async(last["parts"][0])
            content = response.text
            # Estimate tokens - Gemini API returns usage in newer versions
            input_tokens = len(str(messages)) // 4
            output_tokens = len(content) // 4
        except Exception as e:
            err_str = str(e).lower()
            if "429" in err_str or "quota" in err_str or "rate" in err_str:
                raise Exception(f"RATE_LIMIT: {str(e)[:500]}")
            elif "404" in err_str or "not found" in err_str:
                raise Exception(f"MODEL_NOT_FOUND: {str(e)[:500]}")
            elif "401" in err_str or "api key" in err_str:
                raise Exception(f"AUTH_FAILED: {str(e)[:500]}")
            else:
                raise Exception(f"PROVIDER_ERROR: {str(e)[:500]}")
        
        latency = int((time.time() - start) * 1000)
        return AdapterResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency,
            model_used=model_id,
            provider_used="gemini",
            raw_response={"text": content},
            finish_reason="stop"
        )
    
    async def health_check(self, api_key: str, base_url: str) -> bool:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            models = genai.list_models()
            return True
        except:
            return False
