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
} from 'lucide-react';
import { api, type ChatCitation, type ChatMessage } from '@/lib/api';

export default function ChatInterface({
  proposalId,
  proposalTitle,
  onCitationsChange,
}: {
  proposalId?: string | null;
  proposalTitle?: string;
  onCitationsChange?: (citations: ChatCitation[]) => void;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: proposalId
        ? `Hello! I'm your research assistant grounded on your proposal "${proposalTitle}". Ask any question about your attached literature or aims.`
        : "Hello! I'm your research assistant grounded across verified public research records. Ask any question about RIT faculty publications, papers, or methodologies.",
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (e?: FormEvent) => {
    if (e) e.preventDefault();
    const query = input.trim();
    if (!query || loading) return;

    setInput('');
    setError('');
    const userMsg: ChatMessage = { role: 'user', content: query };
    const nextHistory = [...messages, userMsg];
    setMessages(nextHistory);
    setLoading(true);

    try {
      const res = await api.chat({
        message: query,
        history: nextHistory.slice(1), // omit initial greeting
        proposal_id: proposalId || null,
      });

      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: res.response,
      };
      setMessages((prev) => [...prev, assistantMsg]);
      if (res.citations && onCitationsChange) {
        onCitationsChange(res.citations);
      }
    } catch (err: any) {
      setError(err?.message || 'Chat request failed. Please check your connection.');
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'I encountered an error communicating with the research chat engine. Please retry.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([
      {
        role: 'assistant',
        content: proposalId
          ? `Conversation reset. Ready for research questions on "${proposalTitle}".`
          : 'Conversation reset. Ready for research questions on the public literature.',
      },
    ]);
    setError('');
    if (onCitationsChange) onCitationsChange([]);
  };

  const copyToClipboard = async (text: string, index: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 2000);
    } catch {
      // ignore
    }
  };

  return (
    <div className="chat-interface-wrapper">
      <div className="chat-scope-bar">
        <div className="scope-indicator">
          <Sparkles className="w-4 h-4 text-[#225bb2]" />
          <span>
            {proposalId ? (
              <>Grounded on active proposal: <strong>{proposalTitle}</strong></>
            ) : (
              <>Grounded across <strong>Public Literature & RIT Faculty Records</strong></>
            )}
          </span>
        </div>
        <button
          type="button"
          onClick={clearChat}
          className="clear-chat-btn"
          title="Reset conversation"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Clear Chat</span>
        </button>
      </div>

      {error && (
        <div className="alert error chat-error-alert" role="alert">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="chat-messages-container">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`chat-bubble-row ${msg.role === 'user' ? 'user-row' : 'assistant-row'}`}
          >
            <div className={`chat-avatar ${msg.role}`}>
              {msg.role === 'user' ? (
                <UserIcon className="w-4 h-4" />
              ) : (
                <Bot className="w-4 h-4" />
              )}
            </div>

            <div className={`chat-bubble ${msg.role}`}>
              <div className="chat-bubble-content">
                <p>{msg.content}</p>
              </div>

              {msg.role === 'assistant' && idx > 0 && (
                <div className="bubble-actions">
                  <button
                    type="button"
                    className="copy-bubble-btn"
                    onClick={() => copyToClipboard(msg.content, idx)}
                  >
                    {copiedIndex === idx ? (
                      <>
                        <Check className="w-3 h-3 text-[#14766d]" />
                        <span>Copied</span>
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
        ))}

        {loading && (
          <div className="chat-bubble-row assistant-row">
            <div className="chat-avatar assistant">
              <Bot className="w-4 h-4" />
            </div>
            <div className="chat-bubble assistant typing-bubble">
              <span className="dot" />
              <span className="dot" />
              <span className="dot" />
              <span className="muted small ml-2">Consulting grounded literature…</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSend} className="chat-input-form">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              void handleSend();
            }
          }}
          placeholder="Ask a question about the literature, methodologies, or research evidence (Press Enter to send)…"
          rows={2}
          disabled={loading}
          maxLength={2000}
        />
        <button
          type="submit"
          className="primary chat-send-btn"
          disabled={loading || !input.trim()}
          title="Send message"
        >
          <Send className="w-4 h-4" />
          <span>Send</span>
        </button>
      </form>
    </div>
  );
}
