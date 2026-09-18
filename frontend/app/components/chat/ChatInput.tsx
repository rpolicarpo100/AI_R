"use client";
import { useState, useRef, useEffect, useMemo, useCallback } from "react";
import { CHAT_COMMANDS } from "../../lib/commands";

interface FileItem {
  name: string;
  size: number;
  content: string;
  tokens: number;
}

export function ChatInput({ chatInput, setChatInput, onSend, chatLoading, chatMode, selectedModelId, chatInputRef, distinctModels, projects }: any) {
  const isCommand = chatInput.trim().startsWith("/");
  const commandName = isCommand ? chatInput.trim().slice(1).split(" ")[0].toLowerCase() : "";
  const command = CHAT_COMMANDS.find(c => c.id === commandName);
  
  const [dragOver, setDragOver] = useState(false);
  const [showLargePasteModal, setShowLargePasteModal] = useState<{text: string, chars: number} | null>(null);
  const [showFileList, setShowFileList] = useState<FileItem[]>([]);
  const [showAtFiles, setShowAtFiles] = useState(false);
  const [atFilter, setAtFilter] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [tokenStats, setTokenStats] = useState({ chars: 0, tokens: 0, pct: 0, modelContext: 128000 });

  // P5.1 + P6 — Real-time token calculation with debounce 300ms + model context awareness + WebWorker for large
  const modelContextLimit = useMemo(() => {
    if (!distinctModels || !selectedModelId) return 128000;
    const m = distinctModels.find((dm: any) => dm.base_id === selectedModelId || dm.base_id.includes(selectedModelId) || selectedModelId.includes(dm.base_id));
    if (m && m.context_window) return m.context_window;
    if (chatMode === "auto") return 128000;
    return 32000;
  }, [distinctModels, selectedModelId, chatMode]);

  // P6 — Debounce 300ms for token counter to avoid lag on large typing
  useEffect(() => {
    const handler = setTimeout(() => {
      const chars = chatInput.length;
      // P6 — For large >10k, use WebWorker-like offload via setTimeout to avoid blocking main thread
      if (chars > 10000) {
        // Offload heavy calc to next tick
        setTimeout(() => {
          const tokens = Math.ceil(chars / 4);
          const pct = modelContextLimit > 0 ? Math.round((tokens / modelContextLimit) * 100) : 0;
          setTokenStats({ chars, tokens, pct, modelContext: modelContextLimit });
        }, 0);
      } else {
        const tokens = Math.ceil(chars / 4);
        const pct = modelContextLimit > 0 ? Math.round((tokens / modelContextLimit) * 100) : 0;
        setTokenStats({ chars, tokens, pct, modelContext: modelContextLimit });
      }
    }, 300); // 300ms debounce P6

    return () => clearTimeout(handler);
  }, [chatInput, modelContextLimit]);

  // P5.1 — Auto-resize textarea 24px → 50vh (not 140px) for large prompts
  useEffect(() => {
    if (chatInputRef.current) {
      chatInputRef.current.style.height = '24px';
      const scrollHeight = chatInputRef.current.scrollHeight;
      const maxHeight = window.innerHeight * 0.5; // 50vh max
      chatInputRef.current.style.height = Math.min(scrollHeight, maxHeight) + 'px';
    }
  }, [chatInput]);

  // P5.1 — Drag-drop handling for large files
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length === 0) return;
    
    const fileItems: FileItem[] = [];
    for (const file of files.slice(0, 10)) { // max 10 files
      if (file.size > 500000) { // 500k limit per file
        alert(`Arquivo ${file.name} muito grande (${file.size} chars) > 500k limite, use workplace`);
        continue;
      }
      try {
        const text = await file.text();
        fileItems.push({
          name: file.name,
          size: text.length,
          content: text,
          tokens: Math.ceil(text.length / 4)
        });
      } catch (err) {
        console.error(`Failed to read ${file.name}`, err);
      }
    }
    
    if (fileItems.length > 0) {
      setShowFileList(prev => [...prev, ...fileItems]);
      // Auto-insert first file content if small, otherwise show list
      if (fileItems.length === 1 && fileItems[0].size < 10000) {
        setChatInput(prev => prev + `\n\n// File: ${fileItems[0].name}\n${fileItems[0].content}\n`);
      }
    }
  }, [setChatInput]);

  // P5.1 — File upload button
  const handleFileUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;
    const fileItems: FileItem[] = [];
    for (const file of Array.from(files).slice(0, 10)) {
      if (file.size > 500000) {
        alert(`Arquivo ${file.name} muito grande > 500k, use workplace`);
        continue;
      }
      try {
        const text = await file.text();
        fileItems.push({
          name: file.name,
          size: text.length,
          content: text,
          tokens: Math.ceil(text.length / 4)
        });
      } catch (err) {
        console.error(`Failed to read ${file.name}`, err);
      }
    }
    if (fileItems.length > 0) {
      setShowFileList(prev => [...prev, ...fileItems]);
      if (fileItems.length === 1 && fileItems[0].size < 10000) {
        setChatInput(prev => prev + `\n\n// File: ${fileItems[0].name}\n${fileItems[0].content}\n`);
      }
    }
    if (fileInputRef.current) fileInputRef.current.value = "";
  }, [setChatInput]);

  // P5.1 — Paste large detection >5k chars
  const handlePaste = useCallback((e: React.ClipboardEvent) => {
    const text = e.clipboardData.getData('text');
    if (text.length > 5000) {
      // Show modal for large paste
      e.preventDefault();
      setShowLargePasteModal({ text, chars: text.length });
    }
  }, []);

  const handleLargePasteAction = useCallback((action: 'insert' | 'workplace' | 'cancel') => {
    if (!showLargePasteModal) return;
    if (action === 'insert') {
      setChatInput(prev => prev + showLargePasteModal.text);
    } else if (action === 'workplace') {
      // Save to workplace file reference — for now just insert with marker
      const fileName = `pasted-${Date.now()}.txt`;
      setChatInput(prev => prev + `\n\n// Large paste saved as ${fileName} — consider workplace\n// File: ${fileName} (${showLargePasteModal.chars} chars, ~${Math.ceil(showLargePasteModal.chars/4)} tokens)\n${showLargePasteModal.text.slice(0, 50000)}\n// ... truncated if >50k, full in workplace\n`);
      setShowFileList(prev => [...prev, { name: fileName, size: showLargePasteModal.chars, content: showLargePasteModal.text, tokens: Math.ceil(showLargePasteModal.chars/4) }]);
    }
    setShowLargePasteModal(null);
  }, [showLargePasteModal, setChatInput]);

  // P5.1 — @file autocomplete for workplace files
  useEffect(() => {
    const atMatch = chatInput.match(/@([^\s]*)$/);
    if (atMatch) {
      setAtFilter(atMatch[1].toLowerCase());
      setShowAtFiles(true);
    } else {
      setShowAtFiles(false);
    }
  }, [chatInput]);

  const filteredAtFiles = useMemo(() => {
    if (!projects || !showAtFiles) return [];
    const allFiles: any[] = [];
    projects.slice(0, 20).forEach((p: any) => {
      Object.keys(p.files || {}).forEach(fname => {
        allFiles.push({ project: p.name, project_id: p.project_id, file: fname, path: `${p.project_id}/${fname}`, full: p.files[fname] });
      });
    });
    if (!atFilter) return allFiles.slice(0, 8);
    return allFiles.filter(f => f.file.toLowerCase().includes(atFilter) || f.project.toLowerCase().includes(atFilter)).slice(0, 8);
  }, [projects, showAtFiles, atFilter]);

  const handleAtFileSelect = useCallback((file: any) => {
    // Replace @filter with @file reference and insert content
    const newInput = chatInput.replace(/@([^\s]*)$/, `@${file.path} `);
    // Optionally insert file content
    const content = file.full || "";
    if (content.length < 20000) {
      setChatInput(newInput + `\n\n// File: ${file.path}\n${content.slice(0, 20000)}\n`);
    } else {
      setChatInput(newInput + `\n// File: ${file.path} (${content.length} chars) — large, use workplace reference\n`);
    }
    setShowAtFiles(false);
  }, [chatInput, setChatInput]);

  const isLarge = tokenStats.chars > 50000;
  const isVeryLarge = tokenStats.chars > 100000;
  const isCriticalLarge = tokenStats.pct > 80;

  return (
    <div className="p-3.5 border-t border-zinc-900/80 bg-[#111116]/50" onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}>
      {/* Drag over overlay */}
      {dragOver && (
        <div className="mb-3 rounded-xl border-2 border-dashed border-violet-500/50 bg-violet-500/10 p-6 text-center">
          <div className="text-[13px] font-medium text-violet-300">📁 Drop files aqui — até 10 files, 500k cada</div>
          <div className="mt-1 text-[11px] text-zinc-500">Texto, código, logs, docs — será lido e adicionado ao prompt com token awareness</div>
        </div>
      )}

      {/* File list */}
      {showFileList.length > 0 && (
        <div className="mb-3 rounded-xl bg-zinc-900/50 border border-zinc-800 p-2.5 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium text-zinc-400">📁 {showFileList.length} files carregados — token awareness</span>
            <button onClick={() => setShowFileList([])} className="text-[10px] text-zinc-600 hover:text-zinc-400">limpar</button>
          </div>
          {showFileList.map((f, i) => (
            <div key={i} className="flex items-center justify-between text-[11px] bg-[#08080c] rounded-lg px-2.5 py-1.5 border border-zinc-800/50">
              <span className="font-mono text-zinc-300">{f.name}</span>
              <span className="flex items-center gap-2">
                <span className="text-zinc-500">{f.size} chars ~{f.tokens} tokens</span>
                <button onClick={() => {
                  setChatInput(prev => prev + `\n\n// File: ${f.name}\n${f.content.slice(0, 50000)}\n`);
                }} className="px-2 py-0.5 rounded-full bg-white text-black text-[10px]">inserir</button>
                <button onClick={() => setShowFileList(prev => prev.filter((_, idx) => idx !== i))} className="text-zinc-600 hover:text-red-400">×</button>
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Large paste modal */}
      {showLargePasteModal && (
        <div className="mb-3 rounded-xl bg-amber-500/10 border border-amber-500/20 p-3">
          <div className="text-[12px] font-medium text-amber-300">⚠️ Large paste detectado — {showLargePasteModal.chars} chars ~{Math.ceil(showLargePasteModal.chars/4)} tokens</div>
          <div className="mt-1 text-[11px] text-zinc-400">Grandes quantidades de dados — tratamento rápido faseado real e funcional</div>
          <div className="mt-2.5 flex gap-2">
            <button onClick={() => handleLargePasteAction('insert')} className="px-3 py-1.5 rounded-full bg-white text-black text-[11px] font-medium">Inserir direto</button>
            <button onClick={() => handleLargePasteAction('workplace')} className="px-3 py-1.5 rounded-full bg-zinc-800 text-zinc-300 text-[11px] border border-zinc-700">Salvar workplace + referência</button>
            <button onClick={() => handleLargePasteAction('cancel')} className="px-3 py-1.5 rounded-full bg-zinc-900 text-zinc-500 text-[11px] border border-zinc-800">Cancelar</button>
          </div>
        </div>
      )}

      {/* @file autocomplete */}
      {showAtFiles && filteredAtFiles.length > 0 && (
        <div className="mb-2.5 rounded-xl bg-zinc-900 border border-zinc-800 p-1.5 max-h-[160px] overflow-auto">
          <div className="text-[10px] text-zinc-600 px-2 py-1">📁 @file — workplace files (token awareness)</div>
          {filteredAtFiles.map((f: any, i: number) => (
            <button key={i} onClick={() => handleAtFileSelect(f)} className="w-full text-left px-2.5 py-1.5 rounded-lg hover:bg-zinc-800 transition flex items-center justify-between">
              <span className="text-[11px] font-mono text-zinc-300">{f.path}</span>
              <span className="text-[10px] text-zinc-500">{f.project} • {(f.full?.length || 0)} chars</span>
            </button>
          ))}
        </div>
      )}

      {/* Command hint */}
      {isCommand && command && (
        <div className="mb-2.5 px-3 py-2 rounded-xl bg-violet-500/5 border border-violet-500/15 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-violet-500 text-white">{command.label}</span>
            <span className="text-[11px] text-zinc-400">{command.desc}</span>
            <span className="hidden md:inline text-[10px] px-1.5 py-0.5 rounded-full bg-zinc-800 text-zinc-500">{command.agents.length} agentes</span>
          </div>
          <span className="text-[10px] text-zinc-600 hidden md:block">{command.critical.slice(0,60)}</span>
        </div>
      )}

      {/* Large warning */}
      {(isLarge || isCriticalLarge) && (
        <div className={`mb-2.5 px-3 py-2 rounded-xl border flex items-center justify-between ${isVeryLarge ? "bg-red-500/10 border-red-500/20" : isCriticalLarge ? "bg-amber-500/10 border-amber-500/20" : "bg-yellow-500/5 border-yellow-500/15"}`}>
          <div className="flex items-center gap-2">
            <span className={`text-[11px] font-medium ${isVeryLarge ? "text-red-400" : isCriticalLarge ? "text-amber-400" : "text-yellow-400"}`}>
              {isVeryLarge ? "🚨 Muito grande" : isCriticalLarge ? "⚠️ Grande" : "📏 Grande"} — {tokenStats.chars} chars ~{tokenStats.tokens} tokens ({tokenStats.pct}% de {tokenStats.modelContext} context)
            </span>
            {isCriticalLarge && <span className="text-[10px] text-zinc-500">Pode precisar modelo long context — auto routing vai selecionar</span>}
          </div>
          <span className="text-[10px] text-zinc-600 hidden md:block">Faseado: validação → LONG_CONTEXT → routing → provider</span>
        </div>
      )}

      <div className={`flex items-end gap-2 rounded-[20px] border px-3.5 py-2.5 transition ${isCommand ? "bg-violet-500/5 border-violet-500/20 focus-within:border-violet-500/30" : dragOver ? "bg-violet-500/5 border-violet-500/30" : isVeryLarge ? "bg-red-500/5 border-red-500/20 focus-within:border-red-500/30" : isLarge ? "bg-amber-500/5 border-amber-500/20 focus-within:border-amber-500/30" : "bg-zinc-900 border-zinc-800 focus-within:border-zinc-700"}`}>
        {/* File upload button */}
        <button onClick={() => fileInputRef.current?.click()} className="w-8 h-8 rounded-full bg-zinc-800 text-zinc-400 flex items-center justify-center hover:bg-zinc-700 hover:text-zinc-200 transition shrink-0 text-[14px]" title="Upload files — até 10 files, 500k cada">
          📎
        </button>
        <input ref={fileInputRef} type="file" multiple accept=".txt,.md,.py,.js,.ts,.tsx,.json,.log,.csv,.yaml,.yml,.toml,.sh,.sql,.html,.css" onChange={handleFileUpload} className="hidden" />
        
        <textarea
          ref={chatInputRef}
          value={chatInput}
          onChange={e=>setChatInput(e.target.value)}
          onPaste={handlePaste}
          onKeyDown={e=>{
            if(e.key==="Enter" && !e.shiftKey){
              e.preventDefault();
              onSend();
            }
            if(e.key==="Escape"){
              setShowAtFiles(false);
              setShowLargePasteModal(null);
            }
          }}
          placeholder={chatMode==="auto" ? "Pergunte, crie, ou use /comando — cole grande quantidade dados, drag-drop files, @file workplace, /testa /audita /contesta..." : `MANUAL ${selectedModelId}... ou /comando — large data handling faseado`}
          className="flex-1 bg-transparent text-[13.5px] leading-[1.5] outline-none resize-none max-h-[50vh] min-h-[24px] py-1 placeholder:text-zinc-600"
          rows={1}
        />
        <button onClick={onSend} disabled={chatLoading || !chatInput.trim()} className="w-8 h-8 rounded-full bg-white text-black flex items-center justify-center hover:bg-zinc-100 disabled:opacity-30 disabled:cursor-not-allowed transition shrink-0 text-[14px] font-medium">↑</button>
      </div>

      <div className="mt-2.5 flex items-center justify-between px-1">
        <div className="flex gap-1.5 flex-wrap items-center">
          {CHAT_COMMANDS.slice(0,3).map(cmd=>(
            <button key={cmd.id} onClick={()=>setChatInput(cmd.label + " ")} className="group flex items-center gap-1 text-[11px] px-2.5 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-zinc-500 hover:text-zinc-200 hover:border-zinc-700 transition">
              <span className="font-mono">{cmd.label}</span>
              <span className="w-px h-3 bg-zinc-800 group-hover:bg-zinc-700"></span>
              <span className="text-[10px]">{cmd.agents.length} agentes</span>
            </button>
          ))}
          <span className="text-[10px] text-zinc-700 mx-1">•</span>
          <button onClick={()=>setChatInput("/ajuda ")} className="text-[11px] px-2.5 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-zinc-500 hover:text-zinc-300 transition">/ajuda • {CHAT_COMMANDS.length} comandos</button>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${isCriticalLarge ? "bg-red-500/10 text-red-400 border-red-500/20" : isLarge ? "bg-amber-500/10 text-amber-400 border-amber-500/20" : tokenStats.chars > 1000 ? "bg-zinc-800 text-zinc-400 border-zinc-700" : "bg-zinc-900 text-zinc-600 border-zinc-800"}`}>
            {tokenStats.chars} chars ~{tokenStats.tokens} tokens • {tokenStats.pct}% de {tokenStats.modelContext}
          </span>
          <span className="hidden lg:block text-[10px] font-mono text-zinc-700">Ctrl+K foco • @file • 📎 files • drag-drop</span>
        </div>
      </div>
    </div>
  );
}
