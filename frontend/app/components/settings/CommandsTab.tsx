"use client";
import { CHAT_COMMANDS } from "../../lib/commands";

export function CommandsTab() {
  return (
    <div className="space-y-3">
      <div className="flex gap-2 text-[11px]"><span className="px-2 py-1 rounded-full bg-white text-black">{CHAT_COMMANDS.length} comandos</span><span className="px-2 py-1 rounded-full bg-violet-500/10 text-violet-400 border border-violet-500/20">empoderam agentes • terceiro olho aberto</span><span className="px-2 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-zinc-500">sem templates • você no centro</span></div>
      <div className="grid md:grid-cols-2 gap-2">
        {CHAT_COMMANDS.map(cmd=>(
          <div key={cmd.id} className={`p-2.5 rounded-xl border bg-zinc-900 ${cmd.color==="emerald"?"border-emerald-500/20":cmd.color==="amber"?"border-amber-500/20":cmd.color==="red"?"border-red-500/20":cmd.color==="violet"?"border-violet-500/20":cmd.color==="blue"?"border-blue-500/20":"border-zinc-800"}`}>
            <div className="flex justify-between"><span className="font-mono font-medium text-[12px]">{cmd.label}</span><span className="text-[9px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-500">{cmd.agents.length} agentes</span></div>
            <div className="text-[11px] text-zinc-400 mt-1">{cmd.desc}</div>
            <div className="text-[10px] text-zinc-500 mt-1">Agentes: {cmd.agents.join(", ")||"—"}</div>
            <div className="text-[10px] mt-1 px-2 py-1 rounded bg-[#08080c] border border-zinc-800"><span className="text-zinc-600">Crítica:</span> <span className="text-zinc-400">{cmd.critical}</span></div>
          </div>
        ))}
      </div>
      <div className="p-2.5 rounded-xl bg-zinc-900 border border-zinc-800 text-[11px]">
        <div className="font-medium">⌨️ Atalhos P11 CLEAN + Comandos</div>
        <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-1.5">
          <div className="p-2 rounded-lg bg-[#08080c] border border-zinc-800 flex justify-between"><span>Ctrl+K</span><span className="text-zinc-500">Focar chat</span></div>
          <div className="p-2 rounded-lg bg-[#08080c] border border-zinc-800 flex justify-between"><span>Ctrl+L</span><span className="text-zinc-500">Limpa chat</span></div>
          <div className="p-2 rounded-lg bg-[#08080c] border border-zinc-800 flex justify-between"><span>Ctrl+B</span><span className="text-zinc-500">Workplace</span></div>
          <div className="p-2 rounded-lg bg-[#08080c] border border-zinc-800 flex justify-between"><span>Ctrl+J</span><span className="text-zinc-500">Agentes</span></div>
          <div className="p-2 rounded-lg bg-[#08080c] border border-zinc-800 flex justify-between"><span>Ctrl+S</span><span className="text-zinc-500">Salvar</span></div>
          <div className="p-2 rounded-lg bg-[#08080c] border border-zinc-800 flex justify-between"><span>Ctrl+Shift+D</span><span className="text-zinc-500">Bulk delete</span></div>
          <div className="p-2 rounded-lg bg-[#08080c] border border-zinc-800 flex justify-between"><span>Ctrl+/</span><span className="text-zinc-500">Atalhos</span></div>
          <div className="p-2 rounded-lg bg-[#08080c] border border-zinc-800 flex justify-between"><span>Esc</span><span className="text-zinc-500">Fechar</span></div>
        </div>
        <div className="mt-2 p-2 rounded-lg bg-violet-500/5 border border-violet-500/20 text-[11px] text-zinc-400">P11: Chat limpo sem templates, comandos empoderam agentes, terceiro olho aberto, você no centro. Componentes &lt;200l, atalhos, drag&drop, bulk delete, hard delete com confirmação. 57 providers 726 models 219 measured 38.1% chat.</div>
      </div>
    </div>
  );
}
