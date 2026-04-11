import { type KnowledgeCatalogEntry } from '../api/knowledge';
import { TrashIcon, SpinnerIcon } from './KnowledgeIcons';
import { getFileIcon } from './knowledgeFileIcon';
import { KnowledgeFileRowMeta } from './KnowledgeFileRowMeta';

export interface UploadStatus {
  fileId: string | null;
  state: 'uploading' | 'success' | 'idle';
}

interface DeleteConfirm {
  id: string;
  name: string;
}

export interface KnowledgeFileRowProps {
  file: KnowledgeCatalogEntry;
  isRemoving: boolean;
  isAdding: boolean;
  uploadStatus: UploadStatus;
  deleteConfirm: DeleteConfirm | null;
  cancelBtnRef: React.RefObject<HTMLButtonElement | null>;
  tagsExpanded: boolean;
  rowRef: (el: HTMLDivElement | null) => void;
  onEdit: (id: string) => void;
  onDeleteRequest: (id: string, name: string) => void;
  onDeleteConfirm: () => void;
  onDeleteCancel: () => void;
  onToggleTags: (id: string) => void;
}

function rowClassName(isRemoving: boolean, isAdding: boolean, isSuccess: boolean) {
  return [
    'knowledge-file-row',
    isRemoving && 'removing',
    isAdding && 'adding',
    isSuccess && 'upload-success',
  ]
    .filter(Boolean)
    .join(' ');
}

interface RowActionsProps {
  file: KnowledgeCatalogEntry;
  isDeleting: boolean;
  isUploading: boolean;
  onDeleteRequest: (id: string, name: string) => void;
}

function RowActions({ file: f, isDeleting, isUploading, onDeleteRequest }: RowActionsProps) {
  return (
    <>
      {!isDeleting && (
        <button
          className="knowledge-delete-btn"
          onClick={(e) => {
            e.stopPropagation();
            onDeleteRequest(f.id, f.name);
          }}
          aria-label={`Delete ${f.name}`}
        >
          <TrashIcon />
        </button>
      )}
      {isUploading && (
        <span className="knowledge-upload-spinner" aria-label="Uploading">
          <SpinnerIcon />
        </span>
      )}
    </>
  );
}

export function KnowledgeFileRow({
  file: f,
  isRemoving,
  isAdding,
  uploadStatus,
  deleteConfirm,
  cancelBtnRef,
  tagsExpanded,
  rowRef,
  onEdit,
  onDeleteRequest,
  onDeleteConfirm,
  onDeleteCancel,
  onToggleTags,
}: KnowledgeFileRowProps) {
  const isSuccess = uploadStatus.fileId === f.id && uploadStatus.state === 'success';
  const isUploading = uploadStatus.fileId === f.id && uploadStatus.state === 'uploading';
  const isDeleting = deleteConfirm?.id === f.id;
  return (
    <div
      ref={rowRef}
      className={rowClassName(isRemoving, isAdding, isSuccess)}
      tabIndex={0}
      onClick={() => !isDeleting && onEdit(f.id)}
      onKeyDown={(e) => e.key === 'Enter' && !isDeleting && onEdit(f.id)}
      aria-label={`Edit ${f.name}`}
    >
      <div className="knowledge-file-icon">{getFileIcon(f.fileType)}</div>
      <KnowledgeFileRowMeta
        file={f}
        isSuccess={isSuccess}
        isDeleting={isDeleting}
        tagsExpanded={tagsExpanded}
        cancelBtnRef={cancelBtnRef}
        onDeleteConfirm={onDeleteConfirm}
        onDeleteCancel={onDeleteCancel}
        onToggleTags={onToggleTags}
      />
      <RowActions
        file={f}
        isDeleting={isDeleting}
        isUploading={isUploading}
        onDeleteRequest={onDeleteRequest}
      />
    </div>
  );
}
