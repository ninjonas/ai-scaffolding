import { useCallback, useEffect, useRef, useState } from 'react';
// doUploadRef breaks the self-reference cycle: the retry closure captures the ref,
// which is updated each render to point at the latest doUpload instance.
import { uploadKnowledgeFile, type KnowledgeCatalogEntry } from '../api/knowledge';

const ACCEPTED_EXTENSIONS = ['.md', '.txt', '.json', '.yml'];
const MAX_FILE_SIZE = 500 * 1024;

export interface UploadStatus {
  fileId: string | null;
  state: 'uploading' | 'success' | 'idle';
}

interface UseKnowledgeUploadOptions {
  tab: 'project' | 'conversation';
  conversationId?: string;
  onSuccess: (entry: KnowledgeCatalogEntry) => void;
  onToast: (message: string, retry?: () => void) => void;
}

export function validateUploadFile(file: File): string | null {
  const ext = '.' + (file.name.split('.').pop()?.toLowerCase() ?? '');
  if (!ACCEPTED_EXTENSIONS.includes(ext))
    return 'Unsupported file type. Accepted: .md, .txt, .json, .yml';
  if (file.size > MAX_FILE_SIZE) return 'File exceeds 500KB limit';
  return null;
}

export function useKnowledgeUpload({
  tab,
  conversationId,
  onSuccess,
  onToast,
}: UseKnowledgeUploadOptions) {
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>({ fileId: null, state: 'idle' });
  const [isDragging, setIsDragging] = useState(false);
  const dragCounterRef = useRef(0);
  const doUploadRef = useRef<(file: File) => Promise<void>>(async () => {});

  const doUpload = useCallback(
    async (file: File) => {
      const validationError = validateUploadFile(file);
      if (validationError) {
        onToast(validationError);
        return;
      }
      setUploadStatus({ fileId: `uploading-${Date.now()}`, state: 'uploading' });
      try {
        const uploaded = await uploadKnowledgeFile({
          filename: file.name,
          content: await file.text(),
          scope: tab,
          ...(tab === 'conversation' && conversationId ? { conversationId } : {}),
        });
        const entry: KnowledgeCatalogEntry = {
          id: uploaded.id,
          name: uploaded.name,
          description: uploaded.description,
          tags: uploaded.tags,
          fileType: uploaded.fileType,
          scope: uploaded.scope,
        };
        setUploadStatus({ fileId: uploaded.id, state: 'success' });
        setTimeout(() => setUploadStatus({ fileId: null, state: 'idle' }), 300);
        onSuccess(entry);
      } catch {
        setUploadStatus({ fileId: null, state: 'idle' });
        onToast('Upload failed. Try again.', () => doUploadRef.current(file));
      }
    },
    [tab, conversationId, onSuccess, onToast],
  );

  useEffect(() => {
    doUploadRef.current = doUpload;
  }, [doUpload]);

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

  const handleDragOver = (e: React.DragEvent) => e.preventDefault();

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    dragCounterRef.current = 0;
    setIsDragging(false);
    Array.from(e.dataTransfer.files).forEach((f) => doUpload(f));
  };

  return {
    uploadStatus,
    isDragging,
    doUpload,
    handleDragEnter,
    handleDragLeave,
    handleDragOver,
    handleDrop,
  };
}
