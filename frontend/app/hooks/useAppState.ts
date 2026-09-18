"use client";
import { useEffect, useState, useMemo } from "react";
import { api } from "../lib/api";

export function useAppState() {
  const [stats, setStats] = useState<any>(null);
  const [providers, setProviders] = useState<any[]>([]);
  const [models, setModels] = useState<any[]>([]);
  const [rigor, setRigor] = useState<any>(null);
  const [agents, setAgents] = useState<any[]>([]);
  const [skills, setSkills] = useState<any[]>([]);
  const [projects, setProjects] = useState<any[]>([]);

  const distinctModels = useMemo(()=>{
    const map = new Map();
    models.forEach((m:any)=>{
      const base = m.model_id.split("/").pop();
      const existing = map.get(base);
      if(!existing || (m.overall_score||0) > (existing.overall_score||0)) map.set(base, {...m, base_id: base});
    });
    return Array.from(map.values()).sort((a:any,b:any)=>(b.overall_score||0)-(a.overall_score||0));
  }, [models]);

  const fetchAll = async () => {
    try {
      const [s, p, m, r, ag, sk, proj] = await Promise.all([
        api.get("/api/dashboard/stats"),
        api.get("/api/providers"),
        api.get("/api/models"),
        api.get("/api/benchmark/rigor").catch(()=>null),
        api.get("/api/agents").catch(()=>[]),
        api.get("/api/agents/skills").catch(()=>[]),
        api.get("/api/projects").catch(()=>[]),
      ]);
      setStats(s); setProviders(p); setModels(m); setRigor(r);
      setAgents(ag); setSkills(sk); setProjects(proj);
    } catch(e){ console.error(e); }
  };

  useEffect(()=>{ fetchAll(); const id=setInterval(fetchAll, 15000); return ()=>clearInterval(id); }, []);

  return { stats, providers, models, rigor, agents, skills, projects, setProjects, distinctModels, fetchAll };
}
