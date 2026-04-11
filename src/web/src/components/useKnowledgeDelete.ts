import { useRef, useState } from 'react';
import { deleteKnowledgeFile, type KnowledgeCatalogEntry } from '../api/knowledge';

interface DeleteConfirm {
  id: string;
  name: string;
}

interface UseKnowledgeDeleteOptions {
  files: KnowledgeCatalogEntry[];
  cancelBtnRef: React.RefObject<HTMLButtonElement | null>;
  onFilesChange: (updater: (prev: KnowledgeCatalogEntry[]) => KnowledgeCatalogEntry[]) => void;
  onToast: (message: string) => void;
}

export function useKnowledgeDelete({
  files,
  cancelBtnRef,
  onFilesChange,
  onToast,
}: UseKnowledgeDeleteOptions) {
  const [deleteConfirm, setDeleteConfirm] = useState<DeleteConfirm | null>(null);
  const [removingIds, setRemovingIds] = useState<Set<string>>(new Set());
  const nextFocusRef = useRef<string | null>(null);
  const fileRowRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  const handleDeleteRequest = (id: string, name: string) => {
    const idx = files.findIndex((f) => f.id === id);
    nextFocusRef.current = files[idx + 1]?.id ?? files[idx - 1]?.id ?? null;
    setDeleteConfirm({ id, name });
    requestAnimationFrame(() => cancelBtnRef.current?.focus());
  };

  const handleDeleteConfirm = async () => {
    if (!deleteConfirm) return;
    const { id } = deleteConfirm;
    setDeleteConfirm(null);
    setRemovingIds((prev) => new Set(prev).add(id));
    try {
      await deleteKnowledgeFile(id);
      onFilesChange((prev) => prev.filter((f) => f.id !== id));
    } catch {
      onToast('Delete failed. Try again.');
    } finally {
      const nextId = nextFocusRef.current;
      setTimeout(() => {
        setRemovingIds((prev) => {
          const n = new Set(prev);
          n.delete(id);
          return n;
        });
        if (nextId) requestAnimationFrame(() => fileRowRefs.current.get(nextId)?.focus());
      }, 150);
    }
  };

  return {
    deleteConfirm,
    removingIds,
    fileRowRefs,
    handleDeleteRequest,
    handleDeleteConfirm,
    handleDeleteCancel: () => setDeleteConfirm(null),
  };
}
