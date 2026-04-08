import { useState, useRef, useEffect } from 'react';
import { sendMessage, type ChatResponse, type ToolCall } from '../api/chat';
import { ChatInput } from './ChatInput';
import { MessageBubble } from './MessageBubble';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: ToolCall[];
}

export function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (content: string, images: string[]) => {
    const userMessage: ChatMessage = { role: 'user', content };
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
    <div className="chat-container">
      <div className="chat-header">
        <h1>Scaffolding Chat</h1>
      </div>
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">Send a message to start a conversation.</div>
        )}
        {messages.map((msg, i) => (
          <MessageBubble key={i} role={msg.role} content={msg.content} toolCalls={msg.toolCalls} />
        ))}
        {loading && <MessageBubble role="assistant" content="Thinking..." loading />}
        {error && <div className="chat-error">{error}</div>}
        <div ref={messagesEndRef} />
      </div>
      <ChatInput onSend={handleSend} disabled={loading} />
    </div>
  );
}
