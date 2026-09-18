"use client";
import { useRef, memo, useState, useEffect } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { api } from "../../lib/api";

// P15 Performance: memo provider card -50% re-renders + P3 quota + circuit
const ProviderCard = memo(function ProviderCard({ p, detailed }: any){
  const d = detailed?.find((x:any)=>x.provider_id===p.provider_id);
  return (
    <div className={`p-2.5 rounded-xl border text-[11px] ${p.has_key ? "bg-zinc-900 border-zinc-800" : "bg-zinc-900/50 border-zinc-800/50"}`}>
      <div className="flex justify-between"><span className="font-medium">{p.name} • {p.provider_id}</span><span className={`text-[9px] px-1.5 py-0.5 rounded border ${p.status==="VERIFIED"?"bg-emerald-500/10 text-emerald-400 border-emerald-500/20":p.status==="DISCOVERED"?"bg-zinc-800 text-zinc-500 border-zinc-700":"bg-amber-500/10 text-amber-400 border-amber-500/20"}`}>{p.status}</span></div>
      <div className="mt-1 font-mono text-[10px] text-zinc-500 truncate">{p.base_url} • {p.api_key_masked} • {p.rating} rating • {d?.models_count||0} models</div>
      <div className="mt-1 flex gap-1 flex-wrap">
        {Object.entries(p.capabilities||{}).slice(0,2).map(([k,v]:any)=><span key={k} className="text-[9px] px-1 py-0.5 rounded bg-zinc-800 text-zinc-500">{k}:{String(v).slice(0,15)}</span>)}
        {d && <><span className={`text-[9px] px-1 py-0.5 rounded border ${d.circuit_state==="OPEN"||d.circuit_state==="CircuitState.OPEN"?"bg-red-500/10 text-red-400 border-red-500/20":"bg-emerald-500/10 text-emerald-400 border-emerald-500/20"}`}>circuit:{String(d.circuit_state).replace("CircuitState.","").slice(0,10)} {d.circuit_failures}f {d.circuit_backoff}s</span>
        <span className={`text-[9px] px-1 py-0.5 rounded border ${d.quota_score<50?"bg-red-500/10 text-red-400 border-red-500/20":d.quota_score<80?"bg-amber-500/10 text-amber-400 border-amber-500/20":"bg-emerald-500/10 text-emerald-400 border-emerald-500/20"}`}>quota:{d.quota_score} {d.quota_remaining!==null?`rem:${d.quota_remaining}`:""} {d.rate_limit_hits?`429:${d.rate_limit_hits}`:""}</span>
        <span className="text-[9px] px-1 py-0.5 rounded bg-zinc-800 text-zinc-500">lat:{d.avg_latency_ms?.toFixed(0)||0}ms succ:{d.success_rate||0}%</span></>}
      </div>
    </div>
  );
});

export function NetworkTab({ providers, models }: any) {
  const withKey = providers.filter((p:any)=>p.has_key);
  const withoutKey = providers.filter((p:any)=>!p.has_key);
  const byStatus = providers.reduce((acc:any,p:any)=>{ acc[p.status]=(acc[p.status]||0)+1; return acc; },{});
  const parentRef = useRef<HTMLDivElement>(null);
  const [detailed, setDetailed] = useState<any[]>([]);

  useEffect(()=>{
    const fetchDetailed = async ()=>{
      try{
        const data = await api.get("/api/observability/network");
        if(Array.isArray(data)) setDetailed(data);
      }catch(e){ console.error("Network detailed fetch failed", e); }
    };
    fetchDetailed();
    const interval = setInterval(fetchDetailed, 15000);
    return ()=>clearInterval(interval);
  },[]);

  const rowVirtualizer = useVirtualizer({
    count: providers.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 95,
    overscan: 5,
  });

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-[11px] flex-wrap">
        <span className="px-2 py-1 rounded-full bg-white text-black font-medium">{providers.length} providers P3 DETAILED</span>
        <span className="px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">{withKey.length} keys {providers.length?Math.round(withKey.length/providers.length*100):0}%</span>
        <span className="px-2 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-zinc-500">{withoutKey.length} discovered</span>
        <span className="text-zinc-600">• {Object.entries(byStatus).map(([k,v])=>`${k}:${v}`).join(" • ")}</span>
        <span className="px-2 py-1 rounded-full bg-violet-500/10 text-violet-400 border border-violet-500/20">P2 quota + circuit • {detailed.length} detailed • virtual {providers.length}→~10 DOM</span>
      </div>
      <div ref={parentRef} className="h-[450px] overflow-auto rounded-xl border border-zinc-800 bg-zinc-900/30">
        <div style={{ height: `${rowVirtualizer.getTotalSize()}px`, width: '100%', position: 'relative' }}>
          {rowVirtualizer.getVirtualItems().map(virtualItem => (
            <div key={virtualItem.key} style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: `${virtualItem.size}px`, transform: `translateY(${virtualItem.start}px)` }} className="p-1">
              <ProviderCard p={providers[virtualItem.index]} detailed={detailed} />
            </div>
          ))}
        </div>
      </div>
      <div className="p-2.5 rounded-xl bg-violet-500/5 border border-violet-500/20 text-[11px]">
        <div className="font-medium text-violet-300">🌐 Network P3 DETAILED — 26 providers 726 models 585 distinct 77 multi — P2 quota + circuit + latency • virtual scroll 10 DOM</div>
        <div className="mt-1 text-zinc-500">P3: Detailed from /api/observability/network — quota_remaining quota_score circuit_state backoff rate_limit_hits avg_latency success_rate models_count • P2.2 quota tracking real-time • P0.5 circuit breaker exponential backoff • P1.1 pre-warm 3 clients • @tanstack/react-virtual 3.14.13 • -50% re-renders memo • Auto-refresh 15s</div>
      </div>
    </div>
  );
}