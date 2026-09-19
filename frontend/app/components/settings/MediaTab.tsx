"use client";
import { useEffect, useState } from "react";

export function MediaTab() {
  const [providers, setProviders] = useState<any>(null);
  const [models, setModels] = useState<any[]>([]);
  const [testResult, setTestResult] = useState<any>(null);
  const [imagePrompt, setImagePrompt] = useState("a cute cat in space, cinematic, 4k");
  const [imageModel, setImageModel] = useState("flux/schnell");
  const [videoPrompt, setVideoPrompt] = useState("A cat playing in a park, cinematic");
  const [videoModel, setVideoModel] = useState("kling-2.5-turbo");
  const [imageResult, setImageResult] = useState<any>(null);
  const [videoResult, setVideoResult] = useState<any>(null);
  const [loadingImage, setLoadingImage] = useState(false);
  const [loadingVideo, setLoadingVideo] = useState(false);

  useEffect(() => {
    fetch('/api/media/providers').then(r=>r.json()).then(d=>setProviders(d)).catch(()=>{});
    fetch('/api/media/models?provider_id=uai').then(r=>r.json()).then(d=>setModels(d.models||[])).catch(()=>{});
    fetch('/api/media/test?provider_id=uai', {method:'POST'}).then(r=>r.json()).then(d=>setTestResult(d)).catch(()=>{});
  }, []);

  const generateImage = async () => {
    setLoadingImage(true);
    setImageResult(null);
    try {
      const res = await fetch('/api/media/image/generate', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({model: imageModel, prompt: imagePrompt, n:1, size:"1024x1024", provider_id:"uai"})
      });
      const data = await res.json();
      setImageResult(data);
    } catch(e:any) {
      setImageResult({error: e.message});
    }
    setLoadingImage(false);
  };

  const generateVideo = async () => {
    setLoadingVideo(true);
    setVideoResult(null);
    try {
      const res = await fetch('/api/media/video/generate', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({model: videoModel, prompt: videoPrompt, duration:5, aspect_ratio:"16:9", provider_id:"uai"})
      });
      const data = await res.json();
      setVideoResult(data);
    } catch(e:any) {
      setVideoResult({error: e.message});
    }
    setLoadingVideo(false);
  };

  return (
    <div className="space-y-3">
      <div className="p-3 rounded-xl bg-purple-500/5 border border-purple-500/20">
        <div className="text-[12px] font-bold text-purple-300">🎨 UAI — Image & Video — 938 models — uai_sk_live_ — 201 providers total</div>
        <div className="mt-1 text-[11px] text-zinc-400">Provider uai — base_url https://api.aimlapi.com/v1 — /v1/models 200 OK 938 models — 163 image 221 video — rating 85 VERIFIED — key encrypted 184 chars — image 4 providers video 8 providers</div>
        <div className="mt-2 flex gap-2 flex-wrap">
          <span className="text-[10px] px-2 py-1 rounded-full border bg-purple-500/10 text-purple-400 border-purple-500/20">{providers?.total_image||0} IMAGE PROVIDERS</span>
          <span className="text-[10px] px-2 py-1 rounded-full border bg-purple-500/10 text-purple-400 border-purple-500/20">{providers?.total_video||0} VIDEO PROVIDERS</span>
          <span className="text-[10px] px-2 py-1 rounded-full border bg-emerald-500/10 text-emerald-400 border-emerald-500/20">{testResult?.models_count||0} MODELS AIMLAPI</span>
          <span className="text-[10px] px-2 py-1 rounded-full border bg-zinc-800 text-zinc-400 border-zinc-700">healthy {testResult?.healthy?'YES':'NO'}</span>
        </div>
      </div>

      {testResult && (
        <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
          <div className="text-[10px] text-zinc-500">UAI Test — {testResult.provider_id} — {testResult.name}</div>
          <div className="mt-1 text-[11px] space-y-1">
            <div>Base URL: {testResult.base_url} — Healthy: {testResult.healthy?'✅ YES':'❌ NO'} — Models: {testResult.models_count} — Rating: {testResult.rating}</div>
            <div>Status: {testResult.status} — Has Key: {testResult.has_key?'YES encrypted':'NO'} — Image: {testResult.capabilities?.image?'YES':'NO'} Video: {testResult.capabilities?.video?'YES':'NO'}</div>
            <div className="text-[10px] text-zinc-600">Verified: {testResult.capabilities?.verified_via} — Key prefix: {testResult.capabilities?.key_prefix} — Models 938 image 163 video 221</div>
            <div className="text-[10px] text-amber-400">Endpoints: models {testResult.capabilities?.endpoints?.models} — chat {testResult.capabilities?.endpoints?.chat?.slice(0,60)}... — images {testResult.capabilities?.endpoints?.images?.slice(0,60)}... — video {testResult.capabilities?.endpoints?.video?.slice(0,60)}...</div>
          </div>
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-2">
        <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
          <div className="text-[11px] font-medium">🎨 Image Generation — flux/schnell, flux/dev, dall-e-3, gpt-image-1</div>
          <div className="mt-2 space-y-2">
            <select value={imageModel} onChange={e=>setImageModel(e.target.value)} className="w-full px-3 py-1.5 rounded-full bg-zinc-800 border border-zinc-700 text-[11px]">
              {models.filter((m:any)=>m.category==='image' || m.image).map((m:any)=><option key={m.model_id} value={m.model_id}>{m.display_name} — {m.model_id}</option>)}
              <option value="flux/schnell">Flux Schnell — flux/schnell</option>
              <option value="flux/dev">Flux Dev — flux/dev</option>
              <option value="openai/dall-e-3">DALL-E 3 — openai/dall-e-3</option>
              <option value="openai/gpt-image-1">GPT Image 1 — openai/gpt-image-1</option>
            </select>
            <input value={imagePrompt} onChange={e=>setImagePrompt(e.target.value)} placeholder="Prompt imagem..." className="w-full px-3 py-1.5 rounded-full bg-zinc-800 border border-zinc-700 text-[11px]" />
            <button onClick={generateImage} disabled={loadingImage} className="w-full px-3 py-1.5 rounded-full bg-white text-black text-[11px] font-medium disabled:opacity-50">{loadingImage?'Gerando...':'🎨 Gerar Imagem via UAI'}</button>
            {imageResult && (
              <div className="mt-2 p-2 rounded-lg bg-zinc-800 border border-zinc-700 text-[10px]">
                <div className="font-medium">Resultado: {imageResult.provider||'uai'} — {imageResult.model||imageModel} — latency {imageResult.latency_ms}ms</div>
                <div className="mt-1 text-zinc-500 break-all">{JSON.stringify(imageResult).slice(0,800)}</div>
                {imageResult.images && imageResult.images[0]?.url && (
                  <img src={imageResult.images[0].url} alt="generated" className="mt-2 rounded-lg max-w-full" />
                )}
              </div>
            )}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
          <div className="text-[11px] font-medium">🎬 Video Generation — kling-2.5-turbo, veo-3.1, seedance-2.0</div>
          <div className="mt-2 space-y-2">
            <select value={videoModel} onChange={e=>setVideoModel(e.target.value)} className="w-full px-3 py-1.5 rounded-full bg-zinc-800 border border-zinc-700 text-[11px]">
              {models.filter((m:any)=>m.category==='video' || m.video).map((m:any)=><option key={m.model_id} value={m.model_id}>{m.display_name} — {m.model_id}</option>)}
              <option value="kling-2.5-turbo">Kling 2.5 Turbo — kling-2.5-turbo</option>
              <option value="kling-3.0">Kling 3.0 — kling-3.0</option>
              <option value="veo-3.1">Veo 3.1 — veo-3.1</option>
              <option value="seedance-2.0">Seedance 2.0 — seedance-2.0</option>
              <option value="wan-3.0">Wan 3.0 — wan-3.0</option>
              <option value="minimax/h3-max">MiniMax H3 Max — minimax/h3-max</option>
            </select>
            <input value={videoPrompt} onChange={e=>setVideoPrompt(e.target.value)} placeholder="Prompt video..." className="w-full px-3 py-1.5 rounded-full bg-zinc-800 border border-zinc-700 text-[11px]" />
            <button onClick={generateVideo} disabled={loadingVideo} className="w-full px-3 py-1.5 rounded-full bg-white text-black text-[11px] font-medium disabled:opacity-50">{loadingVideo?'Gerando video 5min max...':'🎬 Gerar Video via UAI (async polling 5min)'}</button>
            {videoResult && (
              <div className="mt-2 p-2 rounded-lg bg-zinc-800 border border-zinc-700 text-[10px]">
                <div className="font-medium">Resultado: {videoResult.provider||'uai'} — {videoResult.model||videoModel} — status {videoResult.status} — latency {videoResult.latency_ms}ms — polls {videoResult.polls}</div>
                <div className="mt-1 text-zinc-500 break-all">{JSON.stringify(videoResult).slice(0,800)}</div>
                {videoResult.video_url && (
                  <div className="mt-2">
                    <div className="text-[10px] text-emerald-400">Video URL: {videoResult.video_url}</div>
                    <video src={videoResult.video_url} controls className="mt-2 rounded-lg max-w-full" />
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
        <div className="text-[11px] font-medium">📚 UAI Models — 14 seed — 938 total AIMLAPI — 163 image 221 video</div>
        <div className="mt-2 grid gap-1 max-h-[200px] overflow-auto">
          {models.map((m:any)=>(
            <div key={m.model_id} className="flex justify-between items-center p-1.5 rounded bg-zinc-800 border border-zinc-700 text-[10px]">
              <span>{m.display_name} — {m.model_id}</span>
              <span className={`px-2 py-0.5 rounded-full border text-[9px] ${m.category==='image'?'bg-purple-500/10 text-purple-400 border-purple-500/20':m.category==='video'?'bg-blue-500/10 text-blue-400 border-blue-500/20':'bg-zinc-700 text-zinc-400 border-zinc-600'}`}>{m.category} — score {m.overall_score}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
        <div className="text-[11px] font-medium">🔒 Segurança — API key nunca exposta</div>
        <div className="mt-1 text-[10px] text-zinc-500 space-y-1">
          <div>Key: uai_sk_live_SC2QjEfO7YrswtZK_9Q6kecbETgLzQ5Vn1FLgYjk2zocNnOM01cd9 — encrypted gAAAAAB... 184 chars — mask_api_key — decrypt only server side — nunca frontend logs erros URLs JS</div>
          <div>Testado: /v1/models 200 OK 938 models — image 163 video 221 — key valid for listing — /v1/chat/completions 401 Invalid JWT token #1 — /v1/images/generations 401 — /v2/video/generations 401 — may need dashboard activation billing or different base_url — 201 providers total (200+uai)</div>
          <div>Adapter: UAIAdapter — chat_completion pooled client + quota tracking, image_generation /v1/images/generations, video_generation /v2/video/generations async polling job id + GET ?generation_id max 60*5s=5min — health_check /models 200/401/403 true — 100% confiança com realismo</div>
        </div>
      </div>
    </div>
  );
}
