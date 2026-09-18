"use client";

export function Header({ 
  activeTab, setActiveTab, projectsCount, providersWithKey, providersTotal, rigorPercent, agentsCount, onShowShortcuts, onToggleAgents, showAgentsPanel 
}: any) {
  return (
    <header className="sticky top-0 z-40 border-b border-zinc-900/80 bg-[#08080c]/80 backdrop-blur-xl">
      <div className="mx-auto max-w-[1600px] px-6 h-[56px] flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-white text-black flex items-center justify-center font-bold text-[11px]">OS</div>
            <span className="font-semibold text-[13px] tracking-tight">AI Provider OS</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-500">P18 v1.2 CLEAN • 60% CHAT</span>
          </div>
          <div className="hidden md:flex items-center gap-1.5 ml-4">
            <button onClick={()=>setActiveTab("chat")} className={`px-3 py-1.5 rounded-full text-[12px] font-medium transition ${activeTab==="chat" ? "bg-white text-black" : "text-zinc-500 hover:text-zinc-300"}`}>💬 Chat</button>
            <button onClick={()=>setActiveTab("settings")} className={`px-3 py-1.5 rounded-full text-[12px] font-medium transition ${activeTab==="settings" ? "bg-white text-black" : "text-zinc-500 hover:text-zinc-300"}`}>⚙️ Settings</button>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="hidden md:flex items-center gap-2 text-[11px]">
            <span className="text-zinc-500">{projectsCount} proj</span>
            <span className="w-px h-3 bg-zinc-800"></span>
            <span className="text-zinc-400">{providersWithKey}/{providersTotal} keys</span>
            <span className="w-px h-3 bg-zinc-800"></span>
            <span className={`px-2 py-0.5 rounded-full text-[10px] border ${rigorPercent >= 45 ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-amber-500/10 text-amber-400 border-amber-500/20"}`}>{rigorPercent}% rigor</span>
            <span className="w-px h-3 bg-zinc-800"></span>
            <span className="text-zinc-500">{agentsCount} agents</span>
          </div>
          <button onClick={onShowShortcuts} className="w-8 h-8 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center text-[11px] hover:text-white">⌨️</button>
          <button onClick={onToggleAgents} className={`w-8 h-8 rounded-full flex items-center justify-center text-[12px] border transition ${showAgentsPanel ? "bg-violet-600 text-white border-violet-500" : "bg-zinc-900 border-zinc-800 text-zinc-500 hover:text-zinc-300"}`}>🤖</button>
        </div>
      </div>
    </header>
  );
}
