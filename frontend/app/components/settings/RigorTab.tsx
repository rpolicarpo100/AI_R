"use client";

export function RigorTab({ rigor }: any) {
  const m = rigor?.models || {};
  const chat = m.chat || {};
  const non = m.non_chat || {};
  const prov = rigor?.providers || {};
  return (
    <div className="space-y-3">
      <div className="grid md:grid-cols-3 gap-2">
        <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800"><div className="text-[10px] text-zinc-500">Models Total</div><div className="text-[20px] font-bold">{m.measured_percent}% <span className="text-[12px] font-normal text-zinc-500">medido</span></div><div className="mt-1 text-[11px]">{m.measured}/{m.total} • {m.verified} verified • {m.discovered} discovered • {m.with_scores} with scores</div><div className={`mt-2 text-[10px] px-2 py-1 rounded-full border inline-block ${m.rigor_status==="LOW"?"bg-amber-500/10 text-amber-400 border-amber-500/20":"bg-emerald-500/10 text-emerald-400 border-emerald-500/20"}`}>{m.rigor_status}</div></div>
        <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800"><div className="text-[10px] text-zinc-500">Chat Only</div><div className="text-[20px] font-bold">{chat.measured_percent}% <span className="text-[12px] font-normal text-zinc-500">medido</span></div><div className="mt-1 text-[11px]">{chat.measured}/{chat.total} • {chat.with_scores} scores • {chat.verified} verified • need {chat.need_80} for 80%</div><div className={`mt-2 text-[10px] px-2 py-1 rounded-full border inline-block ${chat.rigor_status==="LOW"?"bg-amber-500/10 text-amber-400 border-amber-500/20":"bg-emerald-500/10 text-emerald-400 border-emerald-500/20"}`}>{chat.rigor_status} • target 80%</div></div>
        <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800"><div className="text-[10px] text-zinc-500">Providers + Non-Chat</div><div className="text-[20px] font-bold">{prov.with_api_key_percent}% <span className="text-[12px] font-normal text-zinc-500">keys</span></div><div className="mt-1 text-[11px]">{prov.with_api_key}/{prov.total} keys • {prov.measured} measured • non-chat {non.measured}/{non.total} {non.measured_percent}%</div><div className={`mt-2 text-[10px] px-2 py-1 rounded-full border inline-block ${prov.rigor_status==="GOOD"?"bg-emerald-500/10 text-emerald-400 border-emerald-500/20":"bg-amber-500/10 text-amber-400 border-amber-500/20"}`}>{prov.rigor_status}</div></div>
      </div>
      <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/20">
        <div className="text-[11px] font-medium text-emerald-300">✅ Rigor P11 — 0% invenção, honesto, auditado</div>
        <div className="mt-2 grid md:grid-cols-2 gap-2 text-[11px]">
          <div className="p-2 rounded-lg bg-zinc-900 border border-zinc-800"><div className="font-medium">Princípio</div><div className="text-zinc-500 mt-1">{rigor?.principle}</div></div>
          <div className="p-2 rounded-lg bg-zinc-900 border border-zinc-800"><div className="font-medium">Recomendação</div><div className="text-zinc-500 mt-1">{rigor?.recommendation}</div></div>
        </div>
        <div className="mt-2 p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-[11px]">
          <div className="font-medium">Audit: {rigor?.audit?.scores_inventados} inventados • {rigor?.audit?.scores_measured} measured • chat {rigor?.audit?.chat_measured} • non-chat {rigor?.audit?.non_chat_measured} • honest {String(rigor?.audit?.honest)}</div>
          <div className="text-zinc-500 mt-1">{rigor?.audit?.note}</div>
          <div className="mt-1 text-[10px] font-mono text-zinc-600">Non-chat: {non.note} — expected fail CODING benchmark, não conta para rigor chat real. Chat vs non-chat separados P9.1 fix.</div>
        </div>
      </div>
    </div>
  );
}
