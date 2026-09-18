"use client";
import ReactMarkdown from "react-markdown";
import Prism from "prismjs";
import { useEffect, useState } from "react";

export function ChatMessages({ messages, loading, streamEnabled, onSave, chatEndRef }: any) {
  useEffect(() => { 
    // @ts-ignore
    if (typeof Prism !== 'undefined') Prism.highlightAll(); 
  }, [messages]);

  const extractCodeBlocks = (content: string) => {
    const blocks = content.match(/```/g);
    return { hasCode: !!blocks && blocks.length >= 2, files: blocks ? blocks.length / 2 : 0 };
  };

  return (
    <div className="flex-1 overflow-auto">
      {messages.length === 0 && (
        <div className="h-full flex flex-col items-center justify-center px-6 py-16">
          <div className="text-center max-w-[440px]">
            <div className="w-9 h-9 rounded-xl bg-white text-black flex items-center justify-center mx-auto font-bold text-[11px] tracking-widest">OS</div>
            <h3 className="mt-4 font-[650] text-[15px] tracking-tight">Você cria orientando a AI</h3>
            <p className="mt-2 text-[13px] leading-[1.5] text-zinc-500">Chat limpo, sem templates. Agentes contestam, criticam, não ficam na 1ª tentativa. Terceiro olho aberto. Agora com large prompt handling faseado.</p>
          </div>
          <div className="mt-10 w-full max-w-[440px] space-y-2">
            <div className="flex items-center gap-2 text-[11px] font-medium text-zinc-600 uppercase tracking-widest">
              <div className="h-px flex-1 bg-zinc-900"></div>
              Comandos que empoderam agentes + large data
              <div className="h-px flex-1 bg-zinc-900"></div>
            </div>
            {[
              { id: "testa", label: "/testa", desc: "Agentes testam código — unit, edge cases, cobertura", accent: "emerald", agents: "code-reviewer + critic + rigor", critical: "Não aceita 1ª tentativa, exige testes reais" },
              { id: "audita", label: "/audita", desc: "Auditoria segurança, rigor, qualidade — lê arquivos reais", accent: "amber", agents: "rigor + reviewer + security", critical: "Verifica secrets, SSRF, % medido vs inventado" },
              { id: "contesta", label: "/contesta", desc: "Critic contesta — falhas lógicas, alternativas, terceiro olho", accent: "red", agents: "critic + optimizer + intent", critical: "Força melhoria, aponta viés, sugere criticamente" },
            ].map(cmd => (
              <div key={cmd.id} className="group rounded-2xl border border-zinc-900 bg-zinc-900/40 hover:bg-zinc-900/80 hover:border-zinc-800 transition p-3.5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[12px] font-medium text-white">{cmd.label}</span>
                      <span className={`w-1.5 h-1.5 rounded-full ${cmd.accent==='emerald'?'bg-emerald-500':cmd.accent==='amber'?'bg-amber-500':'bg-red-500'}`}></span>
                      <span className="text-[11px] text-zinc-500">{cmd.agents}</span>
                    </div>
                    <div className="mt-1 text-[12px] leading-[1.4] text-zinc-300">{cmd.desc}</div>
                    <div className="mt-1.5 text-[11px] leading-[1.4] text-zinc-500">↳ {cmd.critical}</div>
                  </div>
                  <div className="text-[10px] px-2 py-1 rounded-full bg-zinc-800 text-zinc-500 group-hover:bg-white group-hover:text-black transition">usar</div>
                </div>
              </div>
            ))}
            <div className="rounded-2xl border border-violet-500/20 bg-violet-500/5 p-3.5 mt-3">
              <div className="text-[11px] font-medium text-violet-300">📦 P5 Large Prompt — Faseado Real e Funcional</div>
              <div className="mt-1.5 space-y-1 text-[11px] leading-[1.5] text-zinc-400">
                <div>• Textarea 24px → 50vh, token counter real-time chars/tokens/% context</div>
                <div>• Drag-drop files (10 files 500k cada), 📎 upload, paste large &gt;5k modal</div>
                <div>• @file workplace autocomplete, large warning &gt;50k, collapse &gt;1000 chars</div>
                <div>• Backend faseado: validação per-profile → LONG_CONTEXT → truncation → routing</div>
                <div>• CLINE_CODING 200k chars, BEST 100k, FAST 20k — chars ≠ tokens, tokens principal</div>
              </div>
            </div>
            <div className="pt-2 text-center">
              <span className="text-[11px] text-zinc-600">Digite </span>
              <span className="text-[11px] font-mono text-zinc-400">/ajuda</span>
              <span className="text-[11px] text-zinc-600"> para lista completa • </span>
              <span className="text-[11px] font-mono text-zinc-400">Ctrl+K</span>
              <span className="text-[11px] text-zinc-600"> foco • </span>
              <span className="text-[11px] font-mono text-zinc-400">@file</span>
              <span className="text-[11px] text-zinc-600"> workplace • </span>
              <span className="text-[11px] font-mono text-zinc-400">📎</span>
              <span className="text-[11px] text-zinc-600"> files</span>
            </div>
          </div>
        </div>
      )}

      <div className="px-5 py-6 space-y-6">
        {/* P6 — Virtualization for chat capacity: keep last 50 visible, older collapsed to avoid DOM bloat */}
        {messages.length > 50 && (
          <div className="rounded-xl bg-zinc-900/30 border border-zinc-800/50 px-4 py-2.5 text-center">
            <span className="text-[11px] text-zinc-500">📦 {messages.length - 50} mensagens antigas colapsadas para capacidade — mostrando últimas 50 • virtual scroll</span>
            <button onClick={() => {
              const el = document.getElementById('chat-old-messages');
              if (el) el.style.display = el.style.display === 'none' ? 'block' : 'none';
            }} className="ml-2 text-[11px] px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400 hover:bg-zinc-700">toggle antigas</button>
          </div>
        )}
        <div id="chat-old-messages" style={{display: messages.length > 50 ? 'none' : 'block'}} className="space-y-6">
          {messages.slice(0, messages.length > 50 ? messages.length - 50 : 0).map((m: any, i: number) => {
            const contentLength = m.content?.length || 0;
            return (
              <div key={`old-${i}`} className="group flex justify-start opacity-60 hover:opacity-100 transition">
                <div className="max-w-[82%] bg-zinc-900/30 border border-zinc-800/30 rounded-[16px] px-3 py-2">
                  <div className="text-[11px] font-mono text-zinc-600">{m.role} • {contentLength} chars • colapsado P6</div>
                  <div className="text-[12px] text-zinc-500 truncate">{m.content?.slice(0,100)}...</div>
                </div>
              </div>
            );
          })}
        </div>
        {(messages.length > 50 ? messages.slice(-50) : messages).map((m: any, i: number) => {
          const actualIndex = messages.length > 50 ? (messages.length - 50 + i) : i;
          const codeInfo = m.role === "assistant" ? extractCodeBlocks(m.content) : { hasCode: false, files: 0 };
          const prevPrompt = actualIndex > 0 ? messages[actualIndex - 1]?.content : "";
          const isUser = m.role === "user";
          const isCommandResult = m.commandResult;
          const contentLength = m.content?.length || 0;
          const isLargeContent = contentLength > 1000;
          const estimatedTokens = Math.ceil(contentLength / 4);

          return (
            <div key={i} className={`group flex ${isUser ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[82%] ${isUser ? "bg-white text-black rounded-[20px] rounded-br-[8px] px-4 py-2.5" : m.isError ? "bg-red-500/10 border border-red-500/20 rounded-[20px] rounded-bl-[8px] px-4 py-3.5" : isCommandResult ? "bg-violet-500/5 border border-violet-500/20 rounded-[20px] rounded-bl-[8px] px-4 py-3.5" : "bg-zinc-900/70 border border-zinc-800/80 rounded-[20px] rounded-bl-[8px] px-4 py-3.5"}`}>
                
                {/* Agent indicator for assistant */}
                {!isUser && !m.isError && (
                  <div className="flex items-center gap-2 mb-2.5">
                    <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] ${isCommandResult ? "bg-violet-500 text-white" : "bg-zinc-800 text-zinc-400"}`}>
                      {isCommandResult ? "◈" : "✦"}
                    </div>
                    <span className="text-[11px] font-medium text-zinc-400">
                      {isCommandResult ? `${m.commandResult?.command} • ${m.commandResult?.agents_triggered?.length || 0} agentes` : "AI • auto routing"}
                    </span>
                    {m.meta?.support_agents && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">terceiro olho</span>
                    )}
                    {isLargeContent && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">{contentLength} chars ~{estimatedTokens} tokens</span>
                    )}
                  </div>
                )}

                {isUser && isLargeContent && (
                  <div className="mb-2 flex items-center gap-2 text-[10px] font-mono text-zinc-600">
                    <span>📦 {contentLength} chars ~{estimatedTokens} tokens • faseado</span>
                  </div>
                )}

                <div className={`prose prose-invert max-w-none text-[13.5px] leading-[1.65] ${isUser ? "prose-p:text-black" : ""} prose-pre:bg-[#08080c] prose-pre:border prose-pre:border-zinc-800 prose-code:text-violet-300 prose-p:my-2 prose-headings:font-semibold`}>
                  {m.role === "assistant" ? (
                    <ReactMarkdown
                      components={{
                        code({ inline, className, children, ...props }: any) {
                          const match = /language-(\w+)/.exec(className || '');
                          const lang = match ? match[1] : 'python';
                          return !inline ? (
                            <div className="my-3 rounded-xl overflow-hidden border border-zinc-800 bg-[#08080c]">
                              <div className="flex items-center justify-between px-3 py-1.5 bg-zinc-900/80 border-b border-zinc-800">
                                <span className="text-[10px] font-mono text-zinc-500">{lang}</span>
                                <button onClick={() => navigator.clipboard.writeText(String(children))} className="text-[10px] text-zinc-500 hover:text-zinc-300 transition">copy</button>
                              </div>
                              <pre className="p-3.5 overflow-auto text-[12px] leading-[1.5] max-h-[400px]"><code className={`language-${lang}`} {...props}>{String(children).replace(/\n$/, '')}</code></pre>
                            </div>
                          ) : (
                            <code className="px-1.5 py-0.5 rounded-md bg-zinc-800 text-zinc-200 text-[12px]" {...props}>{children}</code>
                          );
                        }
                      }}
                    >
                      {m.content}
                    </ReactMarkdown>
                  ) : (
                    <CollapsibleContent content={m.content} isLarge={isLargeContent} chars={contentLength} tokens={estimatedTokens} />
                  )}
                </div>

                {/* Command result critical analysis */}
                {isCommandResult && m.commandResult?.critical_analysis && (
                  <div className="mt-3 p-2.5 rounded-xl bg-amber-500/5 border border-amber-500/15">
                    <div className="text-[11px] font-medium text-amber-300">Crítica • terceiro olho aberto</div>
                    <div className="mt-1 text-[11px] leading-[1.5] text-zinc-400">{m.commandResult.critical_analysis}</div>
                  </div>
                )}

                {/* Save to workplace */}
                {m.role === "assistant" && !m.isError && codeInfo.hasCode && (
                  <div className="mt-3 flex items-center gap-2">
                    <button onClick={() => onSave(prevPrompt, m.content, m.meta)} className="px-3.5 py-1.5 rounded-full bg-white text-black text-[11px] font-medium hover:bg-zinc-100 transition">📁 Salvar no Workplace • {codeInfo.files} blocos</button>
                    <span className="text-[10px] text-zinc-600">você decide</span>
                  </div>
                )}

                {/* Meta + Agents - clean */}
                {m.meta && (
                  <div className="mt-3.5 pt-3 border-t border-zinc-800/60 space-y-2.5">
                    <div className="flex items-center gap-2 text-[10px] font-mono text-zinc-500 flex-wrap">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                      <span className="truncate">{m.meta.selected?.slice(0, 60)}</span>
                      <span className="text-zinc-700">•</span>
                      <span>{m.meta.trace?.[0]?.latency_ms}ms</span>
                      <span className="text-zinc-700">•</span>
                      <span>{m.meta.profile}</span>
                      {m.meta.cline_coding && (
                        <>
                          <span className="text-zinc-700">•</span>
                          <span className="text-violet-400">CLINE_CODING</span>
                          <span className="text-zinc-700">•</span>
                          <span>{m.meta.cline_coding.requested_tokens} tokens req / {m.meta.cline_coding.model_context_limit} limit</span>
                        </>
                      )}
                    </div>
                    {m.meta.support_agents && (
                      <div className="rounded-xl bg-[#08080c] border border-zinc-800/60 p-2.5 space-y-1.5">
                        <div className="flex items-center gap-1.5 text-[11px] font-medium text-zinc-400">
                          <span>🤖 Agentes empoderados</span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-violet-500/10 text-violet-400 border border-violet-500/20">pipeline real</span>
                        </div>
                        <div className="grid gap-1 text-[11px] leading-[1.4]">
                          {m.meta.support_agents.intent_analysis && <div className="flex gap-2"><span className="text-violet-400 shrink-0">intent</span><span className="text-zinc-500 truncate">{m.meta.support_agents.intent_analysis.intent_type} • {m.meta.support_agents.intent_analysis.complexity}</span></div>}
                          {m.meta.support_agents.prompt_optimization && <div className="flex gap-2"><span className="text-violet-400 shrink-0">optimizer</span><span className="text-zinc-500 truncate">{m.meta.support_agents.prompt_optimization.improvements?.join(", ").slice(0, 100)}</span></div>}
                          {m.meta.support_agents.critique && <div className="flex gap-2"><span className="text-violet-400 shrink-0">critic</span><span className="text-zinc-500">score {m.meta.support_agents.critique.score}/100 • {m.meta.support_agents.critique.issues?.length || 0} issues</span></div>}
                          {m.meta.support_agents.third_eye && <div className="text-[10px] text-zinc-600 pt-1 border-t border-zinc-800/60">👁️ {m.meta.support_agents.third_eye}</div>}
                        </div>
                        <div className="text-[10px] font-mono text-zinc-700 pt-1 border-t border-zinc-800/60">intent-analyzer → prompt-optimizer → router → main_llm → critic → code-reviewer → rigor-checker</div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-zinc-900/70 border border-zinc-800/80 rounded-[20px] rounded-bl-[8px] px-4 py-3.5">
              <div className="flex items-center gap-2.5">
                <div className="flex gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-violet-500 animate-bounce [animation-delay:-0.3s]"></span>
                  <span className="w-1.5 h-1.5 rounded-full bg-violet-500 animate-bounce [animation-delay:-0.15s]"></span>
                  <span className="w-1.5 h-1.5 rounded-full bg-violet-500 animate-bounce"></span>
                </div>
                <span className="text-[11px] text-zinc-500">Agentes trabalhando — intent, optimizer, critic, reviewer, rigor • faseado</span>
                {streamEnabled && <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">streaming</span>}
              </div>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>
    </div>
  );
}

function CollapsibleContent({ content, isLarge, chars, tokens }: { content: string, isLarge: boolean, chars: number, tokens: number }) {
  const [expanded, setExpanded] = useState(false);
  
  if (!isLarge) {
    return <div className="whitespace-pre-wrap break-words">{content}</div>;
  }

  const preview = content.slice(0, 1000);
  
  return (
    <div>
      <div className="whitespace-pre-wrap break-words">
        {expanded ? content : preview}
        {!expanded && content.length > 1000 && "..."}
      </div>
      <button 
        onClick={() => setExpanded(!expanded)}
        className="mt-2.5 px-3 py-1 rounded-full bg-zinc-800 text-zinc-400 text-[11px] hover:bg-zinc-700 hover:text-zinc-200 transition border border-zinc-700"
      >
        {expanded ? `↑ Recolher • ${chars} chars ~${tokens} tokens` : `↓ Mostrar mais • ${chars} chars ~${tokens} tokens • ${chars - 1000} restantes • faseado`}
      </button>
    </div>
  );
}
