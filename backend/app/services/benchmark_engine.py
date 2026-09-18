"""
BENCHMARK ENGINE - REAL, MEDIDO, SEM INVENÇÃO
Categorias: CODING, REASONING, STRUCTURED OUTPUT, INSTRUCTION FOLLOWING, RELIABILITY, PERFORMANCE
Mede comportamento real, nunca inventa.
"""
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone
import time
import asyncio
import json
import statistics

@dataclass
class BenchmarkTest:
    test_id: str
    category: str  # CODING, REASONING, JSON, TOOL_CALLING, INSTRUCTION, SPEED, RELIABILITY
    name: str
    prompt: str
    expected_contains: List[str] = None  # validação simples
    expected_json_schema: Dict = None
    timeout: int = 30
    retries: int = 1

# Suite real, pequena mas funcional - conforme spec item 12
BENCHMARK_SUITE: List[BenchmarkTest] = [
    # CODING
    BenchmarkTest("coding-01", "CODING", "gerar função python", "Crie uma função Python chamada soma(a,b) que retorna a soma. Apenas código, sem explicação.", ["def soma", "return"], timeout=20),
    BenchmarkTest("coding-02", "CODING", "corrigir bug", "Corrija este código Python:\n\ndef divide(a,b):\n    return a / b\n\nEle falha quando b=0. Corrija.", ["def divide", "if b"], timeout=20),
    BenchmarkTest("coding-03", "CODING", "React component", "Crie um componente React funcional chamado Counter com useState que incrementa um contador. Use TypeScript.", ["Counter", "useState"], timeout=25),
    BenchmarkTest("coding-04", "CODING", "SQL query", "Escreva SQL para selecionar todos os utilizadores com idade > 18 da tabela users, ordenados por nome.", ["SELECT", "users", "WHERE"], timeout=15),
    BenchmarkTest("coding-05", "CODING", "API FastAPI", "Crie um endpoint FastAPI GET /health que retorna {\"status\":\"ok\"}.", ["FastAPI", "/health"], timeout=20),
    
    # REASONING
    BenchmarkTest("reasoning-01", "REASONING", "lógica simples", "Se todos os A são B e alguns B são C, podemos concluir que alguns A são C? Explique passo a passo.", ["não", "alguns"], timeout=20),
    BenchmarkTest("reasoning-02", "REASONING", "planeamento", "Decomponha a tarefa 'Criar loja online' em 5 passos lógicos ordenados por dependência.", ["1", "2"], timeout=20),
    
    # STRUCTURED OUTPUT / JSON
    BenchmarkTest("json-01", "JSON", "JSON válido", "Retorne apenas JSON válido: {\"nome\": \"João\", \"idade\": 30}. Sem texto extra.", ["João", "30"], timeout=15),
    BenchmarkTest("json-02", "JSON", "schema", "Retorne JSON com schema: {\"users\": [{\"id\": number, \"name\": string}]} com 2 users.", ["users", "id", "name"], timeout=15),
    
    # INSTRUCTION FOLLOWING
    BenchmarkTest("instr-01", "INSTRUCTION", "cumprimento exacto", "Responda APENAS com a palavra 'OK', nada mais.", ["OK"], timeout=10),
    
    # SPEED / RELIABILITY - mede performance, não qualidade
    BenchmarkTest("speed-01", "SPEED", "resposta rápida", "Diga olá.", ["olá", "Olá", "ola"], timeout=10),
]

@dataclass
class BenchmarkResultMeasured:
    test_id: str
    category: str
    success: bool
    score: float  # 0-100
    latency_ms: int
    time_to_first_token_ms: int  # UNKNOWN se não streaming
    tokens_per_second: float
    input_tokens: int
    output_tokens: int
    error: str = None
    raw_output: str = None
    timestamp: str = None
    evidence: Dict = None

class BenchmarkEngine:
    def __init__(self, adapter, provider, model):
        self.adapter = adapter
        self.provider = provider
        self.model = model
    
    async def run_single(self, test: BenchmarkTest, api_key: str) -> BenchmarkResultMeasured:
        start = time.time()
        try:
            # Chama adapter real
            resp = await self.adapter.chat_completion(
                model_id=self.model.model_id,
                messages=[{"role": "user", "content": test.prompt}],
                api_key=api_key,
                base_url=self.provider.base_url,
                temperature=0.1,
                max_tokens=500
            )
            latency = int((time.time() - start) * 1000)
            
            # Validação
            output = resp.content or ""
            success = True
            score = 0
            
            if test.expected_contains:
                found = sum(1 for exp in test.expected_contains if exp.lower() in output.lower())
                score = (found / len(test.expected_contains)) * 100
                success = found >= len(test.expected_contains) * 0.5  # 50% threshold
            else:
                success = len(output.strip()) > 0
                score = 100 if success else 0
            
            # JSON validation
            if test.category == "JSON":
                try:
                    json.loads(output.strip().replace("```json","").replace("```","").strip())
                    score = max(score, 80)
                except:
                    # Tenta extrair JSON
                    if "{" in output and "}" in output:
                        score = max(score * 0.5, 20)
                    else:
                        success = False
                        score = 0
            
            # Tokens/s
            total_tokens = resp.output_tokens or len(output)//4
            tps = (total_tokens / (latency/1000)) if latency > 0 else 0
            
            return BenchmarkResultMeasured(
                test_id=test.test_id,
                category=test.category,
                success=success,
                score=score,
                latency_ms=latency,
                time_to_first_token_ms=0,  # UNKNOWN without streaming
                tokens_per_second=round(tps, 2),
                input_tokens=resp.input_tokens,
                output_tokens=resp.output_tokens,
                raw_output=output[:2000],
                timestamp=datetime.now(timezone.utc).isoformat(),
                evidence={
                    "provider": self.provider.provider_id,
                    "model": self.model.model_id,
                    "base_url": self.provider.base_url,
                    "source": "measured",
                    "source_confidence": "measured"
                }
            )
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            err = str(e)[:500]
            # Classifica erro
            error_type = "UNKNOWN"
            if "429" in err or "RATE_LIMIT" in err:
                error_type = "RATE_LIMIT"
            elif "TIMEOUT" in err:
                error_type = "TIMEOUT"
            elif "MODEL_NOT_FOUND" in err:
                error_type = "MODEL_NOT_FOUND"
            
            return BenchmarkResultMeasured(
                test_id=test.test_id,
                category=test.category,
                success=False,
                score=0,
                latency_ms=latency,
                time_to_first_token_ms=0,
                tokens_per_second=0,
                input_tokens=0,
                output_tokens=0,
                error=f"{error_type}: {err}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                evidence={"source": "measured", "error_type": error_type}
            )
    
    async def run_suite(self, api_key: str, categories: List[str] = None) -> Dict[str, Any]:
        categories = categories or ["CODING", "REASONING", "JSON", "SPEED"]
        tests = [t for t in BENCHMARK_SUITE if t.category in categories]
        
        results: List[BenchmarkResultMeasured] = []
        for test in tests:
            result = await self.run_single(test, api_key)
            results.append(result)
            # Pequeno delay para não hit rate limit
            await asyncio.sleep(0.5)
        
        # Agrega por categoria - rigoroso com empty handling
        by_category = {}
        for cat in categories:
            cat_results = [r for r in results if r.category == cat]
            if not cat_results:
                continue
            try:
                avg_score = statistics.mean([r.score for r in cat_results]) if cat_results else 0
            except:
                avg_score = 0
            success_rate = len([r for r in cat_results if r.success]) / len(cat_results) * 100 if cat_results else 0
            try:
                avg_latency = statistics.mean([r.latency_ms for r in cat_results]) if cat_results else 0
            except:
                avg_latency = 0
            tps_list = [r.tokens_per_second for r in cat_results if r.tokens_per_second > 0]
            try:
                avg_tps = statistics.mean(tps_list) if tps_list else 0
            except:
                avg_tps = 0
            
            by_category[cat] = {
                "avg_score": round(avg_score, 1),
                "success_rate": round(success_rate, 1),
                "avg_latency_ms": round(avg_latency, 1),
                "avg_tokens_per_second": round(avg_tps, 1),
                "test_count": len(cat_results),
                "results": [r.__dict__ for r in cat_results]
            }
        
        # Overall - rigoroso
        try:
            overall_score = statistics.mean([r.score for r in results]) if results else 0
        except:
            overall_score = 0
        overall_success = len([r for r in results if r.success]) / len(results) * 100 if results else 0
        
        return {
            "provider_id": self.provider.provider_id,
            "model_id": self.model.model_id,
            "display_name": self.model.display_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "measured",
            "source_confidence": "measured",
            "total_tests": len(results),
            "overall_score": round(overall_score, 1),
            "overall_success_rate": round(overall_success, 1),
            "by_category": by_category,
            "evidence": "All scores from real API calls, no invention",
            "confidence": min(95, len(results) * 10)  # 10 tests = 100% confidence capped at 95
        }

benchmark_engine = BenchmarkEngine
