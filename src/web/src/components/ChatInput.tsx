import { useEffect, useRef, useState, type KeyboardEvent } from 'react';
import { BookIcon, PaperclipIcon, SendArrowIcon } from './ChatInputIcons';
import { KnowledgeMentionDropdown } from './KnowledgeMentionDropdown';
import { MentionHighlight } from './MentionHighlight';
import { useMentionState } from './useMentionState';

export interface AttachedImage {
  dataUrl: string;
  filename: string;
}

interface ChatInputProps {
  onSend: (
    message: string,
    images: AttachedImage[],
    knowledgeFiles: { id: string; name: string }[],
  ) => void;
  disabled: boolean;
  onToggleKnowledge?: () => void;
  knowledgeOpen?: boolean;
  conversationId?: string;
}

const MAX_IMAGE_SIZE = 10 * 1024 * 1024;
const LISTBOX_ID = 'mention-listbox';

export function ChatInput({
  onSend,
  disabled,
  onToggleKnowledge,
  knowledgeOpen,
  conversationId,
}: ChatInputProps) {
  const [images, setImages] = useState<AttachedImage[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const mention = useMentionState({ conversationId, textareaRef });

  useEffect(() => {
    if (!disabled) textareaRef.current?.focus();
  }, [disabled]);

  const handleSend = () => {
    const trimmed = mention.message.trim();
    if (!trimmed) return;
    onSend(
      trimmed,
      images,
      mention.attachedFiles.map((f) => ({ id: f.id, name: f.name })),
    );
    mention.setMessage('');
    setImages([]);
    mention.resetMention();
  };

  const handleRemoveMention = (id: string) => {
    const file = mention.attachedFiles.find((f) => f.id === id);
    if (file) mention.removeMentionFromText(file.name);
    mention.setAttachedFiles((prev) => prev.filter((f) => f.id !== id));
    textareaRef.current?.focus();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (mention.handleMentionKeyDown(e)) return;
    if (mention.handleDropdownKeyDown(e)) return;
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;
    Array.from(files).forEach((file) => {
      if (file.size > MAX_IMAGE_SIZE) return;
      const reader = new FileReader();
      reader.onload = () =>
        setImages((prev) => [...prev, { dataUrl: reader.result as string, filename: file.name }]);
      reader.readAsDataURL(file);
    });
  };

  const activeDescendant =
    mention.dropdownVisible && mention.filteredCatalog.length > 0
      ? `mention-option-${mention.highlightedIndex}`
      : undefined;

  return (
    <div className="chat-input-container" style={{ position: 'relative' }}>
      {mention.dropdownVisible && (
        <KnowledgeMentionDropdown
          items={mention.filteredCatalog}
          highlightedIndex={mention.highlightedIndex}
          onSelect={(entry) => mention.selectFile(entry, mention.message)}
          onHighlight={mention.setHighlightedIndex}
          loading={mention.catalogLoading}
          listboxId={LISTBOX_ID}
        />
      )}

      {images.length > 0 && (
        <div className="attachments-preview">
          {images.map((img, i) => (
            <div key={i} className="image-preview">
              <img src={img.dataUrl} alt={img.filename} />
              <button
                aria-label="Remove image"
                onClick={() => setImages((p) => p.filter((_, j) => j !== i))}
              >
                &times;
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="chat-input-row">
        {onToggleKnowledge && (
          <button
            className={`attach-btn${knowledgeOpen ? ' active' : ''}`}
            type="button"
            onClick={onToggleKnowledge}
            disabled={disabled}
            title="Toggle knowledge sidebar"
            aria-label="Toggle knowledge sidebar"
            aria-pressed={knowledgeOpen}
          >
            <BookIcon />
          </button>
        )}
        <button
          className="attach-btn"
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
          title="Attach image"
          aria-label="Attach image"
        >
          <PaperclipIcon />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          multiple
          hidden
          onChange={handleImageUpload}
        />
        <div className="textarea-wrapper">
          {mention.attachedFiles.length > 0 && (
            <div className="mention-overlay">
              <MentionHighlight
                message={mention.message}
                attachedFiles={mention.attachedFiles}
                onRemove={handleRemoveMention}
              />
            </div>
          )}
          <textarea
            ref={textareaRef}
            className={mention.attachedFiles.length > 0 ? 'has-mentions' : ''}
            value={mention.message}
            onChange={mention.handleTextChange}
            onKeyDown={handleKeyDown}
            placeholder="Type a message... (@ to mention a knowledge file)"
            disabled={disabled}
            rows={1}
            aria-label="Message"
            role="combobox"
            aria-expanded={mention.dropdownVisible}
            aria-controls={mention.dropdownVisible ? LISTBOX_ID : undefined}
            aria-activedescendant={activeDescendant}
            aria-autocomplete="list"
          />
        </div>
        <button
          className="send-btn"
          type="button"
          onClick={handleSend}
          disabled={disabled || !mention.message.trim()}
          aria-label="Send message"
        >
          <SendArrowIcon />
        </button>
      </div>
    </div>
  );
}
