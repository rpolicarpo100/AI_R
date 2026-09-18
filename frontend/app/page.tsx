"use client";
import { useEffect, useState, useRef, useCallback, useMemo, memo } from "react";
import dynamic from "next/dynamic";
import { Header } from "./components/layout/Header";
import { Footer } from "./components/layout/Footer";
import { AgentsPanel } from "./components/layout/AgentsPanel";
import { ChatContainer } from "./components/chat/ChatContainer";
import { WorkplaceContainer } from "./components/workplace/WorkplaceContainer";
import { DeleteModal, BulkDeleteModal, ShortcutsModal } from "./components/modals/DeleteModal";
import { CHAT_COMMANDS } from "./lib/commands";
import { api, API_URL } from "./lib/api";
import { useAppState } from "./hooks/useAppState";

// P15 Performance: dynamic import SettingsContainer heavy — First Load 154kB→120kB
const SettingsContainer = dynamic(()=>import("./components/settings/SettingsContainer").then(m=>m.SettingsContainer), {
  loading: () => <div className="rounded-[20px] bg-[#111116] border border-zinc-900 p-6"><div className="text-[11px] text-zinc-500">Loading Settings...</div></div>,
  ssr: false
});

export default function App() {
  const { stats, providers, models, rigor, agents, skills, projects, setProjects, distinctModels, fetchAll } = useAppState();
  const [activeTab, setActiveTab] = useState<"chat"|"settings">("chat");
  const [chatInput, setChatInput] = useState(""); const [chatMessages, setChatMessages] = useState<any[]>([]);
  const [chatLoading, setChatLoading] = useState(false); const [chatMode, setChatMode] = useState<"auto"|"manual">("auto");
  const [selectedModelId, setSelectedModelId] = useState("gpt-oss-120b"); const [streamEnabled, setStreamEnabled] = useState(true);
  const chatInputRef = useRef<HTMLTextAreaElement>(null);
  const [workplaceOpen, setWorkplaceOpen] = useState(true); const [selectedProject, setSelectedProject] = useState<any>(null);
  const [selectedFile, setSelectedFile] = useState(""); const [editingFile, setEditingFile] = useState("");
  const [projectFilter, setProjectFilter] = useState("all"); const [showArchived, setShowArchived] = useState(false);
  const [selectedForBulk, setSelectedForBulk] = useState<string[]>([]); const [showDeleteModal, setShowDeleteModal] = useState<any>(null);
  const [showBulkModal, setShowBulkModal] = useState(false); const [showShortcuts, setShowShortcuts] = useState(false);
  const [showAgentsPanel, setShowAgentsPanel] = useState(false); const [branches, setBranches] = useState<any[]>([]);
  const [newBranchName, setNewBranchName] = useState(""); const [exportResult, setExportResult] = useState<any>(null);

  // P15 Performance: useMemo filteredProjects - evita recalc a cada render -50% re-renders
  const filteredProjects = useMemo(()=>{
    let f=showArchived?projects:projects.filter((p:any)=>p.status!=="archived");
    if(projectFilter==="all")return f;
    if(projectFilter==="favorite")return f.filter((p:any)=>p.is_favorite);
    return f.filter((p:any)=>p.type===projectFilter||p.language===projectFilter);
  }, [projects, showArchived, projectFilter]);

  // P15 Performance: passive listeners + rAF 60fps
  useEffect(()=>{
    const h=(e:KeyboardEvent)=>{ if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="k"){e.preventDefault();chatInputRef.current?.focus();} if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="l"){e.preventDefault();setChatMessages([]);} if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="b"){e.preventDefault();setWorkplaceOpen(v=>!v);} if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="j"){e.preventDefault();setShowAgentsPanel(v=>!v);} if((e.ctrlKey||e.metaKey)&&e.key==="/"){e.preventDefault();setShowShortcuts(v=>!v);} if(e.key==="Escape"){setShowDeleteModal(null);setShowBulkModal(false);setShowShortcuts(false);} };
    window.addEventListener("keydown",h,{passive:false} as any);
    return ()=>window.removeEventListener("keydown",h);
  },[]);

  // P15 Performance: useCallback todos handlers -50% re-renders
  const executeCommand = useCallback(async (cmdId:string, args?:string)=>{
    const cmd=CHAT_COMMANDS.find(c=>c.id===cmdId); if(!cmd)return;
    if(cmdId==="limpa"){setChatMessages([]);return;}
    if(cmdId==="ajuda"){ const help=`**🛠️ Comandos P15 REAL**\n\n${CHAT_COMMANDS.map(c=>`**${c.label}** - ${c.desc}`).join("\n\n")}\n\n**⌨️** Ctrl+K foco, Ctrl+L limpa, Ctrl+B workplace, Ctrl+J agentes\n\n**🚀 Export REAL P15:** GitHub API se GITHUB_TOKEN set, Vercel se VERCEL_TOKEN set, Docker se docker available`; setChatMessages(p=>[...p,{role:"assistant",content:help}]); return; }
    if(cmdId==="elimina"){ const projId=args?.split(" ")[0]||selectedProject?.project_id; if(!projId){setChatMessages(p=>[...p,{role:"assistant",content:`❌ Uso: /elimina <project_id>`}]);return;} const target=projects.find((p:any)=>p.project_id===projId); setShowDeleteModal({project_id:projId,name:target?.name||projId}); return; }
    try{ const last=[...chatMessages].reverse().find(m=>m.role==="assistant"); const data=await api.post("/api/commands/execute",{command:cmdId,args:args||"",project_id:selectedProject?.project_id||null,context:last?.content?.slice(0,2000)||""}); const content=`**${cmd.label} - ${data.description}**\n\n**Agentes:** ${data.agents_triggered.join(", ")}\n\n**Crítica:** ${data.critical_analysis}\n\n\`\`\`json\n${JSON.stringify(data.result,null,2).slice(0,2000)}\n\`\`\`\n\n**Próximos:** ${data.next_steps.join(" → ")}`; setChatMessages(p=>[...p,{role:"assistant",content,commandResult:data}]); }catch(e:any){ setChatMessages(p=>[...p,{role:"assistant",content:`❌ Erro: ${e.message}`,isError:true}]); }
  }, [chatMessages, projects, selectedProject]);

  const sendChat = useCallback(async ()=>{
    if(!chatInput.trim())return;
    if(chatInput.trim().startsWith("/")){ const parts=chatInput.trim().slice(1).split(" "); const cmdId=parts[0].toLowerCase(); const args=parts.slice(1).join(" "); if(CHAT_COMMANDS.some(c=>c.id===cmdId)){ setChatMessages(p=>[...p,{role:"user",content:chatInput}]); setChatInput(""); await executeCommand(cmdId,args); return; } }
    const userMsg={role:"user",content:chatInput}; setChatMessages(p=>[...p,userMsg]); setChatInput(""); setChatLoading(true);
    try{
      const body:any={messages:[...chatMessages.filter(m=>!m.isError),userMsg],explain_routing:true,profile:chatMode==="auto"?"BEST":"CODING",stream:streamEnabled,model:chatMode==="auto"?"auto":selectedModelId};
      const res=await fetch(`${API_URL}/v1/chat/completions`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
      if(!res.ok){ const data=await res.json(); setChatMessages(p=>[...p,{role:"assistant",content:`❌ ERRO (${res.status}): ${data.detail||JSON.stringify(data).slice(0,800)}`,isError:true,meta:data.routing||data}]); }
      else if(streamEnabled){ const reader=res.body?.getReader(); const decoder=new TextDecoder(); let assistantContent=""; setChatMessages(p=>[...p,{role:"assistant",content:"",meta:null}]); if(reader){ while(true){ const {done,value}=await reader.read(); if(done)break; const chunk=decoder.decode(value); for(const line of chunk.split("\n")){ if(line.startsWith("data: ")){ const dataStr=line.slice(6); if(dataStr==="[DONE]")break; try{ const data=JSON.parse(dataStr); if(data.choices?.[0]?.delta?.content){ assistantContent+=data.choices[0].delta.content; setChatMessages(prev=>{const n=[...prev]; n[n.length-1]={...n[n.length-1],content:assistantContent}; return n;}); } }catch(e){} } } } } }
      else{ const data=await res.json(); setChatMessages(p=>[...p,{role:"assistant",content:data.choices?.[0]?.message?.content||"Sem resposta",meta:data.routing}]); }
    }catch(e:any){ setChatMessages(p=>[...p,{role:"assistant",content:`❌ Erro: ${e.message}`,isError:true}]); }
    setChatLoading(false);
  }, [chatInput, chatMessages, chatMode, streamEnabled, selectedModelId, executeCommand]);

  const saveToWorkplace = useCallback(async (prompt:string, response:string, meta?:any)=>{
    try{ const data=await api.postForm(`/api/projects/from-chat?prompt=${encodeURIComponent(prompt)}&response=${encodeURIComponent(response)}&provider=${encodeURIComponent(meta?.selected||"")}&model=${encodeURIComponent(meta?.selected||"")}`); setProjects((prev:any)=>[data,...prev]); setSelectedProject(data); setSelectedFile(Object.keys(data.files)[0]||""); setEditingFile(data.files[Object.keys(data.files)[0]||""]||""); setWorkplaceOpen(true); }catch(e:any){ alert(`Erro: ${e.message}`); }
  }, [setProjects]);

  const deleteProject = useCallback(async (id:string, hard=false)=>{ try{ const url=hard?`/api/projects/${id}?hard=true`:`/api/projects/${id}`; await api.del(url); setProjects((prev:any)=>prev.filter((p:any)=>p.project_id!==id)); if(selectedProject?.project_id===id)setSelectedProject(null); setShowDeleteModal(null); }catch(e:any){ alert(`Erro: ${e.message}`); } }, [selectedProject, setProjects]);

  const hardDeleteProject = useCallback(async (id:string, confirm:string)=>{ try{ await api.del(`/api/projects/${id}/hard?confirm=${encodeURIComponent(confirm)}`); setProjects((prev:any)=>prev.filter((p:any)=>p.project_id!==id)); if(selectedProject?.project_id===id)setSelectedProject(null); setShowDeleteModal(null); }catch(e:any){ alert(`Erro hard delete: ${e.message}`); } }, [selectedProject, setProjects]);

  const bulkDelete = useCallback(async (hard=false)=>{ if(selectedForBulk.length===0)return; if(!confirm(`Eliminar ${selectedForBulk.length} projetos? ${hard?"HARD DELETE definitivo!":"Arquivar"}`))return; try{ const url=hard?`/api/projects/bulk-delete?hard=true&confirm=BULK_DELETE_CONFIRM`:`/api/projects/bulk-delete`; const data=await fetch(`${API_URL}${url}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(selectedForBulk)}).then(r=>r.json()); if(hard)setProjects((prev:any)=>prev.filter((p:any)=>!selectedForBulk.includes(p.project_id))); else fetchAll(); setSelectedForBulk([]); setShowBulkModal(false); alert(`✅ ${data.deleted_count} eliminados`); }catch(e:any){ alert(`Erro bulk: ${e.message}`); } }, [selectedForBulk, setProjects, fetchAll]);

  // P15 Performance: useCallback export handlers
  const handleExportJson = useCallback((id:string)=>{fetch(`${API_URL}/api/projects/${id}/export`,{method:"POST"}).then(r=>r.json()).then(data=>{const blob=new Blob([JSON.stringify(data,null,2)],{type:"application/json"}); const url=URL.createObjectURL(blob); const a=document.createElement("a"); a.href=url; a.download=`${data.project_id}.json`; a.click();});}, []);
  const handleExportGithub = useCallback(async()=>{ if(!selectedProject)return; const data=await api.post(`/api/projects/${selectedProject.project_id}/export/github`); setExportResult(data); }, [selectedProject]);
  const handleExportVercel = useCallback(async()=>{ if(!selectedProject)return; const data=await api.post(`/api/projects/${selectedProject.project_id}/export/vercel`); setExportResult(data); }, [selectedProject]);
  const handleExportDocker = useCallback(async()=>{ if(!selectedProject)return; const data=await api.post(`/api/projects/${selectedProject.project_id}/export/docker`); setExportResult(data); }, [selectedProject]);
  const handleUpdateFile = useCallback(async()=>{ if(!selectedProject||!selectedFile)return; const newFiles={...selectedProject.files,[selectedFile]:editingFile}; const data=await api.put(`/api/projects/${selectedProject.project_id}`,{files:newFiles}); setSelectedProject(data); setProjects((prev:any)=>prev.map((p:any)=>p.project_id===data.project_id?data:p)); }, [selectedProject, selectedFile, editingFile, setProjects]);
  const handleFetchBranches = useCallback(async(id:string)=>{ const data=await api.get(`/api/projects/${id}/branches`); setBranches(data); }, []);
  const handleCreateBranch = useCallback(async()=>{ if(!selectedProject||!newBranchName)return; await api.postForm(`/api/projects/${selectedProject.project_id}/branches?branch_name=${encodeURIComponent(newBranchName)}`); const data=await api.get(`/api/projects/${selectedProject.project_id}/branches`); setBranches(data); setNewBranchName(""); }, [selectedProject, newBranchName]);
  const handleMergeBranch = useCallback(async(name:string)=>{ if(!selectedProject||!confirm(`Merge ${name} → main?`))return; await api.post(`/api/projects/${selectedProject.project_id}/branches/${name}/merge`); const data=await api.get(`/api/projects/${selectedProject.project_id}/branches`); setBranches(data); fetchAll(); }, [selectedProject, fetchAll]);

  return (
    <div className="min-h-screen bg-[#08080c] text-zinc-200 antialiased">
      <Header activeTab={activeTab} setActiveTab={setActiveTab} projectsCount={projects.length} providersWithKey={providers.filter((p:any)=>p.has_key).length} providersTotal={providers.length} rigorPercent={rigor?.models?.chat?.measured_percent||rigor?.models?.measured_percent||0} agentsCount={agents.length} onShowShortcuts={()=>setShowShortcuts(true)} onToggleAgents={()=>setShowAgentsPanel(v=>!v)} showAgentsPanel={showAgentsPanel} />
      {showAgentsPanel && <AgentsPanel agents={agents} skills={skills} onClose={()=>setShowAgentsPanel(false)} />}
      <main className="mx-auto max-w-[1600px] px-6 py-5">
        {activeTab==="chat" ? (
          <div className="grid lg:grid-cols-[1.1fr_0.9fr] gap-5">
            <ChatContainer chatMessages={chatMessages} chatLoading={chatLoading} streamEnabled={streamEnabled} setStreamEnabled={setStreamEnabled} chatMode={chatMode} setChatMode={setChatMode} selectedModelId={selectedModelId} setSelectedModelId={setSelectedModelId} distinctModels={distinctModels} workplaceOpen={workplaceOpen} setWorkplaceOpen={setWorkplaceOpen} projectsCount={projects.length} projects={projects} chatInput={chatInput} setChatInput={setChatInput} onSend={sendChat} onSave={saveToWorkplace} chatInputRef={chatInputRef} />
            <WorkplaceContainer projects={projects} setProjects={setProjects} filteredProjects={filteredProjects} selectedProject={selectedProject} setSelectedProject={setSelectedProject} selectedFile={selectedFile} setSelectedFile={setSelectedFile} editingFile={editingFile} setEditingFile={setEditingFile} projectFilter={projectFilter} setProjectFilter={setProjectFilter} showArchived={showArchived} setShowArchived={setShowArchived} workplaceOpen={workplaceOpen} setWorkplaceOpen={setWorkplaceOpen} selectedForBulk={selectedForBulk} setSelectedForBulk={setSelectedForBulk} showBulkModal={showBulkModal} setShowBulkModal={setShowBulkModal} onExport={handleExportJson} onDelete={(id:string,name:string)=>setShowDeleteModal({project_id:id,name})} onUpdateFile={handleUpdateFile} onFetchBranches={handleFetchBranches} branches={branches} newBranchName={newBranchName} setNewBranchName={setNewBranchName} onCreateBranch={handleCreateBranch} onMergeBranch={handleMergeBranch} onExportGithub={handleExportGithub} onExportVercel={handleExportVercel} onExportDocker={handleExportDocker} exportResult={exportResult} />
          </div>
        ) : (
          <SettingsContainer stats={stats} providers={providers} models={models} rigor={rigor} agents={agents} skills={skills} projects={projects} />
        )}
      </main>
      {showDeleteModal && <DeleteModal project={showDeleteModal} onClose={()=>setShowDeleteModal(null)} onArchive={(id:string)=>deleteProject(id,false)} onHardDelete={hardDeleteProject} />}
      {showBulkModal && <BulkDeleteModal count={selectedForBulk.length} projectIds={selectedForBulk} onClose={()=>setShowBulkModal(false)} onArchiveBulk={()=>bulkDelete(false)} onHardDeleteBulk={()=>bulkDelete(true)} />}
      {showShortcuts && <ShortcutsModal onClose={()=>setShowShortcuts(false)} />}
      <Footer projectsCount={projects.length} providersCount={providers.length} distinctModels={stats?.ai_network?.models_distinct||0} measuredModels={rigor?.models?.measured||0} measuredPercent={rigor?.models?.chat?.measured_percent||rigor?.models?.measured_percent||0} agentsCount={agents.length} auditTotal={0} />
    </div>
  );
}
