import type { KnowledgeCatalogEntry } from '../api/knowledge';
import { XCircleIcon } from './ChatInputIcons';
import { findEarliestMention } from './mentionUtils';

interface MentionHighlightProps {
  message: string;
  attachedFiles: KnowledgeCatalogEntry[];
  onRemove?: (id: string) => void;
}

function MentionPill(props: {
  text: string;
  fullName: string;
  id: string;
  onRemove?: (id: string) => void;
  k: number;
}) {
  return (
    <span key={props.k} className="mention-pill" title={props.fullName}>
      {props.text}
      {props.onRemove && (
        <button
          className="mention-pill-remove"
          onClick={() => props.onRemove!(props.id)}
          aria-label={`Remove ${props.fullName}`}
          type="button"
        >
          <XCircleIcon />
        </button>
      )}
    </span>
  );
}

export function MentionHighlight({ message, attachedFiles, onRemove }: MentionHighlightProps) {
  if (attachedFiles.length === 0) return <span>{message}</span>;
  const parts: React.ReactNode[] = [];
  let remaining = message;
  let key = 0;
  while (remaining.length > 0) {
    const match = findEarliestMention(remaining, attachedFiles);
    if (!match) {
      parts.push(
        <span key={key} className="mention-text-plain">
          {remaining}
        </span>,
      );
      break;
    }
    if (match.index > 0) {
      parts.push(
        <span key={key++} className="mention-text-plain">
          {remaining.slice(0, match.index)}
        </span>,
      );
    }
    parts.push(
      <MentionPill
        key={key++}
        k={key}
        text={match.text}
        fullName={match.file.name}
        id={match.file.id}
        onRemove={onRemove}
      />,
    );
    remaining = remaining.slice(match.index + match.text.length);
  }
  return <>{parts}</>;
}
