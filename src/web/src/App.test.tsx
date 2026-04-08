import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import App from './App';
import { ChatInput } from './components/ChatInput';
import { MessageBubble } from './components/MessageBubble';

describe('App', () => {
  it('renders the chat header', () => {
    render(<App />);
    expect(screen.getByText('Scaffolding Chat')).toBeInTheDocument();
  });

  it('shows empty state message', () => {
    render(<App />);
    expect(screen.getByText('Send a message to start a conversation.')).toBeInTheDocument();
  });
});

describe('ChatInput', () => {
  it('renders textarea and send button', () => {
    render(<ChatInput onSend={vi.fn()} disabled={false} />);
    expect(screen.getByRole('textbox', { name: /message/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
  });

  it('send button is disabled when input is empty', () => {
    render(<ChatInput onSend={vi.fn()} disabled={false} />);
    expect(screen.getByRole('button', { name: /send/i })).toBeDisabled();
  });

  it('calls onSend with message text on submit', () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} disabled={false} />);
    const textarea = screen.getByRole('textbox', { name: /message/i });
    fireEvent.change(textarea, { target: { value: 'Hello world' } });
    fireEvent.click(screen.getByRole('button', { name: /send/i }));
    expect(onSend).toHaveBeenCalledWith('Hello world', []);
  });
});

describe('MessageBubble', () => {
  it('renders user message with correct class', () => {
    const { container } = render(<MessageBubble role="user" content="Hi there" />);
    expect(container.querySelector('.message-user')).toBeInTheDocument();
  });

  it('renders assistant message with correct class', () => {
    const { container } = render(<MessageBubble role="assistant" content="Hello" />);
    expect(container.querySelector('.message-assistant')).toBeInTheDocument();
  });

  it('renders tool calls when provided', () => {
    const toolCalls = [{ name: 'search', args: {} }];
    render(<MessageBubble role="assistant" content="Used a tool" toolCalls={toolCalls} />);
    expect(screen.getByText('Tools used:')).toBeInTheDocument();
    expect(screen.getByText('search')).toBeInTheDocument();
  });
});
