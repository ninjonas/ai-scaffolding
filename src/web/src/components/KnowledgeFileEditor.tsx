import { useState, useEffect, useRef, useCallback } from 'react';
import { useFocusTrap } from './useFocusTrap';
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
  onDelete?: (id: string) => void;
}

export function KnowledgeFileEditor({
  fileId,
  onSave,
  onClose,
  onDelete,
}: KnowledgeFileEditorProps) {
  const [filename, setFilename] = useState('');
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
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const firstFocusRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setLoading(true);
    getKnowledgeFile(fileId)
      .then((f) => {
        setFilename(f.filename ?? '');
        setName(f.name);
        setDescription(f.description ?? '');
        setTags(f.tags ?? []);
        setContent(f.content ?? '');
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

  const panelRef = useFocusTrap(guardClose);

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

        <div className="knowledge-editor-body">
          {loading ? (
            <div className="knowledge-editor-skeleton">
              {[36, 36, 80, 120].map((h, i) => (
                <div key={i} className="knowledge-skeleton" style={{ height: h }} />
              ))}
            </div>
          ) : (
            <EditorForm
              nameRef={firstFocusRef}
              filename={filename}
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
              onSubmit={handleSubmit}
              showDeleteConfirm={showDeleteConfirm}
              onDeleteClick={onDelete ? () => setShowDeleteConfirm(true) : undefined}
              onDeleteConfirm={() => {
                setShowDeleteConfirm(false);
                onDelete?.(fileId);
                onClose();
              }}
              onDeleteCancel={() => setShowDeleteConfirm(false)}
            />
          )}
        </div>
      </div>
    </div>
  );
}
