import { useState, useEffect, useRef, useCallback } from 'react';
import {
  updateKnowledgeFile,
  getKnowledgeFile,
  type KnowledgeCatalogEntry,
} from '../api/knowledge';
import { CloseIcon } from './KnowledgeIcons';
import { EditorForm } from './KnowledgeEditorForm';
import { KnowledgeUnsavedGuard } from './KnowledgeUnsavedGuard';
import { toCatalogEntry } from './knowledgeEditorHelpers';

interface KnowledgeFileEditorProps {
  fileId: string;
  scope: 'project' | 'conversation';
  conversationId?: string;
  onSave: (entry?: KnowledgeCatalogEntry) => void;
  onClose: () => void;
}

export function KnowledgeFileEditor({ fileId, onSave, onClose }: KnowledgeFileEditorProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [content, setContent] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [dirty, setDirty] = useState(false);
  const [showUnsavedGuard, setShowUnsavedGuard] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const firstFocusRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setLoading(true);
    getKnowledgeFile(fileId)
      .then((f) => {
        setName(f.name);
        setDescription(f.description ?? '');
        setTags(f.tags ?? []);
        setContent('');
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load file'))
      .finally(() => {
        setLoading(false);
        requestAnimationFrame(() => firstFocusRef.current?.focus());
      });
  }, [fileId]);

  const guardClose = useCallback(() => {
    if (dirty) {
      setShowUnsavedGuard(true);
      return;
    }
    onClose();
  }, [dirty, onClose]);

  const trapFocus = useCallback(
    (e: KeyboardEvent) => {
      if (!panelRef.current) return;
      if (e.key === 'Escape') {
        guardClose();
        return;
      }
      if (e.key !== 'Tab') return;
      const focusable = panelRef.current.querySelectorAll<HTMLElement>(
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
    },
    [guardClose],
  );

  useEffect(() => {
    const panel = panelRef.current;
    if (!panel) return;
    panel.addEventListener('keydown', trapFocus);
    return () => panel.removeEventListener('keydown', trapFocus);
  }, [trapFocus]);

  const mark = () => setDirty(true);

  const handleAddTag = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== 'Enter') return;
    e.preventDefault();
    const trimmed = tagInput.trim();
    if (trimmed && !tags.includes(trimmed)) {
      setTags((p) => [...p, trimmed]);
      mark();
    }
    setTagInput('');
  };

  const handleSubmit = async () => {
    if (!name.trim()) {
      setError('Name is required');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const updated = await updateKnowledgeFile(fileId, {
        name,
        description,
        tags,
        ...(content ? { content } : {}),
      });
      setDirty(false);
      onSave(toCatalogEntry(updated));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="knowledge-editor-backdrop" onClick={guardClose}>
      <div
        className="knowledge-editor-panel"
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label="Edit knowledge file"
        onClick={(e) => e.stopPropagation()}
        tabIndex={-1}
      >
        {showUnsavedGuard && (
          <KnowledgeUnsavedGuard
            onDiscard={() => {
              setShowUnsavedGuard(false);
              onClose();
            }}
            onKeep={() => setShowUnsavedGuard(false)}
          />
        )}
        <div className="knowledge-editor-header">
          <h3>Edit file</h3>
          <button className="knowledge-close-btn" onClick={guardClose} aria-label="Close editor">
            <CloseIcon />
          </button>
        </div>

        {loading ? (
          <div className="knowledge-editor-skeleton">
            {[36, 36, 80, 120].map((h, i) => (
              <div key={i} className="knowledge-skeleton" style={{ height: h }} />
            ))}
          </div>
        ) : (
          <EditorForm
            nameRef={firstFocusRef}
            name={name}
            description={description}
            tags={tags}
            tagInput={tagInput}
            content={content}
            saving={saving}
            error={error}
            onNameChange={(v) => {
              setName(v);
              mark();
            }}
            onDescriptionChange={(v) => {
              setDescription(v);
              mark();
            }}
            onTagInputChange={setTagInput}
            onAddTag={handleAddTag}
            onRemoveTag={(tag) => {
              setTags((p) => p.filter((t) => t !== tag));
              mark();
            }}
            onContentChange={(v) => {
              setContent(v);
              mark();
            }}
            onSubmit={handleSubmit}
          />
        )}
      </div>
    </div>
  );
}
