import { useState, useEffect, useRef, useCallback } from 'react';
import { uploadKnowledgeFile, updateKnowledgeFile, getKnowledgeFile } from '../api/knowledge';

interface KnowledgeFileEditorProps {
  fileId?: string;
  scope: 'project' | 'conversation';
  conversationId?: string;
  onSave: () => void;
  onClose: () => void;
}

const MAX_FILE_SIZE = 500 * 1024;

export function KnowledgeFileEditor({
  fileId,
  scope: defaultScope,
  conversationId,
  onSave,
  onClose,
}: KnowledgeFileEditorProps) {
  const [filename, setFilename] = useState('');
  const [content, setContent] = useState('');
  const [scope, setScope] = useState<'project' | 'conversation'>(defaultScope);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(!!fileId);
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!fileId) return;
    getKnowledgeFile(fileId)
      .then((f) => {
        setFilename(f.name);
        setScope(f.scope as 'project' | 'conversation');
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load file'))
      .finally(() => setLoading(false));
  }, [fileId]);

  const trapFocus = useCallback((e: KeyboardEvent) => {
    if (e.key !== 'Tab' || !dialogRef.current) return;
    const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
      'button, input, textarea, select, [tabindex]:not([tabindex="-1"])',
    );
    if (focusable.length === 0) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }, []);

  useEffect(() => {
    document.addEventListener('keydown', trapFocus);
    return () => document.removeEventListener('keydown', trapFocus);
  }, [trapFocus]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > MAX_FILE_SIZE) {
      setError(`File exceeds 500KB limit (${Math.round(file.size / 1024)}KB)`);
      return;
    }
    setError('');
    if (!filename) setFilename(file.name);
    const reader = new FileReader();
    reader.onload = () => setContent(reader.result as string);
    reader.readAsText(file);
  };

  const handleSubmit = async () => {
    if (!filename.trim()) {
      setError('Filename is required');
      return;
    }
    if (!fileId && !content.trim()) {
      setError('Content is required');
      return;
    }
    setSaving(true);
    setError('');
    try {
      if (fileId) {
        await updateKnowledgeFile(fileId, {
          name: filename,
          ...(content ? { content } : {}),
        });
      } else {
        await uploadKnowledgeFile({
          filename,
          content,
          scope,
          ...(scope === 'conversation' && conversationId ? { conversationId } : {}),
        });
      }
      onSave();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="knowledge-editor-backdrop" onClick={onClose}>
      <div
        className="knowledge-editor-modal"
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label={fileId ? 'Edit knowledge file' : 'Upload knowledge file'}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="knowledge-editor-header">
          <h3>{fileId ? 'Edit file' : 'Upload file'}</h3>
          <button className="knowledge-close-btn" onClick={onClose} aria-label="Close">
            &times;
          </button>
        </div>
        {loading ? (
          <div className="knowledge-skeleton" />
        ) : (
          <>
            <label className="knowledge-field-label">
              Filename
              <input
                type="text"
                className="knowledge-input"
                value={filename}
                onChange={(e) => setFilename(e.target.value)}
                placeholder="example.md"
              />
            </label>
            {!fileId && (
              <label className="knowledge-field-label">
                Scope
                <select
                  className="knowledge-input"
                  value={scope}
                  onChange={(e) => setScope(e.target.value as 'project' | 'conversation')}
                >
                  <option value="project">Project</option>
                  {conversationId && <option value="conversation">Conversation</option>}
                </select>
              </label>
            )}
            <label className="knowledge-field-label">
              File
              <input
                type="file"
                accept=".md,.txt,.json,.yml"
                className="knowledge-input"
                onChange={handleFileSelect}
              />
            </label>
            <label className="knowledge-field-label">
              Content
              <textarea
                className="knowledge-textarea"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Paste content or select a file above"
                rows={8}
              />
            </label>
            {error && <div className="knowledge-error">{error}</div>}
            <button className="knowledge-submit-btn" onClick={handleSubmit} disabled={saving}>
              {saving ? 'Saving...' : 'Save'}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
