import React, { useState } from "react";
import { 
  UploadCloud, 
  FileText, 
  Trash2, 
  Eye, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  Database,
  Sliders,
  X,
  Sparkles
} from "lucide-react";
import { fetchDocumentDetails } from "../../services/api";

export default function DocumentLibrary({
  documents,
  loading,
  onUploadDocument,
  onDeleteDocument,
  onSeedSamples,
}) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [chunkSize, setChunkSize] = useState(800);
  const [chunkOverlap, setChunkOverlap] = useState(150);
  const [uploading, setUploading] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  // Chunk Modal state
  const [inspectDoc, setInspectDoc] = useState(null);
  const [loadingChunks, setLoadingChunks] = useState(false);
  const [pageFilter, setPageFilter] = useState("all");

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setUploadError(null);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploading(true);
    setUploadError(null);
    try {
      await onUploadDocument(selectedFile, chunkSize, chunkOverlap);
      setSelectedFile(null);
      // Reset file input
      const input = document.getElementById("file-upload-input");
      if (input) input.value = "";
    } catch (err) {
      setUploadError(err.message || "Failed to upload document");
    } finally {
      setUploading(false);
    }
  };

  const handleSeed = async () => {
    setSeeding(true);
    try {
      await onSeedSamples();
    } catch (err) {
      alert("Error seeding samples: " + err.message);
    } finally {
      setSeeding(false);
    }
  };

  const openInspector = async (doc) => {
    setLoadingChunks(true);
    try {
      const details = await fetchDocumentDetails(doc.id);
      setInspectDoc(details);
      setPageFilter("all");
    } catch (err) {
      alert("Could not load chunk details: " + err.message);
    } finally {
      setLoadingChunks(false);
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  // Filter chunks for modal
  const filteredChunks = inspectDoc?.chunks?.filter((c) => {
    if (pageFilter === "all") return true;
    return c.page_number === Number(pageFilter);
  }) || [];

  const uniquePages = Array.from(new Set(inspectDoc?.chunks?.map((c) => c.page_number) || [])).sort((a, b) => a - b);

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-950 overflow-y-auto p-6 md:p-8 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">
            Document Ingestion & Knowledge Library
          </h2>
          <p className="text-sm text-slate-400">
            Upload enterprise PDFs, policies, and manuals. Documents are automatically chunked, embedded, and indexed into ChromaDB.
          </p>
        </div>

        <button
          onClick={handleSeed}
          disabled={seeding}
          className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-850 border border-brand-500/30 text-brand-300 hover:text-brand-200 text-xs font-semibold shadow-sm transition-all self-start md:self-auto"
        >
          {seeding ? (
            <Loader2 className="w-4 h-4 animate-spin text-brand-400" />
          ) : (
            <Sparkles className="w-4 h-4 text-brand-400" />
          )}
          <span>{seeding ? "Indexing Samples..." : "Seed Enterprise Sample Docs"}</span>
        </button>
      </div>

      {/* Upload Box */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-5">
        <h3 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center gap-2">
          <UploadCloud className="w-4 h-4 text-brand-400" />
          Ingest New Document
        </h3>

        <form onSubmit={handleUpload} className="space-y-4">
          <div className="border-2 border-dashed border-slate-800 hover:border-brand-500/50 rounded-xl p-6 text-center transition-colors bg-slate-900/40">
            <input
              id="file-upload-input"
              type="file"
              accept=".pdf,.txt,.md"
              onChange={handleFileChange}
              className="hidden"
            />
            <label
              htmlFor="file-upload-input"
              className="cursor-pointer flex flex-col items-center space-y-2"
            >
              <FileText className="w-8 h-8 text-slate-400" />
              <div className="text-xs">
                {selectedFile ? (
                  <span className="font-semibold text-brand-300">
                    {selectedFile.name} ({formatBytes(selectedFile.size)})
                  </span>
                ) : (
                  <>
                    <span className="font-semibold text-slate-200">
                      Click to choose a file
                    </span>{" "}
                    <span className="text-slate-500">or drag & drop</span>
                  </>
                )}
              </div>
              <p className="text-[11px] text-slate-500">
                Supported formats: PDF, TXT, MD (Max 25MB)
              </p>
            </label>
          </div>

          {/* Chunking Parameters */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-900/60 p-4 rounded-xl border border-slate-800/80">
            <div>
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="text-slate-400">Chunk Size:</span>
                <span className="font-mono text-brand-300">{chunkSize} chars</span>
              </div>
              <input
                type="range"
                min="300"
                max="2000"
                step="50"
                value={chunkSize}
                onChange={(e) => setChunkSize(Number(e.target.value))}
                className="w-full accent-brand-500"
              />
              <span className="text-[10px] text-slate-500">
                Target characters per chunk snippet
              </span>
            </div>

            <div>
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="text-slate-400">Chunk Overlap:</span>
                <span className="font-mono text-brand-300">{chunkOverlap} chars</span>
              </div>
              <input
                type="range"
                min="0"
                max="400"
                step="25"
                value={chunkOverlap}
                onChange={(e) => setChunkOverlap(Number(e.target.value))}
                className="w-full accent-brand-500"
              />
              <span className="text-[10px] text-slate-500">
                Overlap window to prevent fragmenting context across cuts
              </span>
            </div>
          </div>

          {uploadError && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{uploadError}</span>
            </div>
          )}

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={!selectedFile || uploading}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-semibold shadow-md shadow-brand-500/20 transition-all"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Processing & Indexing...</span>
                </>
              ) : (
                <>
                  <UploadCloud className="w-4 h-4" />
                  <span>Ingest & Vectorize Document</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Document Library Table */}
      <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden shadow-lg">
        <div className="p-4 px-6 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center gap-2">
            <Database className="w-4 h-4 text-emerald-400" />
            Ingested Documents ({documents.length})
          </h3>
          <span className="text-xs text-slate-500">
            Total active knowledge base in ChromaDB
          </span>
        </div>

        <div className="overflow-x-auto">
          {documents.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-xs">
              No documents in the knowledge base. Click "Seed Enterprise Sample Docs" or upload a file above.
            </div>
          ) : (
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 font-medium border-b border-slate-800">
                <tr>
                  <th className="py-3 px-6">Document Name</th>
                  <th className="py-3 px-4">Size</th>
                  <th className="py-3 px-4">Pages</th>
                  <th className="py-3 px-4">Chunks</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Uploaded</th>
                  <th className="py-3 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {documents.map((doc) => (
                  <tr
                    key={doc.id}
                    className="hover:bg-slate-900/40 transition-colors"
                  >
                    <td className="py-3.5 px-6 font-medium text-slate-200 flex items-center space-x-2">
                      <FileText className="w-4 h-4 text-brand-400 shrink-0" />
                      <span className="truncate max-w-xs">{doc.filename}</span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 font-mono">
                      {formatBytes(doc.file_size)}
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">
                      {doc.total_pages}
                    </td>
                    <td className="py-3.5 px-4 text-slate-300 font-mono">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-brand-300 border border-slate-700">
                        {doc.chunk_count}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      {doc.status === "indexed" ? (
                        <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                          <CheckCircle2 className="w-3 h-3" /> Indexed
                        </span>
                      ) : doc.status === "processing" ? (
                        <span className="inline-flex items-center gap-1 text-[11px] text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded-full border border-blue-500/20">
                          <Loader2 className="w-3 h-3 animate-spin" /> Processing
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded-full border border-rose-500/20">
                          <AlertCircle className="w-3 h-3" /> Error
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-slate-500 text-[11px]">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-6 text-right space-x-2">
                      <button
                        onClick={() => openInspector(doc)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-brand-300 hover:bg-slate-800 transition-colors"
                        title="Inspect Chunks"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => {
                          if (confirm(`Delete document '${doc.filename}' and all its vector embeddings?`)) {
                            onDeleteDocument(doc.id);
                          }
                        }}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
                        title="Delete Document"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Chunk Inspector Modal */}
      {inspectDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <FileText className="w-4 h-4 text-brand-400" />
                  Chunk Inspector: {inspectDoc.filename}
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  {inspectDoc.chunk_count} Chunks • {inspectDoc.total_pages} Pages • ChromaDB Collection
                </p>
              </div>

              <div className="flex items-center space-x-3">
                {/* Page Filter */}
                <select
                  value={pageFilter}
                  onChange={(e) => setPageFilter(e.target.value)}
                  className="bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-brand-500"
                >
                  <option value="all">All Pages ({inspectDoc.chunks.length} chunks)</option>
                  {uniquePages.map((pg) => (
                    <option key={pg} value={pg}>
                      Page {pg}
                    </option>
                  ))}
                </select>

                <button
                  onClick={() => setInspectDoc(null)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-5 space-y-3">
              {filteredChunks.map((chunk) => (
                <div
                  key={chunk.id}
                  className="bg-slate-950/80 border border-slate-800/80 rounded-xl p-4 text-xs space-y-2 hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center justify-between text-slate-400 pb-2 border-b border-slate-850">
                    <span className="font-semibold text-slate-300">
                      Chunk #{chunk.chunk_index}
                    </span>
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-0.5 rounded bg-brand-500/15 text-brand-300 font-mono">
                        Page {chunk.page_number}
                      </span>
                      <span className="text-slate-500 font-mono">
                        ~{chunk.token_estimate} tokens
                      </span>
                    </div>
                  </div>
                  <p className="text-slate-300 font-mono text-[11px] whitespace-pre-wrap leading-relaxed">
                    {chunk.content}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
