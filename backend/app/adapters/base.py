from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class AdapterResponse:
    content: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    model_used: str
    provider_used: str
    raw_response: Dict[str, Any] = None
    finish_reason: str = "stop"
    # P20 CLINE_CODING — tool calling support
    tool_calls: Optional[List[Dict[str, Any]]] = None

class BaseAdapter(ABC):
    provider_id: str = "base"
    
    @abstractmethod
    async def chat_completion(self, model_id: str, messages: List[Dict], api_key: str, base_url: str, **kwargs) -> AdapterResponse:
        pass
    
    @abstractmethod
    async def health_check(self, api_key: str, base_url: str) -> bool:
        pass

    def map_error(self, status_code: int, body: str) -> str:
        mapping = {
            401: "AUTH_FAILED",
            403: "FORBIDDEN",
            404: "MODEL_NOT_FOUND",
            408: "TIMEOUT",
            409: "CONFLICT",
            429: "RATE_LIMIT",
            500: "PROVIDER_ERROR",
            502: "BAD_GATEWAY",
            503: "SERVICE_UNAVAILABLE",
            504: "GATEWAY_TIMEOUT",
        }
        return mapping.get(status_code, f"HTTP_{status_code}")
