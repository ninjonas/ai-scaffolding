const MAX_TAGS_INLINE = 3;

interface FileTagsProps {
  tags: string[];
  fileId: string;
  expanded: boolean;
  onToggle: (id: string) => void;
}

export function FileTags({ tags, fileId, expanded, onToggle }: FileTagsProps) {
  const visible = expanded ? tags : tags.slice(0, MAX_TAGS_INLINE);
  const hidden = tags.length - MAX_TAGS_INLINE;
  return (
    <div className="knowledge-file-tags">
      {visible.map((t) => (
        <span key={t} className="knowledge-tag">
          {t}
        </span>
      ))}
      {!expanded && hidden > 0 && (
        <button
          className="knowledge-tag knowledge-tag-more"
          onClick={(e) => {
            e.stopPropagation();
            onToggle(fileId);
          }}
          aria-label={`Show ${hidden} more tags`}
        >
          +{hidden} more
        </button>
      )}
    </div>
  );
}
