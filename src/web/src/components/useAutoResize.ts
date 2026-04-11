import { useCallback, useEffect, type RefObject } from 'react';

const MAX_HEIGHT = 200;

export function useAutoResize(
  textareaRef: RefObject<HTMLTextAreaElement | null>,
  triggerValue: string,
) {
  const autoResize = useCallback(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    if (ta.scrollHeight > MAX_HEIGHT) {
      ta.style.height = `${MAX_HEIGHT}px`;
      ta.style.overflow = 'auto';
    } else {
      ta.style.height = `${ta.scrollHeight}px`;
      ta.style.overflow = 'hidden';
    }
  }, [textareaRef]);

  useEffect(() => {
    autoResize();
  }, [triggerValue, autoResize]);
}
