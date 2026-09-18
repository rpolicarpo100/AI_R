"use client";

export function WorkplaceEditor({ selectedProject, selectedFile, setSelectedFile, editingFile, setEditingFile, onUpdateFile }: any) {
  if(!selectedProject) return null;
  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="px-3 py-2 flex gap-1 overflow-x-auto border-b border-zinc-900">
        {Object.keys(selectedProject.files).map((fname:string)=>(
          <button key={fname} draggable onDragStart={()=>{}} onClick={()=>{setSelectedFile(fname); setEditingFile(selectedProject.files[fname]);}} className={`px-2.5 py-1 rounded-full text-[11px] font-mono whitespace-nowrap border ${selectedFile===fname?"bg-white text-black border-white":"bg-zinc-900 text-zinc-500 border-zinc-800 hover:text-zinc-300"}`}>{fname}</button>
        ))}
      </div>
      {selectedFile ? (
        <div className="flex-1 flex flex-col overflow-hidden p-3">
          <div className="flex justify-between items-center mb-2"><span className="text-[11px] font-mono text-zinc-400">{selectedFile} • Ctrl+S salva • P12 CLEAN</span><button onClick={onUpdateFile} className="text-[10px] px-3 py-1 rounded-full bg-emerald-600 text-white hover:bg-emerald-700">💾 Salvar</button></div>
          <textarea value={editingFile} onChange={e=>setEditingFile(e.target.value)} className="flex-1 rounded-xl bg-[#08080c] border border-zinc-800 p-3 text-[11px] font-mono outline-none focus:border-zinc-700 resize-none" />
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center text-[11px] text-zinc-500">Selecione um arquivo para editar • P12 Editor &lt;200l</div>
      )}
    </div>
  );
}
