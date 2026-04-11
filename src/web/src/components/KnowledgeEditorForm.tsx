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
  filename: string;
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
  onNameChange,
  onDescriptionChange,
}: Pick<
  EditorFormProps,
  'nameRef' | 'name' | 'description' | 'onNameChange' | 'onDescriptionChange'
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
        <textarea
          className="knowledge-input knowledge-description-textarea"
          value={description}
          onChange={(e) => onDescriptionChange(e.target.value)}
          placeholder="Brief description of this file"
          rows={3}
        />
      </label>
    </>
  );
}

function FileDetailsCollapsible({
  filename,
  name,
  content,
}: Pick<EditorFormProps, 'filename' | 'name' | 'content'>) {
  return (
    <details className="knowledge-collapsible">
      <summary className="knowledge-collapsible-summary">File details</summary>
      <div className="knowledge-collapsible-body">
        <label className="knowledge-field-label">
          Filename
          <input
            type="text"
            className="knowledge-input knowledge-input-readonly"
            value={filename}
            readOnly
            tabIndex={-1}
            placeholder="—"
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
      </div>
    </details>
  );
}

export function EditorForm({
  nameRef,
  filename,
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
      <FileDetailsCollapsible filename={filename} name={name} content={content} />
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
