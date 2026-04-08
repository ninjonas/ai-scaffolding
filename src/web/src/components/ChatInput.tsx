import { useState, useRef, type KeyboardEvent } from 'react';

interface ChatInputProps {
  onSend: (message: string, images: string[]) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [images, setImages] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSend = () => {
    const trimmed = message.trim();
    if (!trimmed) return;
    const base64Images = images.map((url) => url.split(',')[1]);
    onSend(trimmed, base64Images);
    setMessage('');
    setImages([]);
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const MAX_IMAGE_SIZE = 10 * 1024 * 1024; // 10MB

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    Array.from(files).forEach((file) => {
      if (file.size > MAX_IMAGE_SIZE) {
        return; // skip files over 10MB
      }
      const reader = new FileReader();
      reader.onload = () => {
        const dataUrl = reader.result as string;
        setImages((prev) => [...prev, dataUrl]);
      };
      reader.readAsDataURL(file);
    });
  };

  return (
    <div className="chat-input-container">
      {images.length > 0 && (
        <div className="image-previews">
          {images.map((img, i) => (
            <div key={i} className="image-preview">
              <img src={img} alt={`Upload ${i + 1}`} />
              <button
                aria-label="Remove image"
                onClick={() => setImages((prev) => prev.filter((_, j) => j !== i))}
              >
                &times;
              </button>
            </div>
          ))}
        </div>
      )}
      <div className="chat-input-row">
        <button
          className="attach-btn"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
          title="Attach image"
          aria-label="Attach image"
        >
          +
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
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message..."
          disabled={disabled}
          rows={1}
          aria-label="Message"
        />
        <button className="send-btn" onClick={handleSend} disabled={disabled || !message.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}
