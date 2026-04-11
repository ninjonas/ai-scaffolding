import { DocumentIcon, PlusIcon } from './KnowledgeIcons';

interface KnowledgeEmptyStateProps {
  tab: 'project' | 'conversation';
  isDragging: boolean;
  onUploadClick: () => void;
}

export function KnowledgeEmptyState({ tab, isDragging, onUploadClick }: KnowledgeEmptyStateProps) {
  return (
    <div className={`knowledge-drop-zone${isDragging ? ' dragging' : ''}`}>
      <div className="knowledge-drop-icon">
        <DocumentIcon />
      </div>
      {tab === 'project' ? (
        <>
          <p className="knowledge-drop-headline">No project files yet</p>
          <p className="knowledge-drop-sub">
            Upload a document to give the assistant persistent context across conversations.
          </p>
          <button className="knowledge-add-btn" onClick={onUploadClick} aria-label="Upload a file">
            <PlusIcon />
            Upload
          </button>
        </>
      ) : (
        <>
          <p className="knowledge-drop-headline">No files attached to this conversation</p>
          <p className="knowledge-drop-sub">
            Upload or drag a file here, or use @ in the chat input.
          </p>
        </>
      )}
    </div>
  );
}
