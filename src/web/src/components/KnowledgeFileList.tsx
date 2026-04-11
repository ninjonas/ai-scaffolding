import { type KnowledgeCatalogEntry } from '../api/knowledge';
import { KnowledgeFileRow, type UploadStatus } from './KnowledgeFileRow';
import { PlusIcon } from './KnowledgeIcons';

interface DeleteConfirm {
  id: string;
  name: string;
}

interface KnowledgeFileListProps {
  files: KnowledgeCatalogEntry[];
  isDragging: boolean;
  uploadStatus: UploadStatus;
  deleteConfirm: DeleteConfirm | null;
  cancelBtnRef: React.RefObject<HTMLButtonElement | null>;
  expandedTags: Record<string, boolean>;
  removingIds: Set<string>;
  addingIds: Set<string>;
  rowRef: (id: string) => (el: HTMLDivElement | null) => void;
  onUploadClick: () => void;
  onEdit: (id: string) => void;
  onDeleteRequest: (id: string, name: string) => void;
  onDeleteConfirm: () => void;
  onDeleteCancel: () => void;
  onToggleTags: (id: string) => void;
}

export function KnowledgeFileList({
  files,
  isDragging,
  uploadStatus,
  deleteConfirm,
  cancelBtnRef,
  expandedTags,
  removingIds,
  addingIds,
  rowRef,
  onUploadClick,
  onEdit,
  onDeleteRequest,
  onDeleteConfirm,
  onDeleteCancel,
  onToggleTags,
}: KnowledgeFileListProps) {
  return (
    <>
      <div className="knowledge-list-header">
        <button className="knowledge-add-btn" onClick={onUploadClick} aria-label="Upload a file">
          <PlusIcon /> Upload
        </button>
      </div>
      <div className={`knowledge-file-list${isDragging ? ' drop-target' : ''}`}>
        {files.map((f) => (
          <KnowledgeFileRow
            key={f.id}
            file={f}
            isRemoving={removingIds.has(f.id)}
            isAdding={addingIds.has(f.id)}
            uploadStatus={uploadStatus}
            deleteConfirm={deleteConfirm}
            cancelBtnRef={cancelBtnRef}
            tagsExpanded={expandedTags[f.id] ?? false}
            rowRef={rowRef(f.id)}
            onEdit={onEdit}
            onDeleteRequest={onDeleteRequest}
            onDeleteConfirm={onDeleteConfirm}
            onDeleteCancel={onDeleteCancel}
            onToggleTags={onToggleTags}
          />
        ))}
      </div>
    </>
  );
}
