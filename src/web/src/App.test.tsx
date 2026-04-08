import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';

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
