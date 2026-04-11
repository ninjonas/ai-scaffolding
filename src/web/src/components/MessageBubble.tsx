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
      <div className="message-content">{content}</div>
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
