interface Toast {
  id: number;
  message: string;
  retry?: () => void;
}

interface KnowledgeToastListProps {
  toasts: Toast[];
}

export function KnowledgeToastList({ toasts }: KnowledgeToastListProps) {
  if (toasts.length === 0) return null;
  return (
    <div className="knowledge-toasts" aria-live="polite">
      {toasts.map((t) => (
        <div key={t.id} className="knowledge-toast">
          <span>{t.message}</span>
          {t.retry && (
            <button className="knowledge-toast-retry" onClick={t.retry}>
              Retry
            </button>
          )}
        </div>
      ))}
    </div>
  );
}
