"use client";
import { memo } from "react";

export const WorkplaceExport = memo(function WorkplaceExport({ selectedProject, onExportGithub, onExportVercel, onExportDocker, exportResult, onExport }: any) {
  if(!selectedProject) return null;
  const isReal = exportResult?.p15_real;
  const githubToken = exportResult?.github_token_set;
  const vercelToken = exportResult?.vercel_token_set;
  const dockerAvail = exportResult?.docker_available;
  return (
    <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-2.5">
      <div className="text-[10px] font-medium text-zinc-400">Export • GitHub Vercel Docker JSON • P15 REAL {isReal? "✅ REAL":""}</div>
      <div className="mt-2 grid grid-cols-3 gap-1">
        <button onClick={onExportGithub} className="py-1.5 rounded-full bg-zinc-800 border border-zinc-700 text-[10px] hover:bg-zinc-700">GitHub {exportResult?.real_attempt && exportResult?.github_repo ? "✅" : ""}</button>
        <button onClick={onExportVercel} className="py-1.5 rounded-full bg-zinc-800 border border-zinc-700 text-[10px] hover:bg-zinc-700">Vercel {vercelToken ? "✅" : ""}</button>
        <button onClick={onExportDocker} className="py-1.5 rounded-full bg-zinc-800 border border-zinc-700 text-[10px] hover:bg-zinc-700">Docker {dockerAvail ? "✅" : ""}</button>
      </div>
      <button onClick={()=>onExport(selectedProject.project_id)} className="mt-1.5 w-full py-1.5 rounded-full bg-white text-black text-[10px] font-medium hover:bg-zinc-100">⬇️ Export JSON</button>
      {exportResult && (
        <div className="mt-2 p-1.5 rounded-lg bg-[#08080c] border border-zinc-800 text-[9px] font-mono text-zinc-500 max-h-[100px] overflow-auto">
          <div className="text-violet-400">P15 REAL: {exportResult.message || JSON.stringify(exportResult).slice(0,200)}</div>
          {exportResult.real_result && <div className="mt-1 text-zinc-600">{JSON.stringify(exportResult.real_result).slice(0,300)}</div>}
          {!exportResult.p15_real && <div>{JSON.stringify(exportResult).slice(0,300)}</div>}
        </div>
      )}
      <div className="mt-2 text-[9px] text-zinc-600">
        P15 REAL: GitHub API se GITHUB_TOKEN set cria repo + push file via contents API • Vercel API token validation • Docker binary check + Dockerfile REAL + audit log • Você cria orientando AI
      </div>
    </div>
  );
});
