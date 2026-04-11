import { useRef, useEffect, useState } from 'react';
import { ChatInput, type AttachedImage } from './ChatInput';
import { KnowledgeSidebar } from './KnowledgeSidebar';
import { MessageBubble } from './MessageBubble';
import { useChatSend, type ChatMessage } from './useChatSend';

function ChatMessages({
  messages,
  loading,
  error,
}: {
  messages: ChatMessage[];
  loading: boolean;
  error: string | undefined;
}) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
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
          knowledgeFiles={msg.knowledgeFiles}
        />
      ))}
      {loading && <MessageBubble role="assistant" content="" loading />}
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
        <ChatMessages messages={messages} loading={loading} error={error} />
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
