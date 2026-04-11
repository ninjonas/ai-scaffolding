import { useState, useEffect, useCallback } from 'react';
import {
  listKnowledgeFiles,
  deleteKnowledgeFile,
  type KnowledgeCatalogEntry,
} from '../api/knowledge';
import { KnowledgeFileEditor } from './KnowledgeFileEditor';

interface KnowledgeSidebarProps {
  conversationId?: string;
  onClose: () => void;
}

const TrashIcon = () => (
  <svg
    width="14"
    height="14"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden
  >
    <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
  </svg>
);

const CloseIcon = () => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden
  >
    <path d="M18 6 6 18M6 6l12 12" />
  </svg>
);

type Scope = 'project' | 'conversation';

export function KnowledgeSidebar({ conversationId, onClose }: KnowledgeSidebarProps) {
  const [tab, setTab] = useState<Scope>('project');
  const [files, setFiles] = useState<KnowledgeCatalogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showEditor, setShowEditor] = useState(false);

  const fetchFiles = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const result = await listKnowledgeFiles(
        tab,
        tab === 'conversation' ? conversationId : undefined,
      );
      setFiles(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load files');
    } finally {
      setLoading(false);
    }
  }, [tab, conversationId]);

  useEffect(() => {
    fetchFiles();
  }, [fetchFiles]);

  const handleDelete = async (id: string, name: string) => {
    if (!window.confirm(`Delete "${name}"?`)) return;
    try {
      await deleteKnowledgeFile(id);
      await fetchFiles();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to delete file');
    }
  };

  return (
    <div className="knowledge-sidebar">
      <div className="knowledge-sidebar-header">
        <h2>Knowledge</h2>
        <button className="knowledge-close-btn" onClick={onClose} aria-label="Close sidebar">
          <CloseIcon />
        </button>
      </div>
      <div className="knowledge-tabs">
        <button
          className={`knowledge-tab ${tab === 'project' ? 'active' : ''}`}
          onClick={() => setTab('project')}
        >
          Project
        </button>
        {conversationId && (
          <button
            className={`knowledge-tab ${tab === 'conversation' ? 'active' : ''}`}
            onClick={() => setTab('conversation')}
          >
            Conversation
          </button>
        )}
      </div>
      <button className="knowledge-upload-btn" onClick={() => setShowEditor(true)}>
        Upload file
      </button>
      {error && <div className="knowledge-error">{error}</div>}
      <div className="knowledge-file-list">
        {loading ? (
          Array.from({ length: 3 }).map((_, i) => <div key={i} className="knowledge-skeleton" />)
        ) : files.length === 0 ? (
          <p className="knowledge-empty">No knowledge files yet. Upload one to get started.</p>
        ) : (
          files.map((f) => (
            <div key={f.id} className="knowledge-file-row">
              <div className="knowledge-file-info">
                <div className="knowledge-file-name">
                  {f.name}
                  <span className="knowledge-file-badge">{f.fileType}</span>
                </div>
                {f.description && <div className="knowledge-file-desc">{f.description}</div>}
                {f.tags.length > 0 && (
                  <div className="knowledge-file-tags">
                    {f.tags.map((t) => (
                      <span key={t} className="knowledge-tag">
                        {t}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <button
                className="knowledge-delete-btn"
                onClick={() => handleDelete(f.id, f.name)}
                aria-label={`Delete ${f.name}`}
              >
                <TrashIcon />
              </button>
            </div>
          ))
        )}
      </div>
      {showEditor && (
        <KnowledgeFileEditor
          scope={tab}
          conversationId={conversationId}
          onSave={() => {
            setShowEditor(false);
            fetchFiles();
          }}
          onClose={() => setShowEditor(false)}
        />
      )}
    </div>
  );
}
