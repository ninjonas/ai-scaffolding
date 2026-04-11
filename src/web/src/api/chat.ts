const API_BASE = '/api';

export interface ChatRequest {
  message: string;
  conversationId?: string;
  images?: string[];
  imageFilenames?: string[];
  knowledgeFileIds?: string[];
}

export interface ToolCall {
  name: string;
  args: Record<string, unknown>;
}

export interface MemoryResult {
  conversationId: string;
  createdAt: string;
  excerpt: string;
}

export interface MemoryConfirmInterrupt {
  type: 'memory_confirm';
  results: MemoryResult[];
  prompt: string;
}

export interface ChatResponse {
  message: string;
  conversationId: string;
  toolCalls: ToolCall[];
  interrupt?: MemoryConfirmInterrupt | null;
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

export async function resumeConversation(
  conversationId: string,
  approved: boolean,
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat/${conversationId}/resume`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approved }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Resume request failed: ${error}`);
  }

  return response.json();
}
