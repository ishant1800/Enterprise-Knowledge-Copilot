import React, { useState, useEffect } from "react";
import { 
  Award, 
  Play, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  ShieldAlert, 
  ShieldCheck, 
  FileText, 
  Loader2, 
  BarChart3,
  ChevronDown,
  ChevronUp
} from "lucide-react";
import { runEvaluation, fetchEvaluationHistory } from "../../services/api";

export default function EvaluationDashboard() {
  const [evalData, setEvalData] = useState(null);
  const [history, setHistory] = useState([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);
  const [expandedRow, setExpandedRow] = useState(null);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const data = await fetchEvaluationHistory();
      setHistory(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleRunBenchmark = async () => {
    setRunning(true);
    setError(null);
    try {
      const res = await runEvaluation();
      setEvalData(res);
      await loadHistory();
    } catch (err) {
      setError(err.message || "Benchmark execution failed");
    } finally {
      setRunning(false);
    }
  };

  const metrics = evalData?.metrics;

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-950 overflow-y-auto p-6 md:p-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Award className="w-5 h-5 text-amber-400" />
            RAG Evaluation & Quality Benchmark
          </h2>
          <p className="text-sm text-slate-400">
            Systematic validation of retrieval relevance, factual grounding, citation presence, and hallucination refusal accuracy.
          </p>
        </div>

        <button
          onClick={handleRunBenchmark}
          disabled={running}
          className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 disabled:opacity-50 text-white text-xs font-semibold shadow-lg shadow-brand-500/20 transition-all self-start md:self-auto"
        >
          {running ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Play className="w-4 h-4 fill-white" />
          )}
          <span>{running ? "Evaluating Pipeline..." : "Run Evaluation Benchmark"}</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
          {error}
        </div>
      )}

      {/* Metric KPI Cards */}
      {metrics ? (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {/* Card 1 */}
          <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-2">
            <span className="text-xs text-slate-400 font-medium">Retrieval Hit Rate</span>
            <div className="flex items-baseline justify-between">
              <span className="text-2xl font-bold text-white font-mono">
                {metrics.retrieval_hit_rate_pct}%
              </span>
              <span className="text-[11px] text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">
                Target &gt; 80%
              </span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-emerald-500 h-full rounded-full"
                style={{ width: `${metrics.retrieval_hit_rate_pct}%` }}
              />
            </div>
          </div>

          {/* Card 2 */}
          <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-2">
            <span className="text-xs text-slate-400 font-medium">Groundedness Score</span>
            <div className="flex items-baseline justify-between">
              <span className="text-2xl font-bold text-white font-mono">
                {metrics.groundedness_avg_pct}%
              </span>
              <span className="text-[11px] text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">
                Faithful
              </span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-brand-500 h-full rounded-full"
                style={{ width: `${metrics.groundedness_avg_pct}%` }}
              />
            </div>
          </div>

          {/* Card 3 */}
          <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-2">
            <span className="text-xs text-slate-400 font-medium">Citation Coverage</span>
            <div className="flex items-baseline justify-between">
              <span className="text-2xl font-bold text-white font-mono">
                {metrics.citation_coverage_pct}%
              </span>
              <span className="text-[11px] text-brand-300 bg-brand-500/10 px-1.5 py-0.5 rounded">
                Provenance
              </span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-indigo-500 h-full rounded-full"
                style={{ width: `${metrics.citation_coverage_pct}%` }}
              />
            </div>
          </div>

          {/* Card 4: Anti-hallucination Refusal */}
          <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-2">
            <span className="text-xs text-slate-400 font-medium">Anti-Hallucination Rate</span>
            <div className="flex items-baseline justify-between">
              <span className="text-2xl font-bold text-white font-mono">
                {metrics.refusal_accuracy_pct}%
              </span>
              <span className="text-[11px] text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded">
                Refusal Check
              </span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-amber-500 h-full rounded-full"
                style={{ width: `${metrics.refusal_accuracy_pct}%` }}
              />
            </div>
          </div>

          {/* Card 5: Latency */}
          <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-2">
            <span className="text-xs text-slate-400 font-medium">Avg Latency</span>
            <div className="flex items-baseline justify-between">
              <span className="text-2xl font-bold text-white font-mono">
                {metrics.avg_latency_ms} <span className="text-xs font-normal text-slate-400">ms</span>
              </span>
              <span className="text-[11px] text-slate-400">
                P95 ~12ms
              </span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div className="bg-sky-400 h-full rounded-full w-4/5" />
            </div>
          </div>
        </div>
      ) : (
        <div className="glass-panel p-8 rounded-2xl text-center space-y-3">
          <BarChart3 className="w-10 h-10 text-brand-400 mx-auto opacity-70" />
          <h4 className="text-base font-semibold text-white">
            No Active Benchmark Run Yet
          </h4>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Click "Run Evaluation Benchmark" above to test the RAG pipeline against standard test cases (policy queries, SOP queries, and out-of-scope hallucination probes).
          </p>
        </div>
      )}

      {/* Benchmark Results Table */}
      {evalData && (
        <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden shadow-lg space-y-0">
          <div className="p-4 px-6 border-b border-slate-800 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider">
              Test Case Execution Breakdown ({evalData.results.length})
            </h3>
            <span className="text-xs text-slate-400">
              Passed: {metrics.passed_count} / {metrics.total_questions}
            </span>
          </div>

          <div className="divide-y divide-slate-800/80">
            {evalData.results.map((r, idx) => {
              const isExpanded = expandedRow === r.id;
              return (
                <div key={r.id} className="p-4 px-6 hover:bg-slate-900/40 transition-colors">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
                    <div className="flex items-start space-x-3">
                      <span className="font-mono text-slate-500 font-semibold shrink-0 mt-0.5">
                        {r.id}
                      </span>
                      <div>
                        <p className="font-medium text-slate-200">{r.question}</p>
                        <div className="flex flex-wrap items-center gap-2 mt-1 text-[11px] text-slate-400">
                          <span>
                            Target: <strong className="text-slate-300">{r.expected_document || "None (Hallucination Probe)"}</strong>
                          </span>
                          <span>•</span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3 text-slate-500" /> {r.latency_ms}ms
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-3 shrink-0">
                      {r.passed ? (
                        <span className="flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          <CheckCircle2 className="w-3.5 h-3.5" /> PASSED
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                          <XCircle className="w-3.5 h-3.5" /> FAILED
                        </span>
                      )}

                      <button
                        onClick={() => setExpandedRow(isExpanded ? null : r.id)}
                        className="p-1 text-slate-400 hover:text-white rounded"
                      >
                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="mt-3 pt-3 border-t border-slate-850 space-y-2 text-xs animate-slide-up">
                      <div className="bg-slate-950/80 p-3 rounded-lg border border-slate-800">
                        <span className="text-slate-400 text-[11px] uppercase font-semibold block mb-1">
                          Generated Answer Output:
                        </span>
                        <p className="text-slate-300 whitespace-pre-wrap">{r.answer}</p>
                      </div>

                      <div className="flex flex-wrap gap-4 text-[11px] text-slate-400">
                        <span>
                          Retrieved Docs:{" "}
                          <strong className="text-slate-300">
                            {r.retrieved_documents.join(", ") || "None above threshold"}
                          </strong>
                        </span>
                        <span>
                          Grounding Score:{" "}
                          <strong className="text-brand-300">{(r.groundedness_score * 100).toFixed(0)}%</strong>
                        </span>
                        <span>
                          Citation Present:{" "}
                          <strong className="text-slate-300">{r.citation_present ? "Yes" : "No"}</strong>
                        </span>
                        {r.notes && (
                          <span className="text-amber-400 font-semibold">{r.notes}</span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
