import type { ToolCall } from '../api/chat';

interface MessageBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: ToolCall[];
  loading?: boolean;
}

export function MessageBubble({ role, content, toolCalls, loading }: MessageBubbleProps) {
  return (
    <div className={`message message-${role}`}>
      <div className="message-role">{role === 'user' ? 'You' : 'Assistant'}</div>
      <div className={`message-content${loading ? ' loading' : ''}`}>{content}</div>
      {toolCalls && toolCalls.length > 0 && (
        <div className="tool-calls">
          <div className="tool-calls-label">Tools used:</div>
          {toolCalls.map((tc, i) => (
            <div key={i} className="tool-call">
              <code>{tc.name}</code>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
