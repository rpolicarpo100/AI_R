"use client";
import { CHAT_COMMANDS } from "../lib/commands";

export function CommandsPalette({ filter, commands, onSelect }: any) {
  const filtered = commands.filter((c: any) => !filter || c.id.includes(filter) || c.desc.toLowerCase().includes(filter));
  
  return (
    <div className="mx-3 mb-2 rounded-2xl bg-zinc-900 border border-zinc-800 shadow-[0_8px_24px_rgba(0,0,0,0.4)] overflow-hidden max-h-[260px] overflow-auto">
      <div className="sticky top-0 px-3 py-2 bg-zinc-900 border-b border-zinc-800 flex items-center justify-between">
        <span className="text-[11px] font-medium text-zinc-400">Comandos • empoderam agentes • sugerem criticamente</span>
        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-violet-500/10 text-violet-400 border border-violet-500/20">{filtered.length} • /testa /audita /contesta</span>
      </div>
      <div className="p-1.5 space-y-0.5">
        {filtered.map((cmd: any) => (
          <button key={cmd.id} onClick={() => onSelect(cmd.label + " ")} className="w-full text-left px-3 py-2.5 rounded-xl hover:bg-zinc-800 flex items-center justify-between group transition">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-mono text-[12px] font-medium text-white">{cmd.label}</span>
                <span className={`w-1.5 h-1.5 rounded-full ${cmd.color==='emerald'?'bg-emerald-500':cmd.color==='amber'?'bg-amber-500':cmd.color==='red'?'bg-red-500':cmd.color==='violet'?'bg-violet-500':'bg-zinc-500'}`}></span>
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-zinc-800 text-zinc-500 group-hover:bg-zinc-700">{cmd.agents.length} agentes</span>
              </div>
              <div className="mt-1 text-[11px] leading-[1.4] text-zinc-400 group-hover:text-zinc-300 truncate">{cmd.desc}</div>
              <div className="mt-1 text-[10px] leading-[1.3] text-zinc-600 group-hover:text-zinc-500 truncate">↳ {cmd.critical}</div>
            </div>
            <div className="ml-2 text-[10px] px-2 py-1 rounded-full bg-zinc-800 text-zinc-500 group-hover:bg-white group-hover:text-black transition shrink-0">usar</div>
          </button>
        ))}
      </div>
      <div className="px-3 py-2 bg-[#0c0c10] border-t border-zinc-800 text-[10px] font-mono text-zinc-600">
        Você no centro • você cria orientando AI • terceiro olho aberto • contesta, critica, não fica na 1ª tentativa
      </div>
    </div>
  );
}

export function ShortcutsHelp({ onClose }: { onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="rounded-[20px] bg-[#111116] border border-zinc-800 p-6 max-w-[500px] w-full">
        <div className="flex justify-between items-center">
          <h3 className="font-semibold text-[14px]">⌨️ Atalhos • Chat Clean v1.2</h3>
          <button onClick={onClose} className="w-7 h-7 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center hover:bg-zinc-800 transition">✕</button>
        </div>
        <div className="mt-4 grid gap-2 text-[12px]">
          <div className="flex justify-between p-2.5 rounded-xl bg-zinc-900 border border-zinc-800"><span className="font-mono text-[11px]">Ctrl+K / Cmd+K</span><span className="text-zinc-500">Focar chat input</span></div>
          <div className="flex justify-between p-2.5 rounded-xl bg-zinc-900 border border-zinc-800"><span className="font-mono text-[11px]">Ctrl+L</span><span className="text-zinc-500">Limpar chat</span></div>
          <div className="flex justify-between p-2.5 rounded-xl bg-zinc-900 border border-zinc-800"><span className="font-mono text-[11px]">Ctrl+B</span><span className="text-zinc-500">Toggle Workplace</span></div>
          <div className="flex justify-between p-2.5 rounded-xl bg-zinc-900 border border-zinc-800"><span className="font-mono text-[11px]">Ctrl+J</span><span className="text-zinc-500">Toggle Agentes</span></div>
          <div className="flex justify-between p-2.5 rounded-xl bg-zinc-900 border border-zinc-800"><span className="font-mono text-[11px]">Ctrl+S</span><span className="text-zinc-500">Salvar arquivo (no editor)</span></div>
          <div className="flex justify-between p-2.5 rounded-xl bg-zinc-900 border border-zinc-800"><span className="font-mono text-[11px]">Ctrl+Shift+D</span><span className="text-zinc-500">Bulk delete</span></div>
          <div className="flex justify-between p-2.5 rounded-xl bg-zinc-900 border border-zinc-800"><span className="font-mono text-[11px]">Ctrl+/</span><span className="text-zinc-500">Mostrar atalhos</span></div>
          <div className="flex justify-between p-2.5 rounded-xl bg-zinc-900 border border-zinc-800"><span className="font-mono text-[11px]">Esc</span><span className="text-zinc-500">Fechar modais</span></div>
          <div className="flex justify-between p-2.5 rounded-xl bg-zinc-900 border border-zinc-800"><span className="font-mono text-[11px]">Drag&Drop</span><span className="text-zinc-500">Arrastar arquivos entre projetos</span></div>
          <div className="flex justify-between p-2.5 rounded-xl bg-emerald-500/5 border border-emerald-500/20"><span className="font-mono text-[11px] text-emerald-400">/testa /audita /contesta</span><span className="text-emerald-400">Comandos críticos v1.2</span></div>
        </div>
        <div className="mt-4 p-3 rounded-xl bg-violet-500/5 border border-violet-500/20 text-[11px] leading-[1.5] text-zinc-400">
          <span className="font-medium text-violet-300">v1.2 Clean:</span> Chat limpo sem templates, comandos empoderam agentes, sugerem criticamente, terceiro olho aberto. Componentes &lt;200 linhas, atalhos teclado, drag&drop workplace, hard delete + bulk + confirmação.
        </div>
      </div>
    </div>
  );
}
