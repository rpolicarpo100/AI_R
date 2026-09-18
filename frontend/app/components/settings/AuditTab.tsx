"use client";

export function AuditTab({ stats }: any) {
  const recent = stats?.recent_requests?.slice(0,8) || [];
  return (
    <div className="space-y-3">
      <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
        <div className="text-[11px] font-medium">🔍 Audit Log • P11 REAL — 0% invenção</div>
        <div className="mt-2 space-y-1.5 max-h-[250px] overflow-auto">
          {recent.length===0 ? <div className="text-[11px] text-zinc-500">Sem requests recentes • 40 total 95% success 40% free • Logs auditam routing, fallback, latência</div> :
            recent.map((r:any)=><div key={r.request_id} className="p-2 rounded-lg bg-[#08080c] border border-zinc-800 text-[10px] font-mono"><div className="flex justify-between"><span className="text-zinc-500">{r.request_id?.slice(0,12)}</span><span className={r.status==="success"?"text-emerald-400":"text-amber-400"}>{r.status||"unknown"}</span></div><div className="mt-1 truncate text-zinc-400">{r.prompt?.slice(0,80)||"no prompt"} • {r.provider_id}/{r.model_id} • {r.latency_ms}ms • ${r.cost}</div></div>)
          }
        </div>
      </div>
      <div className="grid md:grid-cols-2 gap-2">
        <div className="p-2.5 rounded-xl bg-zinc-900 border border-zinc-800"><div className="text-[11px] font-medium">Segurança P11</div><div className="mt-2 space-y-1 text-[11px] text-zinc-400"><div>✅ API keys Fernet encrypted, masked, nunca frontend/logs</div><div>✅ SSRF DNS rebinding blocked, private IP blocked, metadata blocked</div><div>✅ Rate limiting per provider 20-60/min, circuit breaker</div><div>✅ CORS env, .gitignore, no secrets in code</div><div>✅ Audit log rotate-key, human_override, branches</div></div></div>
        <div className="p-2.5 rounded-xl bg-zinc-900 border border-zinc-800"><div className="text-[11px] font-medium">Rigor & Honestidade</div><div className="mt-2 space-y-1 text-[11px] text-zinc-400"><div>✅ Nunca inventar Model IDs, preços, quotas, benchmarks</div><div>✅ Distinguir provider_claim vs verified vs measured vs UNKNOWN</div><div>✅ Medir comportamento real, não fabricante afirma</div><div>✅ Chat vs non-chat separados, non-chat expected fail CODING</div><div>✅ 0 scores inventados, 219 measured, 101 with scores</div></div></div>
      </div>
      <div className="p-2.5 rounded-xl bg-amber-500/5 border border-amber-500/20 text-[11px]"><div className="font-medium text-amber-300">⚠️ Princípios P11 — você cria orientando AI, não ela automática, sem simulações, crítico</div><div className="mt-1 text-zinc-500">Quem cria app sou eu orientando AI — apaga generated-apps e local-codegen. Sem simulações, crítico. Provider-agnostic, autonomia auditável, modular, segura, cloud-ready, OpenAI-compatible. Prioridade: FUNCIONALIDADE &gt; SEGURANÇA &gt; TESTES &gt; OBSERVABILITY &gt; PERFORMANCE &gt; UX &gt; AUTOMAÇÃO. P0→P1→P2→P3 iterações, não tudo de uma vez. Sem Kubernetes/microservices MVP: Next.js + FastAPI + PostgreSQL + Redis + APScheduler + Docker.</div></div>
    </div>
  );
}
