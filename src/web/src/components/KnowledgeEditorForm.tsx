import { getContentPlaceholder, isMonoFileType } from './knowledgeContentHelpers';
import { DeleteSection } from './KnowledgeDeleteSection';

interface TagsEditorProps {
  tags: string[];
  tagInput: string;
  onTagInputChange: (v: string) => void;
  onAddTag: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  onRemoveTag: (tag: string) => void;
}

export function TagsEditor({
  tags,
  tagInput,
  onTagInputChange,
  onAddTag,
  onRemoveTag,
}: TagsEditorProps) {
  return (
    <div className="knowledge-field-label">
      Tags
      <div className="knowledge-tags-editor">
        {tags.map((t) => (
          <span key={t} className="knowledge-tag-chip">
            {t}
            <button
              className="knowledge-tag-remove"
              onClick={() => onRemoveTag(t)}
              aria-label={`Remove tag ${t}`}
            >
              &times;
            </button>
          </span>
        ))}
        <input
          type="text"
          className="knowledge-tag-input"
          value={tagInput}
          onChange={(e) => onTagInputChange(e.target.value)}
          onKeyDown={onAddTag}
          placeholder="Add tag, press Enter"
        />
      </div>
    </div>
  );
}

export interface EditorFormProps {
  nameRef: React.RefObject<HTMLInputElement | null>;
  name: string;
  description: string;
  tags: string[];
  tagInput: string;
  content: string;
  saving: boolean;
  error: string;
  onNameChange: (v: string) => void;
  onDescriptionChange: (v: string) => void;
  onTagInputChange: (v: string) => void;
  onAddTag: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  onRemoveTag: (tag: string) => void;
  onSubmit: () => void;
  showDeleteConfirm?: boolean;
  onDeleteClick?: () => void;
  onDeleteConfirm?: () => void;
  onDeleteCancel?: () => void;
}

function EditorTextFields({
  nameRef,
  name,
  description,
  content,
  onNameChange,
  onDescriptionChange,
}: Pick<
  EditorFormProps,
  'nameRef' | 'name' | 'description' | 'content' | 'onNameChange' | 'onDescriptionChange'
>) {
  return (
    <>
      <label className="knowledge-field-label">
        Name
        <input
          ref={nameRef}
          type="text"
          className="knowledge-input"
          value={name}
          onChange={(e) => onNameChange(e.target.value)}
          placeholder="example.md"
        />
      </label>
      <label className="knowledge-field-label">
        Description
        <input
          type="text"
          className="knowledge-input"
          value={description}
          onChange={(e) => onDescriptionChange(e.target.value)}
          placeholder="Brief description of this file"
        />
      </label>
      <div className="knowledge-field-label">
        Content
        <pre
          className={`knowledge-content-preview${isMonoFileType(name) ? ' knowledge-textarea-mono' : ''}`}
        >
          {content || (
            <span className="knowledge-content-empty">{getContentPlaceholder(name)}</span>
          )}
        </pre>
      </div>
    </>
  );
}

export function EditorForm({
  nameRef,
  name,
  description,
  tags,
  tagInput,
  content,
  saving,
  error,
  onNameChange,
  onDescriptionChange,
  onTagInputChange,
  onAddTag,
  onRemoveTag,
  onSubmit,
  showDeleteConfirm,
  onDeleteClick,
  onDeleteConfirm,
  onDeleteCancel,
}: EditorFormProps) {
  return (
    <>
      <EditorTextFields
        nameRef={nameRef}
        name={name}
        description={description}
        content={content}
        onNameChange={onNameChange}
        onDescriptionChange={onDescriptionChange}
      />
      <TagsEditor
        tags={tags}
        tagInput={tagInput}
        onTagInputChange={onTagInputChange}
        onAddTag={onAddTag}
        onRemoveTag={onRemoveTag}
      />
      {error && <div className="knowledge-error">{error}</div>}
      <button className="knowledge-submit-btn" onClick={onSubmit} disabled={saving}>
        {saving ? 'Saving...' : 'Save'}
      </button>
      <DeleteSection
        showDeleteConfirm={showDeleteConfirm}
        onDeleteClick={onDeleteClick}
        onDeleteConfirm={onDeleteConfirm}
        onDeleteCancel={onDeleteCancel}
      />
    </>
  );
}
