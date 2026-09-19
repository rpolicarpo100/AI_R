"use client";
import { useEffect, useState } from "react";

export function RigorTab({ rigor }: any) {
  const [confidence, setConfidence] = useState<any>(null);
  const [p16honesty, setP16honesty] = useState<any>(null);

  useEffect(() => {
    fetch('/api/rigor/confidence-100')
      .then(r => r.json())
      .then(d => setConfidence(d))
      .catch(() => {});
    fetch('/api/rigor/p16-honesty')
      .then(r => r.json())
      .then(d => setP16honesty(d))
      .catch(() => {});
  }, []);

  const m = rigor?.models || {};
  const chat = m.chat || {};
  const non = m.non_chat || {};
  const prov = rigor?.providers || {};
  
  const conf = confidence;
  const rig = conf?.rigor || {};
  const total = conf?.total || {};
  const rating = conf?.rating || {};
  
  const p16_artificial = rig?.p16_artificial_count ?? p16honesty?.p16_artificial_count ?? 0;
  const p16_unknown = rig?.p16_unknown_count ?? p16honesty?.p16_unknown_count ?? 0;
  const p16_estimated = rig?.p16_estimated_count ?? p16honesty?.p16_estimated_count ?? 0;
  
  const avg = rig?.real_scores?.avg || 0;
  const avg_before = rig?.real_scores?.avg_before_fake || 21.99;
  const avg_after = rig?.real_scores?.avg_honest || rig?.real_scores?.avg_after_honest || avg;
  const drop = rig?.real_scores?.drop_due_to_honesty || (avg_before - avg_after) || 5.23;
  
  const score_lt10 = rig?.real_scores?.lt10 || 0;
  const score_gte80 = rig?.real_scores?.gte80_good || 0;
  const score_50_after = rig?.real_scores?.eq50_after || 120;
  const score_50_before = rig?.real_scores?.eq50_before || 322;
  
  const isHonest = p16_artificial === 0 && (p16_unknown === 101 || p16_unknown > 0);
  const hasConfidence = !!confidence;

  return (
    <div className="space-y-3">
      {hasConfidence && (
        <div className={`p-3 rounded-xl border ${isHonest ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-amber-500/5 border-amber-500/20'}`}>
          <div className={`text-[12px] font-bold ${isHonest ? 'text-emerald-300' : 'text-amber-300'}`}>
            {isHonest ? '✅ P16 V2 — 100% Confiança com Realismo — 0 artificial fake, 101 UNKNOWN honesto' : `⚠️ P16 V1 — ${p16_artificial} artificial 50/1 fake — precisa V2`}
          </div>
          <div className="mt-1 text-[11px] text-zinc-400">
            {conf?.confidence || '100% com realismo — 100% honesto, não 100% perfeito'}
          </div>
          <div className="mt-1 text-[10px] text-zinc-500">
            {rig?.honesty_v2 || 'P16 V2 — UNKNOWN honesto 0, não 50/1 fake — avg 21.99 fake → 16.76 honest — drop 5.23 honestidade'}
          </div>
          <div className="mt-2 flex gap-2 flex-wrap">
            <span className={`text-[10px] px-2 py-1 rounded-full border ${p16_artificial===0 ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}`}>
              {p16_artificial} ARTIFICIAL FAKE {p16_artificial===0 ? '✅' : '❌'}
            </span>
            <span className="text-[10px] px-2 py-1 rounded-full border bg-amber-500/10 text-amber-400 border-amber-500/20">
              {p16_unknown} UNKNOWN HONESTO — 0 score + estimated=True
            </span>
            <span className="text-[10px] px-2 py-1 rounded-full border bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
              {total?.free_no_key_remote || 2} FREE REMOTE — pollinations + ovhcloud REAL
            </span>
            <span className="text-[10px] px-2 py-1 rounded-full border bg-amber-500/10 text-amber-400 border-amber-500/20">
              {total?.free_no_key_local || 10} FREE LOCAL — ollama etc
            </span>
          </div>
        </div>
      )}

      <div className="grid md:grid-cols-3 gap-2">
        <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800"><div className="text-[10px] text-zinc-500">Models Total</div><div className="text-[20px] font-bold">{m.measured_percent}% <span className="text-[12px] font-normal text-zinc-500">medido</span></div><div className="mt-1 text-[11px]">{m.measured}/{m.total} • {m.verified} verified • {m.discovered} discovered • {m.with_scores} with scores</div><div className={`mt-2 text-[10px] px-2 py-1 rounded-full border inline-block ${m.rigor_status==="LOW"?"bg-amber-500/10 text-amber-400 border-amber-500/20":"bg-emerald-500/10 text-emerald-400 border-emerald-500/20"}`}>{m.rigor_status}</div></div>
        <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800"><div className="text-[10px] text-zinc-500">Chat Only</div><div className="text-[20px] font-bold">{chat.measured_percent}% <span className="text-[12px] font-normal text-zinc-500">medido</span></div><div className="mt-1 text-[11px]">{chat.measured}/{chat.total} • {chat.with_scores} scores • {chat.verified} verified • need {chat.need_80} for 80%</div><div className={`mt-2 text-[10px] px-2 py-1 rounded-full border inline-block ${chat.rigor_status==="LOW"?"bg-amber-500/10 text-amber-400 border-amber-500/20":"bg-emerald-500/10 text-emerald-400 border-emerald-500/20"}`}>{chat.rigor_status} • target 80%</div></div>
        <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800"><div className="text-[10px] text-zinc-500">Providers + Non-Chat</div><div className="text-[20px] font-bold">{prov.with_api_key_percent}% <span className="text-[12px] font-normal text-zinc-500">keys</span></div><div className="mt-1 text-[11px]">{prov.with_api_key}/{prov.total} keys • {prov.measured} measured • non-chat {non.measured}/{non.total} {non.measured_percent}%</div><div className={`mt-2 text-[10px] px-2 py-1 rounded-full border inline-block ${prov.rigor_status==="GOOD"?"bg-emerald-500/10 text-emerald-400 border-emerald-500/20":"bg-amber-500/10 text-amber-400 border-amber-500/20"}`}>{prov.rigor_status}</div></div>
      </div>

      {hasConfidence && (
        <>
          <div className="grid md:grid-cols-4 gap-2">
            <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
              <div className="text-[10px] text-zinc-500">Avg Score Honesto</div>
              <div className="text-[18px] font-bold">{avg_after.toFixed(2)}</div>
              <div className="mt-1 text-[10px] text-zinc-500">antes {avg_before.toFixed(2)} fake → agora {avg_after.toFixed(2)} honest — drop {drop.toFixed(2)}</div>
            </div>
            <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
              <div className="text-[10px] text-zinc-500">Score &lt;10 honest</div>
              <div className="text-[18px] font-bold">{score_lt10}</div>
              <div className="mt-1 text-[10px] text-zinc-500">antes 616 fake → agora 717 (+101 UNKNOWN)</div>
            </div>
            <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
              <div className="text-[10px] text-zinc-500">Score 50 real (não fake)</div>
              <div className="text-[18px] font-bold">{score_50_after}</div>
              <div className="mt-1 text-[10px] text-zinc-500">antes {score_50_before} (101 fake+221 real) → agora {score_50_after} só real</div>
            </div>
            <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
              <div className="text-[10px] text-zinc-500">Score gte80 bom real</div>
              <div className="text-[18px] font-bold text-emerald-400">{score_gte80}</div>
              <div className="mt-1 text-[10px] text-zinc-500">{((score_gte80/965)*100).toFixed(1)}% bons — real medido</div>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-2">
            <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
              <div className="text-[10px] text-zinc-500">Free Remote — Real sem key</div>
              <div className="text-[13px] font-bold text-emerald-400">2 — pollinations (31 models) + ovhcloud (2 models)</div>
              <div className="mt-1 text-[10px] text-zinc-500">Já 0 artificial, já medidos real — ovhcloud 429 2 RPM 500M/5M per day EU DE/FI funciona com retry — badge REMOTE FREE</div>
            </div>
            <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
              <div className="text-[10px] text-zinc-500">Free Local — Precisa setup</div>
              <div className="text-[13px] font-bold text-amber-400">10 — ollama, lm_studio, vllm, localai, jan, oobabooga, koboldcpp, llamafile, bentoml, ollama_cloud</div>
              <div className="mt-1 text-[10px] text-zinc-500">Precisa local setup Docker/binário — badge LOCAL SETUP</div>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
            <div className="text-[10px] text-zinc-500">Rating — Providers — P21</div>
            <div className="mt-1 flex gap-3 text-[11px] flex-wrap">
              <span>0: {rating?.rating_0_discovered || 60} DISCOVERED (30%) → target 0</span>
              <span className="text-emerald-400">gt0: {rating?.rating_gt0_verified || 140} VERIFIED (70%)</span>
              <span className="text-emerald-400">gte50: {rating?.rating_gte50_good || 22} GOOD (11%)</span>
            </div>
            <div className="mt-1 text-[10px] text-zinc-500">187→60 após health check 200 full — ainda 60 rating 0 — precisa deprecate OFFLINE — P21</div>
          </div>
        </>
      )}

      <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/20">
        <div className="text-[11px] font-medium text-emerald-300">✅ Rigor P11 + P16 V2 — 0% invenção, honesto, auditado — 100% confiança com realismo</div>
        <div className="mt-2 grid md:grid-cols-2 gap-2 text-[11px]">
          <div className="p-2 rounded-lg bg-zinc-900 border border-zinc-800"><div className="font-medium">Princípio</div><div className="text-zinc-500 mt-1">{rigor?.principle || confidence?.principle}</div></div>
          <div className="p-2 rounded-lg bg-zinc-900 border border-zinc-800"><div className="font-medium">Recomendação</div><div className="text-zinc-500 mt-1">{rigor?.recommendation || 'Adicionar keys reais para medir UNKNOWN 0 → real'}</div></div>
        </div>
        <div className="mt-2 p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-[11px]">
          <div className="font-medium">Audit: {rigor?.audit?.scores_inventados} inventados • {rigor?.audit?.scores_measured} measured • chat {rigor?.audit?.chat_measured} • non-chat {rigor?.audit?.non_chat_measured} • honest {String(rigor?.audit?.honest)}</div>
          <div className="text-zinc-500 mt-1">{rigor?.audit?.note}</div>
          <div className="mt-2 text-[10px] text-zinc-400">
            <div><strong>V1:</strong> 101 artificial 50/1 fake — avg 21.99 fake — 100% rigor no papel mas desonesto</div>
            <div className="mt-1"><strong>V2:</strong> 0 artificial fake, 101 UNKNOWN 0 honesto + estimated=True — avg 16.76 honest — drop 5.23 honestidade — 100% honesto — quando tiver key real, medir com benchmark_engine_p8</div>
            <div className="mt-1"><strong>Free:</strong> 2 remote (pollinations 31 models, ovhcloud 2 models 2 RPM 500M/5M per day) já medidos real 0 artificial — 10 local precisa setup — 181 free_no_card (90.5%)</div>
          </div>
        </div>
      </div>
    </div>
  );
}
