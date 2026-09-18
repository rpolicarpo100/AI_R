"""
CHAT ENHANCER - Agentes de apoio ao chat para otimizar respostas/entendimento
Funcionais, coerentes, precisas, rigorosas, reais, profissionais, contestam, criticam, não ficam na primeira tentativa, terceiro olho aberto
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re
import time

class ChatEnhancer:
    def __init__(self):
        self.version = "1.0"
    
    def analyze_intent(self, prompt: str, history: List[Dict] = None) -> Dict:
        """
        Intent Analyzer Agent - analisa intenção profunda, detecta ambiguidade, extrai requisitos
        """
        prompt_lower = prompt.lower()
        
        # Detectar tipo de pedido
        intent_type = "generic"
        if any(kw in prompt_lower for kw in ["cria", "função", "function", "código", "code"]):
            intent_type = "code_generation"
        elif any(kw in prompt_lower for kw in ["api", "endpoint", "fastapi", "crud"]):
            intent_type = "api_creation"
        elif any(kw in prompt_lower for kw in ["react", "componente", "frontend", "nextjs"]):
            intent_type = "frontend_creation"
        elif any(kw in prompt_lower for kw in ["explica", "como funciona", "o que é", "explain"]):
            intent_type = "explanation"
        elif any(kw in prompt_lower for kw in ["valida", "nif", "teste", "test"]):
            intent_type = "validation_utility"
        elif any(kw in prompt_lower for kw in ["sql", "query", "database"]):
            intent_type = "database"
        
        # Detectar ambiguidades
        ambiguities = []
        if len(prompt.split()) < 5:
            ambiguities.append("Prompt muito curto - pode faltar contexto")
        if intent_type == "code_generation" and "python" not in prompt_lower and "javascript" not in prompt_lower and "typescript" not in prompt_lower:
            ambiguities.append("Linguagem não especificada - assumir Python?")
        if "valida" in prompt_lower and "nif" in prompt_lower and "como" not in prompt_lower:
            ambiguities.append("NIF: precisa validar checksum? Formato? Apenas tamanho?")
        if intent_type == "api_creation" and "endpoint" not in prompt_lower and "crud" not in prompt_lower:
            ambiguities.append("API: quais endpoints? CRUD completo? Autenticação?")
        
        # Extrair requisitos
        requirements = []
        if "apenas código" in prompt_lower or "só código" in prompt_lower or "only code" in prompt_lower:
            requirements.append("Apenas código, sem explicação")
        if "test" in prompt_lower or "teste" in prompt_lower:
            requirements.append("Incluir testes")
        if "docstring" in prompt_lower or "comentário" in prompt_lower or "documenta" in prompt_lower:
            requirements.append("Incluir docstring/comentários")
        if "fastapi" in prompt_lower:
            requirements.append("Usar FastAPI, Pydantic, async")
        if "react" in prompt_lower:
            requirements.append("Usar React, hooks, TypeScript")
        
        # Se não tem requisitos claros, sugerir essenciais
        if not requirements and intent_type in ["code_generation", "api_creation", "validation_utility"]:
            requirements.extend(["Código funcional", "Tratar edge cases", "Sem invenção, APIs reais"])
        
        return {
            "intent_type": intent_type,
            "ambiguities": ambiguities,
            "requirements": requirements,
            "confidence": 90 if not ambiguities else 60,
            "should_clarify": len(ambiguities) > 1,
            "agent": "intent-analyzer-01",
            "skill": "intent_analysis"
        }
    
    def optimize_prompt(self, prompt: str, intent: Dict, history: List[Dict] = None) -> Dict:
        """
        Prompt Optimizer Agent - otimiza prompt, clarifica, adiciona contexto, requisitos, edge cases, terceiro olho
        """
        original = prompt
        intent_type = intent.get("intent_type", "generic")
        requirements = intent.get("requirements", [])
        
        optimized = original
        improvements = []
        
        # Adicionar contexto baseado no tipo
        if intent_type == "validation_utility" and "nif" in prompt.lower():
            if "checksum" not in prompt.lower() and "9 dígitos" not in prompt.lower():
                optimized += "\n\nRequisitos essenciais (terceiro olho): Validar NIF português: 9 dígitos, primeiro dígito não 0, checksum mod 11 (módulo 11), retornar bool, tratar None/vazio, com docstring, testes básicos. Apenas código funcional, sem invenção."
                improvements.append("Adicionado requisitos NIF: 9 dígitos, checksum mod 11, edge cases")
        
        if intent_type == "api_creation" and "fastapi" in prompt.lower():
            if "crud" in prompt.lower() and "model" not in prompt.lower():
                optimized += "\n\nRequisitos: Usar FastAPI, Pydantic models, endpoints CRUD (GET list, GET by id, POST create, PUT update, DELETE), com validação, tratamento erros, docstring, sem simulação, APIs reais."
                improvements.append("Adicionado requisitos API: Pydantic, CRUD, validação, tratamento erros")
        
        if intent_type == "code_generation":
            if "apenas código" not in prompt.lower():
                optimized += "\n\nInstrução: Gere apenas código funcional, preciso, rigoroso, real, profissional. Trate edge cases, sem invenção, APIs reais, com boas práticas. Se usar bibliotecas, verifique que existem."
                improvements.append("Adicionado instrução rigor: funcional, edge cases, sem invenção")
        
        # Terceiro olho - sempre adicionar verificações
        third_eye_checks = []
        if intent_type in ["code_generation", "api_creation", "validation_utility"]:
            third_eye_checks.extend([
                "Verificar se código funciona (não só parece funcionar)",
                "Tratar edge cases: None, vazio, formato inválido, limites",
                "Não inventar APIs, bibliotecas, endpoints - usar reais",
                "Adicionar docstring e comentários essenciais",
                "Pensar em segurança: validação input, sem injection"
            ])
        
        # Se prompt muito curto, expandir
        if len(original.split()) < 10:
            optimized = f"{original}\n\nContexto: Usuário quer {intent_type}. Requisitos: {', '.join(requirements)}. Terceiro olho: {', '.join(third_eye_checks[:3])}"
            improvements.append("Prompt expandido por ser curto - adicionado contexto e terceiro olho")
        
        return {
            "original_prompt": original,
            "optimized_prompt": optimized,
            "improvements": improvements,
            "third_eye_checks": third_eye_checks,
            "intent": intent,
            "agent": "prompt-optimizer-01",
            "skill": "prompt_engineering",
            "should_use_optimized": len(improvements) > 0
        }
    
    def critique_response(self, original_prompt: str, optimized_prompt: str, response: str, intent: Dict) -> Dict:
        """
        Critic Agent - critica resposta, funcional, coerente, precisa, rigorosa, real, profissional, contesta, terceiro olho, não fica na primeira tentativa
        """
        response_lower = response.lower()
        prompt_lower = original_prompt.lower()
        
        issues = []
        suggestions = []
        score = 100
        
        # Funcionalidade - CRÍTICO: sem código para pedido código = falha grave, terceiro olho não aceita
        if intent.get("intent_type") in ["code_generation", "validation_utility", "api_creation"]:
            if "def " not in response and "class " not in response and "function" not in response_lower and "import" not in response_lower:
                issues.append("❌ Não parece conter código funcional - apenas explicação?")
                score -= 40  # mais crítico - era 30, agora 40 para garantir retry
            if "nif" in prompt_lower and "def " in response:
                # Verificar NIF específico
                if "len" not in response_lower or "9" not in response:
                    issues.append("⚠️ NIF: não verifica tamanho 9 dígitos?")
                    score -= 15
                if "mod" not in response_lower and "checksum" not in response_lower and "% 11" not in response and "%11" not in response:
                    issues.append("⚠️ NIF: não verifica checksum mod 11? Terceiro olho: validação incompleta")
                    score -= 20
                    suggestions.append("Adicionar validação checksum mod 11: soma ponderada dos 8 primeiros dígitos, mod 11, compara com 9º dígito")
        
        # Coerência
        if len(response.strip()) < 20:
            issues.append("❌ Resposta muito curta, incoerente")
            score -= 40
        
        # Precisão
        if "apenas código" in prompt_lower and len(response.split()) > 200 and "```" not in response:
            issues.append("⚠️ Pediu apenas código mas resposta tem muito texto explicativo")
            score -= 10
        
        # Rigor - sem invenção
        # Detectar possível invenção: bibliotecas que não existem, APIs inventadas
        invented_patterns = [
            "import super_nif_validator",  # biblioteca inventada
            "from magic_validation import",
        ]
        for pattern in invented_patterns:
            if pattern in response_lower:
                issues.append(f"❌ Possível invenção: {pattern} - biblioteca não existe, marcar UNKNOWN")
                score -= 25
        
        # Real - código deve ser executável
        if "def " in response and "return" not in response_lower:
            issues.append("⚠️ Função sem return? Pode não ser funcional")
            score -= 15
        
        # Profissionalismo
        if intent.get("intent_type") == "code_generation":
            if "docstring" not in response_lower and '"""' not in response and "'''" not in response:
                suggestions.append("Adicionar docstring para profissionalismo")
                score -= 5
            if "try" not in response_lower and "except" not in response_lower and len(response) > 200:
                suggestions.append("Adicionar tratamento erros try/except para robustez")
        
        # Terceiro olho - edge cases, segurança, performance
        third_eye = []
        if intent.get("intent_type") in ["code_generation", "validation_utility"]:
            if "none" not in response_lower and "null" not in response_lower and "vazio" not in prompt_lower:
                third_eye.append("Terceiro olho: tratar None, vazio, tipo errado - edge cases")
            if "segurança" not in response_lower and "valid" in response_lower:
                third_eye.append("Terceiro olho: validação input para segurança - injection?")
            if len(response) > 500 and "performance" not in response_lower:
                third_eye.append("Terceiro olho: considerar performance para inputs grandes")
        
        # Decidir se deve retry - CRÍTICO: não ficar na primeira tentativa, terceiro olho aberto
        should_retry = (score < 70 and len(issues) >= 1) or (score < 80 and len(issues) > 1)
        retry_prompt = ""
        if should_retry:
            retry_prompt = f"Resposta anterior teve score {score}/100 com issues: {', '.join(issues[:3])}. Melhorar: {', '.join(suggestions[:2])}. Terceiro olho: {', '.join(third_eye[:2])}. Tente novamente de forma funcional, coerente, precisa, rigorosa, real, profissional."
        
        return {
            "score": max(0, score),
            "issues": issues,
            "suggestions": suggestions,
            "third_eye": third_eye,
            "should_retry": should_retry,
            "retry_prompt": retry_prompt,
            "is_functional": score >= 70,
            "is_coherent": len(issues) == 0 or score >= 60,
            "is_precise": score >= 75,
            "is_rigorous": "invenção" not in ' '.join(issues).lower(),
            "is_professional": score >= 80,
            "agent": "critic-01",
            "skill": "response_critique",
            "critique": f"Score {score}/100 - Issues: {len(issues)}, Suggestions: {len(suggestions)}, Terceiro olho: {len(third_eye)} checks"
        }
    
    def review_code(self, code: str, language: str = "python", prompt: str = "") -> Dict:
        """
        Code Reviewer Agent - revisa código, segurança, performance, boas práticas
        """
        issues = []
        suggestions = []
        score = 100
        
        code_lower = code.lower()
        
        # Segurança
        if "eval(" in code or "exec(" in code:
            issues.append("🔴 CRÍTICO Segurança: eval/exec perigoso - risco injection")
            score -= 40
        if "api_key" in code_lower and "=" in code and ("sk-" in code or "api_" in code_lower):
            issues.append("🔴 CRÍTICO Segurança: API key hardcoded no código - usar .env")
            score -= 35
        if "password" in code_lower and "=" in code and len(code) < 500:
            issues.append("⚠️ Segurança: password hardcoded?")
            score -= 20
        
        # Performance
        if "for " in code and "for " in code[code.find("for ")+4:]:
            suggestions.append("Performance: loops aninhados - considerar otimização")
        if language == "python" and "import" in code and code.count("import") > 10:
            suggestions.append("Performance: muitos imports - verificar necessários")
        
        # Boas práticas
        if language == "python":
            if "def " in code and '"""' not in code and "'''" not in code:
                suggestions.append("Boas práticas: adicionar docstring")
            if "print(" in code and "def " in code:
                suggestions.append("Boas práticas: evitar print em função, usar return ou logging")
        
        # Funcional
        if "def " in code and code.count("def ") > 0 and "return" not in code_lower:
            issues.append("⚠️ Função sem return - funcional?")
            score -= 15
        
        return {
            "score": max(0, score),
            "issues": issues,
            "suggestions": suggestions,
            "is_secure": len([i for i in issues if "CRÍTICO" in i]) == 0,
            "is_performant": score >= 70,
            "is_professional": score >= 80,
            "agent": "code-reviewer-01",
            "skill": "code_review"
        }
    
    def enhance_chat(self, prompt: str, history: List[Dict] = None) -> Dict:
        """
        Fluxo completo: intent -> optimize -> retorna enhanced prompt com trace de agentes
        """
        start = time.time()
        
        # 1. Intent Analysis
        intent = self.analyze_intent(prompt, history)
        
        # 2. Prompt Optimization
        optimized = self.optimize_prompt(prompt, intent, history)
        
        latency = int((time.time() - start) * 1000)
        
        return {
            "original_prompt": prompt,
            "optimized_prompt": optimized["optimized_prompt"] if optimized["should_use_optimized"] else prompt,
            "should_use_optimized": optimized["should_use_optimized"],
            "intent": intent,
            "optimization": optimized,
            "agents_trace": [
                {"agent": "intent-analyzer-01", "skill": "intent_analysis", "result": intent},
                {"agent": "prompt-optimizer-01", "skill": "prompt_engineering", "result": optimized}
            ],
            "latency_ms": latency,
            "recommendation": "Usar optimized_prompt se should_use_optimized, senão original. Terceiro olho sempre ativo."
        }
    
    def enhance_response(self, original_prompt: str, optimized_prompt: str, response: str, intent: Dict) -> Dict:
        """
        Após gerar resposta, critica, revisa, sugere retry se necessário - terceiro olho, não fica na primeira tentativa
        """
        start = time.time()
        
        # 1. Critique
        critique = self.critique_response(original_prompt, optimized_prompt, response, intent)
        
        # 2. Code Review se tem código
        code_review = None
        if "def " in response or "class " in response or "import " in response:
            # Extrair código dos blocos
            code_blocks = re.findall(r'```(?:python|javascript|typescript)?\n(.*?)```', response, re.DOTALL)
            if code_blocks:
                code = code_blocks[0]
                code_review = self.review_code(code, "python", original_prompt)
        
        latency = int((time.time() - start) * 1000)
        
        return {
            "critique": critique,
            "code_review": code_review,
            "should_retry": critique["should_retry"],
            "retry_prompt": critique["retry_prompt"],
            "final_score": critique["score"],
            "is_ready": critique["score"] >= 70,
            "agents_trace": [
                {"agent": "critic-01", "skill": "response_critique", "result": critique},
                {"agent": "code-reviewer-01", "skill": "code_review", "result": code_review} if code_review else None,
                {"agent": "rigor-checker-01", "skill": "rigor_check", "result": {"honest": critique["is_rigorous"]}}
            ],
            "latency_ms": latency
        }

chat_enhancer = ChatEnhancer()
