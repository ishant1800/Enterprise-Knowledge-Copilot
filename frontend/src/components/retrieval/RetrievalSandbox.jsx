import React, { useState } from "react";
import { 
  Search, 
  Sliders, 
  Layers, 
  FileText, 
  Clock, 
  CheckCircle2, 
  Loader2,
  Sparkles
} from "lucide-react";
import { testRetrieval } from "../../services/api";

export default function RetrievalSandbox({ documents }) {
  const [query, setQuery] = useState("What is the password rotation policy?");
  const [topK, setTopK] = useState(6);
  const [similarityThreshold, setSimilarityThreshold] = useState(0.20);
  const [enableReranking, setEnableReranking] = useState(true);
  const [docFilter, setDocFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    e?.preventDefault();
    if (!query.trim() || loading) return;

    setLoading(true);
    setError(null);
    try {
      const data = await testRetrieval({
        query: query.trim(),
        topK,
        similarityThreshold,
        enableReranking,
        documentIdFilter: docFilter || null,
      });
      setResults(data);
    } catch (err) {
      setError(err.message || "Retrieval test failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-950 overflow-y-auto p-6 md:p-8 space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <Search className="w-5 h-5 text-brand-400" />
          Retrieval & Reranking Sandbox
        </h2>
        <p className="text-sm text-slate-400">
          Inspect raw semantic vector search results, similarity scores, and hybrid reranking decisions in real-time.
        </p>
      </div>

      {/* Control Panel */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-5">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="flex flex-col md:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter a test query for vector similarity search..."
                className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 shadow-inner"
              />
            </div>
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="flex items-center justify-center space-x-2 px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-semibold shadow-md shadow-brand-500/20 transition-all shrink-0"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              <span>Test Retrieval</span>
            </button>
          </div>

          {/* Hyperparameters */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 bg-slate-900/60 p-4 rounded-xl border border-slate-800/80 text-xs">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-slate-400">Top-K Candidates:</span>
                <span className="font-mono text-brand-300">{topK}</span>
              </div>
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
              <div className="flex justify-between mb-1">
                <span className="text-slate-400">Similarity Threshold:</span>
                <span className="font-mono text-brand-300">{similarityThreshold.toFixed(2)}</span>
              </div>
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
              <span className="text-slate-400 mb-1">Reranking Mode:</span>
              <label className="flex items-center space-x-2 cursor-pointer mt-1">
                <input
                  type="checkbox"
                  checked={enableReranking}
                  onChange={(e) => setEnableReranking(e.target.checked)}
                  className="rounded accent-brand-500"
                />
                <span className="text-slate-300">Hybrid Reranker (Lexical + Dense)</span>
              </label>
            </div>

            <div>
              <span className="text-slate-400 block mb-1">Document Scope:</span>
              <select
                value={docFilter}
                onChange={(e) => setDocFilter(e.target.value)}
                className="w-full bg-slate-850 border border-slate-700 rounded px-2.5 py-1 text-slate-200 text-xs focus:outline-none focus:border-brand-500"
              >
                <option value="">All Documents</option>
                {documents.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.filename}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </form>

        {error && (
          <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
            {error}
          </div>
        )}
      </div>

      {/* Results View */}
      {results && (
        <div className="space-y-4">
          <div className="flex items-center justify-between px-2">
            <div className="flex items-center space-x-3 text-xs text-slate-400">
              <span className="font-semibold text-slate-200">
                Matched Chunks: {results.total_found}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1 font-mono text-slate-300">
                <Clock className="w-3.5 h-3.5 text-brand-400" />
                {results.execution_time_ms} ms
              </span>
            </div>
          </div>

          {results.chunks.length === 0 ? (
            <div className="glass-panel p-8 rounded-2xl text-center text-xs text-slate-400 space-y-2">
              <p className="font-medium text-slate-300">No chunks met the similarity threshold ({similarityThreshold}).</p>
              <p className="text-slate-500">
                This demonstrates active hallucination prevention: the system refuses to send irrelevant context to the LLM.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3">
              {results.chunks.map((c, idx) => (
                <div
                  key={c.chunk_id}
                  className="glass-panel rounded-xl p-4 border border-slate-800 space-y-2.5 hover:border-slate-700 transition-colors"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-slate-850 text-xs">
                    <div className="flex items-center space-x-2">
                      <span className="w-5 h-5 rounded-full bg-brand-500/20 text-brand-300 flex items-center justify-center font-bold text-[10px]">
                        #{idx + 1}
                      </span>
                      <span className="font-semibold text-slate-200 flex items-center gap-1">
                        <FileText className="w-3.5 h-3.5 text-brand-400" />
                        {c.filename}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[11px]">
                        Page {c.page_number}
                      </span>
                      <span className="px-2 py-0.5 rounded bg-brand-500/15 text-brand-300 font-mono text-[11px] font-semibold">
                        Relevance: {(c.score * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  {/* Score meter bar */}
                  <div className="w-full bg-slate-850 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-brand-500 to-emerald-400 h-full rounded-full transition-all"
                      style={{ width: `${Math.min(100, Math.max(0, c.score * 100))}%` }}
                    />
                  </div>

                  <p className="text-xs text-slate-300 font-mono bg-slate-950/60 p-3 rounded-lg border border-slate-900 leading-relaxed whitespace-pre-wrap">
                    {c.content}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
