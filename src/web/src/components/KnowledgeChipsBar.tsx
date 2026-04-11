import type { KnowledgeCatalogEntry } from '../api/knowledge';
import { DocumentIcon } from './ChatInputIcons';

interface KnowledgeChipsBarProps {
  images: string[];
  attachedFiles: KnowledgeCatalogEntry[];
  onRemoveImage: (index: number) => void;
  onRemoveFile: (id: string) => void;
}

export function KnowledgeChipsBar({
  images,
  attachedFiles,
  onRemoveImage,
  onRemoveFile,
}: KnowledgeChipsBarProps) {
  return (
    <div className="attachments-preview">
      {images.map((img, i) => (
        <div key={`img-${i}`} className="image-preview">
          <img src={img} alt={`Upload ${i + 1}`} />
          <button aria-label="Remove image" onClick={() => onRemoveImage(i)}>
            &times;
          </button>
        </div>
      ))}
      {attachedFiles.map((file) => (
        <div key={file.id} className="knowledge-chip">
          <DocumentIcon />
          <span>{file.name}</span>
          <button aria-label={`Remove ${file.name}`} onClick={() => onRemoveFile(file.id)}>
            &times;
          </button>
        </div>
      ))}
    </div>
  );
}
