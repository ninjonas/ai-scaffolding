import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  deleteKnowledgeFile,
  listKnowledgeFiles,
  uploadKnowledgeFile,
  type KnowledgeCatalogEntry,
  type KnowledgeFileResponse,
} from './knowledge';

const mockEntry: KnowledgeCatalogEntry = {
  id: 'file-1',
  name: 'Test Doc',
  description: 'A test document',
  tags: ['tag1'],
  fileType: 'md',
  scope: 'project',
};

const mockFileResponse: KnowledgeFileResponse = {
  id: 'file-1',
  name: 'Test Doc',
  description: 'A test document',
  tags: ['tag1'],
  fileType: 'md',
  scope: 'project',
  conversationId: null,
  createdAt: '2025-01-01T00:00:00Z',
  updatedAt: '2025-01-01T00:00:00Z',
};

function mockFetch(data: unknown, ok = true, status = 200) {
  return vi.fn().mockResolvedValue({
    ok,
    status,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(ok ? '' : 'error details'),
  });
}

beforeEach(() => {
  vi.stubGlobal('fetch', mockFetch([mockEntry]));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('listKnowledgeFiles', () => {
  it('calls the correct URL with scope param', async () => {
    const fetchMock = mockFetch([mockEntry]);
    vi.stubGlobal('fetch', fetchMock);

    await listKnowledgeFiles('project');

    const url = fetchMock.mock.calls[0][0] as string;
    expect(url).toContain('/api/knowledge');
    expect(url).toContain('scope=project');
  });

  it('includes conversationId param when provided', async () => {
    const fetchMock = mockFetch([mockEntry]);
    vi.stubGlobal('fetch', fetchMock);

    await listKnowledgeFiles('conversation', 'conv-123');

    const url = fetchMock.mock.calls[0][0] as string;
    expect(url).toContain('conversationId=conv-123');
  });

  it('returns parsed array', async () => {
    vi.stubGlobal('fetch', mockFetch([mockEntry]));
    const result = await listKnowledgeFiles('project');
    expect(result).toEqual([mockEntry]);
  });
});

describe('uploadKnowledgeFile', () => {
  it('POSTs to the correct URL', async () => {
    const fetchMock = mockFetch(mockFileResponse);
    vi.stubGlobal('fetch', fetchMock);

    await uploadKnowledgeFile({ filename: 'doc.md', content: '# Hello', scope: 'project' });

    expect(fetchMock.mock.calls[0][0]).toBe('/api/knowledge');
    expect(fetchMock.mock.calls[0][1].method).toBe('POST');
  });

  it('sends JSON body with filename and content', async () => {
    const fetchMock = mockFetch(mockFileResponse);
    vi.stubGlobal('fetch', fetchMock);

    await uploadKnowledgeFile({ filename: 'doc.md', content: '# Hello', scope: 'project' });

    const body = JSON.parse(fetchMock.mock.calls[0][1].body);
    expect(body.filename).toBe('doc.md');
    expect(body.content).toBe('# Hello');
  });

  it('returns parsed response', async () => {
    vi.stubGlobal('fetch', mockFetch(mockFileResponse));
    const result = await uploadKnowledgeFile({
      filename: 'doc.md',
      content: 'x',
      scope: 'project',
    });
    expect(result.id).toBe('file-1');
  });
});

describe('deleteKnowledgeFile', () => {
  it('sends DELETE to the correct URL', async () => {
    const fetchMock = mockFetch(null);
    vi.stubGlobal('fetch', fetchMock);

    await deleteKnowledgeFile('file-1');

    expect(fetchMock.mock.calls[0][0]).toBe('/api/knowledge/file-1');
    expect(fetchMock.mock.calls[0][1].method).toBe('DELETE');
  });
});

describe('error handling', () => {
  it('throws on non-ok response', async () => {
    vi.stubGlobal('fetch', mockFetch(null, false, 404));

    await expect(listKnowledgeFiles('project')).rejects.toThrow('Knowledge API error');
  });
});
