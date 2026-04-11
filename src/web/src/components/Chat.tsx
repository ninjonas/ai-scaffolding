import { useRef, useEffect, useState } from 'react';
import { ChatInput, type AttachedImage } from './ChatInput';
import { KnowledgeSidebar } from './KnowledgeSidebar';
import { MemoryConfirmCard } from './MemoryConfirmCard';
import { MessageBubble } from './MessageBubble';
import { useChatSend, type ChatMessage } from './useChatSend';

function SearchingMemoryIndicator() {
  return (
    <div className="message message-assistant message-loading">
      <div className="message-role">Assistant</div>
      <div className="searching-memory">
        <span className="searching-memory-dot" />
        <span className="searching-memory-dot" />
        <span className="searching-memory-dot" />
        <span className="searching-memory-label">Searching memory</span>
      </div>
    </div>
  );
}

function MessageItem({
  msg,
  index,
  loading,
  onResume,
}: {
  msg: ChatMessage;
  index: number;
  loading: boolean;
  onResume: (approved: boolean) => Promise<void>;
}) {
  if (msg.role === 'memory_confirm' && msg.interrupt) {
    return (
      <MemoryConfirmCard
        key={index}
        interrupt={msg.interrupt}
        onResume={onResume}
        disabled={loading}
      />
    );
  }
  return (
    <MessageBubble
      key={index}
      role={msg.role as 'user' | 'assistant'}
      content={msg.content}
      toolCalls={msg.toolCalls}
      images={msg.images}
      knowledgeFiles={msg.knowledgeFiles}
    />
  );
}

function ChatMessages({
  messages,
  loading,
  error,
  onResume,
}: {
  messages: ChatMessage[];
  loading: boolean;
  error: string | undefined;
  onResume: (approved: boolean) => Promise<void>;
}) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const hasMemoryConfirm = messages.some((m) => m.role === 'memory_confirm');

  return (
    <div className="chat-messages">
      {messages.length === 0 && (
        <div className="chat-empty">
          <div className="chat-empty-greeting">Hi there, how can I help?</div>
          <div className="chat-empty-hint">Ask me anything to get started</div>
        </div>
      )}
      {messages.map((msg, i) => (
        <MessageItem key={i} msg={msg} index={i} loading={loading} onResume={onResume} />
      ))}
      {loading && !hasMemoryConfirm && <MessageBubble role="assistant" content="" loading />}
      {loading && hasMemoryConfirm && <SearchingMemoryIndicator />}
      {error && <div className="chat-error">{error}</div>}
      <div ref={messagesEndRef} />
    </div>
  );
}

export function Chat() {
  const {
    messages,
    conversationId,
    loading,
    error,
    knowledgeRefreshKey,
    handleSend,
    handleResume,
    handleNewChat,
  } = useChatSend();
  const [showKnowledge, setShowKnowledge] = useState(false);

  const onNewChat = () => {
    handleNewChat();
    setShowKnowledge(false);
  };

  return (
    <div className="chat-layout">
      <div className="chat-container">
        <div className="chat-header">
          <h1>Scaffolding Chat</h1>
          <button className="new-chat-btn" onClick={onNewChat} disabled={loading}>
            New Chat
          </button>
        </div>
        <ChatMessages messages={messages} loading={loading} error={error} onResume={handleResume} />
        <ChatInput
          onSend={handleSend}
          disabled={loading}
          onToggleKnowledge={() => setShowKnowledge((prev) => !prev)}
          knowledgeOpen={showKnowledge}
          conversationId={conversationId}
        />
      </div>
      {showKnowledge && (
        <KnowledgeSidebar
          conversationId={conversationId}
          onClose={() => setShowKnowledge(false)}
          refreshKey={knowledgeRefreshKey}
        />
      )}
    </div>
  );
}

export type { AttachedImage };
