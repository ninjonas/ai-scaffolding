interface KnowledgeUnsavedGuardProps {
  onDiscard: () => void;
  onKeep: () => void;
}

export function KnowledgeUnsavedGuard({ onDiscard, onKeep }: KnowledgeUnsavedGuardProps) {
  return (
    <div className="knowledge-editor-unsaved-guard" role="alert">
      <p>You have unsaved changes. Discard them?</p>
      <div className="knowledge-editor-unsaved-guard-actions">
        <button className="knowledge-btn-danger" onClick={onDiscard}>
          Discard changes
        </button>
        <button className="knowledge-btn-secondary" onClick={onKeep}>
          Keep editing
        </button>
      </div>
    </div>
  );
}
