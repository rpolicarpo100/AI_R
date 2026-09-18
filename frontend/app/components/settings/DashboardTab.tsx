"use client";

export function DashboardTab({ stats, rigor, providers, models, projects }: any) {
  const ai = stats?.ai_network || {};
  const best = stats?.best_now || {};
  const req = stats?.requests || {};
  const p05 = stats?.p0_5_stability || {};
  const p1 = stats?.p1_performance || {};
  const p2q = stats?.p2_quotas || {};
  const p2ac = stats?.p2_async_critic || {};
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800"><div className="text-[10px] text-zinc-500">Providers</div><div className="text-[18px] font-bold">{ai.total_providers||providers.length}</div><div className="text-[10px] text-zinc-600">{ai.providers_online} online • {ai.providers_discovered} discovered • {ai.models_deprecated||p05.deprecated_count||0} deprecated</div></div>
        <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800"><div className="text-[10px] text-zinc-500">Models</div><div className="text-[18px] font-bold">{ai.models_available||models.length}</div><div className="text-[10px] text-zinc-600">{ai.models_distinct} distinct • {ai.models_multi_provider} multi • {ai.models_deprecated||0} deprecated</div></div>
        <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800"><div className="text-[10px] text-zinc-500">Measured</div><div className="text-[18px] font-bold">{rigor?.models?.measured||0} <span className="text-[12px] text-zinc-500">{rigor?.models?.measured_percent||0}%</span></div><div className="text-[10px] text-zinc-600">{rigor?.models?.chat?.measured} chat {rigor?.models?.chat?.measured_percent}% • {p1.http_pool_clients||0} pooled</div></div>
        <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800"><div className="text-[10px] text-zinc-500">Requests</div><div className="text-[18px] font-bold">{req.total||0}</div><div className="text-[10px] text-zinc-600">{req.success_rate}% success • {req.free_usage_percent}% free • {p2q.total_429_hits_last_hour||0} 429/h</div></div>
      </div>
      <div className="grid md:grid-cols-2 gap-3">
        <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
          <div className="text-[11px] font-medium">🏆 Best Now • REAL medido • P2</div>
          <div className="mt-2 space-y-1.5 text-[11px]">
            <div className="flex justify-between p-2 rounded-lg bg-[#08080c] border border-zinc-800"><span className="text-zinc-500">Provider</span><span className="font-medium">{best.best_provider?.name} • {best.best_provider?.id}</span></div>
            <div className="flex justify-between p-2 rounded-lg bg-[#08080c] border border-zinc-800"><span className="text-zinc-500">Coding</span><span className="font-medium">{best.best_coding_model?.name} • {best.best_coding_model?.score}</span></div>
            <div className="flex justify-between p-2 rounded-lg bg-[#08080c] border border-zinc-800"><span className="text-zinc-500">Reasoning</span><span className="font-medium">{best.best_reasoning_model?.name?.slice(0,30)}</span></div>
            <div className="flex justify-between p-2 rounded-lg bg-[#08080c] border border-zinc-800"><span className="text-zinc-500">Fastest</span><span className="font-medium">{best.fastest_model?.name} • {best.fastest_model?.score}</span></div>
          </div>
          <div className="mt-3 p-2 rounded-lg bg-violet-500/5 border border-violet-500/20 text-[10px]">
            <div className="font-medium text-violet-300">⚡ P1 Performance • P2 Quota • P0.5 Stability</div>
            <div className="mt-1 text-zinc-500">P1.1 Pre-warm: {p1.pre_warm||"167ms vs 1014ms 83% faster"} • Pool: {p1.http_pool_clients||0} clients • Cache hit: {p1.provider_cache_hit?"✅":"❌"} age {p1.provider_cache_age||0}s</div>
            <div className="text-zinc-500">P0.5: Deprecated {p05.deprecated_count||0} • Circuits OPEN {p05.circuits_open||0} • Model failures {Object.keys(p05.model_failures||{}).length}</div>
            <div className="text-zinc-500">P2.2 Quota: {p2q.total_providers_tracked||0} tracked • {p2q.providers_with_quota_headers||0} with headers • {p2q.total_429_hits_last_hour||0} 429/h • P2.3 Async critic: {p2ac.enabled?"✅":"❌"} {p2ac.description?.slice(0,60)||"TTFB 500ms vs 2-5s"}</div>
          </div>
        </div>
        <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
          <div className="text-[11px] font-medium">📊 Network • {ai.total_providers||26} providers {ai.models_available||726} models • P2 Enhanced</div>
          <div className="mt-2 text-[10px] font-mono text-zinc-500">{ai.verification_291}</div>
          <div className="mt-2 grid grid-cols-3 gap-1.5 text-[10px]">
            <div className="p-2 rounded-lg bg-emerald-500/5 border border-emerald-500/10"><div className="text-emerald-400 font-medium">{ai.providers_online} online</div><div className="text-zinc-600">healthy • {p1.http_pool_clients||0} pooled</div></div>
            <div className="p-2 rounded-lg bg-amber-500/5 border border-amber-500/10"><div className="text-amber-400 font-medium">{ai.providers_degraded} degraded</div><div className="text-zinc-600">{p05.circuits_open||0} circuits OPEN</div></div>
            <div className="p-2 rounded-lg bg-zinc-800 border border-zinc-700"><div className="text-zinc-400 font-medium">{ai.providers_discovered} discovered</div><div className="text-zinc-600">{ai.models_deprecated||0} deprecated • {p2q.total_429_hits_last_hour||0} 429/h</div></div>
          </div>
          <div className="mt-2 text-[11px]">Projects: <span className="font-bold">{projects.length}</span> • KIE 206 models • Groq 3 keys • Pollinations free • Quota tracked {p2q.total_providers_tracked||0}</div>
          <div className="mt-2 p-2 rounded-lg bg-zinc-800/50 border border-zinc-800 text-[10px] font-mono text-zinc-500">
            <div>P0: 12435 fix 200, 110k→413, token single source, rerouting</div>
            <div>P0.5: DEPRECATED 3x 404, cache key fix, backoff 60→300, Retry-After</div>
            <div>P1: pre-warm 83% faster 1014→167ms, version sync, max_completion_tokens</div>
            <div>P2: quota tracking real-time, network detailed, async critic 80% faster</div>
          </div>
        </div>
      </div>
    </div>
  );
}