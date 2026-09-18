"use client";
import { useState } from "react";

export function DeleteModal({ project, onClose, onArchive, onHardDelete }: any) {
  const [deleteHard, setDeleteHard] = useState(false);
  const [confirmText, setConfirmText] = useState("");
  const [confirmChecked, setConfirmChecked] = useState(false);

  if (!project) return null;

  const isConfirmValid = confirmText === project.project_id && confirmChecked;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="rounded-[20px] bg-[#111116] border border-zinc-800 p-6 max-w-[420px] w-full shadow-[0_16px_48px_rgba(0,0,0,0.5)]">
        <div className="flex items-start justify-between gap-3">
          <div className="w-8 h-8 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center text-[14px]">🗑️</div>
          <button onClick={onClose} className="w-7 h-7 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-500 hover:text-zinc-300 transition">✕</button>
        </div>

        <h3 className="mt-3 font-[650] text-[14px] tracking-tight">Eliminar projeto?</h3>
        <div className="mt-2 p-2.5 rounded-xl bg-zinc-900 border border-zinc-800">
          <div className="text-[11px] font-mono text-zinc-500">ID: {project.project_id}</div>
          <div className="text-[12px] font-medium text-white mt-1 truncate">{project.name}</div>
          <div className="text-[11px] text-zinc-500 mt-1">{project.file_count || Object.keys(project.files||{}).length} arquivos • {project.type} • {project.language}</div>
        </div>

        <div className="mt-4 space-y-3">
          <div className="flex rounded-full bg-zinc-900 border border-zinc-800 p-0.5">
            <button onClick={()=>setDeleteHard(false)} className={`flex-1 py-1.5 rounded-full text-[11px] font-medium transition ${!deleteHard ? "bg-white text-black" : "text-zinc-500 hover:text-zinc-300"}`}>📦 Arquivar (soft)</button>
            <button onClick={()=>setDeleteHard(true)} className={`flex-1 py-1.5 rounded-full text-[11px] font-medium transition ${deleteHard ? "bg-red-600 text-white" : "text-zinc-500 hover:text-zinc-300"}`}>💥 Hard Delete</button>
          </div>

          {!deleteHard ? (
            <div className="p-3 rounded-xl bg-amber-500/5 border border-amber-500/15">
              <div className="text-[11px] font-medium text-amber-300">Soft delete — arquiva</div>
              <div className="mt-1 text-[11px] leading-[1.4] text-zinc-500">Projeto vai para arquivados, pode restaurar via API. Generations e branches mantidos. Você no centro, você decide.</div>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="p-3 rounded-xl bg-red-500/5 border border-red-500/15">
                <div className="text-[11px] font-medium text-red-300">⚠️ Hard delete — definitivo, irreversível</div>
                <div className="mt-1 text-[11px] leading-[1.4] text-zinc-500">Elimina projeto + generations + branches permanentemente. Não há restore. Audit log registra com severity warning. Terceiro olho: confirme conscientemente.</div>
              </div>

              <div className="space-y-2.5">
                <div>
                  <label className="text-[11px] font-medium text-zinc-400">Digite o project_id para confirmar:</label>
                  <div className="mt-1.5 relative">
                    <input 
                      value={confirmText} 
                      onChange={e=>setConfirmText(e.target.value)} 
                      placeholder={project.project_id} 
                      className="w-full rounded-xl bg-zinc-900 border border-zinc-800 px-3 py-2.5 text-[12px] font-mono outline-none focus:border-red-500/30 focus:bg-zinc-900 transition" 
                    />
                    {confirmText && (
                      <span className={`absolute right-2.5 top-2.5 text-[10px] px-1.5 py-0.5 rounded-full border ${isConfirmValid ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-red-500/10 text-red-400 border-red-500/20"}`}>
                        {isConfirmValid ? "✓ válido" : "✗ inválido"}
                      </span>
                    )}
                  </div>
                </div>

                <label className="flex items-start gap-2 p-2.5 rounded-xl bg-zinc-900 border border-zinc-800 hover:border-zinc-700 cursor-pointer transition">
                  <input type="checkbox" checked={confirmChecked} onChange={e=>setConfirmChecked(e.target.checked)} className="mt-0.5 rounded" />
                  <span className="text-[11px] leading-[1.4] text-zinc-400">Confirmo que quero eliminar definitivamente <span className="font-mono text-white">{project.project_id}</span> e entendo que é irreversível. Audit log será gerado.</span>
                </label>
              </div>
            </div>
          )}

          <div className="flex gap-2 pt-1">
            <button onClick={onClose} className="flex-1 py-2.5 rounded-full bg-zinc-900 border border-zinc-800 text-[12px] font-medium hover:bg-zinc-800 transition">Cancelar (Esc)</button>
            {deleteHard ? (
              <button onClick={()=>onHardDelete(project.project_id, confirmText)} disabled={!isConfirmValid} className="flex-1 py-2.5 rounded-full bg-red-600 text-white text-[12px] font-medium hover:bg-red-700 disabled:opacity-30 disabled:cursor-not-allowed transition">💥 Hard Delete definitivo</button>
            ) : (
              <button onClick={()=>onArchive(project.project_id)} className="flex-1 py-2.5 rounded-full bg-white text-black text-[12px] font-medium hover:bg-zinc-100 transition">📦 Arquivar projeto</button>
            )}
          </div>

          {!deleteHard && (
            <button onClick={()=>setDeleteHard(true)} className="w-full text-[11px] text-zinc-500 hover:text-red-400 transition">Quero hard delete definitivo e irreversível →</button>
          )}
        </div>

        <div className="mt-4 flex items-center gap-2 text-[10px] font-mono text-zinc-600">
          <span className="w-1 h-1 rounded-full bg-violet-500"></span>
          <span>v1.2 Clean: Soft arquiva (restore via /restore), Hard elimina + generations + branches • Esc fecha • Você no centro</span>
        </div>
      </div>
    </div>
  );
}

export function BulkDeleteModal({ count, projectIds, onClose, onArchiveBulk, onHardDeleteBulk }: any) {
  const [hard, setHard] = useState(false);
  const [confirmText, setConfirmText] = useState("");
  const [checked, setChecked] = useState(false);

  if (count===0) return null;

  const isConfirmValid = confirmText === "BULK_DELETE_CONFIRM" && checked;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="rounded-[20px] bg-[#111116] border border-zinc-800 p-6 max-w-[440px] w-full shadow-[0_16px_48px_rgba(0,0,0,0.5)]">
        <div className="flex items-start justify-between gap-3">
          <div className="w-8 h-8 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-[14px]">🗑️</div>
          <button onClick={onClose} className="w-7 h-7 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-500 hover:text-zinc-300 transition">✕</button>
        </div>

        <h3 className="mt-3 font-[650] text-[14px] tracking-tight">Bulk Delete • {count} projetos</h3>
        <div className="mt-2 p-2.5 rounded-xl bg-zinc-900 border border-zinc-800 max-h-[80px] overflow-auto">
          <div className="text-[10px] font-mono text-zinc-500">{projectIds.slice(0,5).join(", ")}{count>5 ? ` +${count-5} mais` : ""}</div>
        </div>

        <div className="mt-4 space-y-3">
          <div className="flex rounded-full bg-zinc-900 border border-zinc-800 p-0.5">
            <button onClick={()=>setHard(false)} className={`flex-1 py-1.5 rounded-full text-[11px] font-medium transition ${!hard ? "bg-white text-black" : "text-zinc-500"}`}>📦 Arquivar {count}</button>
            <button onClick={()=>setHard(true)} className={`flex-1 py-1.5 rounded-full text-[11px] font-medium transition ${hard ? "bg-red-600 text-white" : "text-zinc-500"}`}>💥 Hard Delete {count}</button>
          </div>

          {hard && (
            <div className="space-y-2.5">
              <div className="p-3 rounded-xl bg-red-500/5 border border-red-500/15">
                <div className="text-[11px] font-medium text-red-300">⚠️ Bulk hard delete — {count} projetos definitivo</div>
                <div className="mt-1 text-[11px] leading-[1.4] text-zinc-500">Elimina {count} projetos + generations + branches permanentemente. Audit log warning. Confirmação obrigatória.</div>
              </div>
              <div>
                <label className="text-[11px] font-medium text-zinc-400">Digite BULK_DELETE_CONFIRM:</label>
                <input value={confirmText} onChange={e=>setConfirmText(e.target.value)} placeholder="BULK_DELETE_CONFIRM" className="mt-1.5 w-full rounded-xl bg-zinc-900 border border-zinc-800 px-3 py-2.5 text-[12px] font-mono outline-none focus:border-red-500/30 transition" />
              </div>
              <label className="flex items-start gap-2 p-2.5 rounded-xl bg-zinc-900 border border-zinc-800 cursor-pointer">
                <input type="checkbox" checked={checked} onChange={e=>setChecked(e.target.checked)} className="mt-0.5 rounded" />
                <span className="text-[11px] leading-[1.4] text-zinc-400">Confirmo bulk hard delete de {count} projetos, irreversível, com audit log.</span>
              </label>
            </div>
          )}

          <div className="flex gap-2 pt-1">
            <button onClick={onClose} className="flex-1 py-2.5 rounded-full bg-zinc-900 border border-zinc-800 text-[12px] font-medium hover:bg-zinc-800 transition">Cancelar (Esc)</button>
            {hard ? (
              <button onClick={onHardDeleteBulk} disabled={!isConfirmValid} className="flex-1 py-2.5 rounded-full bg-red-600 text-white text-[12px] font-medium hover:bg-red-700 disabled:opacity-30 disabled:cursor-not-allowed transition">💥 Hard Delete {count}</button>
            ) : (
              <button onClick={onArchiveBulk} className="flex-1 py-2.5 rounded-full bg-amber-600 text-white text-[12px] font-medium hover:bg-amber-700 transition">📦 Arquivar {count}</button>
            )}
          </div>
        </div>

        <div className="mt-4 text-[10px] font-mono text-zinc-600">v1.2 Clean: Bulk delete + Drag&Drop + Shortcuts Ctrl+Shift+D • Hard precisa BULK_DELETE_CONFIRM • Esc fecha • Você no centro</div>
      </div>
    </div>
  );
}

export function ShortcutsModal({ onClose }: any) {
  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="rounded-[20px] bg-[#111116] border border-zinc-800 p-6 max-w-[520px] w-full shadow-[0_16px_48px_rgba(0,0,0,0.5)]">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2.5">
            <div className="w-6 h-6 rounded-full bg-white text-black flex items-center justify-center text-[11px]">⌨️</div>
            <h3 className="font-[650] text-[14px] tracking-tight">Atalhos • Chat Clean v1.2 + Workplace</h3>
          </div>
          <button onClick={onClose} className="w-7 h-7 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-500 hover:text-zinc-300 transition">✕</button>
        </div>

        <div className="mt-5 grid gap-2 text-[12px]">
          <div className="flex justify-between items-center p-2.5 rounded-xl bg-zinc-900 border border-zinc-800"><span className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-zinc-800">Ctrl+K / Cmd+K</span><span className="text-zinc-500">Focar chat input • clean</span></div>
          <div className="flex justify-between items-center p-2.5 rounded-xl bg-zinc-900 border border-zinc-800"><span className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-zinc-800">Ctrl+L</span><span className="text-zinc-500">Limpar chat • mantém workplace</span></div>
          <div className="flex justify-between items-center p-2.5 rounded-xl bg-zinc-900 border border-zinc-800"><span className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-zinc-800">Ctrl+B</span><span className="text-zinc-500">Toggle Workplace • multi-arquivo</span></div>
          <div className="flex justify-between items-center p-2.5 rounded-xl bg-zinc-900 border border-zinc-800"><span className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-zinc-800">Ctrl+J</span><span className="text-zinc-500">Toggle Agentes • empoderados</span></div>
          <div className="flex justify-between items-center p-2.5 rounded-xl bg-zinc-900 border border-zinc-800"><span className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-zinc-800">Ctrl+S</span><span className="text-zinc-500">Salvar arquivo (no editor)</span></div>
          <div className="flex justify-between items-center p-2.5 rounded-xl bg-zinc-900 border border-zinc-800"><span className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-zinc-800">Ctrl+Shift+D</span><span className="text-zinc-500">Bulk delete • hard + confirmação</span></div>
          <div className="flex justify-between items-center p-2.5 rounded-xl bg-zinc-900 border border-zinc-800"><span className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-zinc-800">Ctrl+/</span><span className="text-zinc-500">Mostrar atalhos • v1.2</span></div>
          <div className="flex justify-between items-center p-2.5 rounded-xl bg-zinc-900 border border-zinc-800"><span className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-zinc-800">Esc</span><span className="text-zinc-500">Fechar modais • você no centro</span></div>
          <div className="flex justify-between items-center p-2.5 rounded-xl bg-zinc-900 border border-zinc-800"><span className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-zinc-800">Drag&Drop</span><span className="text-zinc-500">Arrastar arquivos entre projetos • real</span></div>
          <div className="flex justify-between items-center p-2.5 rounded-xl bg-violet-500/5 border border-violet-500/20"><span className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-violet-500 text-white">/testa /audita /contesta</span><span className="text-violet-300">Comandos críticos • empoderam agentes</span></div>
        </div>

        <div className="mt-4 p-3 rounded-xl bg-violet-500/5 border border-violet-500/20 text-[11px] leading-[1.5] text-zinc-400">
          <span className="font-medium text-violet-300">v1.2 Clean:</span> Chat limpo sem templates, comandos sugerem criticamente, agentes contestam, criticam, não ficam na 1ª tentativa, terceiro olho aberto. Workplace: hard delete + bulk + confirmação com audit log. Componentes &lt;200 linhas, você cria orientando AI.
        </div>
      </div>
    </div>
  );
}
