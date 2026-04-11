import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { KnowledgeSidebar } from './KnowledgeSidebar';
import type { KnowledgeCatalogEntry } from '../api/knowledge';

vi.mock('../api/knowledge', () => ({
  listKnowledgeFiles: vi.fn(),
  uploadKnowledgeFile: vi.fn(),
  deleteKnowledgeFile: vi.fn(),
  getKnowledgeFile: vi.fn(),
  updateKnowledgeFile: vi.fn(),
}));

import * as knowledgeApi from '../api/knowledge';

const mockEntry: KnowledgeCatalogEntry = {
  id: 'file-1',
  name: 'Test Doc',
  description: 'A useful document',
  tags: ['tag1'],
  fileType: 'md',
  scope: 'project',
};

beforeEach(() => {
  vi.mocked(knowledgeApi.listKnowledgeFiles).mockResolvedValue([]);
});

afterEach(() => {
  vi.clearAllMocks();
});

describe('KnowledgeSidebar', () => {
  it('renders sidebar landmark', async () => {
    render(<KnowledgeSidebar onClose={vi.fn()} />);
    expect(screen.getByRole('complementary', { name: /knowledge base/i })).toBeInTheDocument();
  });

  it('renders close button', async () => {
    render(<KnowledgeSidebar onClose={vi.fn()} />);
    expect(screen.getByRole('button', { name: /close sidebar/i })).toBeInTheDocument();
  });

  it('calls onClose when close button clicked', async () => {
    const onClose = vi.fn();
    render(<KnowledgeSidebar onClose={onClose} />);
    fireEvent.click(screen.getByRole('button', { name: /close sidebar/i }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('shows empty state when no files', async () => {
    vi.mocked(knowledgeApi.listKnowledgeFiles).mockResolvedValue([]);
    render(<KnowledgeSidebar onClose={vi.fn()} />);
    await waitFor(() => expect(screen.getByText(/no project files yet/i)).toBeInTheDocument());
  });

  it('renders file list when files are present', async () => {
    vi.mocked(knowledgeApi.listKnowledgeFiles).mockResolvedValue([mockEntry]);
    render(<KnowledgeSidebar onClose={vi.fn()} />);
    await waitFor(() => expect(screen.getByText('Test Doc')).toBeInTheDocument());
  });

  it('switches to conversation scope on tab click', async () => {
    vi.mocked(knowledgeApi.listKnowledgeFiles).mockResolvedValue([]);
    render(<KnowledgeSidebar onClose={vi.fn()} conversationId="conv-1" />);
    await waitFor(() => expect(screen.getByText(/no project files/i)).toBeInTheDocument());
    const convTab = screen.getByRole('tab', { name: /conversation/i });
    fireEvent.click(convTab);
    await waitFor(() =>
      expect(screen.getByText(/no files attached to this conversation/i)).toBeInTheDocument(),
    );
  });
});
