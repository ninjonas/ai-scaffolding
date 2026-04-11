import { type KnowledgeCatalogEntry } from '../api/knowledge';
import { CheckIcon } from './KnowledgeIcons';
import { FileTags } from './KnowledgeFileTags';
import { KnowledgeDeleteConfirm } from './KnowledgeDeleteConfirm';

interface KnowledgeFileRowMetaProps {
  file: KnowledgeCatalogEntry;
  isSuccess: boolean;
  isDeleting: boolean;
  tagsExpanded: boolean;
  cancelBtnRef: React.RefObject<HTMLButtonElement | null>;
  onDeleteConfirm: () => void;
  onDeleteCancel: () => void;
  onToggleTags: (id: string) => void;
}

export function KnowledgeFileRowMeta({
  file: f,
  isSuccess,
  isDeleting,
  tagsExpanded,
  cancelBtnRef,
  onDeleteConfirm,
  onDeleteCancel,
  onToggleTags,
}: KnowledgeFileRowMetaProps) {
  return (
    <div className="knowledge-file-info">
      <div className="knowledge-file-name">
        {f.name}
        {isSuccess && (
          <span className="knowledge-upload-check" aria-label="Upload successful">
            <CheckIcon />
          </span>
        )}
      </div>
      {f.description && <div className="knowledge-file-desc">{f.description}</div>}
      {f.scope === 'conversation' && (
        <div className="knowledge-file-linked">Linked to this conversation.</div>
      )}
      {f.tags.length > 0 && (
        <FileTags tags={f.tags} fileId={f.id} expanded={tagsExpanded} onToggle={onToggleTags} />
      )}
      {isDeleting && (
        <KnowledgeDeleteConfirm
          fileId={f.id}
          fileName={f.name}
          cancelBtnRef={cancelBtnRef}
          onConfirm={onDeleteConfirm}
          onCancel={onDeleteCancel}
        />
      )}
    </div>
  );
}
