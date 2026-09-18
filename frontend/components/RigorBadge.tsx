"use client";
export function RigorBadge({source, confidence, testCount}:{source:string, confidence?:number, testCount?:number}){
  const getColor = () => {
    if(source==="measured") return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
    if(source==="verified") return "bg-blue-500/10 text-blue-400 border-blue-500/30";
    if(source==="provider_claim") return "bg-amber-500/10 text-amber-400 border-amber-500/30";
    return "bg-slate-700/30 text-slate-500 border-slate-600/30";
  };
  const label = source==="measured" ? `MEDIDO (${testCount||0} testes)` : source==="verified" ? "VERIFICADO" : source==="provider_claim" ? "PROVIDER CLAIM" : "UNKNOWN";
  return (
    <span className={`text-[9px] mono px-2 py-0.5 rounded-full border ${getColor()}`}>
      {label} {confidence!==undefined ? `• conf ${confidence}%` : ""}
    </span>
  );
}
