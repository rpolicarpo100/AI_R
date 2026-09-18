"use client";

// P10 - Comandos críticos v1.2 - sem templates, só comandos que empoderam agentes
export const CHAT_COMMANDS = [
  { id: "testa", label: "/testa", desc: "Agentes testam último código - unit, integração, edge cases", agents: ["code-reviewer-01","critic-01","rigor-checker-01"], color: "emerald", critical: "Não fica na 1ª tentativa, testa casos limite, exige cobertura" },
  { id: "audita", label: "/audita", desc: "Auditoria completa: segurança, rigor, qualidade - relatório crítico", agents: ["rigor-checker-01","code-reviewer-01","security-audit"], color: "amber", critical: "Verifica secrets, SSRF, injection, % medido vs inventado" },
  { id: "contesta", label: "/contesta", desc: "Critic contesta última resposta - falhas lógicas, alternativas, terceiro olho", agents: ["critic-01","prompt-optimizer-01","intent-analyzer-01"], color: "red", critical: "Não aceita 1ª tentativa, força melhoria, terceiro olho aberto" },
  { id: "melhora", label: "/melhora", desc: "Melhora código: performance, legibilidade, segurança", agents: ["prompt-optimizer-01","code-reviewer-01","critic-01"], color: "violet", critical: "Otimiza sem quebrar, mede antes/depois" },
  { id: "explica", label: "/explica", desc: "Explica código linha a linha, tradeoffs, complexidade", agents: ["intent-analyzer-01","rigor-checker-01","code-reviewer-01"], color: "blue", critical: "Rigorosa, não inventa, mede complexidade real" },
  { id: "benchmark", label: "/benchmark", desc: "Roda benchmark real no modelo atual", agents: ["benchmark_coding","benchmark_json","benchmark_speed"], color: "indigo", critical: "Mede comportamento real, nunca inventa" },
  { id: "rigor", label: "/rigor", desc: "Mostra rigor atual: % medido, inventado, UNKNOWN", agents: ["rigor-checker-01"], color: "emerald", critical: "0% invenção, honesto" },
  { id: "seguranca", label: "/seguranca", desc: "Audita segurança: keys, SSRF, CORS, secrets", agents: ["security_audit"], color: "red", critical: "Fernet, masked, .gitignore, rate limiting, SSRF DNS" },
  { id: "agentes", label: "/agentes", desc: "Mostra agentes ativos e como empoderar", agents: ["router-01","intent-analyzer-01","prompt-optimizer-01","critic-01","code-reviewer-01","rigor-checker-01"], color: "violet", critical: "Agentes contestam, criticam, não ficam na 1ª tentativa" },
  { id: "exporta", label: "/exporta", desc: "Exporta projeto: github | vercel | docker", agents: ["code-reviewer-01"], color: "emerald", critical: "Você cria orientando AI - export é ponte" },
  { id: "branch", label: "/branch", desc: "Cria branch para feature sem quebrar main", agents: [], color: "blue", critical: "Merge com detecção conflitos + human_override" },
  { id: "elimina", label: "/elimina", desc: "Elimina projeto - arquiva ou hard delete", agents: [], color: "red", critical: "Soft arquiva, hard elimina com confirmação" },
  { id: "limpa", label: "/limpa", desc: "Limpa chat, mantém workplace", agents: [], color: "slate", critical: "Você no centro, você decide" },
  { id: "ajuda", label: "/ajuda", desc: "Lista comandos + atalhos P10", agents: [], color: "slate", critical: "Comandos empoderam agentes + Ctrl+K etc" },
];

export type ChatCommand = typeof CHAT_COMMANDS[0];
