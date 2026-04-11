import { useState, useEffect, useCallback, useRef } from 'react';
import {
  listKnowledgeFiles,
  deleteKnowledgeFile,
  type KnowledgeCatalogEntry,
} from '../api/knowledge';
import { KnowledgeFileEditor } from './KnowledgeFileEditor';
import { CloseIcon, DocumentIcon, PlusIcon, TrashIcon } from './KnowledgeIcons';

interface KnowledgeSidebarProps {
  conversationId?: string;
  onClose: () => void;
}

type Scope = 'project' | 'conversation';

export function KnowledgeSidebar({ conversationId, onClose }: KnowledgeSidebarProps) {
  const [tab, setTab] = useState<Scope>('project');
  const [files, setFiles] = useState<KnowledgeCatalogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showEditor, setShowEditor] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const dragCounterRef = useRef(0);

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

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    dragCounterRef.current += 1;
    if (dragCounterRef.current === 1) setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    dragCounterRef.current -= 1;
    if (dragCounterRef.current === 0) setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    dragCounterRef.current = 0;
    setIsDragging(false);
    setShowEditor(true);
  };

  const openEditor = () => setShowEditor(true);

  const isEmpty = !loading && files.length === 0;
  const hasFiles = !loading && files.length > 0;

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

      {error && <div className="knowledge-error">{error}</div>}

      {loading && (
        <div className="knowledge-file-list">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="knowledge-skeleton" />
          ))}
        </div>
      )}

      {isEmpty && (
        <div
          className={`knowledge-drop-zone${isDragging ? ' dragging' : ''}`}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={openEditor}
          role="button"
          tabIndex={0}
          aria-label="Upload knowledge file"
          onKeyDown={(e) => e.key === 'Enter' && openEditor()}
        >
          <div className="knowledge-drop-icon">
            <DocumentIcon />
          </div>
          <p className="knowledge-drop-headline">Drop files here</p>
          <p className="knowledge-drop-sub">or click to browse</p>
        </div>
      )}

      {hasFiles && (
        <>
          <button className="knowledge-add-btn" onClick={openEditor}>
            <PlusIcon />
            Add file
          </button>
          <div
            className={`knowledge-file-list${isDragging ? ' drop-target' : ''}`}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          >
            {files.map((f) => (
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
            ))}
          </div>
        </>
      )}

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
