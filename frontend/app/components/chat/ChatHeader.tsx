"use client";

export function ChatHeader({ chatMode, setChatMode, selectedModelId, distinctModels, streamEnabled, setStreamEnabled, workplaceOpen, setWorkplaceOpen, projectsCount }: any) {
  return (
    <div className="px-4 py-3 border-b border-zinc-900/80 flex items-center justify-between bg-[#111116]">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${chatMode==="auto" ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]" : "bg-violet-500 shadow-[0_0_8px_rgba(139,92,246,0.4)]"}`}></div>
          <span className="text-[12px] font-[550] tracking-tight">{chatMode==="auto" ? "AUTO" : `MANUAL`}</span>
          <span className="text-[11px] text-zinc-600 font-mono hidden md:block">{chatMode==="auto" ? "ranking + failover • 26 provs" : selectedModelId.slice(0,32)}</span>
        </div>
        <div className="flex items-center gap-1 ml-1 p-0.5 rounded-full bg-zinc-900 border border-zinc-800">
          <button onClick={()=>setChatMode("auto")} className={`px-2.5 py-1 rounded-full text-[11px] font-medium transition ${chatMode==="auto" ? "bg-white text-black shadow-sm" : "text-zinc-500 hover:text-zinc-300"}`}>AUTO</button>
          <button onClick={()=>setChatMode("manual")} className={`px-2.5 py-1 rounded-full text-[11px] font-medium transition ${chatMode==="manual" ? "bg-white text-black shadow-sm" : "text-zinc-500 hover:text-zinc-300"}`}>MANUAL</button>
        </div>
      </div>
      <div className="flex items-center gap-1.5">
        <button onClick={()=>setStreamEnabled(!streamEnabled)} className={`px-2.5 py-1 rounded-full text-[10px] font-medium border transition ${streamEnabled ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-zinc-900 text-zinc-500 border-zinc-800 hover:border-zinc-700"}`}>
          <span className="flex items-center gap-1"><span className={`w-1 h-1 rounded-full ${streamEnabled ? "bg-emerald-500 animate-pulse" : "bg-zinc-600"}`}></span>{streamEnabled ? "stream" : "no-stream"}</span>
        </button>
        <button onClick={()=>setWorkplaceOpen(!workplaceOpen)} className={`px-2.5 py-1 rounded-full text-[10px] font-medium border transition ${workplaceOpen ? "bg-white text-black border-white" : "bg-zinc-900 text-zinc-500 border-zinc-800 hover:border-zinc-700"}`}>📁 {projectsCount}</button>
      </div>
    </div>
  );
}

export function ChatModelSelect({ selectedModelId, setSelectedModelId, distinctModels }: any) {
  return (
    <div className="px-4 py-2.5 border-b border-zinc-900/80 bg-zinc-900/20">
      <select value={selectedModelId} onChange={e=>setSelectedModelId(e.target.value)} className="w-full rounded-xl bg-zinc-900 border border-zinc-800 px-3 py-2 text-[12px] outline-none focus:border-zinc-700 focus:bg-zinc-900 transition">
        {distinctModels.slice(0,50).map((m:any)=>(
          <option key={m.base_id} value={m.base_id}>{m.base_id} • {m.overall_score} • {m.providers_count} provs</option>
        ))}
      </select>
    </div>
  );
}
