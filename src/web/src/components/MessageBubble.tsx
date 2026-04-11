import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { ToolCall } from '../api/chat';

interface KnowledgeChip {
  id: string;
  name: string;
}

interface MessageBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: ToolCall[];
  images?: string[];
  knowledgeFiles?: KnowledgeChip[];
  loading?: boolean;
}

function ToolCallsSection({ toolCalls }: { toolCalls: ToolCall[] }) {
  return (
    <div className="tool-calls">
      <div className="tool-calls-label">Tools used:</div>
      {toolCalls.map((tc, i) => (
        <div key={i} className="tool-call">
          <code>{tc.name}</code>
        </div>
      ))}
    </div>
  );
}

const MENTION_PATTERN = /@\[([^\]]+)\]/g;

function renderMentions(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  const regex = new RegExp(MENTION_PATTERN);
  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    parts.push(
      <span key={match.index} className="mention-pill mention-pill-static">
        @{match[1]}
      </span>,
    );
    lastIndex = regex.lastIndex;
  }
  if (lastIndex < text.length) parts.push(text.slice(lastIndex));
  return parts;
}

function UserMessageContent({ images, content }: { images?: string[]; content: string }) {
  return (
    <>
      {images && images.length > 0 && (
        <div className="message-images">
          {images.map((img, i) => (
            <img
              key={i}
              src={`data:image/jpeg;base64,${img}`}
              alt={`Upload ${i + 1}`}
              className="message-image"
            />
          ))}
        </div>
      )}
      <div className="message-content">{renderMentions(content)}</div>
    </>
  );
}

function AssistantMessageContent({ content }: { content: string }) {
  return (
    <div className="message-content markdown-body">
      <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
    </div>
  );
}

export function MessageBubble({ role, content, toolCalls, images, loading }: MessageBubbleProps) {
  return (
    <div className={`message message-${role}${loading ? ' message-loading' : ''}`}>
      {role === 'assistant' && <div className="message-role">Assistant</div>}
      {loading ? (
        <div className="typing-dots" aria-hidden>
          <span />
          <span />
          <span />
        </div>
      ) : role === 'assistant' ? (
        <AssistantMessageContent content={content} />
      ) : (
        <UserMessageContent images={images} content={content} />
      )}
      {!loading && toolCalls && toolCalls.length > 0 && <ToolCallsSection toolCalls={toolCalls} />}
    </div>
  );
}
