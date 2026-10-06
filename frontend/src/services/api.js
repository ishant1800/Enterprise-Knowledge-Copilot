const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}

export async function fetchDocuments() {
  const res = await fetch(`${API_BASE}/documents`);
  if (!res.ok) throw new Error("Failed to load documents");
  return res.json();
}

export async function fetchDocumentDetails(documentId) {
  const res = await fetch(`${API_BASE}/documents/${documentId}`);
  if (!res.ok) throw new Error("Failed to fetch document details");
  return res.json();
}

export async function uploadDocument(file, chunkSize = 800, chunkOverlap = 150) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("chunk_size", chunkSize);
  formData.append("chunk_overlap", chunkOverlap);

  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Failed to upload document");
  }
  return res.json();
}

export async function deleteDocument(documentId) {
  const res = await fetch(`${API_BASE}/documents/${documentId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete document");
  return res.json();
}

export async function seedSampleDocuments() {
  const res = await fetch(`${API_BASE}/documents/seed-samples`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to seed sample documents");
  return res.json();
}

export async function listConversations() {
  const res = await fetch(`${API_BASE}/chat/conversations`);
  if (!res.ok) throw new Error("Failed to fetch conversations");
  return res.json();
}

export async function getConversation(conversationId) {
  const res = await fetch(`${API_BASE}/chat/conversations/${conversationId}`);
  if (!res.ok) throw new Error("Failed to load conversation");
  return res.json();
}

export async function deleteConversation(conversationId) {
  const res = await fetch(`${API_BASE}/chat/conversations/${conversationId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete conversation");
  return res.json();
}

export async function sendChatMessage({
  conversationId,
  message,
  topK = 5,
  similarityThreshold = null,
  enableReranking = true,
  documentIdFilter = null,
}) {
  const payload = {
    conversation_id: conversationId || null,
    message,
    top_k: topK,
    similarity_threshold: similarityThreshold,
    enable_reranking: enableReranking,
    document_id_filter: documentIdFilter,
  };

  const res = await fetch(`${API_BASE}/chat/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Chat request failed" }));
    throw new Error(err.detail || "Failed to get answer from copilot");
  }
  return res.json();
}

export async function testRetrieval({
  query,
  topK = 6,
  similarityThreshold = 0.20,
  enableReranking = true,
  documentIdFilter = null,
}) {
  const res = await fetch(`${API_BASE}/retrieval/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      top_k: topK,
      similarity_threshold: similarityThreshold,
      enable_reranking: enableReranking,
      document_id_filter: documentIdFilter,
    }),
  });
  if (!res.ok) throw new Error("Retrieval test query failed");
  return res.json();
}

export async function runEvaluation() {
  const res = await fetch(`${API_BASE}/eval/run`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to execute benchmark");
  return res.json();
}

export async function fetchEvaluationHistory() {
  const res = await fetch(`${API_BASE}/eval/history`);
  if (!res.ok) throw new Error("Failed to fetch evaluation history");
  return res.json();
}
