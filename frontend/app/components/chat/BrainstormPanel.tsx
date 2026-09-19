"use client";
import { useState } from "react";

export function BrainstormPanel({ brainstorm, onSelectApproach, onCreateProject }: any) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  if (!brainstorm) return null;

  const isBuild = brainstorm.is_build || brainstorm.approaches;
  const approaches = brainstorm.approaches || [];
  const interpretations = brainstorm.interpretations || [];
  const best = brainstorm.best_approach || brainstorm.best_interpretation;
  const suggested = brainstorm.suggested_templates || [];
  const recommendation = brainstorm.recommendation || "";

  return (
    <div className="mx-5 my-4 rounded-[20px] border border-violet-500/20 bg-[#0f0f17] overflow-hidden">
      <div className="px-4 py-3 border-b border-zinc-800/80 bg-violet-500/5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-6 h-6 rounded-full bg-violet-500 text-white flex items-center justify-center text-[11px]">🧠</span>
          <span className="text-[12px] font-[600] text-violet-200">Brainstorming — Mais perto do objetivo final</span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400 border border-zinc-700">{brainstorm.templates_count || 20} templates</span>
        </div>
        <div className="text-[10px] font-mono text-zinc-500">{brainstorm.brainstorm_id}</div>
      </div>

      <div className="p-4 space-y-3">
        <div className="text-[11px] leading-[1.5] text-zinc-400">{recommendation}</div>

        {isBuild ? (
          <>
            <div className="flex items-center gap-2 text-[11px] font-medium text-zinc-500 uppercase tracking-widest">
              <div className="h-px flex-1 bg-zinc-800"></div>
              3-5 abordagens — MVP vs Full vs Custom — Você no centro
              <div className="h-px flex-1 bg-zinc-800"></div>
            </div>
            <div className="grid gap-2.5">
              {approaches.map((ap: any) => (
                <div
                  key={ap.id}
                  onClick={() => setSelectedId(ap.id)}
                  className={`group rounded-2xl border p-3.5 cursor-pointer transition ${
                    selectedId === ap.id
                      ? "border-violet-500/50 bg-violet-500/10"
                      : ap.id === best?.id
                      ? "border-emerald-500/30 bg-emerald-500/5 hover:bg-emerald-500/10"
                      : "border-zinc-800 bg-zinc-900/40 hover:bg-zinc-900/80 hover:border-zinc-700"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-[12px] font-[600] text-white">{ap.name}</span>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full border ${ap.closest_to_final >= 90 ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/20" : ap.closest_to_final >= 80 ? "bg-amber-500/10 text-amber-300 border-amber-500/20" : "bg-zinc-800 text-zinc-400 border-zinc-700"}`}>
                          {ap.closest_to_final}% perto objetivo
                        </span>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400 border border-zinc-700">{ap.effort}</span>
                        {ap.id === best?.id && <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-500 text-white">★ Melhor</span>}
                      </div>
                      <div className="mt-1.5 text-[11px] leading-[1.4] text-zinc-400">{ap.description}</div>
                      <div className="mt-2 flex items-center gap-2 flex-wrap">
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-500 border border-zinc-700">📦 {ap.template}</span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-500 border border-zinc-700">{ap.tech_stack?.slice(0,60)}</span>
                      </div>
                      <div className="mt-2 grid grid-cols-2 gap-2 text-[10px] leading-[1.4]">
                        <div>
                          <div className="text-emerald-400 font-medium">✓ Pros</div>
                          <div className="text-zinc-500">{ap.pros?.slice(0,2).join(" • ")}</div>
                        </div>
                        <div>
                          <div className="text-amber-400 font-medium">△ Cons</div>
                          <div className="text-zinc-500">{ap.cons?.slice(0,2).join(" • ")}</div>
                        </div>
                      </div>
                      <div className="mt-2 text-[10px] text-zinc-600">🎯 {ap.best_for}</div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectApproach?.(ap);
                        onCreateProject?.(ap);
                      }}
                      className="shrink-0 px-3 py-1.5 rounded-full bg-white text-black text-[11px] font-medium hover:bg-zinc-100 transition"
                    >
                      Escolher esta
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {suggested.length > 0 && (
              <div className="rounded-xl bg-zinc-900/40 border border-zinc-800 p-3">
                <div className="text-[11px] font-medium text-zinc-400">Templates sugeridos (20 disponíveis P22)</div>
                <div className="mt-2 flex gap-2 flex-wrap">
                  {suggested.map((s: any) => (
                    <span key={s.template} className="text-[10px] px-2 py-1 rounded-full bg-violet-500/10 text-violet-300 border border-violet-500/20">
                      {s.template} — {s.name} ({s.score})
                    </span>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <>
            <div className="flex items-center gap-2 text-[11px] font-medium text-zinc-500 uppercase tracking-widest">
              <div className="h-px flex-1 bg-zinc-800"></div>
              3-5 interpretações — Qual objetivo final real?
              <div className="h-px flex-1 bg-zinc-800"></div>
            </div>
            <div className="grid gap-2">
              {interpretations.map((interp: any) => (
                <div
                  key={interp.id}
                  className={`rounded-2xl border p-3 ${
                    interp.id === best?.id ? "border-emerald-500/30 bg-emerald-500/5" : "border-zinc-800 bg-zinc-900/40"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-medium text-white">{interp.type}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400">{interp.closest_to_final}% perto objetivo</span>
                    {interp.id === best?.id && <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-500 text-white">★ Melhor</span>}
                  </div>
                  <div className="mt-1 text-[11px] leading-[1.4] text-zinc-400">{interp.interpretation}</div>
                  {interp.questions && (
                    <div className="mt-2 text-[10px] text-amber-300">
                      <div className="font-medium">Perguntas clarificação:</div>
                      <div className="text-zinc-500">{interp.questions.slice(0,2).join(" • ")}</div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
        )}

        <div className="rounded-xl bg-[#08080c] border border-zinc-800/60 p-2.5 flex items-center justify-between">
          <span className="text-[10px] font-mono text-zinc-600">🧠 brainstorm_id {brainstorm.brainstorm_id} • P24 deep integration • 20 templates • você no centro • terceiro olho</span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-500/10 text-violet-400 border border-violet-500/20">P24 DONE</span>
        </div>
      </div>
    </div>
  );
}
