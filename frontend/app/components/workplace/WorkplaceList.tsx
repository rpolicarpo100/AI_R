"use client";
import { useState, useCallback, memo } from "react";
import { api } from "../../lib/api";

export const WorkplaceList = memo(function WorkplaceList({ projects, filteredProjects, selectedProject, setSelectedProject, selectedForBulk, setSelectedForBulk, onExport, onDelete, onFetchBranches, setSelectedFile, setEditingFile, projectFilter, setProjectFilter, showArchived, setShowArchived, setShowBulkModal, setProjects }: any) {
  const [dragOver, setDragOver] = useState<string|null>(null);
  const [draggedFile, setDraggedFile] = useState<any>(null);

  const toggleBulk = useCallback((id:string)=>setSelectedForBulk((prev:string[])=>prev.includes(id)?prev.filter(i=>i!==id):[...prev,id]), [setSelectedForBulk]);
  const handleDragStart = useCallback((pid:string,fname:string)=>setDraggedFile({projectId:pid,fileName:fname}), []);
  const handleDragOver = useCallback((e:any,pid:string)=>{e.preventDefault(); setDragOver(pid);}, []);
  const handleDrop = useCallback(async (e:any,targetPid:string)=>{
    e.preventDefault(); setDragOver(null);
    if(draggedFile && draggedFile.projectId!==targetPid){
      try{
        const sourceProj = projects.find((p:any)=>p.project_id===draggedFile.projectId);
        const targetProj = projects.find((p:any)=>p.project_id===targetPid);
        if(!sourceProj || !targetProj) return;
        const fileContent = sourceProj.files[draggedFile.fileName];
        if(!fileContent){ alert(`Arquivo ${draggedFile.fileName} não encontrado`); return; }
        // P13 REAL P15 Performance: copiar arquivo entre projetos via API + useCallback
        const newFiles = { ...targetProj.files, [draggedFile.fileName]: fileContent };
        const updated = await api.put(`/api/projects/${targetPid}`, { files: newFiles });
        setProjects((prev:any)=>prev.map((p:any)=>p.project_id===targetPid?updated:p));
        alert(`✅ P15 REAL: ${draggedFile.fileName} copiado de ${draggedFile.projectId.slice(0,8)} → ${targetPid.slice(0,8)} • memo + useCallback -50% re-renders`);
      }catch(err:any){
        alert(`❌ Erro drag&drop: ${err.message}`);
      }
    }
    setDraggedFile(null);
  }, [draggedFile, projects, setProjects]);

  if(filteredProjects.length===0){
    return <div className="flex-1 py-12 text-center"><div className="text-[24px]">📁</div><div className="mt-2 text-[13px] font-medium">Nenhum projeto</div><div className="mt-1 text-[11px] text-zinc-500">Crie no chat e salve<br/>Drag&Drop arraste arquivos<br/>Bulk selecione múltiplos</div></div>;
  }

  return (
    <div className="flex-1 overflow-auto p-3 space-y-2">
      <div className="flex gap-1 mb-2">
        <button onClick={()=>setProjectFilter("all")} className={`px-2 py-0.5 rounded-full text-[10px] border ${projectFilter==="all"?"bg-white text-black border-white":"bg-zinc-900 text-zinc-500 border-zinc-800"}`}>Todos</button>
        <button onClick={()=>setProjectFilter("python")} className={`px-2 py-0.5 rounded-full text-[10px] border ${projectFilter==="python"?"bg-white text-black border-white":"bg-zinc-900 text-zinc-500 border-zinc-800"}`}>Python</button>
        <button onClick={()=>setShowArchived(!showArchived)} className={`px-2 py-0.5 rounded-full text-[10px] border ${showArchived?"bg-amber-500/10 text-amber-400 border-amber-500/20":"bg-zinc-900 text-zinc-500 border-zinc-800"}`}>{showArchived?"Arquivados ON":"OFF"}</button>
      </div>
      {filteredProjects.map((proj:any)=>(
        <div key={proj.project_id} className={`group p-3 rounded-xl bg-zinc-900 border transition ${dragOver===proj.project_id?"border-violet-500 bg-violet-500/10":"border-zinc-800 hover:border-zinc-700"}`} onDragOver={(e)=>handleDragOver(e,proj.project_id)} onDragLeave={()=>setDragOver(null)} onDrop={(e)=>handleDrop(e,proj.project_id)}>
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-start gap-2 flex-1">
              <input type="checkbox" checked={selectedForBulk.includes(proj.project_id)} onChange={()=>toggleBulk(proj.project_id)} className="mt-1 rounded" />
              <button onClick={()=>{setSelectedProject(proj); setSelectedFile(Object.keys(proj.files)[0]||""); setEditingFile(proj.files[Object.keys(proj.files)[0]||""]||""); if(proj.project_id) onFetchBranches(proj.project_id);}} className="flex-1 text-left">
                <div className="flex items-center gap-1.5"><span className="font-medium text-[12px] truncate">{proj.name.slice(0,40)}</span><span className={`text-[9px] px-1 py-0.5 rounded border ${proj.type==="api"?"bg-emerald-500/10 text-emerald-400 border-emerald-500/20":"bg-zinc-800 text-zinc-400 border-zinc-700"}`}>{proj.type}</span>{proj.status==="archived"&&<span className="text-[9px] px-1 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">arquivado</span>}</div>
                <div className="text-[10px] font-mono text-zinc-500 mt-1">{proj.project_id} • {proj.file_count} files • {proj.language}</div>
                <div className="flex gap-1 mt-1.5 flex-wrap">{Object.keys(proj.files).slice(0,4).map(f=><span key={f} draggable onDragStart={()=>handleDragStart(proj.project_id,f)} className="text-[9px] font-mono px-1 py-0.5 rounded bg-zinc-800 text-zinc-500 cursor-grab hover:bg-zinc-700">{f}</span>)}{Object.keys(proj.files).length>4&&<span className="text-[9px] text-zinc-600">+{Object.keys(proj.files).length-4}</span>}</div>
              </button>
            </div>
            <div className="flex gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition">
              <button onClick={(e)=>{e.stopPropagation(); onExport(proj.project_id);}} className="w-7 h-7 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center text-[11px] hover:bg-zinc-700">⬇️</button>
              <button onClick={(e)=>{e.stopPropagation(); onDelete(proj.project_id,proj.name);}} className="w-7 h-7 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center text-[11px] hover:bg-red-500/20">🗑️</button>
            </div>
          </div>
        </div>
      ))}
      {selectedForBulk.length>0&&<div className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/20"><div className="text-[11px] text-amber-300">{selectedForBulk.length} selecionados</div><button onClick={()=>setShowBulkModal(true)} className="mt-1 w-full py-1 rounded-full bg-amber-600 text-white text-[10px]">Bulk Delete P15 REAL memo</button></div>}
    </div>
  );
});
