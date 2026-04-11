import { useState } from 'react';
import { sendMessage, type ToolCall } from '../api/chat';
import { uploadKnowledgeFile } from '../api/knowledge';
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
}

export function useChatSend(): UseChatSendResult {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();
  const [knowledgeRefreshKey, setKnowledgeRefreshKey] = useState(0);

  const uploadImages = async (images: AttachedImage[], convId: string) => {
    try {
      await Promise.all(
        images.map((img) =>
          uploadKnowledgeFile({
            filename: img.filename,
            content: img.dataUrl.split(',')[1],
            scope: 'conversation',
            conversationId: convId,
          }),
        ),
      );
      setKnowledgeRefreshKey((k) => k + 1);
    } catch {
      // image knowledge upload is non-critical, swallow errors
    }
  };

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
        knowledgeFileIds: knowledgeFiles.length > 0 ? knowledgeFiles.map((f) => f.id) : undefined,
      });

      setConversationId(response.conversationId);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: response.message, toolCalls: response.toolCalls },
      ]);

      if (images.length > 0) {
        await uploadImages(images, response.conversationId);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return { messages, conversationId, loading, error, knowledgeRefreshKey, handleSend };
}
