const API_BASE = '/api';

export interface ChatRequest {
  message: string;
  conversationId?: string;
  images?: string[];
  knowledgeFileIds?: string[];
}

export interface ToolCall {
  name: string;
  args: Record<string, unknown>;
}

export interface ChatResponse {
  message: string;
  conversationId: string;
  toolCalls: ToolCall[];
}

export async function sendMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Chat request failed: ${error}`);
  }

  return response.json();
}
