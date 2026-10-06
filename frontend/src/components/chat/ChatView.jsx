import React, { useState, useRef, useEffect } from "react";
import { 
  Send, 
  Sparkles, 
  ShieldCheck, 
  AlertTriangle, 
  Sliders, 
  FileText, 
  ChevronDown, 
  ChevronUp, 
  ExternalLink,
  Layers,
  Clock,
  RotateCcw
} from "lucide-react";

const SUGGESTED_QUESTIONS = [
  "What is the password rotation policy and minimum length requirement?",
  "What are the procedures for rolling back a failed production deployment?",
  "What is the monthly high-speed internet stipend and reimbursement limit?",
  "What are the four data classification levels?",
  "Can employees upload confidential data into public AI services?",
  "What is the employee stock purchase plan discount percentage?"
];

export default function ChatView({
  conversation,
  messages,
  loading,
  onSendMessage,
  documents,
}) {
  const [inputText, setInputText] = useState("");
  const [showControls, setShowControls] = useState(false);
  const [topK, setTopK] = useState(5);
  const [similarityThreshold, setSimilarityThreshold] = useState(0.20);
  const [enableReranking, setEnableReranking] = useState(true);
  const [selectedDocFilter, setSelectedDocFilter] = useState("");
  const [expandedQuotes, setExpandedQuotes] = useState({});
  const [expandedChunks, setExpandedChunks] = useState({});

  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!inputText.trim() || loading) return;

    onSendMessage({
      message: inputText.trim(),
      topK,
      similarityThreshold,
      enableReranking,
      documentIdFilter: selectedDocFilter || null,
    });
    setInputText("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const toggleQuote = (msgId, index) => {
    const key = `${msgId}_${index}`;
    setExpandedQuotes((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-950 overflow-hidden">
      {/* Top Header Bar */}
      <header className="h-16 px-6 border-b border-slate-800 flex items-center justify-between glass-panel z-10">
        <div>
          <h2 className="text-sm font-semibold text-white truncate max-w-md">
            {conversation?.title || "Enterprise Knowledge Copilot"}
          </h2>
          <p className="text-xs text-slate-400">
            Strictly Grounded RAG with Inline Provenance
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowControls(!showControls)}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
              showControls
                ? "bg-brand-600/20 text-brand-300 border-brand-500/40"
                : "bg-slate-900 text-slate-300 border-slate-800 hover:bg-slate-800"
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>RAG Controls</span>
          </button>
        </div>
      </header>

      {/* RAG Controls Drawer */}
      {showControls && (
        <div className="bg-slate-900/95 border-b border-slate-800 p-4 px-6 grid grid-cols-1 md:grid-cols-4 gap-4 text-xs animate-slide-up">
          <div>
            <label className="text-slate-400 font-medium block mb-1">
              Top-K Chunks ({topK})
            </label>
            <input
              type="range"
              min="1"
              max="12"
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="w-full accent-brand-500 cursor-pointer"
            />
          </div>

          <div>
            <label className="text-slate-400 font-medium block mb-1">
              Similarity Threshold ({similarityThreshold.toFixed(2)})
            </label>
            <input
              type="range"
              min="0.0"
              max="0.8"
              step="0.05"
              value={similarityThreshold}
              onChange={(e) => setSimilarityThreshold(Number(e.target.value))}
              className="w-full accent-brand-500 cursor-pointer"
            />
          </div>

          <div className="flex flex-col justify-center">
            <label className="text-slate-400 font-medium block mb-1">
              Hybrid Reranker
            </label>
            <label className="flex items-center space-x-2 cursor-pointer mt-1">
              <input
                type="checkbox"
                checked={enableReranking}
                onChange={(e) => setEnableReranking(e.target.checked)}
                className="rounded accent-brand-500"
              />
              <span className="text-slate-300">Lexical + Semantic Rerank</span>
            </label>
          </div>

          <div>
            <label className="text-slate-400 font-medium block mb-1">
              Document Scope Filter
            </label>
            <select
              value={selectedDocFilter}
              onChange={(e) => setSelectedDocFilter(e.target.value)}
              className="w-full bg-slate-850 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs focus:outline-none focus:border-brand-500"
            >
              <option value="">All Uploaded Documents</option>
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.filename}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* Message Stream */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="max-w-2xl mx-auto py-12 text-center animate-fade-in">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-brand-600 to-indigo-500 mx-auto flex items-center justify-center shadow-xl shadow-brand-500/20 mb-4">
              <Sparkles className="w-7 h-7 text-white" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">
              Enterprise Knowledge Copilot
            </h3>
            <p className="text-sm text-slate-400 max-w-md mx-auto mb-8">
              Ask natural-language questions about internal SOPs, security guidelines, and policies. Answers are strictly grounded in retrieved documents with verified page citations.
            </p>

            <div className="text-left">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-3">
                Suggested Prompts
              </span>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                {SUGGESTED_QUESTIONS.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setInputText(q);
                    }}
                    className="p-3 text-left rounded-xl bg-slate-900 hover:bg-slate-850 border border-slate-800 hover:border-slate-700 text-xs text-slate-300 hover:text-white transition-all shadow-sm"
                  >
                    "{q}"
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((m) => (
            <div
              key={m.id}
              className={`flex flex-col ${
                m.role === "user" ? "items-end" : "items-start"
              }`}
            >
              {m.role === "user" ? (
                /* User Bubble */
                <div className="max-w-2xl bg-brand-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-md text-sm leading-relaxed">
                  {m.content}
                </div>
              ) : (
                /* Assistant Bubble */
                <div className="max-w-3xl w-full bg-slate-900 border border-slate-800/90 rounded-2xl rounded-tl-sm p-5 shadow-lg space-y-4">
                  {/* Grounding & Confidence Meta Header */}
                  <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-800">
                    <div className="flex items-center space-x-2">
                      {m.is_grounded ? (
                        <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
                          <ShieldCheck className="w-3.5 h-3.5" />
                          Directly Supported by Sources
                        </span>
                      ) : (
                        <span className="flex items-center gap-1.5 text-xs font-medium text-amber-400 bg-amber-500/10 px-2.5 py-1 rounded-full border border-amber-500/20">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          Insufficient Context Refusal
                        </span>
                      )}

                      <span className="text-[11px] text-slate-400 px-2 py-0.5 rounded bg-slate-800 border border-slate-700/60 uppercase tracking-wide">
                        Confidence: {m.confidence}
                      </span>
                    </div>

                    <span className="text-[11px] text-slate-500">
                      {new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>

                  {/* Main Answer Content */}
                  <div className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap font-sans">
                    {m.content}
                  </div>

                  {/* Source / Citation Cards */}
                  {m.citations && m.citations.length > 0 && (
                    <div className="pt-2">
                      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                        Source Citations ({m.citations.length})
                      </span>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {m.citations.map((c, idx) => {
                          const quoteKey = `${m.id}_${idx}`;
                          const isExpanded = expandedQuotes[quoteKey];

                          return (
                            <div
                              key={idx}
                              className="bg-slate-950/70 border border-slate-800 rounded-lg p-2.5 text-xs space-y-1.5 transition-all hover:border-slate-700"
                            >
                              <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-1.5 font-medium text-slate-200 truncate pr-2">
                                  <FileText className="w-3.5 h-3.5 text-brand-400 shrink-0" />
                                  <span className="truncate">{c.document_name}</span>
                                </div>
                                <span className="text-[11px] px-1.5 py-0.5 rounded bg-brand-500/15 text-brand-300 font-mono shrink-0">
                                  Page {c.page_number}
                                </span>
                              </div>

                              {c.quote && (
                                <div>
                                  <button
                                    onClick={() => toggleQuote(m.id, idx)}
                                    className="flex items-center space-x-1 text-[11px] text-slate-400 hover:text-slate-200 transition-colors"
                                  >
                                    <span>{isExpanded ? "Hide excerpt" : "View source excerpt"}</span>
                                    {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                                  </button>
                                  {isExpanded && (
                                    <p className="mt-1.5 p-2 rounded bg-slate-900 border border-slate-800 text-[11px] text-slate-300 italic">
                                      "{c.quote}"
                                    </p>
                                  )}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}

        {/* Loading Indicator */}
        {loading && (
          <div className="flex items-start max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-4 space-x-3 shadow-lg animate-pulse-subtle">
            <div className="w-6 h-6 rounded-full bg-brand-500/20 border border-brand-500/30 flex items-center justify-center shrink-0">
              <Sparkles className="w-3.5 h-3.5 text-brand-400 animate-spin" />
            </div>
            <div className="space-y-1">
              <p className="text-xs font-medium text-slate-300">
                Searching vector index & synthesizing grounded answer...
              </p>
              <p className="text-[11px] text-slate-500">
                Evaluating candidate chunks and verifying citation provenance
              </p>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="p-4 px-6 border-t border-slate-800 glass-panel">
        <form onSubmit={handleSubmit} className="relative flex items-center">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about policies, SOPs, or documentation... (Press Enter to send)"
            rows={2}
            className="w-full bg-slate-900/90 text-sm text-slate-100 placeholder-slate-500 rounded-xl pl-4 pr-14 py-3 border border-slate-800 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-all resize-none shadow-inner"
          />

          <button
            type="submit"
            disabled={!inputText.trim() || loading}
            className="absolute right-3.5 bottom-3.5 p-2 rounded-lg bg-brand-600 hover:bg-brand-500 disabled:opacity-40 disabled:hover:bg-brand-600 text-white transition-all shadow-md shadow-brand-500/20"
            title="Send Message"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
        <div className="flex items-center justify-between text-[11px] text-slate-500 mt-2 px-1">
          <span>Enterprise Knowledge Copilot • Strict Anti-Hallucination Active</span>
          <span>Shift + Enter for new line</span>
        </div>
      </div>
    </div>
  );
}
