import { useCallback, useEffect, useRef, type KeyboardEvent } from 'react';
import { BookIcon, PaperclipIcon, SendArrowIcon } from './ChatInputIcons';
import { KnowledgeMentionDropdown } from './KnowledgeMentionDropdown';
import { MentionHighlight } from './MentionHighlight';
import { useAutoResize } from './useAutoResize';
import { useImageAttachments, type AttachedImage } from './useImageAttachments';
import { useMentionState } from './useMentionState';

export type { AttachedImage };

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

const LISTBOX_ID = 'mention-listbox';

export function ChatInput({
  onSend,
  disabled,
  onToggleKnowledge,
  knowledgeOpen,
  conversationId,
}: ChatInputProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const mention = useMentionState({ conversationId, textareaRef });
  const imgAttach = useImageAttachments();
  useAutoResize(textareaRef, mention.message);

  useEffect(() => {
    if (!disabled) textareaRef.current?.focus();
  }, [disabled]);

  const overlayRef = useRef<HTMLDivElement>(null);

  const syncOverlayScroll = useCallback(() => {
    const ta = textareaRef.current;
    const overlay = overlayRef.current;
    if (ta && overlay) overlay.scrollTop = ta.scrollTop;
  }, []);

  const handleSend = () => {
    const trimmed = mention.message.trim();
    if (!trimmed) return;
    const expanded = mention.expandMentions(trimmed);
    onSend(
      expanded,
      imgAttach.images,
      mention.attachedFiles.map((f) => ({ id: f.id, name: f.name })),
    );
    mention.setMessage('');
    imgAttach.clearImages();
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
    if (e.target.files) imgAttach.addFiles(e.target.files);
    textareaRef.current?.focus();
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

      {imgAttach.images.length > 0 && (
        <div className="attachments-preview">
          {imgAttach.images.map((img, i) => (
            <div key={i} className="image-preview">
              <img src={img.dataUrl} alt={img.filename} />
              <button aria-label="Remove image" onClick={() => imgAttach.removeImage(i)}>
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
            <div ref={overlayRef} className="mention-overlay">
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
            onScroll={syncOverlayScroll}
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
