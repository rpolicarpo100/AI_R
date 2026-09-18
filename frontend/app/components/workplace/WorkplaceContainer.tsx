"use client";
import { memo } from "react";
import { WorkplaceList } from "./WorkplaceList";
import { WorkplaceEditor } from "./WorkplaceEditor";
import { WorkplaceBranches } from "./WorkplaceBranches";
import { WorkplaceExport } from "./WorkplaceExport";

export const WorkplaceContainer = memo(function WorkplaceContainer(props:any) {
  const { projects, selectedProject, setSelectedProject, workplaceOpen, setWorkplaceOpen, selectedForBulk } = props;
  if(!workplaceOpen){
    return (
      <div className="space-y-3">
        <div className="rounded-[20px] bg-[#111116] border border-zinc-900 p-4">
          <div className="flex items-center justify-between"><h4 className="text-[11px] font-medium text-zinc-400">WORKPLACE • {projects.length} • P15 REAL+PERF</h4><button onClick={()=>setWorkplaceOpen(true)} className="text-[11px] px-2.5 py-1 rounded-full bg-white text-black">Abrir</button></div>
          <div className="mt-3 space-y-1.5">{projects.slice(0,3).map((p:any)=><div key={p.project_id} className="p-2 rounded-xl bg-zinc-900 border border-zinc-800 text-[11px]"><div className="font-medium truncate">{p.name.slice(0,30)}</div><div className="text-[10px] text-zinc-500">{p.file_count} files • {p.type}</div></div>)}</div>
          {selectedForBulk.length>0&&<div className="mt-3 p-2 rounded-xl bg-amber-500/10 border border-amber-500/20"><div className="text-[11px] text-amber-300">{selectedForBulk.length} sel</div></div>}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-[20px] bg-[#111116] border border-zinc-900 flex flex-col h-[84vh] overflow-hidden">
      <div className="px-5 py-3.5 border-b border-zinc-900 flex items-center justify-between">
        <div className="flex items-center gap-2.5"><span className="text-[12px] font-medium">📁 Workplace • {props.filteredProjects.length} • P15 REAL+PERF</span><span className="text-[10px] px-2 py-0.5 rounded-full bg-zinc-900 border border-zinc-800 text-zinc-500">{props.projects.length} total</span><span className="text-[9px] px-1.5 py-0.5 rounded-full bg-violet-500/10 text-violet-400 border border-violet-500/20">memo</span></div>
        <div className="flex items-center gap-1.5">
          {selectedForBulk.length>0&&<><span className="text-[10px] px-2 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">{selectedForBulk.length} sel</span><button onClick={()=>props.setShowBulkModal(true)} className="px-2.5 py-1 rounded-full bg-red-600 text-white text-[10px]">Bulk 🗑️</button><button onClick={()=>props.setSelectedForBulk([])} className="px-2 py-1 rounded-full bg-zinc-800 border border-zinc-700 text-[10px]">✕</button></>}
          <button onClick={()=>setWorkplaceOpen(false)} className="w-7 h-7 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-500 hover:text-zinc-300">✕</button>
        </div>
      </div>

      {!selectedProject ? (
        <WorkplaceList {...props} />
      ) : (
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="px-3 py-2.5 border-b border-zinc-900 flex items-center justify-between"><button onClick={()=>setSelectedProject(null)} className="text-[11px] px-2.5 py-1 rounded-full bg-zinc-900 border border-zinc-800 hover:bg-zinc-800">← Voltar • {selectedProject.name.slice(0,25)}</button><div className="flex gap-1"><button onClick={()=>props.onExport(selectedProject.project_id)} className="text-[10px] px-2.5 py-1 rounded-full bg-white text-black">⬇️ Export</button><button onClick={()=>props.onDelete(selectedProject.project_id,selectedProject.name)} className="text-[10px] px-2.5 py-1 rounded-full bg-zinc-900 border border-zinc-800 hover:bg-red-500/10 text-zinc-400 hover:text-red-400">🗑️ Eliminar</button></div></div>
          <div className="px-3 py-2.5 bg-zinc-900/50 border-b border-zinc-900"><div className="font-medium text-[12px]">{selectedProject.name}</div><div className="text-[10px] font-mono text-zinc-500 mt-1">{selectedProject.project_id} • {selectedProject.type} • {selectedProject.language} • {selectedProject.file_count} files • P15 REAL+PERF memo</div></div>
          <WorkplaceEditor {...props} />
          <div className="border-t border-zinc-900 p-3 grid grid-cols-2 gap-2">
            <WorkplaceBranches {...props} />
            <WorkplaceExport {...props} />
          </div>
        </div>
      )}
    </div>
  );
});
