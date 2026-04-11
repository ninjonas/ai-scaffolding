import { useRef, useState, type KeyboardEvent } from 'react';
import { BookIcon, PaperclipIcon, SendArrowIcon } from './ChatInputIcons';
import { KnowledgeMentionDropdown } from './KnowledgeMentionDropdown';
import { KnowledgeChipsBar } from './KnowledgeChipsBar';
import { useMentionState } from './useMentionState';

interface KnowledgeChip {
  id: string;
  name: string;
}

export interface AttachedImage {
  dataUrl: string;
  filename: string;
}

interface ChatInputProps {
  onSend: (message: string, images: AttachedImage[], knowledgeFiles: KnowledgeChip[]) => void;
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

  const {
    message,
    setMessage,
    attachedFiles,
    setAttachedFiles,
    filteredCatalog,
    catalogLoading,
    highlightedIndex,
    setHighlightedIndex,
    dropdownVisible,
    selectFile,
    handleTextChange,
    handleDropdownKeyDown,
    resetMention,
  } = useMentionState({ conversationId, textareaRef });

  const handleSend = () => {
    const trimmed = message.trim();
    if (!trimmed) return;
    onSend(
      trimmed,
      images,
      attachedFiles.map((f) => ({ id: f.id, name: f.name })),
    );
    setMessage('');
    setImages([]);
    resetMention();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (handleDropdownKeyDown(e)) return;
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
    dropdownVisible && filteredCatalog.length > 0
      ? `mention-option-${highlightedIndex}`
      : undefined;

  return (
    <div className="chat-input-container" style={{ position: 'relative' }}>
      {dropdownVisible && (
        <KnowledgeMentionDropdown
          items={filteredCatalog}
          highlightedIndex={highlightedIndex}
          onSelect={(entry) => selectFile(entry, message)}
          onHighlight={setHighlightedIndex}
          loading={catalogLoading}
          listboxId={LISTBOX_ID}
        />
      )}

      {(images.length > 0 || attachedFiles.length > 0) && (
        <KnowledgeChipsBar
          images={images}
          attachedFiles={attachedFiles}
          onRemoveImage={(i) => setImages((prev) => prev.filter((_, j) => j !== i))}
          onRemoveFile={(id) => setAttachedFiles((prev) => prev.filter((f) => f.id !== id))}
        />
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
        <textarea
          ref={textareaRef}
          value={message}
          onChange={handleTextChange}
          onKeyDown={handleKeyDown}
          placeholder="Type a message... (@ to mention a knowledge file)"
          disabled={disabled}
          rows={1}
          aria-label="Message"
          role="combobox"
          aria-expanded={dropdownVisible}
          aria-controls={dropdownVisible ? LISTBOX_ID : undefined}
          aria-activedescendant={activeDescendant}
          aria-autocomplete="list"
        />
        <button
          className="send-btn"
          type="button"
          onClick={handleSend}
          disabled={disabled || !message.trim()}
          aria-label="Send message"
        >
          <SendArrowIcon />
        </button>
      </div>
    </div>
  );
}
