import { useRef } from 'react';
import type { KnowledgeCatalogEntry } from '../api/knowledge';
import { DocumentIcon } from './ChatInputIcons';

interface KnowledgeMentionDropdownProps {
  items: KnowledgeCatalogEntry[];
  highlightedIndex: number;
  onSelect: (entry: KnowledgeCatalogEntry) => void;
  onHighlight: (index: number) => void;
  loading: boolean;
  listboxId: string;
}

const dropdownStyle = {
  position: 'absolute' as const,
  bottom: '100%',
  left: 32,
  right: 32,
  marginBottom: 4,
  background: 'var(--surface)',
  border: '1px solid var(--border)',
  borderRadius: 10,
  padding: '4px 0',
  listStyle: 'none',
  margin: 0,
  zIndex: 100,
  maxHeight: 280,
  overflowY: 'auto' as const,
  animation: 'mentionFadeIn 150ms ease',
  boxShadow: '0 8px 24px rgba(0,0,0,0.3)',
};

interface DropdownItemProps {
  entry: KnowledgeCatalogEntry;
  index: number;
  highlighted: boolean;
  onSelect: (entry: KnowledgeCatalogEntry) => void;
  onHighlight: (index: number) => void;
}

function DropdownItem({ entry, index, highlighted, onSelect, onHighlight }: DropdownItemProps) {
  return (
    <li
      id={`mention-option-${index}`}
      role="option"
      aria-selected={highlighted}
      onMouseDown={(e) => {
        e.preventDefault();
        onSelect(entry);
      }}
      onMouseEnter={() => onHighlight(index)}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '8px 14px',
        cursor: 'pointer',
        background: highlighted ? 'rgba(167,139,250,0.12)' : 'transparent',
        fontSize: 13,
      }}
    >
      <span style={{ color: 'var(--text)', opacity: 0.7, flexShrink: 0 }}>
        <DocumentIcon />
      </span>
      <span
        style={{
          flex: 1,
          color: 'var(--text-h)',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
      >
        {entry.name}
      </span>
      <span
        style={{
          fontSize: 11,
          padding: '2px 6px',
          borderRadius: 4,
          background: 'rgba(167,139,250,0.15)',
          color: 'var(--accent)',
          flexShrink: 0,
        }}
      >
        {entry.scope}
      </span>
    </li>
  );
}

export function KnowledgeMentionDropdown({
  items,
  highlightedIndex,
  onSelect,
  onHighlight,
  loading,
  listboxId,
}: KnowledgeMentionDropdownProps) {
  const dropdownRef = useRef<HTMLUListElement>(null);

  return (
    <ul
      ref={dropdownRef}
      id={listboxId}
      role="listbox"
      aria-label="Knowledge files"
      className="mention-dropdown"
      style={dropdownStyle}
    >
      {loading && (
        <li style={{ padding: '10px 14px', color: 'var(--text)', opacity: 0.6, fontSize: 13 }}>
          Loading...
        </li>
      )}
      {!loading && items.length === 0 && (
        <li style={{ padding: '10px 14px', color: 'var(--text)', opacity: 0.6, fontSize: 13 }}>
          No matching files
        </li>
      )}
      {!loading &&
        items.map((entry, i) => (
          <DropdownItem
            key={entry.id}
            entry={entry}
            index={i}
            highlighted={i === highlightedIndex}
            onSelect={onSelect}
            onHighlight={onHighlight}
          />
        ))}
    </ul>
  );
}
