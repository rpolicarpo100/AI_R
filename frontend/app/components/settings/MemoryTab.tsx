"use client";
import { useEffect, useState } from "react";

export function MemoryTab() {
  const [stats, setStats] = useState<any>(null);
  const [memories, setMemories] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [filterCategory, setFilterCategory] = useState("");
  const [filterFreeType, setFilterFreeType] = useState("");

  useEffect(() => {
    fetch('/api/memory/stats').then(r=>r.json()).then(d=>setStats(d)).catch(()=>{});
    fetch('/api/memory/list?limit=50').then(r=>r.json()).then(d=>setMemories(d.memories||[])).catch(()=>{});
    fetch('/api/memory/categories').then(r=>r.json()).then(d=>setCategories(d.categories||[])).catch(()=>{});
  }, []);

  const doSearch = async () => {
    if (!search.trim()) return;
    const res = await fetch(`/api/memory/search?q=${encodeURIComponent(search)}&limit=20`);
    const data = await res.json();
    setSearchResults(data.results||[]);
  };

  const doFilter = async () => {
    let url = `/api/memory/list?limit=50`;
    if (filterCategory) url += `&category=${filterCategory}`;
    if (filterFreeType) url += `&free_type=${filterFreeType}`;
    const res = await fetch(url);
    const data = await res.json();
    setMemories(data.memories||[]);
  };

  const archiveSite = async (url: string) => {
    const res = await fetch(`/api/memory/archive?url=${encodeURIComponent(url)}`, {method: 'POST'});
    const data = await res.json();
    alert(`Archive ${url}: ${data.status} — HTTP ${data.http_status} — rating ${data.rating?.toFixed(1)} — size ${data.content_size}`);
    // Refresh
    fetch('/api/memory/list?limit=50').then(r=>r.json()).then(d=>setMemories(d.memories||[]));
  };

  const auditMemory = async () => {
    const res = await fetch('/api/memory/audit?limit=10&concurrency=3', {method: 'POST'});
    const data = await res.json();
    alert(`Audit: ${data.summary} — ONLINE ${data.online} REACHABLE ${data.reachable_but_error} OFFLINE ${data.offline}`);
    fetch('/api/memory/stats').then(r=>r.json()).then(d=>setStats(d));
    fetch('/api/memory/list?limit=50').then(r=>r.json()).then(d=>setMemories(d.memories||[]));
  };

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/20">
        <div className="text-[12px] font-bold text-emerald-300">🧠 Apikeyless Memory — Melhora memória da AI — arquiva sites apikeyless para acesso rápido e análises rápidas</div>
        <div className="mt-1 text-[11px] text-zinc-400">Repositório continuamente aumentado, auditado, rating e categoria — 15 seed reais verificados + increase contínuo — 100% confiança com realismo</div>
        <div className="mt-2 flex gap-2 flex-wrap">
          <span className="text-[10px] px-2 py-1 rounded-full border bg-emerald-500/10 text-emerald-400 border-emerald-500/20">{stats?.total||0} SITES ARQUIVADOS</span>
          <span className="text-[10px] px-2 py-1 rounded-full border bg-zinc-800 text-zinc-400 border-zinc-700">Avg rating {stats?.avg_rating?.toFixed(1)||0}</span>
          <span className="text-[10px] px-2 py-1 rounded-full border bg-emerald-500/10 text-emerald-400 border-emerald-500/20">{stats?.rating_gte80||0} GTE80 BOM</span>
          <span className="text-[10px] px-2 py-1 rounded-full border bg-amber-500/10 text-amber-400 border-amber-500/20">{stats?.rating_gte50||0} GTE50</span>
          <button onClick={auditMemory} className="text-[10px] px-3 py-1 rounded-full bg-white text-black font-medium hover:bg-zinc-200">🔍 AUDITAR 10 SITES</button>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid md:grid-cols-3 gap-2">
          <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
            <div className="text-[10px] text-zinc-500">Categorias</div>
            <div className="mt-1 text-[11px] space-y-1">
              {Object.entries(stats.category_count||{}).map(([cat,count])=>(
                <div key={cat} className="flex justify-between"><span>{cat}</span><span className="text-emerald-400">{count as number}</span></div>
              ))}
            </div>
          </div>
          <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
            <div className="text-[10px] text-zinc-500">Free Type</div>
            <div className="mt-1 text-[11px] space-y-1">
              {Object.entries(stats.free_type_count||{}).map(([ft,count])=>(
                <div key={ft} className="flex justify-between"><span>{ft||'no_card'}</span><span className="text-emerald-400">{count as number}</span></div>
              ))}
            </div>
          </div>
          <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
            <div className="text-[10px] text-zinc-500">Status Auditado</div>
            <div className="mt-1 text-[11px] space-y-1">
              {Object.entries(stats.status_count||{}).map(([st,count])=>(
                <div key={st} className="flex justify-between"><span>{st}</span><span className={st==='ONLINE'?'text-emerald-400':st==='OFFLINE'?'text-red-400':'text-amber-400'}>{count as number}</span></div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Search e filtros */}
      <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
        <div className="text-[10px] text-zinc-500 mb-2">🔍 Busca para análises rápidas + filtros para acesso rápido</div>
        <div className="flex gap-2 flex-wrap">
          <input value={search} onChange={e=>setSearch(e.target.value)} onKeyDown={e=>e.key==='Enter'&&doSearch()} placeholder="Busca: free, eu, gdpr, llm, image, ollama..." className="px-3 py-1.5 rounded-full bg-zinc-800 border border-zinc-700 text-[11px] w-[250px]" />
          <button onClick={doSearch} className="px-3 py-1.5 rounded-full bg-white text-black text-[11px] font-medium">Buscar</button>
          <select value={filterCategory} onChange={e=>setFilterCategory(e.target.value)} className="px-3 py-1.5 rounded-full bg-zinc-800 border border-zinc-700 text-[11px]">
            <option value="">Todas categorias</option>
            {categories.map((c:any)=><option key={c.category} value={c.category}>{c.category} ({c.count})</option>)}
          </select>
          <select value={filterFreeType} onChange={e=>setFilterFreeType(e.target.value)} className="px-3 py-1.5 rounded-full bg-zinc-800 border border-zinc-700 text-[11px]">
            <option value="">Todos free_type</option>
            <option value="remote">remote — free_no_key_remote</option>
            <option value="local">local — free_no_key_local</option>
            <option value="no_card">no_card — free_no_card</option>
          </select>
          <button onClick={doFilter} className="px-3 py-1.5 rounded-full bg-zinc-800 border border-zinc-700 text-[11px]">Filtrar</button>
        </div>
        
        {searchResults.length>0 && (
          <div className="mt-3">
            <div className="text-[11px] font-medium">Resultados busca "{search}" — {searchResults.length}</div>
            <div className="mt-2 grid gap-2">
              {searchResults.map((r:any)=>(
                <div key={r.id} className="p-2 rounded-lg bg-zinc-800 border border-zinc-700">
                  <div className="flex justify-between items-start">
                    <div className="text-[11px] font-medium">{r.name}</div>
                    <div className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Score {r.score} — Rating {r.rating?.toFixed(0)}</div>
                  </div>
                  <div className="mt-1 text-[10px] text-zinc-500">{r.description?.slice(0,120)}... — {r.category} — {r.url}</div>
                  <div className="mt-1 text-[10px] text-zinc-600">{r.content_summary?.slice(0,100)}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Lista memória — acesso rápido rating desc */}
      <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
        <div className="text-[10px] text-zinc-500 mb-2">📚 Repositório — {memories.length} sites — ordenado por rating desc para acesso rápido — continuamente aumentado, auditado, rating e categoria</div>
        <div className="grid gap-2 max-h-[400px] overflow-auto">
          {memories.map((m:any)=>(
            <div key={m.id} className="p-2 rounded-lg bg-zinc-800 border border-zinc-700">
              <div className="flex justify-between items-start gap-2">
                <div className="text-[11px] font-medium flex-1">{m.name}</div>
                <div className="flex gap-1">
                  <span className={`text-[9px] px-2 py-0.5 rounded-full border ${m.rating>=80?'bg-emerald-500/10 text-emerald-400 border-emerald-500/20':m.rating>=50?'bg-amber-500/10 text-amber-400 border-amber-500/20':'bg-red-500/10 text-red-400 border-red-500/20'}`}>Rating {m.rating?.toFixed(0)}</span>
                  <span className="text-[9px] px-2 py-0.5 rounded-full bg-zinc-700 text-zinc-400 border border-zinc-600">{m.category}</span>
                  <span className={`text-[9px] px-2 py-0.5 rounded-full border ${m.status==='ONLINE'?'bg-emerald-500/10 text-emerald-400 border-emerald-500/20':m.status==='OFFLINE'?'bg-red-500/10 text-red-400 border-red-500/20':'bg-amber-500/10 text-amber-400 border-amber-500/20'}`}>{m.status}</span>
                </div>
              </div>
              <div className="mt-1 text-[10px] text-zinc-500">{m.description?.slice(0,150)}...</div>
              <div className="mt-1 flex gap-2 flex-wrap items-center">
                <span className="text-[9px] text-zinc-600">{m.url}</span>
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-zinc-700 text-zinc-400">free_type: {m.free_type||'no_card'} {m.free_no_key_remote?'REMOTE':''} {m.free_no_key_local?'LOCAL':''}</span>
                <span className="text-[9px] text-zinc-600">latency {m.latency_ms}ms — audits {m.audit_count} — size {m.content_size}</span>
                <button onClick={()=>archiveSite(m.url)} className="text-[9px] px-2 py-0.5 rounded-full bg-white text-black font-medium">📥 Arquivar para acesso rápido</button>
              </div>
              {m.tags && (
                <div className="mt-1 flex gap-1 flex-wrap">
                  {m.tags.slice(0,6).map((tag:string)=><span key={tag} className="text-[8px] px-1.5 py-0.5 rounded bg-zinc-700 text-zinc-500">{tag}</span>)}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Como aumentar continuamente */}
      <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
        <div className="text-[11px] font-medium">🔄 Como aumentar continuamente repositório — auditado e rating e categoria</div>
        <div className="mt-1 text-[10px] text-zinc-500 space-y-1">
          <div><strong>Seed inicial:</strong> 15 sites reais verificados 2026-09-18 — pollinations 31 models free remote, ovhcloud 2 models 2 RPM 500M/5M per day EU DE/FI, freetheai 80+ models Discord key, puter browser, berget Sweden EU-sovereign, opper Sweden 700+ models zero retention, eurouter Netherlands 100+ models 10K req/mo free GDPR, greenpt French Scaleway GDPR, ollama local, lm_studio local, cloudflare 10K neurons/day, huggingface 300+ models, perchance image, jina 10M embedding, voyage 50M embedding</div>
          <div><strong>Aumentar:</strong> POST /api/memory/increase com [{"url":"https://...","name":"...","category":"llm_free_remote","rating":80,"tags":["free"]}] — já testado libertai + llmwise → 15→17 total</div>
          <div><strong>Auditar:</strong> POST /api/memory/audit?limit=20&concurrency=5 — fetch conteúdo markdown 20K + summary 500 chars + rating breakdown uptime latency free_quality gdpr eu_sovereign content_quality overall — audit_history last 20</div>
          <div><strong>Arquivar:</strong> POST /api/memory/archive?url=... — fetch conteúdo para acesso rápido — content_markdown 20K + content_summary 500 chars + content_hash + content_size — latency_ms + status ONLINE/OFFLINE/REACHABLE_BUT_ERROR</div>
          <div><strong>Rating:</strong> 0-100 baseado em uptime, latency (0ms=100, 5000ms=0), free_quality (100 free_no_key, 80 free_no_card, 50 needs key), gdpr (90 se eu/gdpr tag), eu_sovereign (100 se eu_gdpr), content_quality — overall avg breakdown</div>
          <div><strong>Categoria:</strong> llm_free_remote, llm_free_local, llm_free_no_card, llm_eu_sovereign, image_free, video_free, audio_free, embedding_free, docs, code, etc + subcategory eu_gdpr, discord_key, browser, local_setup, cloudflare, huggingface, etc</div>
          <div><strong>Acesso rápido:</strong> GET /api/memory/list?category=llm_free_remote&min_rating=80&free_type=remote&limit=50 — ordenado por rating desc — 100% rápido, sem fetch externo, conteúdo já arquivado local</div>
          <div><strong>Análises rápidas:</strong> GET /api/memory/search?q=eu&limit=20 — busca semântica simples por nome, descrição, tags, categoria, url — score + rating — para análises rápidas</div>
          <div><strong>Contínuo:</strong> APScheduler daily audit + increase via web_search novos apikeyless sites — futuro: adicionar job scheduler para auditar 20 sites/dia e buscar novos sites via web_search free AI API 2026</div>
        </div>
      </div>
    </div>
  );
}
