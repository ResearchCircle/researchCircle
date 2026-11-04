'use client';

import { useState, useRef, useEffect, type FormEvent } from 'react';
import {
  Send,
  Bot,
  User as UserIcon,
  Sparkles,
  RotateCcw,
  AlertCircle,
  Copy,
  Check,
  BookOpen,
  Plus,
  MessageSquare,
  Trash2,
  PanelLeftClose,
  PanelLeft,
  Search,
} from 'lucide-react';
import { api, type ChatCitation, type ChatMessage } from '@/lib/api';

export interface ChatSession {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  proposalId?: string | null;
  proposalTitle?: string;
  messages: ChatMessage[];
  citations: ChatCitation[];
}

const STORAGE_KEY = 'tbr_research_chat_sessions_v2';

const STARTER_PROMPTS = [
  {
    title: 'Christopher Homan Research',
    subtitle: 'AI, prompt refinement & NLP at RIT',
    prompt: "What research areas does Christopher Homan focus on, and what are his recent papers?",
  },
  {
    title: 'Foundational Publications',
    subtitle: 'Deep Learning, IoT & BM25 retrieval',
    prompt: 'Summarize the foundational papers on deep learning and IoT available in the corpus.',
  },
  {
    title: 'Collaborator Discovery',
    subtitle: 'Multimodal sensing & perception',
    prompt: 'Which faculty at RIT specialize in multimodal dialogue, sensing, and accessibility?',
  },
  {
    title: 'Literature Synthesis',
    subtitle: 'Formulate an NSF research approach',
    prompt: 'How can agentic workflows and prompt refinement improve sensor data interpretation?',
  },
];

function createDefaultSession(proposalId?: string | null, proposalTitle?: string): ChatSession {
  return {
    id: `session_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
    title: 'New Research Chat',
    createdAt: Date.now(),
    updatedAt: Date.now(),
    proposalId,
    proposalTitle,
    messages: [
      {
        role: 'assistant',
        content: proposalId
          ? `Hello! I am your research assistant grounded on "${proposalTitle}". Ask any question about your attached publications or aims.`
          : "Hello! I am your research assistant grounded across 3,000+ verified publications and RIT faculty records. Ask any question about researchers, papers, or methodologies.",
      },
    ],
    citations: [],
  };
}

export default function ChatInterface({
  proposalId,
  proposalTitle,
  onCitationsChange,
}: {
  proposalId?: string | null;
  proposalTitle?: string;
  onCitationsChange?: (citations: ChatCitation[]) => void;
}) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>('');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Load chat sessions from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setSessions(parsed);
          setActiveSessionId(parsed[0].id);
          if (parsed[0].citations && onCitationsChange) {
            onCitationsChange(parsed[0].citations);
          }
          return;
        }
      }
    } catch {
      // ignore parse error
    }

    // Default session fallback
    const initSession = createDefaultSession(proposalId, proposalTitle);
    setSessions([initSession]);
    setActiveSessionId(initSession.id);
  }, []);

  // Save sessions to localStorage on mutation
  useEffect(() => {
    if (sessions.length > 0) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
      } catch {
        // ignore storage errors
      }
    }
  }, [sessions]);

  const activeSession =
    sessions.find((s) => s.id === activeSessionId) || sessions[0] || createDefaultSession(proposalId, proposalTitle);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeSession?.messages, loading]);

  const handleCreateNewChat = () => {
    const newSession = createDefaultSession(proposalId, proposalTitle);
    setSessions((prev) => [newSession, ...prev]);
    setActiveSessionId(newSession.id);
    setError('');
    if (onCitationsChange) onCitationsChange([]);
    setTimeout(() => textareaRef.current?.focus(), 100);
  };

  const handleSelectSession = (id: string) => {
    setActiveSessionId(id);
    setError('');
    const target = sessions.find((s) => s.id === id);
    if (target && onCitationsChange) {
      onCitationsChange(target.citations || []);
    }
  };

  const handleDeleteSession = (id: string) => {
    const updated = sessions.filter((s) => s.id !== id);
    if (updated.length === 0) {
      const fresh = createDefaultSession(proposalId, proposalTitle);
      setSessions([fresh]);
      setActiveSessionId(fresh.id);
      if (onCitationsChange) onCitationsChange([]);
    } else {
      setSessions(updated);
      if (activeSessionId === id) {
        setActiveSessionId(updated[0].id);
        if (onCitationsChange) onCitationsChange(updated[0].citations || []);
      }
    }
  };

  const handleSendPrompt = async (queryText: string) => {
    const query = queryText.trim();
    if (!query || loading) return;

    setInput('');
    setError('');

    // Maintain conversation context: all user/assistant messages prior to this query
    const previousTurns = activeSession.messages.filter((m) => m.role === 'user' || m.role === 'assistant');
    // omit greeting if it was the very first message
    const historyPayload = previousTurns.length > 1 ? previousTurns.slice(1) : [];

    const userMsg: ChatMessage = { role: 'user', content: query };
    const nextMessages = [...activeSession.messages, userMsg];

    // Auto-title session if it was still "New Research Chat"
    const newTitle =
      activeSession.title === 'New Research Chat'
        ? query.length > 36
          ? query.slice(0, 34) + '…'
          : query
        : activeSession.title;

    // Update active session optimistically
    setSessions((prev) =>
      prev.map((s) =>
        s.id === activeSession.id
          ? {
              ...s,
              title: newTitle,
              updatedAt: Date.now(),
              messages: nextMessages,
            }
          : s
      )
    );

    setLoading(true);

    try {
      const res = await api.chat({
        message: query,
        history: historyPayload,
        proposal_id: proposalId || null,
      });

      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: res.response,
      };

      const finalMessages = [...nextMessages, assistantMsg];
      const finalCitations = res.citations || [];

      setSessions((prev) =>
        prev.map((s) =>
          s.id === activeSession.id
            ? {
                ...s,
                updatedAt: Date.now(),
                messages: finalMessages,
                citations: finalCitations,
              }
            : s
        )
      );

      if (finalCitations && onCitationsChange) {
        onCitationsChange(finalCitations);
      }
    } catch (err: any) {
      setError(err?.message || 'Chat request failed. Check server status or credentials.');
      setSessions((prev) =>
        prev.map((s) =>
          s.id === activeSession.id
            ? {
                ...s,
                messages: [
                  ...nextMessages,
                  {
                    role: 'assistant',
                    content: 'I encountered an error communicating with the research chat engine. Please try again.',
                  },
                ],
              }
            : s
        )
      );
    } finally {
      setLoading(false);
    }
  };

  const handleFormSubmit = (e?: FormEvent) => {
    if (e) e.preventDefault();
    void handleSendPrompt(input);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void handleSendPrompt(input);
    }
  };

  const copyToClipboard = async (text: string, index: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 2000);
    } catch {
      // fallback
    }
  };

  // Whether the active session is currently empty (only contains default greeting)
  const isSessionEmpty = activeSession.messages.length <= 1;

  return (
    <div className="chat-interface-wrapper">
      {/* Left Sidebar: Recent Chats (ChatGPT style) */}
      <aside className={`chat-sessions-sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sessions-header">
          <button type="button" className="new-chat-button" onClick={handleCreateNewChat}>
            <Plus className="w-4 h-4 text-blue-600" />
            <span>New Chat</span>
          </button>
        </div>

        <div className="sessions-list">
          <div className="sessions-group-label">Recent Conversations</div>
          {sessions.map((s) => (
            <div
              key={s.id}
              className={`session-item ${s.id === activeSession.id ? 'active' : ''}`}
              onClick={() => handleSelectSession(s.id)}
            >
              <MessageSquare className="w-3.5 h-3.5 shrink-0 text-slate-500" />
              <span className="session-title" title={s.title}>
                {s.title}
              </span>
              <button
                type="button"
                className="session-delete-btn"
                title="Delete chat"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteSession(s.id);
                }}
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      </aside>

      {/* Main Chat Conversation Area */}
      <div className="chat-conversation-area">
        {/* Top Header & Scope Bar */}
        <div className="chat-scope-bar">
          <div className="scope-indicator">
            <button
              type="button"
              className="sidebar-toggle-btn"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              title={sidebarOpen ? 'Collapse sidebar' : 'Open recent chats'}
            >
              {sidebarOpen ? <PanelLeftClose className="w-4 h-4" /> : <PanelLeft className="w-4 h-4" />}
            </button>
            <span style={{ fontWeight: 650 }}>{activeSession.title}</span>
            {proposalId && (
              <span className="tag" style={{ marginLeft: 6 }}>
                Proposal: {proposalTitle || 'Active'}
              </span>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="muted" style={{ fontSize: 11 }}>
              {activeSession.messages.length > 1
                ? `${Math.floor((activeSession.messages.length - 1) / 2)} turn context`
                : 'Fresh chat'}
            </span>
            <button
              type="button"
              className="clear-chat-btn"
              onClick={handleCreateNewChat}
              title="Start a new chat session"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset</span>
            </button>
          </div>
        </div>

        {error && (
          <div className="alert error chat-error-alert" role="alert">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Message Stream */}
        <div className="chat-messages-container">
          {isSessionEmpty ? (
            /* ChatGPT-style Welcome & Starter Prompts */
            <div className="chat-empty-hero">
              <div className="hero-icon-wrapper">
                <Sparkles className="w-6 h-6" />
              </div>
              <h2>Research Literature Assistant</h2>
              <p>
                Grounded strictly on 3,000+ verified publications and RIT faculty facts. Ask any research question, compare methodologies, or synthesize literature.
              </p>

              <div className="prompt-starter-grid">
                {STARTER_PROMPTS.map((item, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className="prompt-starter-card"
                    onClick={() => void handleSendPrompt(item.prompt)}
                  >
                    <span className="card-heading">
                      <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                      {item.title}
                    </span>
                    <span className="card-subtext">{item.subtitle}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            activeSession.messages.map((msg, index) => {
              if (index === 0 && msg.role === 'assistant') {
                return (
                  <div key={index} className="chat-bubble-row assistant-row">
                    <div className="chat-avatar assistant">
                      <Bot className="w-4 h-4" />
                    </div>
                    <div className="chat-bubble assistant">
                      <p style={{ margin: 0 }}>{msg.content}</p>
                    </div>
                  </div>
                );
              }

              const isUser = msg.role === 'user';
              return (
                <div key={index} className={`chat-bubble-row ${isUser ? 'user-row' : 'assistant-row'}`}>
                  <div className={`chat-avatar ${isUser ? 'user' : 'assistant'}`}>
                    {isUser ? <UserIcon className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                  </div>
                  <div className={`chat-bubble ${isUser ? 'user' : 'assistant'}`}>
                    <div className="markdown-content" style={{ whiteSpace: 'pre-wrap' }}>
                      {msg.content}
                    </div>

                    {!isUser && (
                      <div className="bubble-actions">
                        <button
                          type="button"
                          className="copy-bubble-btn"
                          onClick={() => copyToClipboard(msg.content, index)}
                          title="Copy response"
                        >
                          {copiedIndex === index ? (
                            <>
                              <Check className="w-3 h-3 text-emerald-600" />
                              <span style={{ color: '#059669' }}>Copied</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3 h-3" />
                              <span>Copy</span>
                            </>
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}

          {loading && (
            <div className="chat-bubble-row assistant-row">
              <div className="chat-avatar assistant">
                <Bot className="w-4 h-4" />
              </div>
              <div className="chat-bubble assistant typing-bubble">
                <div className="dot" style={{ animationDelay: '0ms' }} />
                <div className="dot" style={{ animationDelay: '200ms' }} />
                <div className="dot" style={{ animationDelay: '400ms' }} />
                <span style={{ fontSize: 12, color: '#64748b', marginLeft: 8 }}>
                  Consulting grounded literature & generating verified answer…
                </span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <form onSubmit={handleFormSubmit} className="chat-input-form">
          <textarea
            ref={textareaRef}
            rows={2}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a research question or explore literature (Enter to send, Shift+Enter for newline)…"
            disabled={loading}
          />
          <button
            type="submit"
            className="primary"
            disabled={!input.trim() || loading}
            style={{ minHeight: 42, padding: '0 16px' }}
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
