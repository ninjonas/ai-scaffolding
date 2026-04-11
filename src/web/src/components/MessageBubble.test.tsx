import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { MessageBubble } from './MessageBubble';

describe('MessageBubble', () => {
  it('does not render role label for user messages', () => {
    render(<MessageBubble role="user" content="Hello" />);
    expect(screen.queryByText('You')).not.toBeInTheDocument();
  });

  it('renders assistant role label', () => {
    render(<MessageBubble role="assistant" content="Hello" />);
    expect(screen.getByText('Assistant')).toBeInTheDocument();
  });

  it('renders message content', () => {
    render(<MessageBubble role="user" content="My message here" />);
    expect(screen.getByText('My message here')).toBeInTheDocument();
  });

  it('renders tool calls section when toolCalls provided', () => {
    const toolCalls = [
      { name: 'search_web', args: { query: 'test' } },
      { name: 'read_file', args: { path: '/tmp/file.txt' } },
    ];
    render(<MessageBubble role="assistant" content="Done" toolCalls={toolCalls} />);
    expect(screen.getByText('Tools used:')).toBeInTheDocument();
    expect(screen.getByText('search_web')).toBeInTheDocument();
    expect(screen.getByText('read_file')).toBeInTheDocument();
  });

  it('does not render tool calls section when empty', () => {
    render(<MessageBubble role="assistant" content="No tools" toolCalls={[]} />);
    expect(screen.queryByText('Tools used:')).not.toBeInTheDocument();
  });

  it('renders typing indicator when loading prop is true', () => {
    const { container } = render(<MessageBubble role="assistant" content="" loading />);
    expect(container.querySelector('.message-loading')).toBeInTheDocument();
    expect(container.querySelector('.typing-dots')).toBeInTheDocument();
    expect(container.querySelector('.message-content')).not.toBeInTheDocument();
  });
});
