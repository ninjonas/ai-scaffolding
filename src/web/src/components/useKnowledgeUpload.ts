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
  onRefresh?: () => void;
  onToast: (message: string, retry?: () => void) => void;
}

export function validateUploadFile(file: File): string | null {
  const ext = '.' + (file.name.split('.').pop()?.toLowerCase() ?? '');
  if (!ACCEPTED_EXTENSIONS.includes(ext))
    return 'Unsupported file type. Accepted: .md, .txt, .json, .yml';
  if (file.size > MAX_FILE_SIZE) return 'File exceeds 500KB limit';
  return null;
}

async function performUpload(
  file: File,
  tab: 'project' | 'conversation',
  conversationId: string | undefined,
): Promise<KnowledgeCatalogEntry> {
  const uploaded = await uploadKnowledgeFile({
    filename: file.name,
    content: await file.text(),
    scope: tab,
    ...(tab === 'conversation' && conversationId ? { conversationId } : {}),
  });
  return {
    id: uploaded.id,
    name: uploaded.name,
    description: uploaded.description,
    tags: uploaded.tags,
    fileType: uploaded.fileType,
    scope: uploaded.scope,
    enriched: false,
  };
}

function useUploadRefs(onRefresh: (() => void) | undefined) {
  const doUploadRef = useRef<(file: File) => Promise<void>>(async () => {});
  const onRefreshRef = useRef(onRefresh);
  const refreshTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    onRefreshRef.current = onRefresh;
  }, [onRefresh]);
  useEffect(
    () => () => {
      if (refreshTimerRef.current !== null) clearTimeout(refreshTimerRef.current);
    },
    [],
  );
  return { doUploadRef, onRefreshRef, refreshTimerRef };
}

function useDragHandlers(onFiles: (files: File[]) => void) {
  const [isDragging, setIsDragging] = useState(false);
  const dragCounterRef = useRef(0);

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
    onFiles(Array.from(e.dataTransfer.files));
  };

  return { isDragging, handleDragEnter, handleDragLeave, handleDragOver, handleDrop };
}

export function useKnowledgeUpload({
  tab,
  conversationId,
  onSuccess,
  onRefresh,
  onToast,
}: UseKnowledgeUploadOptions) {
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>({ fileId: null, state: 'idle' });
  const { doUploadRef, onRefreshRef, refreshTimerRef } = useUploadRefs(onRefresh);

  const doUpload = useCallback(
    async (file: File) => {
      const validationError = validateUploadFile(file);
      if (validationError) {
        onToast(validationError);
        return;
      }
      setUploadStatus({ fileId: `uploading-${Date.now()}`, state: 'uploading' });
      try {
        const entry = await performUpload(file, tab, conversationId);
        setUploadStatus({ fileId: entry.id, state: 'success' });
        setTimeout(() => setUploadStatus({ fileId: null, state: 'idle' }), 300);
        onSuccess(entry);
        if (onRefreshRef.current) {
          refreshTimerRef.current = setTimeout(() => {
            refreshTimerRef.current = null;
            onRefreshRef.current?.();
          }, 3000);
        }
      } catch {
        setUploadStatus({ fileId: null, state: 'idle' });
        onToast('Upload failed. Try again.', () => doUploadRef.current(file));
      }
    },
    [tab, conversationId, onSuccess, onToast, doUploadRef, onRefreshRef, refreshTimerRef],
  );

  useEffect(() => {
    doUploadRef.current = doUpload;
  }, [doUpload, doUploadRef]);

  const drag = useDragHandlers((files) => files.forEach((f) => doUpload(f)));

  return { uploadStatus, doUpload, ...drag };
}
