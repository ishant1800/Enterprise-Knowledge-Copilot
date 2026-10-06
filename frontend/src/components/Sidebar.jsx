import React from "react";
import { 
  MessageSquare, 
  Files, 
  Search, 
  Award, 
  Plus, 
  Trash2, 
  Database, 
  Cpu, 
  CheckCircle2, 
  AlertCircle 
} from "lucide-react";

export default function Sidebar({
  activeTab,
  setActiveTab,
  conversations,
  currentConvId,
  onSelectConversation,
  onNewChat,
  onDeleteConversation,
  systemHealth,
  docCount,
}) {
  return (
    <aside className="w-72 bg-slate-900 border-r border-slate-800 flex flex-col h-screen select-none">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-800/80">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-400 flex items-center justify-center shadow-lg shadow-brand-500/20">
            <Cpu className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-tight text-white flex items-center gap-1.5">
              Knowledge Copilot
              <span className="text-[10px] uppercase font-semibold tracking-wider px-1.5 py-0.5 rounded bg-brand-500/20 text-brand-300 border border-brand-500/30">
                MVP
              </span>
            </h1>
            <p className="text-xs text-slate-400">Enterprise RAG Engine</p>
          </div>
        </div>
      </div>

      {/* Primary Navigation Tabs */}
      <div className="p-3 space-y-1">
        <button
          onClick={() => setActiveTab("chat")}
          className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
            activeTab === "chat"
              ? "bg-brand-600/20 text-brand-300 border border-brand-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
          }`}
        >
          <div className="flex items-center space-x-2.5">
            <MessageSquare className="w-4 h-4" />
            <span>Copilot Chat</span>
          </div>
        </button>

        <button
          onClick={() => setActiveTab("documents")}
          className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
            activeTab === "documents"
              ? "bg-brand-600/20 text-brand-300 border border-brand-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
          }`}
        >
          <div className="flex items-center space-x-2.5">
            <Files className="w-4 h-4" />
            <span>Document Library</span>
          </div>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
            {docCount}
          </span>
        </button>

        <button
          onClick={() => setActiveTab("retrieval")}
          className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
            activeTab === "retrieval"
              ? "bg-brand-600/20 text-brand-300 border border-brand-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
          }`}
        >
          <div className="flex items-center space-x-2.5">
            <Search className="w-4 h-4" />
            <span>Retrieval Sandbox</span>
          </div>
        </button>

        <button
          onClick={() => setActiveTab("eval")}
          className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
            activeTab === "eval"
              ? "bg-brand-600/20 text-brand-300 border border-brand-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
          }`}
        >
          <div className="flex items-center space-x-2.5">
            <Award className="w-4 h-4" />
            <span>Evaluation Suite</span>
          </div>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
            Benchmark
          </span>
        </button>
      </div>

      {/* Conversations Section (when Chat tab is active) */}
      <div className="flex-1 flex flex-col min-h-0 border-t border-slate-800/70 pt-3 px-3">
        <div className="flex items-center justify-between px-2 mb-2">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Conversations
          </span>
          <button
            onClick={onNewChat}
            className="flex items-center gap-1 text-xs text-brand-400 hover:text-brand-300 font-medium px-2 py-1 rounded hover:bg-brand-500/10 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            New
          </button>
        </div>

        <div className="flex-1 overflow-y-auto space-y-1 pr-1">
          {conversations.length === 0 ? (
            <div className="text-center py-6 px-3 text-xs text-slate-500">
              No previous chats yet. Start a conversation!
            </div>
          ) : (
            conversations.map((c) => (
              <div
                key={c.id}
                onClick={() => onSelectConversation(c.id)}
                className={`group flex items-center justify-between px-2.5 py-2 rounded-md text-xs cursor-pointer transition-all ${
                  currentConvId === c.id
                    ? "bg-slate-800 text-white font-medium shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
              >
                <div className="flex items-center space-x-2 truncate pr-2">
                  <MessageSquare className="w-3.5 h-3.5 shrink-0 opacity-70" />
                  <span className="truncate">{c.title || "Untitled Conversation"}</span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteConversation(c.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 hover:text-rose-400 p-1 rounded transition-opacity"
                  title="Delete chat"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* System Status Footer */}
      <div className="p-3 border-t border-slate-800 bg-slate-950/60">
        <div className="bg-slate-900/90 rounded-lg p-2.5 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center space-x-1.5 text-slate-400">
              <Database className="w-3.5 h-3.5 text-brand-400" />
              <span>ChromaDB Vectors:</span>
            </div>
            <span className="font-mono text-slate-200 font-semibold">
              {systemHealth?.vector_store?.total_vectors ?? 0}
            </span>
          </div>

          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center space-x-1.5 text-slate-400">
              <Cpu className="w-3.5 h-3.5 text-emerald-400" />
              <span>LLM Pipeline:</span>
            </div>
            <div className="flex items-center space-x-1">
              {systemHealth?.openai?.configured ? (
                <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20 flex items-center gap-1">
                  <CheckCircle2 className="w-2.5 h-2.5" /> OpenAI Live
                </span>
              ) : (
                <span className="text-[10px] text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20 flex items-center gap-1" title="Offline deterministic grounding active">
                  <AlertCircle className="w-2.5 h-2.5" /> Local Fallback
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
