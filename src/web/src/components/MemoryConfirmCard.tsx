import { type MemoryConfirmInterrupt } from '../api/chat';

interface MemoryConfirmCardProps {
  interrupt: MemoryConfirmInterrupt;
  onResume: (approved: boolean) => Promise<void>;
  disabled?: boolean;
}

function ResultPreview({ result }: { result: MemoryConfirmInterrupt['results'][number] }) {
  const date = new Date(result.createdAt).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
  const excerpt =
    result.excerpt.length > 120 ? result.excerpt.slice(0, 120) + '\u2026' : result.excerpt;

  return (
    <div className="memory-result">
      <div className="memory-result-date">{date}</div>
      <div className="memory-result-excerpt">{excerpt}</div>
    </div>
  );
}

export function MemoryConfirmCard({ interrupt, onResume, disabled }: MemoryConfirmCardProps) {
  const previews = interrupt.results.slice(0, 3);

  return (
    <div className="memory-confirm-card">
      <div className="memory-confirm-heading">I found relevant context from past conversations</div>
      {previews.length > 0 && (
        <div className="memory-confirm-results">
          {previews.map((r, i) => (
            <ResultPreview key={i} result={r} />
          ))}
        </div>
      )}
      <div className="memory-confirm-actions">
        <button
          className="memory-confirm-btn memory-confirm-btn--primary"
          onClick={() => onResume(true)}
          disabled={disabled}
        >
          Use context
        </button>
        <button
          className="memory-confirm-btn memory-confirm-btn--ghost"
          onClick={() => onResume(false)}
          disabled={disabled}
        >
          Skip
        </button>
      </div>
    </div>
  );
}
