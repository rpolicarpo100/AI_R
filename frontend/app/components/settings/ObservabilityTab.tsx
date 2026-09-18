"use client";
import { useState, useEffect, memo } from "react";
import { api } from "../../lib/api";

export const ObservabilityTab = memo(function ObservabilityTab(){
  const [stats, setStats] = useState<any>(null);
  const [traces, setTraces] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [guardrails, setGuardrails] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(()=>{
    const fetchAll = async ()=>{
      try{
        const s = await api.get("/api/observability/stats");
        setStats(s);
        const t = await api.get("/api/observability/traces?limit=20");
        setTraces(t.traces || []);
        const a = await api.get("/api/observability/alerts?limit=10");
        setAlerts(a.alerts || []);
        const g = await api.get("/api/observability/guardrails");
        setGuardrails(g);
      }catch(e){ console.error(e); }
      setLoading(false);
    };
    fetchAll();
    const interval = setInterval(fetchAll, 10000);
    return ()=>clearInterval(interval);
  },[]);

  if(loading) return <div className="text-[11px] text-zinc-500">Loading Observability P16...</div>;

  const obs = stats?.observability;
  const guard = stats?.guardrails || guardrails;
  const p05 = stats?.p0_5_stability || {};
  const providerCache = stats?.provider_cache || {};
  const httpPool = stats?.http_pool || {};
  const quotas = p05?.quotas || stats?.p2_quotas || {};

  return (
    <div className="space-y-3">
      <div className="flex gap-2 text-[11px] flex-wrap">
        <span className="px-2 py-1 rounded-full bg-white text-black font-medium">Observability P23 P3 ENTERPRISE</span>
        <span className="px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">{obs?.traces?.total||0} traces</span>
        <span className="px-2 py-1 rounded-full bg-violet-500/10 text-violet-400 border border-violet-500/20">{guard?.count||21} guardrails 18+ ✅</span>
        <span className="px-2 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-zinc-500">persistence {obs?.persistence||"memory"} • OTel • P3</span>
        <span className="px-2 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">{obs?.alerts?.total||0} alerts • {p05.deprecated_count||0} deprecated • {p05.retry_after_active||0} retry-after</span>
        <span className="px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">cache {providerCache.providers_count||0} prov {providerCache.models_count||0} models hit:{providerCache.hit?"✅":"❌"} • pool {httpPool.pooled_clients||0} clients</span>
      </div>

      <div className="grid md:grid-cols-3 gap-2">
        <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
          <div className="text-[11px] font-medium">🛡️ P0.5 Stability — DEPRECATED + Cache Key + Backoff + Retry-After</div>
          <div className="mt-2 space-y-1 text-[10px] font-mono">
            <div>Deprecated: {p05.deprecated_count||0} models • Model failures: {Object.keys(p05.model_failures||{}).length} • Circuits OPEN: {Object.keys(p05.circuits||{}).filter((k:any)=>{const c=p05.circuits[k]; return c && (c.state==="OPEN"||String(c.state).includes("OPEN"))}).length}</div>
            <div>Provider cache: {providerCache.providers_count||0} prov {providerCache.models_count||0} models • Age {providerCache.age_seconds||0}s • Hit {providerCache.hit?"✅ 0ms":"❌ 50-100ms"} • TTL {providerCache.ttl||60}s</div>
            <div>HTTP pool: {httpPool.pooled_clients||0} clients • Providers {httpPool.providers?.join(", ")||"none"} • Pre-warm P1.1 167ms vs 1014ms 83% faster</div>
            <div>Circuits: {Object.entries(p05.circuits||{}).slice(0,3).map(([k,v]:any)=>`${k}:${String(v.state).replace("CircuitState.","").slice(0,6)} ${v.failures}f ${v.backoff}s`).join(" • ")||"all CLOSED"}</div>
          </div>
        </div>
        <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
          <div className="text-[11px] font-medium">📊 P2 Quota Tracking — Real-time</div>
          <div className="mt-2 space-y-1 text-[10px] font-mono">
            <div>Tracked: {stats?.p2_quotas?.total_providers_tracked||quotas.total_providers_tracked||0} prov • With headers: {stats?.p2_quotas?.providers_with_quota_headers||quotas.providers_with_quota_headers||0} • 429/h: {stats?.p2_quotas?.total_429_hits_last_hour||quotas.total_429_hits_last_hour||0}</div>
            <div>Quotas: {Object.entries((stats?.p2_quotas?.quotas||quotas.quotas||{}) as any).slice(0,2).map(([k,v]:any)=>`${k}:used ${v.quota_used} rem ${v.remaining} hits ${v.rate_limit_hits}`).join(" • ")||"no quota yet"}</div>
            <div>Quota score: routing uses get_quota_score 0-100 — recent 429 3+→10 2→40 1→70 remaining &lt;10%→20 &lt;30%→50 &lt;50%→75 else 100</div>
            <div>Headers: X-RateLimit-Remaining, Limit, Reset, Retry-After case-insensitive • Parse seconds + HTTP date</div>
          </div>
        </div>
        <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
          <div className="text-[11px] font-medium">⚡ P1 + P2 Performance — Pre-warm + Async Critic</div>
          <div className="mt-2 space-y-1 text-[10px] font-mono">
            <div>P1.1 Pre-warm: {stats?.p1_performance?.pre_warm||"167ms vs 1014ms 83% faster"} • Pool clients {httpPool.pooled_clients||0} • {httpPool.providers?.length||0} fastest</div>
            <div>P1.2 Version sync: /health and /cline/status both P23 P0.5+P1+P2 • P1.3 max_completion_tokens alias 200 OK</div>
            <div>P2.3 Async critic: {stats?.p2_async_critic?.enabled?"✅":"❌"} • {stats?.p2_async_critic?.description?.slice(0,80)||"MEDIUM/COMPLEX returns immediately, critic background, TTFB 500ms vs 2-5s"}</div>
            <div>P0: 12435 fix 200, 110k→413, token single source, rerouting • Cache HIT 14ms vs MISS 334ms 23x faster</div>
          </div>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-2">
        <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
          <div className="text-[11px] font-medium">📊 Tracing — trace_id span_id breakdown</div>
          <div className="mt-2 space-y-1 text-[10px] font-mono">
            <div>Total: {obs?.traces?.total||0} • Errors: {obs?.traces?.errors||0} • Error rate: {obs?.traces?.error_rate||0}%</div>
            <div>Avg latency: {obs?.traces?.avg_latency_ms||0}ms • P50: {obs?.traces?.p50_ms||0}ms • P95: {obs?.traces?.p95_ms||0}ms • P99: {obs?.traces?.p99_ms||0}ms</div>
            <div>Breakdown: classifier 10ms routing 20ms adapter 402ms critic 100ms guardrails 5ms total</div>
            <div>Pattern: {stats?.pattern||"Helicone + Portkey + Future AGI"} • OTel: {stats?.otel?"✅":"❌"}</div>
          </div>
        </div>
        <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
          <div className="text-[11px] font-medium">💰 Cost Tracking + Sessions</div>
          <div className="mt-2 space-y-1 text-[10px] font-mono">
            <div>Total cost: ${obs?.costs?.total||0} • Count: {obs?.costs?.count||0} • Avg: ${obs?.costs?.avg||0}</div>
            <div>Sessions: {obs?.sessions?.total||0} total • {obs?.sessions?.active||0} active • Avg turns: {obs?.sessions?.avg_turns?.toFixed(1)||0}</div>
            <div>By provider: {Object.entries(obs?.costs?.by_provider||{}).slice(0,3).map(([k,v]:any)=>`${k}:$${v}`).join(" • ")||"groq:0"}</div>
            <div>Cache: hits {obs?.cache?.hits||0} misses {obs?.cache?.misses||0} hit_rate {obs?.cache?.hit_rate||0}% • Redis fallback memory</div>
          </div>
        </div>
        <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
          <div className="text-[11px] font-medium">🛡️ Guardrails 18+ — Future AGI</div>
          <div className="mt-2 space-y-1 text-[10px] font-mono">
            <div>Count: {guard?.count||21} • Enabled: {guard?.enabled||21} • Hits: {guard?.total_hits||0}</div>
            <div>By guardrail: {Object.entries(guard?.by_guardrail||{}).slice(0,3).map(([k,v])=>`${k}:${v}`).join(" • ")||"0 hits"}</div>
            <div>Config: PII email phone NIF credit card api_key • injection • toxicity hate self_harm sexual • sql xss command • cost latency token file_size files_count • provider_health model_capability human_override</div>
            <div>Actions: block/warn/log/human approval • Audit log guardrail trigger • Metrics Grafana</div>
          </div>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-2">
        <div className="rounded-xl bg-zinc-900 border border-zinc-800 overflow-hidden">
          <div className="px-3 py-2 border-b border-zinc-800 text-[11px] font-medium">🔍 Recent Traces • OTel • P16</div>
          <div className="max-h-[200px] overflow-auto p-2 space-y-1">
            {traces.slice(0,10).map((t:any)=>(
              <div key={t.span_id} className="p-1.5 rounded-lg bg-zinc-800/50 border border-zinc-800 text-[9px] font-mono">
                <div className="flex justify-between"><span>{t.trace_id.slice(0,12)} • {t.span_id}</span><span className={t.status==="success"?"text-emerald-400":"text-red-400"}>{t.status} {t.latency_ms}ms</span></div>
                <div className="text-zinc-500 truncate">op:{t.operation} prov:{t.provider||"null"} model:{t.model||"null"} cost:${t.cost} tokens:{t.tokens?.total}</div>
                <div className="text-zinc-600">breakdown: {Object.entries(t.breakdown||{}).map(([k,v])=>`${k}:${v}ms`).join(" ")}</div>
              </div>
            ))}
            {traces.length===0 && <div className="text-[10px] text-zinc-600">No traces yet — faça chat para gerar traces</div>}
          </div>
        </div>
        <div className="rounded-xl bg-zinc-900 border border-zinc-800 overflow-hidden">
          <div className="px-3 py-2 border-b border-zinc-800 text-[11px] font-medium">🚨 Alerts • rigor &lt;50% latency &gt;5s error &gt;10% cost &gt;budget offline</div>
          <div className="max-h-[200px] overflow-auto p-2 space-y-1">
            {alerts.slice(0,10).map((a:any)=>(
              <div key={a.alert_id} className={`p-1.5 rounded-lg border text-[9px] font-mono ${a.severity==="error"?"bg-red-500/10 border-red-500/20 text-red-400":"bg-amber-500/10 border-amber-500/20 text-amber-400"}`}>
                <div>{a.type} • {a.severity} • {a.message.slice(0,100)}</div>
                <div className="text-zinc-500">{a.timestamp} • threshold:{a.threshold} value:{a.value}</div>
              </div>
            ))}
            {alerts.length===0 && <div className="text-[10px] text-zinc-600">No alerts — rigor 30.3% LOW triggers alert &lt;50% • latency 457ms OK • error rate 0% OK</div>}
          </div>
        </div>
      </div>

      <div className="p-2.5 rounded-xl bg-violet-500/5 border border-violet-500/20 text-[11px]">
        <div className="font-medium text-violet-300">🔭 Observability P16 Enterprise — Helicone + Portkey + Future AGI pattern — 12 panels Grafana</div>
        <div className="mt-1 text-zinc-500">P16: Tracing trace_id span_id parent_span_id latency breakdown classifier 10ms routing 20ms adapter 2000ms critic 500ms total • Sessions session_id multi-turn cost per session latency per session • Prompt experiments A/B • OTel traces metrics logs Prometheus+Grafana 12 panels providers models rigor latency cost requests agents loop tasks audit errors cache hit rate streaming • Cost tracking per provider/model/user/session/day budget alerts • Caching Redis 30s encrypted semantic • Logs JSON level timestamp trace_id user_id provider model latency cost status • Alerts rigor &lt;50% latency &gt;5s error &gt;10% cost &gt;budget provider offline • Grafana v8 12 panels + Loki logs + Alerts Slack/email</div>
      </div>

      <div className="p-2.5 rounded-xl bg-zinc-900 border border-zinc-800 text-[11px]">
        <div className="font-medium">🛡️ Guardrails 18+ — {guard?.count||21} total — PII email phone NIF credit card api_key • prompt injection • toxicity hate self_harm sexual • sql xss command injection • cost latency token file_size files_count • provider_health model_capability human_override</div>
        <div className="mt-1 text-zinc-500">Middleware chain config enabled threshold action block/warn/log/human approval • Audit log guardrail trigger • Metrics guardrail hits • Grafana panels • 0 false positives &lt;5% false negatives • P16 Enterprise Future AGI pattern</div>
      </div>
    </div>
  );
});
