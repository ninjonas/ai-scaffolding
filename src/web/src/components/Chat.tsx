import { useState, useRef, useEffect } from 'react';
import { sendMessage, type ChatResponse, type ToolCall } from '../api/chat';
import { ChatInput } from './ChatInput';
import { KnowledgeSidebar } from './KnowledgeSidebar';
import { MessageBubble } from './MessageBubble';

const BookIcon = () => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden
  >
    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
  </svg>
);

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: ToolCall[];
  images?: string[];
}

export function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();
  const [showKnowledge, setShowKnowledge] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (content: string, images: string[]) => {
    const userMessage: ChatMessage = {
      role: 'user',
      content,
      images: images.length > 0 ? images : undefined,
    };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setError(undefined);

    try {
      const response: ChatResponse = await sendMessage({
        message: content,
        conversationId,
        images: images.length > 0 ? images : undefined,
      });

      setConversationId(response.conversationId);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.message,
          toolCalls: response.toolCalls,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-layout">
      <div className="chat-container">
        <div className="chat-header">
          <h1>Scaffolding Chat</h1>
          <div className="chat-header-actions">
            <button
              className={`knowledge-toggle-btn${showKnowledge ? ' active' : ''}`}
              type="button"
              onClick={() => setShowKnowledge((prev) => !prev)}
              title="Toggle knowledge sidebar"
              aria-label="Toggle knowledge sidebar"
            >
              <BookIcon />
            </button>
          </div>
        </div>
        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="chat-empty">
              <div className="chat-empty-greeting">Hi there, how can I help?</div>
              <div className="chat-empty-hint">Ask me anything to get started</div>
            </div>
          )}
          {messages.map((msg, i) => (
            <MessageBubble
              key={i}
              role={msg.role}
              content={msg.content}
              toolCalls={msg.toolCalls}
              images={msg.images}
            />
          ))}
          {loading && <MessageBubble role="assistant" content="" loading />}
          {error && <div className="chat-error">{error}</div>}
          <div ref={messagesEndRef} />
        </div>
        <ChatInput
          onSend={handleSend}
          disabled={loading}
          onAttachKnowledge={() => setShowKnowledge(true)}
        />
      </div>
      {showKnowledge && (
        <KnowledgeSidebar conversationId={conversationId} onClose={() => setShowKnowledge(false)} />
      )}
    </div>
  );
}
