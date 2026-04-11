import { useState } from 'react';
import { sendMessage, type ToolCall } from '../api/chat';
import type { AttachedImage } from './ChatInput';

interface KnowledgeChip {
  id: string;
  name: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: ToolCall[];
  images?: string[];
  knowledgeFiles?: KnowledgeChip[];
}

interface UseChatSendResult {
  messages: ChatMessage[];
  conversationId: string | undefined;
  loading: boolean;
  error: string | undefined;
  knowledgeRefreshKey: number;
  handleSend: (
    content: string,
    images: AttachedImage[],
    knowledgeFiles: KnowledgeChip[],
  ) => Promise<void>;
  handleNewChat: () => void;
}

export function useChatSend(): UseChatSendResult {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();
  const [knowledgeRefreshKey, setKnowledgeRefreshKey] = useState(0);

  const handleSend = async (
    content: string,
    images: AttachedImage[],
    knowledgeFiles: KnowledgeChip[],
  ) => {
    const base64Images = images.map((img) => img.dataUrl.split(',')[1]);
    const userMessage: ChatMessage = {
      role: 'user',
      content,
      images: base64Images.length > 0 ? base64Images : undefined,
      knowledgeFiles: knowledgeFiles.length > 0 ? knowledgeFiles : undefined,
    };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setError(undefined);

    try {
      const response = await sendMessage({
        message: content,
        conversationId,
        images: base64Images.length > 0 ? base64Images : undefined,
        imageFilenames: images.length > 0 ? images.map((img) => img.filename) : undefined,
        knowledgeFileIds: knowledgeFiles.length > 0 ? knowledgeFiles.map((f) => f.id) : undefined,
      });

      setConversationId(response.conversationId);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: response.message, toolCalls: response.toolCalls },
      ]);

      if (images.length > 0) {
        setKnowledgeRefreshKey((k) => k + 1);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setConversationId(undefined);
    setError(undefined);
    setKnowledgeRefreshKey(0);
  };

  return {
    messages,
    conversationId,
    loading,
    error,
    knowledgeRefreshKey,
    handleSend,
    handleNewChat,
  };
}
