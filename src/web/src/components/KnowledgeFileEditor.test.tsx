import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { KnowledgeFileEditor } from './KnowledgeFileEditor';
import type { KnowledgeFileResponse } from '../api/knowledge';

vi.mock('../api/knowledge', () => ({
  getKnowledgeFile: vi.fn(),
  updateKnowledgeFile: vi.fn(),
  listKnowledgeFiles: vi.fn(),
}));

import * as knowledgeApi from '../api/knowledge';

const mockFile: KnowledgeFileResponse = {
  id: 'file-1',
  name: 'Test Doc',
  description: 'A useful document',
  tags: ['tag1'],
  fileType: 'md',
  scope: 'project',
  conversationId: null,
  createdAt: '2025-01-01T00:00:00Z',
  updatedAt: '2025-01-01T00:00:00Z',
};

beforeEach(() => {
  vi.mocked(knowledgeApi.getKnowledgeFile).mockResolvedValue(mockFile);
  vi.mocked(knowledgeApi.updateKnowledgeFile).mockResolvedValue(mockFile);
});

afterEach(() => {
  vi.clearAllMocks();
});

describe('KnowledgeFileEditor', () => {
  it('renders dialog with accessible label', async () => {
    render(
      <KnowledgeFileEditor fileId="file-1" scope="project" onSave={vi.fn()} onClose={vi.fn()} />,
    );
    expect(screen.getByRole('dialog', { name: /edit knowledge file/i })).toBeInTheDocument();
  });

  it('loads and displays file name', async () => {
    render(
      <KnowledgeFileEditor fileId="file-1" scope="project" onSave={vi.fn()} onClose={vi.fn()} />,
    );
    await waitFor(() => expect(screen.getByDisplayValue('Test Doc')).toBeInTheDocument());
  });

  it('calls close handler when close button clicked', async () => {
    const onClose = vi.fn();
    render(
      <KnowledgeFileEditor fileId="file-1" scope="project" onSave={vi.fn()} onClose={onClose} />,
    );
    fireEvent.click(screen.getByRole('button', { name: /close editor/i }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls updateKnowledgeFile on save', async () => {
    const onSave = vi.fn();
    render(
      <KnowledgeFileEditor fileId="file-1" scope="project" onSave={onSave} onClose={vi.fn()} />,
    );
    await waitFor(() => screen.getByDisplayValue('Test Doc'));

    fireEvent.click(screen.getByRole('button', { name: /save/i }));

    await waitFor(() =>
      expect(knowledgeApi.updateKnowledgeFile).toHaveBeenCalledWith(
        'file-1',
        expect.objectContaining({ name: 'Test Doc' }),
      ),
    );
    expect(onSave).toHaveBeenCalled();
  });
});
