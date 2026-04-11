const API_BASE = '/api/knowledge';

export interface KnowledgeCatalogEntry {
  id: string;
  name: string;
  description: string;
  tags: string[];
  fileType: string;
  scope: string;
  enriched: boolean;
}

export interface KnowledgeFileResponse {
  id: string;
  filename: string;
  name: string;
  description: string;
  content: string;
  tags: string[];
  fileType: string;
  scope: string;
  enriched: boolean;
  conversationId: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface KnowledgeUploadRequest {
  filename: string;
  content: string;
  scope: 'project' | 'conversation';
  conversationId?: string;
}

export interface KnowledgeUpdateRequest {
  name?: string;
  description?: string;
  tags?: string[];
  content?: string;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Knowledge API error: ${error}`);
  }
  return response.json();
}

export async function listKnowledgeFiles(
  scope: 'project' | 'conversation',
  conversationId?: string,
): Promise<KnowledgeCatalogEntry[]> {
  const params = new URLSearchParams({ scope });
  if (conversationId) params.set('conversationId', conversationId);
  const response = await fetch(`${API_BASE}?${params}`);
  return handleResponse<KnowledgeCatalogEntry[]>(response);
}

export async function uploadKnowledgeFile(
  data: KnowledgeUploadRequest,
): Promise<KnowledgeFileResponse> {
  const response = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<KnowledgeFileResponse>(response);
}

export async function getKnowledgeFile(id: string): Promise<KnowledgeFileResponse> {
  const response = await fetch(`${API_BASE}/${id}`);
  return handleResponse<KnowledgeFileResponse>(response);
}

export async function updateKnowledgeFile(
  id: string,
  data: KnowledgeUpdateRequest,
): Promise<KnowledgeFileResponse> {
  const response = await fetch(`${API_BASE}/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<KnowledgeFileResponse>(response);
}

export async function deleteKnowledgeFile(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/${id}`, { method: 'DELETE' });
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Knowledge API error: ${error}`);
  }
}
