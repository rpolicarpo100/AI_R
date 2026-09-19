"use client";
import { useState } from "react";
import { DashboardTab } from "./DashboardTab";
import { NetworkTab } from "./NetworkTab";
import { BenchmarksTab } from "./BenchmarksTab";
import { RigorTab } from "./RigorTab";
import { AgentsTab } from "./AgentsTab";
import { AuditTab } from "./AuditTab";
import { CommandsTab } from "./CommandsTab";
import { ObservabilityTab } from "./ObservabilityTab";
import { MemoryTab } from "./MemoryTab";

const TABS = [
  { id: "dashboard", label: "Dashboard", icon: "📊" },
  { id: "network", label: "Network", icon: "🌐" },
  { id: "benchmarks", label: "Benchmarks", icon: "🏆" },
  { id: "rigor", label: "Rigor", icon: "✅" },
  { id: "memory", label: "Memory", icon: "🧠" },
  { id: "agents", label: "Agents", icon: "🤖" },
  { id: "audit", label: "Audit", icon: "🔍" },
  { id: "commands", label: "Commands", icon: "⌨️" },
  { id: "observability", label: "Observability", icon: "🔭" },
];

export function SettingsContainer({ stats, providers, models, rigor, agents, skills, projects }: any) {
  const [active, setActive] = useState("dashboard");
  return (
    <div className="rounded-[20px] bg-[#111116] border border-zinc-900 overflow-hidden">
      <div className="px-5 py-3 border-b border-zinc-900 flex items-center justify-between">
        <div className="flex items-center gap-2"><span className="text-[13px] font-medium">⚙️ Settings P16 V2 + P21 + Memory ENTERPRISE</span><span className="text-[10px] px-2 py-0.5 rounded-full bg-zinc-900 border border-zinc-800 text-zinc-500">{providers.length} provs • {models.length} models • {rigor?.models?.measured_percent||0}% rigor • {rigor?.models?.chat?.measured_percent||0}% chat • 17 memory</span></div>
        <div className="text-[10px] text-zinc-600">200 provs 965 models 0 artificial 101 UNKNOWN 50 OFFLINE 10 LOCAL • 9 tabs • P16 V2 + P21 + Memory Apikeyless Archive • 15 seed + continuous increase</div>
      </div>
      <div className="px-3 py-2 border-b border-zinc-900 flex gap-1 overflow-x-auto">
        {TABS.map(t=><button key={t.id} onClick={()=>setActive(t.id)} className={`px-3 py-1.5 rounded-full text-[11px] font-medium whitespace-nowrap border transition ${active===t.id ? "bg-white text-black border-white" : "bg-zinc-900 text-zinc-500 border-zinc-800 hover:text-zinc-300"}`}>{t.icon} {t.label}</button>)}
      </div>
      <div className="p-4 max-h-[70vh] overflow-auto">
        {active==="dashboard" && <DashboardTab stats={stats} rigor={rigor} providers={providers} models={models} projects={projects} />}
        {active==="network" && <NetworkTab providers={providers} models={models} />}
        {active==="benchmarks" && <BenchmarksTab models={models} />}
        {active==="rigor" && <RigorTab rigor={rigor} />}
        {active==="memory" && <MemoryTab />}
        {active==="agents" && <AgentsTab agents={agents} skills={skills} providers={providers} models={models} />}
        {active==="audit" && <AuditTab stats={stats} />}
        {active==="commands" && <CommandsTab />}
        {active==="observability" && <ObservabilityTab />}
      </div>
    </div>
  );
}
