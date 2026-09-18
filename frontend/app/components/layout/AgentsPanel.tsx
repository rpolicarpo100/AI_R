"use client";

export function AgentsPanel({ agents, skills, onClose }: any) {
  return (
    <div className="border-b border-violet-500/15 bg-[radial-gradient(ellipse_at_top,_rgba(139,92,246,0.08),transparent_60%)]">
      <div className="mx-auto max-w-[1600px] px-6 py-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-6 h-6 rounded-full bg-violet-500 text-white flex items-center justify-center text-[11px]">◈</div>
            <h3 className="text-[12px] font-[600] tracking-tight">Agentes Empoderados v1.2 • {agents.length} ativos • {skills.length} skills • Terceiro olho aberto</h3>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">contesta • critica • não fica na 1ª tentativa</span>
          </div>
          <button onClick={onClose} className="w-7 h-7 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-500 hover:text-zinc-300 hover:border-zinc-700 transition">✕</button>
        </div>

        <div className="grid md:grid-cols-3 lg:grid-cols-6 gap-2.5">
          {agents.slice(0,6).map((a:any)=>(
            <div key={a.agent_id} className="group rounded-2xl bg-zinc-900/60 border border-zinc-800 hover:border-zinc-700 hover:bg-zinc-900 transition p-3">
              <div className="flex items-center justify-between">
                <span className="font-[550] text-[11px] tracking-tight">{a.name}</span>
                <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">L{a.evolution_level}</span>
              </div>
              <div className="mt-1 flex items-center gap-1.5 text-[10px] text-zinc-500">
                <span className="w-1 h-1 rounded-full bg-violet-500"></span>
                <span className="truncate">{a.role} • {a.rating} • {a.success_count}✓ {a.proficiency}%</span>
              </div>
              <div className="mt-2 text-[11px] leading-[1.4] text-zinc-400 line-clamp-2 group-hover:text-zinc-300">{a.description}</div>
              <div className="mt-2 h-px bg-zinc-800 group-hover:bg-zinc-700 transition"></div>
              <div className="mt-2 text-[10px] font-mono text-zinc-600">👁️ terceiro olho • contesta 1ª tentativa</div>
            </div>
          ))}
        </div>

        <div className="mt-3.5 grid md:grid-cols-3 gap-2.5">
          <div className="rounded-2xl bg-emerald-500/[0.04] border border-emerald-500/15 p-3">
            <div className="flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-[10px] text-emerald-400">✓</span>
              <span className="text-[11px] font-[550] text-emerald-300">/testa • Testa código real</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">code-reviewer + critic + rigor</span>
            </div>
            <div className="mt-2 text-[11px] leading-[1.4] text-zinc-500">Agentes leem arquivos reais do projeto, sugerem unit, integração, edge cases, security, performance. Não aceita 1ª tentativa, exige cobertura.</div>
            <div className="mt-2 text-[10px] font-mono text-zinc-600">↳ critical: exige testes reais, não simulação, mede % coberto</div>
          </div>
          <div className="rounded-2xl bg-amber-500/[0.04] border border-amber-500/15 p-3">
            <div className="flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-[10px] text-amber-400">◐</span>
              <span className="text-[11px] font-[550] text-amber-300">/audita • Auditoria completa</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">rigor + reviewer + security</span>
            </div>
            <div className="mt-2 text-[11px] leading-[1.4] text-zinc-500">Verifica secrets, SSRF, injection, % medido vs inventado, qualidade código, contesta falhas. Lê arquivos reais, não mock.</div>
            <div className="mt-2 text-[10px] font-mono text-zinc-600">↳ critical: verifica .env, Fernet, masked keys, audit log</div>
          </div>
          <div className="rounded-2xl bg-red-500/[0.04] border border-red-500/15 p-3">
            <div className="flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center text-[10px] text-red-400">◈</span>
              <span className="text-[11px] font-[550] text-red-300">/contesta • Contesta resposta</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/20">critic + optimizer + intent</span>
            </div>
            <div className="mt-2 text-[11px] leading-[1.4] text-zinc-500">Critic contesta última resposta, aponta falhas lógicas, alternativas, viés. Força melhoria, terceiro olho aberto, sugere criticamente.</div>
            <div className="mt-2 text-[10px] font-mono text-zinc-600">↳ critical: não aceita 1ª tentativa, terceiro olho, você no centro</div>
          </div>
        </div>

        <div className="mt-3 flex items-center gap-2 text-[11px]">
          <span className="text-zinc-600">Pipeline real:</span>
          <span className="font-mono text-[10px] px-2 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-zinc-500">intent-analyzer → prompt-optimizer → router → main_llm → critic → code-reviewer → rigor-checker</span>
          <span className="text-zinc-700">•</span>
          <span className="text-zinc-500">Você cria orientando AI, agentes apoiam, você decide</span>
        </div>
      </div>
    </div>
  );
}
