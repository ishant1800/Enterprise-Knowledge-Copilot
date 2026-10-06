import React, { useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import ChatView from "./components/chat/ChatView";
import DocumentLibrary from "./components/documents/DocumentLibrary";
import RetrievalSandbox from "./components/retrieval/RetrievalSandbox";
import EvaluationDashboard from "./components/evaluations/EvaluationDashboard";

import {
  fetchHealth,
  fetchDocuments,
  uploadDocument,
  deleteDocument,
  seedSampleDocuments,
  listConversations,
  getConversation,
  deleteConversation,
  sendChatMessage,
} from "./services/api";

export default function App() {
  const [activeTab, setActiveTab] = useState("chat");
  const [systemHealth, setSystemHealth] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [currentConvId, setCurrentConvId] = useState(null);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [docsLoading, setDocsLoading] = useState(false);

  // Initialize app data
  useEffect(() => {
    refreshAll();
  }, []);

  const refreshAll = async () => {
    try {
      const [h, docs, convs] = await Promise.all([
        fetchHealth().catch(() => null),
        fetchDocuments().catch(() => []),
        listConversations().catch(() => []),
      ]);
      setSystemHealth(h);
      setDocuments(docs);
      setConversations(convs);

      // If conversations exist, select the most recent one
      if (convs.length > 0 && !currentConvId) {
        selectConversation(convs[0].id);
      }
    } catch (e) {
      console.error("Initialization error:", e);
    }
  };

  const selectConversation = async (convId) => {
    setCurrentConvId(convId);
    try {
      const detail = await getConversation(convId);
      setCurrentConversation(detail);
      setMessages(detail.messages || []);
    } catch (e) {
      console.error("Failed to load conversation", e);
    }
  };

  const handleNewChat = () => {
    setCurrentConvId(null);
    setCurrentConversation(null);
    setMessages([]);
    setActiveTab("chat");
  };

  const handleDeleteConversation = async (convId) => {
    try {
      await deleteConversation(convId);
      const updated = conversations.filter((c) => c.id !== convId);
      setConversations(updated);
      if (currentConvId === convId) {
        if (updated.length > 0) {
          selectConversation(updated[0].id);
        } else {
          handleNewChat();
        }
      }
    } catch (e) {
      alert("Failed to delete conversation: " + e.message);
    }
  };

  const handleSendMessage = async (chatParams) => {
    setChatLoading(true);

    // Optimistically add user message
    const tempUserMsg = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: chatParams.message,
      citations: [],
      is_grounded: true,
      confidence: "high",
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const res = await sendChatMessage({
        conversationId: currentConvId,
        message: chatParams.message,
        topK: chatParams.topK,
        similarityThreshold: chatParams.similarityThreshold,
        enableReranking: chatParams.enableReranking,
        documentIdFilter: chatParams.documentIdFilter,
      });

      // Update active conversation
      setCurrentConvId(res.conversation_id);
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== tempUserMsg.id),
        res.user_message,
        res.assistant_message,
      ]);

      // Refresh conversations list to update title
      const convs = await listConversations();
      setConversations(convs);
    } catch (err) {
      // Show error in chat
      const errorMsg = {
        id: `err-${Date.now()}`,
        role: "assistant",
        content: `Error: ${err.message || "Could not retrieve answer"}`,
        citations: [],
        is_grounded: false,
        confidence: "unsupported",
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleUploadDocument = async (file, chunkSize, chunkOverlap) => {
    await uploadDocument(file, chunkSize, chunkOverlap);
    const docs = await fetchDocuments();
    setDocuments(docs);
    const h = await fetchHealth().catch(() => null);
    if (h) setSystemHealth(h);
  };

  const handleDeleteDocument = async (docId) => {
    await deleteDocument(docId);
    const docs = await fetchDocuments();
    setDocuments(docs);
    const h = await fetchHealth().catch(() => null);
    if (h) setSystemHealth(h);
  };

  const handleSeedSamples = async () => {
    await seedSampleDocuments();
    const docs = await fetchDocuments();
    setDocuments(docs);
    const h = await fetchHealth().catch(() => null);
    if (h) setSystemHealth(h);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100">
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        conversations={conversations}
        currentConvId={currentConvId}
        onSelectConversation={selectConversation}
        onNewChat={handleNewChat}
        onDeleteConversation={handleDeleteConversation}
        systemHealth={systemHealth}
        docCount={documents.length}
      />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {activeTab === "chat" && (
          <ChatView
            conversation={currentConversation}
            messages={messages}
            loading={chatLoading}
            onSendMessage={handleSendMessage}
            documents={documents}
          />
        )}

        {activeTab === "documents" && (
          <DocumentLibrary
            documents={documents}
            loading={docsLoading}
            onUploadDocument={handleUploadDocument}
            onDeleteDocument={handleDeleteDocument}
            onSeedSamples={handleSeedSamples}
          />
        )}

        {activeTab === "retrieval" && (
          <RetrievalSandbox documents={documents} />
        )}

        {activeTab === "eval" && (
          <EvaluationDashboard />
        )}
      </main>
    </div>
  );
}
