"""
Brainstorming Service — Vertente de brainstorming antes de construir ou responder
Objetivo: fazer algo mais perto do objetivo final, não ficar na 1ª tentativa
- Antes de responder: brainstorm 3-5 interpretações possíveis do que usuário realmente quer
- Antes de construir: brainstorm 3-5 abordagens arquiteturais, tradeoffs, MVP vs full, template mais próximo
- Você no centro, human override, terceiro olho aberto, contesta, critica
P22: 20 templates (13+7)
P24: Deep integration — chamado automaticamente no chat flow quando construir app ou ambíguo
"""

from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime, timezone

# Templates disponíveis para brainstorming de apps — P22 20 total (13+7)
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
    "react-counter": {"name": "React Counter + Hooks", "type": "frontend", "best_for": "React, hooks, state, contador"},
    "sql-analytics": {"name": "SQL Analytics Dashboard", "type": "fullstack", "best_for": "SQL, analytics, dashboard, métricas"},
    "python-nif": {"name": "Python NIF Validator", "type": "api", "best_for": "Python, NIF, validação, API"},
    # P22 7 novos
    "chat-rag": {"name": "Chat RAG 200 Providers", "type": "fullstack", "best_for": "chat, RAG, embeddings, 200 providers, OpenAI-compatible, streaming, vector"},
    "saas-auth": {"name": "SaaS Auth JWT Roles", "type": "fullstack", "best_for": "SaaS, auth, JWT, roles, dashboard, billing, 200 providers"},
    "portfolio-blog": {"name": "Portfolio + Blog MD SEO", "type": "frontend", "best_for": "portfolio, blog, markdown, SEO, 200 providers"},
    "ecommerce-ai": {"name": "E-commerce AI Recommendations", "type": "frontend", "best_for": "ecommerce, AI, recomendações, embeddings, UAI image, 200 providers"},
    "dashboard-analytics": {"name": "Dashboard Analytics AI", "type": "fullstack", "best_for": "dashboard, analytics, AI insights, gráficos, observability, grafana, 200 providers"},
    "landing-ai": {"name": "Landing AI Chat Streaming", "type": "frontend", "best_for": "landing, AI, chat, streaming, UAI 938 models, 200 providers"},
    "api-webhook": {"name": "API Gateway Webhooks", "type": "api", "best_for": "API, gateway, webhooks, FastAPI, 201 providers, 780 models, 938 UAI, rate limiting"},
}

class BrainstormingService:
    def __init__(self):
        self.version = "2.0 P24 — Brainstorming deep integration 20 templates — antes construir/responder — mais perto objetivo final — você no centro"
    
    def should_auto_brainstorm(self, user_prompt: str, profile: str = None) -> Dict[str, Any]:
        """
        P24 — Detecta se deve fazer brainstorm automático antes de responder/construir
        Critérios: profile=CODING, prompt contém app/site/cria/build, ambiguidade <5 palavras, sem ?, etc
        """
        prompt_lower = user_prompt.lower()
        triggers = []
        
        # Trigger 1: Keywords construir app — P24 precisa ser preciso, evitar falsos positivos como FastAPI contém api
        build_keywords = ["cria app", "construir app", "build app", "cria site", "criar app", "criar site", "landing page", "dashboard", "ecommerce", "portfolio", "saas", "chat app", "cria blog", "cria api", "build api", "faz um app", "faz uma app", "faz site", "cria landing", "cria dashboard", "cria ecommerce", "cria portfolio", "cria saas", "construir site", "build site"]
        matched_build = []
        for kw in build_keywords:
            if kw in prompt_lower:
                # Evitar falso positivo api dentro de fastapi — verificar se kw é substring mas com contexto construir
                if kw in ["api", "blog"] and len(kw) <= 3:
                    # Só se tiver verbo construir junto
                    if not any(v in prompt_lower for v in ["cria", "construir", "build", "faz", "criar"]):
                        continue
                matched_build.append(kw)
        if matched_build:
            triggers.append({"type": "build_keyword", "matched": matched_build[:3], "confidence": 90})
        
        # Trigger 2: Profile CODING
        if profile and profile.upper() in ["CODING", "CLINE_CODING"]:
            triggers.append({"type": "profile_coding", "profile": profile, "confidence": 70})
        
        # Trigger 3: Ambiguidade — prompt muito curto <5 palavras E contém app/site/cria/build OU sem ? (ambíguo real)
        word_count = len(user_prompt.split())
        if word_count < 5 and "?" not in user_prompt:
            # Só se contém indício de construir ou é muito ambíguo sem ser pergunta
            if any(w in prompt_lower for w in ["app", "site", "cria", "faz", "build", "landing", "dashboard"]):
                triggers.append({"type": "short_prompt", "words": word_count, "confidence": 60, "reason": "Prompt muito curto + contém app/site — múltiplas interpretações"})
            elif word_count <= 2:
                triggers.append({"type": "short_prompt", "words": word_count, "confidence": 55, "reason": "Prompt extremamente curto <=2 palavras — ambíguo"})
        
        # Trigger 4: Sem ? e curto <20 chars sem pergunta explícita mas contém app/site
        if "?" not in user_prompt and len(user_prompt) < 30 and any(w in prompt_lower for w in ["app", "site", "cria", "faz"]):
            triggers.append({"type": "ambiguous_no_question", "confidence": 65})
        
        # Trigger 5: Contém "como" + app/site — objetivo final mais profundo
        if any(w in prompt_lower for w in ["como fazer", "como criar", "qual melhor", "melhor forma"]) and any(w in prompt_lower for w in ["app", "site", "landing", "dashboard"]):
            triggers.append({"type": "deep_objective", "confidence": 75, "reason": "Pergunta sobre melhor forma — precisa brainstorm abordagens"})
        
        should = len(triggers) > 0
        confidence = max([t["confidence"] for t in triggers], default=0) if triggers else 0
        
        return {
            "should_brainstorm": should,
            "confidence": confidence,
            "triggers": triggers,
            "is_build_intent": any(t["type"] == "build_keyword" for t in triggers),
            "is_ambiguous": any(t["type"] in ["short_prompt", "ambiguous_no_question"] for t in triggers),
            "reason": f"Triggers {len(triggers)}: {[t['type'] for t in triggers]}" if triggers else "Nenhum trigger — resposta direta OK"
        }
    
    def brainstorm_before_respond(self, user_prompt: str, chat_history: List[Dict] = None, profile: str = "BEST") -> Dict[str, Any]:
        """
        Brainstorm antes de responder — 3-5 interpretações possíveis do que usuário realmente quer
        Para ficar mais perto do objetivo final, não ficar na 1ª tentativa
        P24 deep integration: chamado automaticamente no chat flow
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
        
        # Auto brainstorm check P24
        auto_check = self.should_auto_brainstorm(user_prompt, profile)
        
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
                "interpretation": f"Usuário quer construir app/site — objetivo final é ter algo funcional, não só código. Precisa escolher template mais próximo entre 20 templates, definir MVP, features essenciais",
                "confidence": 80,
                "pros": ["Foca no objetivo final funcional", "Considera templates 20 disponíveis (13+7 P22)", "Pensa em MVP vs full", "Você no centro"],
                "cons": ["Precisa mais perguntas para confirmar", "Mais tempo"],
                "closest_to_final": 85,
                "suggested_templates": self._suggest_templates(user_prompt),
                "mvp": "Versão mínima funcional com 1-2 features core — 5 min",
                "full": "Versão completa com todas features + deploy GitHub/Vercel/Docker REAL — 30 min"
            })
        else:
            # É pergunta/explicação
            interpretations.append({
                "id": 2,
                "type": "objetivo_profundo",
                "interpretation": f"Objetivo final por trás de '{user_prompt}' pode ser: entender conceito, resolver problema, ou tomar decisão. Não só responder, mas ajudar a atingir objetivo — terceiro olho",
                "confidence": 70,
                "pros": ["Vai além da pergunta literal", "Mais útil", "Terceiro olho aberto"],
                "cons": ["Pode assumir demais"],
                "closest_to_final": 75
            })
        
        # Interpretação 3: Alternativa crítica
        interpretations.append({
            "id": 3,
            "type": "alternativa_critica",
            "interpretation": f"Alternativa crítica: e se '{user_prompt}' não for a melhor forma de atingir objetivo? Existe abordagem melhor? Contesta, critica, terceiro olho — não fica na 1ª tentativa",
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
                "interpretation": "Prompt ambíguo — precisa clarificação antes de construir/responder para ficar mais perto do objetivo final — você no centro human override",
                "confidence": 40,
                "pros": ["Evita construir coisa errada", "Você no centro, human override"],
                "cons": ["Adiciona 1 turno extra"],
                "closest_to_final": 90,
                "questions": [
                    "Qual é o objetivo final? O que queres ter no fim?",
                    "É para construir app/site ou só responder pergunta?",
                    "Qual é o público alvo e o problema que resolve?",
                    "Tens preferência de template (20 disponíveis) ou tech stack?"
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
            "auto_check": auto_check,
            "ambiguities": ambiguities,
            "interpretations": interpretations,
            "best_interpretation": best,
            "recommendation": f"Melhor: {best['type']} — {best['interpretation']} — {best['closest_to_final']}% perto do objetivo final",
            "next_step": "Se construir: escolher template 20 + definir MVP (5min 70%, Fullstack 90% 30min, Custom 95% 1-2h). Se responder: usar best_interpretation + third eye crítico",
            "templates_count": len(TEMPLATES),
            "version": self.version
        }
    
    def brainstorm_before_build(self, user_prompt: str, available_templates: List[str] = None) -> Dict[str, Any]:
        """
        Brainstorm antes de construir app/site — 3-5 abordagens arquiteturais
        P24 deep integration: chamado automaticamente quando construir app detectado
        """
        available_templates = available_templates or list(TEMPLATES.keys())
        
        # Sugere templates
        suggested = self._suggest_templates(user_prompt)
        
        auto_check = self.should_auto_brainstorm(user_prompt, "CODING")
        
        # 3-5 abordagens
        approaches = []
        
        # Abordagem 1: MVP rápido com template existente
        approaches.append({
            "id": 1,
            "type": "mvp_template",
            "name": f"MVP Rápido com template {suggested[0]['template'] if suggested else 'landing-page'}",
            "description": f"Usa template existente mais próximo do objetivo entre 20 templates, customiza mínimo, deploy rápido — você no centro",
            "template": suggested[0]['template'] if suggested else "landing-page",
            "template_name": suggested[0]['name'] if suggested else "Landing Page Moderna",
            "tech_stack": "Next.js 15.3.5 estável + Tailwind + 200 providers gateway + UAI 938 models",
            "features": ["1-2 features core", "Funcional em 5 min", "Deploy Vercel/Docker REAL", "Build npm run build OK"],
            "pros": ["Rápido 5 min", "Funcional real", "Usa 20 templates testados P22", "Sem invenção", "Você no centro"],
            "cons": ["Pode não ter todas features do objetivo final", "Customização limitada"],
            "closest_to_final": 70,
            "effort": "Baixo — 5 min",
            "best_for": "Validar ideia rápido, MVP"
        })
        
        # Abordagem 2: Fullstack com 200 providers + UAI
        approaches.append({
            "id": 2,
            "type": "fullstack_200",
            "name": "Fullstack com 200 Providers Gateway + UAI 938 models",
            "description": "Frontend + Backend + Gateway 201 providers OpenAI-compatible, 50 adapters, streaming, tool calling, UAI image video — 20 templates",
            "template": "python-fastapi-react" if "python-fastapi-react" in available_templates else suggested[0]['template'] if suggested else "nextjs-app",
            "template_name": "Fullstack FastAPI + React" if "python-fastapi-react" in available_templates else suggested[0]['name'] if suggested else "Next.js 14 App Router",
            "tech_stack": "Next.js 15.3.5 + FastAPI + 201 providers + 50 adapters + 20 templates + UAI 938 models image 163 video 221",
            "features": ["Chat AI com 201 providers", "Workplace multi-arquivo", "Agentes 24 skills 23 + builders", "Deploy GitHub/Vercel/Docker REAL", "RAG embeddings streaming"],
            "pros": ["Completo, enterprise, 201 providers", "OpenAI-compatible gateway", "Agentes apoio terceiro olho", "UAI image/video"],
            "cons": ["Mais complexo, 30 min", "Precisa keys para 201 providers"],
            "closest_to_final": 90,
            "effort": "Médio — 30 min",
            "best_for": "Produto final robusto, SaaS, dashboard com AI"
        })
        
        # Abordagem 3: Custom do zero — você no centro
        approaches.append({
            "id": 3,
            "type": "custom_zero",
            "name": "Custom do Zero — Você no Centro",
            "description": "Você cria orientando AI, não auto-geração. Você no centro, human override. Constrói do zero com AI orientando — terceiro olho",
            "template": "custom",
            "template_name": "Custom do Zero",
            "tech_stack": "Você escolhe — Next.js, FastAPI, React, etc — 20 templates como referência",
            "features": ["Você define tudo", "AI orienta, você decide", "Iterativo P0→P3", "Terceiro olho aberto"],
            "pros": ["100% custom, você no centro", "Aprende construindo", "Sem templates limitantes", "Mais perto objetivo final"],
            "cons": ["Mais tempo, 1-2h", "Precisa mais orientação"],
            "closest_to_final": 95,
            "effort": "Alto — 1-2h",
            "best_for": "Objetivo final muito específico, aprendizado"
        })
        
        # Abordagem 4: Específica por domínio — usa 7 novos templates P22
        prompt_lower = user_prompt.lower()
        if any(word in prompt_lower for word in ["ecommerce", "loja", "shop", "carrinho"]):
            approaches.append({
                "id": 4,
                "type": "ecommerce_especifico",
                "name": "E-commerce AI com recomendações + UAI image",
                "description": "E-commerce AI template P22 + carrinho + checkout + AI recomendações embeddings 200 providers + UAI image",
                "template": "ecommerce-ai",
                "template_name": "E-commerce AI Recommendations",
                "tech_stack": "Next.js 15.3.5 + Tailwind + 200 providers para recomendações + UAI 938 image",
                "features": ["Lista produtos", "Carrinho", "Checkout", "Recomendações AI embeddings", "UAI image generation produtos"],
                "pros": ["Específico para e-commerce", "AI recomendações", "UAI image", "Funcional P22"],
                "cons": ["Precisa dados produtos"],
                "closest_to_final": 85,
                "effort": "Médio — 20 min",
                "best_for": "Loja online com AI"
            })
        elif any(word in prompt_lower for word in ["dashboard", "saas", "métricas", "admin", "analytics"]):
            approaches.append({
                "id": 4,
                "type": "dashboard_especifico",
                "name": "Dashboard Analytics AI + Observability",
                "description": "Dashboard Analytics AI template P22 + sidebar + métricas + gráficos + tabelas + AI insights + observability grafana",
                "template": "dashboard-analytics",
                "template_name": "Dashboard Analytics AI",
                "tech_stack": "Next.js 15.3.5 + Tailwind + 200 providers + observability",
                "features": ["Sidebar", "Métricas", "Gráficos", "Tabelas", "200 providers stats", "AI insights", "Grafana"],
                "pros": ["Pronto para SaaS", "Métricas reais", "200 providers", "P22 novo"],
                "cons": ["Precisa dados"],
                "closest_to_final": 85,
                "effort": "Médio — 20 min",
                "best_for": "SaaS, admin, dashboard analytics"
            })
        elif any(word in prompt_lower for word in ["chat", "rag", "embeddings", "vector", "conversa"]):
            approaches.append({
                "id": 4,
                "type": "chat_rag_especifico",
                "name": "Chat RAG 200 Providers + Streaming",
                "description": "Chat RAG template P22 + RAG 200 providers embeddings streaming vector DB",
                "template": "chat-rag",
                "template_name": "Chat RAG 200 Providers",
                "tech_stack": "Next.js 15.3.5 + FastAPI + 200 providers + embeddings + streaming + vector",
                "features": ["Chat AI", "RAG", "Embeddings", "200 providers", "Streaming", "Vector DB"],
                "pros": ["RAG real", "200 providers", "Streaming", "P22 novo"],
                "cons": ["Precisa vector DB"],
                "closest_to_final": 88,
                "effort": "Médio — 25 min",
                "best_for": "Chat com RAG, conhecimento"
            })
        elif any(word in prompt_lower for word in ["landing", "marketing", "produto", "startup"]):
            approaches.append({
                "id": 4,
                "type": "landing_ai_especifico",
                "name": "Landing AI Chat Streaming UAI 938 models",
                "description": "Landing AI template P22 + Chat streaming UAI 938 models image video",
                "template": "landing-ai",
                "template_name": "Landing AI Chat Streaming",
                "tech_stack": "Next.js 15.3.5 + Tailwind + UAI 938 models + 200 providers",
                "features": ["Landing moderna", "AI Chat streaming", "UAI image video", "Conversão"],
                "pros": ["Landing com AI", "UAI 938 models", "Streaming", "P22 novo"],
                "cons": ["Precisa copy"],
                "closest_to_final": 87,
                "effort": "Baixo — 15 min",
                "best_for": "Landing page com AI"
            })
        elif any(word in prompt_lower for word in ["portfolio", "blog", "markdown", "seo"]):
            approaches.append({
                "id": 4,
                "type": "portfolio_blog_especifico",
                "name": "Portfolio Blog MD SEO 200 providers",
                "description": "Portfolio Blog template P22 + MD SEO 200 providers",
                "template": "portfolio-blog",
                "template_name": "Portfolio + Blog MD SEO",
                "tech_stack": "Next.js 15.3.5 + MD + SEO + 200 providers",
                "features": ["Portfolio", "Blog MD", "SEO", "200 providers"],
                "pros": ["Portfolio + Blog", "MD SEO", "P22 novo"],
                "cons": ["Precisa conteúdo"],
                "closest_to_final": 86,
                "effort": "Baixo — 15 min",
                "best_for": "Portfolio pessoal + blog"
            })
        elif any(word in prompt_lower for word in ["auth", "login", "jwt", "roles", "billing"]):
            approaches.append({
                "id": 4,
                "type": "saas_auth_especifico",
                "name": "SaaS Auth JWT Roles Dashboard Billing",
                "description": "SaaS Auth template P22 + JWT roles dashboard billing 200 providers",
                "template": "saas-auth",
                "template_name": "SaaS Auth JWT Roles",
                "tech_stack": "Next.js 15.3.5 + FastAPI + JWT + 200 providers",
                "features": ["Auth JWT", "Roles", "Dashboard", "Billing", "200 providers"],
                "pros": ["Auth completo", "SaaS pronto", "P22 novo"],
                "cons": ["Precisa DB"],
                "closest_to_final": 88,
                "effort": "Médio — 25 min",
                "best_for": "SaaS com auth"
            })
        
        best = max(approaches, key=lambda x: x['closest_to_final'])
        
        return {
            "brainstorm_id": f"bs-build-{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_prompt": user_prompt,
            "available_templates": available_templates,
            "available_count": len(available_templates),
            "suggested_templates": suggested,
            "approaches": approaches,
            "best_approach": best,
            "auto_check": auto_check,
            "recommendation": f"Melhor: {best['name']} — {best['closest_to_final']}% perto do objetivo final — Effort {best['effort']} — Template {best['template']} entre 20",
            "next_step": f"Criar projeto com template {best['template']} + customizar para objetivo final: {user_prompt} — Você no centro escolhe",
            "mvp_vs_full": {
                "mvp": approaches[0],
                "full": approaches[1] if len(approaches) > 1 else approaches[0],
                "custom": approaches[2] if len(approaches) > 2 else None,
                "specific": approaches[3] if len(approaches) > 3 else None
            },
            "templates_count": len(TEMPLATES),
            "p22_new": ["chat-rag", "saas-auth", "portfolio-blog", "ecommerce-ai", "dashboard-analytics", "landing-ai", "api-webhook"],
            "version": self.version
        }
    
    def _suggest_templates(self, user_prompt: str) -> List[Dict[str, Any]]:
        """Sugere templates mais próximos do objetivo final — 20 templates P22"""
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
            # Score por tipo específico P22
            if 'landing' in prompt_lower and 'landing' in tid:
                score += 40
            if 'dashboard' in prompt_lower and 'dashboard' in tid:
                score += 40
            if 'ecommerce' in prompt_lower and 'ecommerce' in tid:
                score += 40
            if 'blog' in prompt_lower and ('blog' in tid):
                score += 40
            if 'chat' in prompt_lower and 'chat' in tid:
                score += 40
            if 'portfolio' in prompt_lower and 'portfolio' in tid:
                score += 40
            if 'api' in prompt_lower and 'api' in tid:
                score += 40
            if 'crud' in prompt_lower and tid == 'fastapi-crud':
                score += 40
            if 'rag' in prompt_lower and tid == 'chat-rag':
                score += 50
            if 'auth' in prompt_lower and tid == 'saas-auth':
                score += 50
            if 'analytics' in prompt_lower and tid == 'dashboard-analytics':
                score += 50
            if 'ai' in prompt_lower and tid in ['ecommerce-ai', 'landing-ai', 'dashboard-analytics', 'chat-rag']:
                score += 30
            if 'webhook' in prompt_lower and tid == 'api-webhook':
                score += 50
            
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
print(f"[Brainstorming P24] Loaded — 20 templates (13+7 P22) — deep integration auto_check — version {brainstorming_service.version}")
