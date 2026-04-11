import { useState, useEffect, useCallback, useRef } from 'react';
import {
  listKnowledgeFiles,
  deleteKnowledgeFile,
  type KnowledgeCatalogEntry,
} from '../api/knowledge';
import { KnowledgeFileEditor } from './KnowledgeFileEditor';
import { KnowledgeFileList } from './KnowledgeFileList';
import { KnowledgeEmptyState } from './KnowledgeEmptyState';
import { KnowledgeScopeTabBar } from './KnowledgeScopeTabBar';
import { KnowledgeToastList } from './KnowledgeToastList';
import { useKnowledgeUpload } from './useKnowledgeUpload';
import { useKnowledgeDelete } from './useKnowledgeDelete';
import { CloseIcon } from './KnowledgeIcons';

const ACCEPTED_TYPES = '.md,.txt,.json,.yml';
type Scope = 'project' | 'conversation';
type Toast = { id: number; message: string; retry?: () => void };
interface KnowledgeSidebarProps {
  conversationId?: string;
  onClose: () => void;
}

export function KnowledgeSidebar({ conversationId, onClose }: KnowledgeSidebarProps) {
  const [tab, setTab] = useState<Scope>('project');
  const [files, setFiles] = useState<KnowledgeCatalogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [editFileId, setEditFileId] = useState<string | null>(null);
  const [showEditor, setShowEditor] = useState(false);
  const [expandedTags, setExpandedTags] = useState<Record<string, boolean>>({});
  const [addingIds, setAddingIds] = useState<Set<string>>(new Set());
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cancelBtnRef = useRef<HTMLButtonElement>(null);
  const toastCounterRef = useRef(0);

  const addToast = useCallback((message: string, retry?: () => void) => {
    const id = ++toastCounterRef.current;
    setToasts((prev) => [...prev, { id, message, retry }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), retry ? 5000 : 4000);
  }, []);

  const fetchFiles = useCallback(async () => {
    setLoading(true);
    try {
      const result = await listKnowledgeFiles(
        tab,
        tab === 'conversation' ? conversationId : undefined,
      );
      setFiles(result);
    } catch {
      addToast('Failed to load files.');
    } finally {
      setLoading(false);
    }
  }, [tab, conversationId, addToast]);

  useEffect(() => {
    fetchFiles();
  }, [fetchFiles]);

  const handleUploadSuccess = useCallback((entry: KnowledgeCatalogEntry) => {
    setFiles((prev) => [...prev, entry]);
    setAddingIds((prev) => new Set(prev).add(entry.id));
    setTimeout(
      () =>
        setAddingIds((prev) => {
          const n = new Set(prev);
          n.delete(entry.id);
          return n;
        }),
      400,
    );
  }, []);

  const {
    uploadStatus,
    isDragging,
    doUpload,
    handleDragEnter,
    handleDragLeave,
    handleDragOver,
    handleDrop,
  } = useKnowledgeUpload({
    tab,
    conversationId,
    onSuccess: handleUploadSuccess,
    onRefresh: fetchFiles,
    onToast: addToast,
  });

  const {
    deleteConfirm,
    removingIds,
    fileRowRefs,
    handleDeleteRequest,
    handleDeleteConfirm,
    handleDeleteCancel,
  } = useKnowledgeDelete({ files, cancelBtnRef, onFilesChange: setFiles, onToast: addToast });

  const handleSaveFromEditor = (newEntry?: KnowledgeCatalogEntry) => {
    setShowEditor(false);
    if (newEntry)
      setFiles((prev) => prev.map((f) => (f.id === newEntry.id ? { ...f, ...newEntry } : f)));
    else fetchFiles();
  };

  const rowRef = (id: string) => (el: HTMLDivElement | null) => {
    if (el) fileRowRefs.current.set(id, el);
    else fileRowRefs.current.delete(id);
  };

  return (
    <aside
      className="knowledge-sidebar"
      role="complementary"
      aria-label="Knowledge base"
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      <div className="knowledge-sidebar-header">
        <h2>Knowledge</h2>
        <button className="knowledge-close-btn" onClick={onClose} aria-label="Close sidebar">
          <CloseIcon />
        </button>
      </div>
      <KnowledgeScopeTabBar tab={tab} conversationId={conversationId} onTabChange={setTab} />
      <KnowledgeToastList toasts={toasts} />
      {loading && (
        <div className="knowledge-file-list">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="knowledge-skeleton" />
          ))}
        </div>
      )}
      {!loading && files.length === 0 && (
        <KnowledgeEmptyState
          tab={tab}
          isDragging={isDragging}
          onUploadClick={() => fileInputRef.current?.click()}
        />
      )}
      {!loading && files.length > 0 && (
        <KnowledgeFileList
          files={files}
          isDragging={isDragging}
          uploadStatus={uploadStatus}
          deleteConfirm={deleteConfirm}
          cancelBtnRef={cancelBtnRef}
          expandedTags={expandedTags}
          removingIds={removingIds}
          addingIds={addingIds}
          rowRef={rowRef}
          onUploadClick={() => fileInputRef.current?.click()}
          onEdit={(id) => {
            setEditFileId(id);
            setShowEditor(true);
          }}
          onDeleteRequest={handleDeleteRequest}
          onDeleteConfirm={handleDeleteConfirm}
          onDeleteCancel={handleDeleteCancel}
          onToggleTags={(id) => setExpandedTags((prev) => ({ ...prev, [id]: !prev[id] }))}
        />
      )}
      <input
        ref={fileInputRef}
        type="file"
        accept={ACCEPTED_TYPES}
        style={{ display: 'none' }}
        aria-hidden="true"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) doUpload(file);
          e.target.value = '';
        }}
      />
      {showEditor && editFileId && (
        <KnowledgeFileEditor
          fileId={editFileId}
          scope={tab}
          conversationId={conversationId}
          onSave={handleSaveFromEditor}
          onClose={() => setShowEditor(false)}
          onDelete={async (id) => {
            try {
              await deleteKnowledgeFile(id);
              setFiles((prev) => prev.filter((f) => f.id !== id));
              setShowEditor(false);
            } catch {
              addToast('Delete failed. Try again.');
            }
          }}
        />
      )}
    </aside>
  );
}
