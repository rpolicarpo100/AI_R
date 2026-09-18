"use client";
import { AgentNetworkDiagram } from "./AgentNetworkDiagram";

export function AgentsTab({ agents, skills, providers, models }: any) {
  return (
    <div className="space-y-3">
      <div className="flex gap-2 text-[11px]"><span className="px-2 py-1 rounded-full bg-white text-black">{agents.length} agentes</span><span className="px-2 py-1 rounded-full bg-violet-500/10 text-violet-400 border border-violet-500/20">{skills.length} skills</span><span className="px-2 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-zinc-500">empoderados • terceiro olho aberto • P16 Network Diagram</span></div>
      
      <AgentNetworkDiagram agents={agents} providers={providers} models={models} />

      <div className="grid md:grid-cols-3 gap-2">
        {agents.slice(0,9).map((a:any)=>(
          <div key={a.agent_id} className="p-2.5 rounded-xl bg-zinc-900 border border-zinc-800">
            <div className="flex justify-between"><span className="font-medium text-[11px]">{a.name}</span><span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">L{a.evolution_level} • {a.rating}</span></div>
            <div className="text-[10px] text-zinc-500 mt-1">{a.role} • {a.success_count}✓ {a.failure_count}✗ • {a.specialization||"general"}</div>
            <div className="text-[10px] text-zinc-400 mt-1 line-clamp-2">{a.description}</div>
            <div className="mt-1 flex gap-1 flex-wrap">{(a.skills||[]).slice(0,3).map((s:string)=><span key={s} className="text-[9px] px-1 py-0.5 rounded bg-zinc-800 text-zinc-500">{s}</span>)}</div>
          </div>
        ))}
      </div>
      <div className="grid md:grid-cols-2 gap-2">
        <div className="p-2.5 rounded-xl bg-zinc-900 border border-zinc-800"><div className="text-[11px] font-medium">Skills • {skills.length}</div><div className="mt-2 flex gap-1 flex-wrap max-h-[120px] overflow-auto">{skills.slice(0,20).map((s:any)=><span key={s.skill_id} className="text-[10px] px-2 py-1 rounded-full bg-zinc-800 border border-zinc-700">{s.name} • {s.category}</span>)}</div></div>
        <div className="p-2.5 rounded-xl bg-violet-500/5 border border-violet-500/20"><div className="text-[11px] font-medium text-violet-300">🤖 Agentes P11 — empoderados por comandos</div><div className="mt-2 space-y-1 text-[11px] text-zinc-400"><div><span className="text-emerald-400">/testa</span> → code-reviewer, critic, rigor-checker testa edge cases</div><div><span className="text-amber-400">/audita</span> → rigor-checker, security-audit verifica secrets SSRF</div><div><span className="text-red-400">/contesta</span> → critic, prompt-optimizer terceiro olho aberto</div><div><span className="text-violet-400">/agentes</span> → mostra agentes ativos + como empoderar</div></div><div className="mt-2 text-[10px] text-zinc-500">Princípio: você cria orientando AI, não ela automática. Agentes contestam, criticam, não ficam 1ª tentativa. Você no centro.</div></div>
      </div>
    </div>
  );
}
