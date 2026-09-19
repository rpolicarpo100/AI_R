"use client";
import { useRef, useEffect, useState, useMemo } from "react";
import { ChatHeader, ChatModelSelect } from "./ChatHeader";
import { ChatMessages } from "../ChatMessages";
import { ChatInput } from "./ChatInput";
import { CommandsPalette } from "../CommandsPalette";
import { CHAT_COMMANDS } from "../../lib/commands";

export function ChatContainer({
  chatMessages, chatLoading, streamEnabled, setStreamEnabled,
  chatMode, setChatMode, selectedModelId, setSelectedModelId, distinctModels,
  workplaceOpen, setWorkplaceOpen, projectsCount,
  chatInput, setChatInput, onSend, onSave, onCreateFromTemplate, chatInputRef,
  projects
}: any) {
  const chatEndRef = useRef<HTMLDivElement>(null);
  const [showCommands, setShowCommands] = useState(false);
  const [commandFilter, setCommandFilter] = useState("");

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages, chatLoading]);

  useEffect(() => {
    if (chatInput.startsWith("/")) {
      setShowCommands(true);
      setCommandFilter(chatInput.slice(1).toLowerCase().split(" ")[0]);
    } else {
      setShowCommands(false);
    }
  }, [chatInput]);

  const filteredCommands = useMemo(() => {
    if (!commandFilter) return CHAT_COMMANDS;
    return CHAT_COMMANDS.filter(c => c.id.includes(commandFilter) || c.desc.toLowerCase().includes(commandFilter));
  }, [commandFilter]);

  return (
    <div className="rounded-[20px] bg-[#111116] border border-zinc-900 flex flex-col h-[84vh] overflow-hidden shadow-[0_0_0_1px_rgba(0,0,0,0.1),0_4px_24px_rgba(0,0,0,0.4)]">
      <ChatHeader
        chatMode={chatMode} setChatMode={setChatMode}
        selectedModelId={selectedModelId} distinctModels={distinctModels}
        streamEnabled={streamEnabled} setStreamEnabled={setStreamEnabled}
        workplaceOpen={workplaceOpen} setWorkplaceOpen={setWorkplaceOpen}
        projectsCount={projectsCount}
      />
      {chatMode === "manual" && (
        <ChatModelSelect selectedModelId={selectedModelId} setSelectedModelId={setSelectedModelId} distinctModels={distinctModels} />
      )}
      <ChatMessages messages={chatMessages} loading={chatLoading} streamEnabled={streamEnabled} onSave={onSave} onCreateFromTemplate={onCreateFromTemplate} chatEndRef={chatEndRef} />
      {showCommands && filteredCommands.length > 0 && (
        <CommandsPalette filter={commandFilter} commands={filteredCommands} onSelect={(cmd: string) => { setChatInput(cmd); setShowCommands(false); }} />
      )}
      <ChatInput
        chatInput={chatInput} setChatInput={setChatInput}
        onSend={onSend} chatLoading={chatLoading}
        chatMode={chatMode} selectedModelId={selectedModelId}
        distinctModels={distinctModels}
        projects={projects}
        chatInputRef={chatInputRef}
      />
    </div>
  );
}
