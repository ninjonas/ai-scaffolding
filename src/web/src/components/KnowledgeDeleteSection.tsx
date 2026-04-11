interface DeleteSectionProps {
  showDeleteConfirm?: boolean;
  onDeleteClick?: () => void;
  onDeleteConfirm?: () => void;
  onDeleteCancel?: () => void;
}

export function DeleteSection({
  showDeleteConfirm,
  onDeleteClick,
  onDeleteConfirm,
  onDeleteCancel,
}: DeleteSectionProps) {
  if (!onDeleteClick) return null;
  return (
    <div className="knowledge-editor-delete-section">
      {showDeleteConfirm ? (
        <div className="knowledge-editor-delete-confirm">
          <p className="knowledge-editor-delete-warning">
            This file will no longer be available in chat.
          </p>
          <div className="knowledge-editor-delete-actions">
            <button className="knowledge-btn-cancel" onClick={onDeleteCancel}>
              Cancel
            </button>
            <button className="knowledge-btn-danger" onClick={onDeleteConfirm}>
              Delete
            </button>
          </div>
        </div>
      ) : (
        <button className="knowledge-editor-delete-btn" onClick={onDeleteClick}>
          Delete file
        </button>
      )}
    </div>
  );
}
