"use client";

export function WorkplaceBranches({ selectedProject, branches, newBranchName, setNewBranchName, onCreateBranch, onMergeBranch, onFetchBranches }: any) {
  if(!selectedProject) return null;
  return (
    <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-2.5">
      <div className="flex justify-between items-center"><span className="text-[10px] font-medium text-zinc-400">Branches • {branches.length||1} • P12</span><button onClick={()=>onFetchBranches(selectedProject.project_id)} className="w-5 h-5 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center text-[10px]">↻</button></div>
      <div className="mt-2 flex gap-1">
        <input value={newBranchName} onChange={e=>setNewBranchName(e.target.value)} placeholder="feature-x" className="flex-1 rounded-full bg-[#08080c] border border-zinc-800 px-2.5 py-1 text-[10px] font-mono outline-none focus:border-zinc-700" />
        <button onClick={onCreateBranch} className="px-2.5 py-1 rounded-full bg-white text-black text-[10px]">+ Branch</button>
      </div>
      <div className="mt-2 space-y-1 max-h-[80px] overflow-auto">
        {(branches.length?branches:[{branch_name:"main",is_merged:false}]).map((b:any)=>(
          <div key={b.branch_name} className="flex justify-between items-center text-[10px] font-mono p-1.5 rounded bg-[#08080c] border border-zinc-800">
            <span>{b.branch_name} {b.is_merged?"✓ merged":""}</span>
            {b.branch_name!=="main"&&!b.is_merged&&<button onClick={()=>onMergeBranch(b.branch_name)} className="px-1.5 py-0.5 rounded bg-emerald-600 text-white text-[9px]">Merge → main</button>}
          </div>
        ))}
      </div>
      <div className="mt-2 text-[9px] text-zinc-600">P12: Branch para feature sem quebrar main • Merge com detecção conflitos + human_override</div>
    </div>
  );
}
