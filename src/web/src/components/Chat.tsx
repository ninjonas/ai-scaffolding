import { useState, useRef, useEffect } from 'react';
import { sendMessage, type ChatResponse, type ToolCall } from '../api/chat';
import { ChatInput } from './ChatInput';
import { KnowledgeSidebar } from './KnowledgeSidebar';
import { MessageBubble } from './MessageBubble';

interface KnowledgeChip {
  id: string;
  name: string;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: ToolCall[];
  images?: string[];
  knowledgeFiles?: KnowledgeChip[];
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

  const handleSend = async (content: string, images: string[], knowledgeFiles: KnowledgeChip[]) => {
    const userMessage: ChatMessage = {
      role: 'user',
      content,
      images: images.length > 0 ? images : undefined,
      knowledgeFiles: knowledgeFiles.length > 0 ? knowledgeFiles : undefined,
    };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setError(undefined);

    try {
      const response: ChatResponse = await sendMessage({
        message: content,
        conversationId,
        images: images.length > 0 ? images : undefined,
        knowledgeFileIds: knowledgeFiles.length > 0 ? knowledgeFiles.map((f) => f.id) : undefined,
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
              knowledgeFiles={msg.knowledgeFiles}
            />
          ))}
          {loading && <MessageBubble role="assistant" content="" loading />}
          {error && <div className="chat-error">{error}</div>}
          <div ref={messagesEndRef} />
        </div>
        <ChatInput
          onSend={handleSend}
          disabled={loading}
          onToggleKnowledge={() => setShowKnowledge((prev) => !prev)}
          knowledgeOpen={showKnowledge}
          conversationId={conversationId}
        />
      </div>
      {showKnowledge && (
        <KnowledgeSidebar conversationId={conversationId} onClose={() => setShowKnowledge(false)} />
      )}
    </div>
  );
}
