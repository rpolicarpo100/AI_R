"""
Brainstorming Service — Vertente de brainstorming antes de construir ou responder
Objetivo: fazer algo mais perto do objetivo final, não ficar na 1ª tentativa
- Antes de responder: brainstorm 3-5 interpretações possíveis do que usuário realmente quer
- Antes de construir: brainstorm 3-5 abordagens arquiteturais, tradeoffs, MVP vs full, template mais próximo
- Você no centro, human override, terceiro olho aberto, contesta, critica
"""

from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime, timezone

# Templates disponíveis para brainstorming de apps
TEMPLATES = {
    "landing-page": {"name": "Landing Page Moderna", "type": "frontend", "best_for": "marketing, produto, startup, conversão"},
    "dashboard-saas": {"name": "Dashboard SaaS", "type": "fullstack", "best_for": "SaaS, métricas, admin, 200 providers"},
    "ecommerce": {"name": "E-commerce Minimal", "type": "frontend", "best_for": "loja, produtos, carrinho, checkout"},
    "blog-md": {"name": "Blog Markdown", "type": "frontend", "best_for": "blog, conteúdo, markdown"},
    "chat-app": {"name": "Chat App Real-time", "type": "fullstack", "best_for": "chat, mensagens, real-time, AI, 200 providers"},
    "portfolio": {"name": "Portfolio Pessoal", "type": "frontend", "best_for": "portfolio, pessoal, projetos"},
    "api-gateway": {"name": "API Gateway 200 Providers", "type": "api", "best_for": "API, gateway, routing, OpenAI-compatible"},
    "fastapi-crud": {"name": "FastAPI CRUD API", "type": "api", "best_for": "API, CRUD, backend"},
    "nextjs-app": {"name": "Next.js 14 App Router", "type": "frontend", "best_for": "Next.js, App Router, fullstack"},
    "python-fastapi-react": {"name": "Fullstack FastAPI + React", "type": "fullstack", "best_for": "fullstack, FastAPI, React"},
}

class BrainstormingService:
    def __init__(self):
        self.version = "1.0 — Brainstorming antes de construir/responder — mais perto do objetivo final"
    
    def brainstorm_before_respond(self, user_prompt: str, chat_history: List[Dict] = None, profile: str = "BEST") -> Dict[str, Any]:
        """
        Brainstorm antes de responder — 3-5 interpretações possíveis do que usuário realmente quer
        Para ficar mais perto do objetivo final, não ficar na 1ª tentativa
        """
        chat_history = chat_history or []
        
        # Análise de ambiguidade
        ambiguities = []
        if len(user_prompt.split()) < 5:
            ambiguities.append("Prompt muito curto — pode ter múltiplas interpretações")
        if "?" not in user_prompt and len(user_prompt) < 20:
            ambiguities.append("Sem pergunta explícita — intenção pode ser construir, explicar, ou melhorar")
        if any(word in user_prompt.lower() for word in ["app", "site", "cria", "faz", "build"]):
            ambiguities.append("Pode ser pedido para construir app/site — precisa brainstorming de templates")
        
        # 3-5 interpretações possíveis
        interpretations = []
        
        # Interpretação 1: Literal
        interpretations.append({
            "id": 1,
            "type": "literal",
            "interpretation": f"Usuário quer exatamente: {user_prompt}",
            "confidence": 60,
            "pros": ["Direto, sem assumir", "Rápido"],
            "cons": ["Pode não ser o objetivo final", "Pode faltar contexto"],
            "closest_to_final": 50
        })
        
        # Interpretação 2: Objetivo final mais profundo
        if any(word in user_prompt.lower() for word in ["app", "site", "landing", "dashboard", "ecommerce", "blog", "chat", "portfolio", "api"]):
            # É pedido de construção
            interpretations.append({
                "id": 2,
                "type": "construir_app",
                "interpretation": f"Usuário quer construir app/site — objetivo final é ter algo funcional, não só código. Precisa escolher template mais próximo, definir MVP, features essenciais",
                "confidence": 80,
                "pros": ["Foca no objetivo final funcional", "Considera templates 13 disponíveis", "Pensa em MVP vs full"],
                "cons": ["Precisa mais perguntas para confirmar", "Mais tempo"],
                "closest_to_final": 85,
                "suggested_templates": self._suggest_templates(user_prompt),
                "mvp": "Versão mínima funcional com 1-2 features core",
                "full": "Versão completa com todas features + deploy"
            })
        else:
            # É pergunta/explicação
            interpretations.append({
                "id": 2,
                "type": "objetivo_profundo",
                "interpretation": f"Objetivo final por trás de '{user_prompt}' pode ser: entender conceito, resolver problema, ou tomar decisão. Não só responder, mas ajudar a atingir objetivo",
                "confidence": 70,
                "pros": ["Vai além da pergunta literal", "Mais útil", "Terceiro olho aberto"],
                "cons": ["Pode assumir demais"],
                "closest_to_final": 75
            })
        
        # Interpretação 3: Alternativa crítica
        interpretations.append({
            "id": 3,
            "type": "alternativa_critica",
            "interpretation": f"Alternativa crítica: e se '{user_prompt}' não for a melhor forma de atingir objetivo? Existe abordagem melhor? Contesta, critica, terceiro olho",
            "confidence": 50,
            "pros": ["Contesta, não fica na 1ª tentativa", "Pode sugerir melhor caminho", "Crítico e pragmático"],
            "cons": ["Pode ser visto como não cooperativo se mal explicado"],
            "closest_to_final": 70,
            "critical_question": f"Qual é o objetivo final por trás de '{user_prompt}'? O que queres realmente alcançar?"
        })
        
        # Interpretação 4: Se for ambíguo, adiciona
        if ambiguities:
            interpretations.append({
                "id": 4,
                "type": "clarificacao",
                "interpretation": "Prompt ambíguo — precisa clarificação antes de construir/responder para ficar mais perto do objetivo final",
                "confidence": 40,
                "pros": ["Evita construir coisa errada", "Você no centro, human override"],
                "cons": ["Adiciona 1 turno extra"],
                "closest_to_final": 90,
                "questions": [
                    "Qual é o objetivo final? O que queres ter no fim?",
                    "É para construir app/site ou só responder pergunta?",
                    "Qual é o público alvo e o problema que resolve?",
                    "Tens preferência de template ou tech stack?"
                ],
                "ambiguities": ambiguities
            })
        
        # Escolhe a mais próxima do objetivo final
        best = max(interpretations, key=lambda x: x['closest_to_final'])
        
        return {
            "brainstorm_id": f"bs-{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_prompt": user_prompt,
            "profile": profile,
            "ambiguities": ambiguities,
            "interpretations": interpretations,
            "best_interpretation": best,
            "recommendation": f"Melhor: {best['type']} — {best['interpretation']} — {best['closest_to_final']}% perto do objetivo final",
            "next_step": "Se construir: escolher template + definir MVP. Se responder: usar best_interpretation + third eye crítico",
            "version": self.version
        }
    
    def brainstorm_before_build(self, user_prompt: str, available_templates: List[str] = None) -> Dict[str, Any]:
        """
        Brainstorm antes de construir app/site — 3-5 abordagens arquiteturais
        """
        available_templates = available_templates or list(TEMPLATES.keys())
        
        # Sugere templates
        suggested = self._suggest_templates(user_prompt)
        
        # 3-5 abordagens
        approaches = []
        
        # Abordagem 1: MVP rápido com template existente
        approaches.append({
            "id": 1,
            "type": "mvp_template",
            "name": f"MVP Rápido com template {suggested[0]['template'] if suggested else 'landing-page'}",
            "description": f"Usa template existente mais próximo do objetivo, customiza mínimo, deploy rápido",
            "template": suggested[0]['template'] if suggested else "landing-page",
            "template_name": suggested[0]['name'] if suggested else "Landing Page Moderna",
            "tech_stack": "Next.js 15.3.5 estável + Tailwind + 200 providers gateway",
            "features": ["1-2 features core", "Funcional em 5 min", "Deploy Vercel/Docker"],
            "pros": ["Rápido 5 min", "Funcional real", "Usa 13 templates testados", "Sem invenção"],
            "cons": ["Pode não ter todas features do objetivo final", "Customização limitada"],
            "closest_to_final": 70,
            "effort": "Baixo — 5 min",
            "best_for": "Validar ideia rápido, MVP"
        })
        
        # Abordagem 2: Fullstack com 200 providers
        approaches.append({
            "id": 2,
            "type": "fullstack_200",
            "name": "Fullstack com 200 Providers Gateway",
            "description": "Frontend + Backend + Gateway 200 providers OpenAI-compatible, 50 adapters, streaming, tool calling",
            "template": "python-fastapi-react" if "python-fastapi-react" in available_templates else suggested[0]['template'] if suggested else "nextjs-app",
            "tech_stack": "Next.js 15.3.5 + FastAPI + 200 providers + 50 adapters + 13 templates",
            "features": ["Chat AI com 200 providers", "Workplace multi-arquivo", "Agentes 21 skills 24", "Deploy GitHub/Vercel/Docker REAL"],
            "pros": ["Completo, enterprise, 200 providers", "OpenAI-compatible gateway", "Agentes apoio terceiro olho"],
            "cons": ["Mais complexo, 30 min", "Precisa keys para 200 providers"],
            "closest_to_final": 90,
            "effort": "Médio — 30 min",
            "best_for": "Produto final robusto, SaaS, dashboard com AI"
        })
        
        # Abordagem 3: Custom do zero
        approaches.append({
            "id": 3,
            "type": "custom_zero",
            "name": "Custom do Zero — Você no Centro",
            "description": "Você cria orientando AI, não auto-geração. Você no centro, human override. Constrói do zero com AI orientando",
            "template": "custom",
            "tech_stack": "Você escolhe — Next.js, FastAPI, React, etc",
            "features": ["Você define tudo", "AI orienta, você decide", "Iterativo P0→P3"],
            "pros": ["100% custom, você no centro", "Aprende construindo", "Sem templates limitantes"],
            "cons": ["Mais tempo, 1-2h", "Precisa mais orientação"],
            "closest_to_final": 95,
            "effort": "Alto — 1-2h",
            "best_for": "Objetivo final muito específico, aprendizado"
        })
        
        # Abordagem 4: Se for e-commerce, dashboard, etc — específica
        if any(word in user_prompt.lower() for word in ["ecommerce", "loja", "shop", "carrinho"]):
            approaches.append({
                "id": 4,
                "type": "ecommerce_especifico",
                "name": "E-commerce com carrinho + checkout + 200 providers para recomendações AI",
                "description": "E-commerce Minimal template + carrinho + checkout + AI recomendações com 200 providers",
                "template": "ecommerce",
                "tech_stack": "Next.js 15.3.5 + Tailwind + 200 providers para recomendações",
                "features": ["Lista produtos", "Carrinho", "Checkout", "Recomendações AI com 200 providers"],
                "pros": ["Específico para e-commerce", "AI recomendações", "Funcional"],
                "cons": ["Precisa dados produtos"],
                "closest_to_final": 85,
                "effort": "Médio — 20 min",
                "best_for": "Loja online com AI"
            })
        elif any(word in user_prompt.lower() for word in ["dashboard", "saas", "métricas", "admin"]):
            approaches.append({
                "id": 4,
                "type": "dashboard_especifico",
                "name": "Dashboard SaaS com métricas + 200 providers",
                "description": "Dashboard SaaS template + sidebar + métricas + gráficos + tabelas + 200 providers",
                "template": "dashboard-saas",
                "tech_stack": "Next.js 15.3.5 + Tailwind + 200 providers",
                "features": ["Sidebar", "Métricas", "Gráficos", "Tabelas", "200 providers stats"],
                "pros": ["Pronto para SaaS", "Métricas reais", "200 providers"],
                "cons": ["Precisa dados"],
                "closest_to_final": 85,
                "effort": "Médio — 20 min",
                "best_for": "SaaS, admin, dashboard"
            })
        
        best = max(approaches, key=lambda x: x['closest_to_final'])
        
        return {
            "brainstorm_id": f"bs-build-{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_prompt": user_prompt,
            "available_templates": available_templates,
            "suggested_templates": suggested,
            "approaches": approaches,
            "best_approach": best,
            "recommendation": f"Melhor: {best['name']} — {best['closest_to_final']}% perto do objetivo final — Effort {best['effort']}",
            "next_step": f"Criar projeto com template {best['template']} + customizar para objetivo final: {user_prompt}",
            "mvp_vs_full": {
                "mvp": approaches[0],
                "full": approaches[1] if len(approaches) > 1 else approaches[0],
                "custom": approaches[2] if len(approaches) > 2 else None
            },
            "version": self.version
        }
    
    def _suggest_templates(self, user_prompt: str) -> List[Dict[str, Any]]:
        """Sugere templates mais próximos do objetivo final"""
        prompt_lower = user_prompt.lower()
        scored = []
        
        for tid, t in TEMPLATES.items():
            score = 0
            # Score por palavras chave
            if tid in prompt_lower:
                score += 50
            if t['type'] in prompt_lower:
                score += 20
            for word in t['best_for'].split(','):
                if word.strip() in prompt_lower:
                    score += 15
            # Score por tipo
            if 'landing' in prompt_lower and tid == 'landing-page':
                score += 40
            if 'dashboard' in prompt_lower and tid == 'dashboard-saas':
                score += 40
            if 'ecommerce' in prompt_lower and tid == 'ecommerce':
                score += 40
            if 'blog' in prompt_lower and tid == 'blog-md':
                score += 40
            if 'chat' in prompt_lower and tid == 'chat-app':
                score += 40
            if 'portfolio' in prompt_lower and tid == 'portfolio':
                score += 40
            if 'api' in prompt_lower and tid == 'api-gateway':
                score += 40
            if 'crud' in prompt_lower and tid == 'fastapi-crud':
                score += 40
            
            scored.append({
                "template": tid,
                "name": t['name'],
                "type": t['type'],
                "best_for": t['best_for'],
                "score": score,
                "reason": f"Match {score} — best_for {t['best_for']}"
            })
        
        scored_sorted = sorted(scored, key=lambda x: x['score'], reverse=True)
        # Retorna top 3 com score >0, ou top 3 geral se todos 0
        top = [s for s in scored_sorted if s['score'] > 0][:3]
        if not top:
            top = scored_sorted[:3]
        
        return top

# Singleton
brainstorming_service = BrainstormingService()
