interface KnowledgeDeleteConfirmProps {
  fileId: string;
  fileName: string;
  cancelBtnRef: React.RefObject<HTMLButtonElement | null>;
  onConfirm: () => void;
  onCancel: () => void;
}

export function KnowledgeDeleteConfirm({
  fileId,
  fileName,
  cancelBtnRef,
  onConfirm,
  onCancel,
}: KnowledgeDeleteConfirmProps) {
  return (
    <div
      className="knowledge-delete-confirm"
      role="alertdialog"
      aria-describedby={`delete-desc-${fileId}`}
      onClick={(e) => e.stopPropagation()}
    >
      <span id={`delete-desc-${fileId}`}>Delete {fileName}?</span>
      <div className="knowledge-delete-confirm-actions">
        <button
          ref={cancelBtnRef}
          className="knowledge-btn-cancel"
          onClick={(e) => {
            e.stopPropagation();
            onCancel();
          }}
        >
          Cancel
        </button>
        <button
          className="knowledge-btn-danger"
          onClick={(e) => {
            e.stopPropagation();
            onConfirm();
          }}
        >
          Delete
        </button>
      </div>
    </div>
  );
}
