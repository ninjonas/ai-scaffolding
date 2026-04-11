import { useCallback, useEffect, useRef } from 'react';

export function useFocusTrap(onEscape: () => void) {
  const ref = useRef<HTMLDivElement>(null);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!ref.current) return;
      if (e.key === 'Escape') {
        onEscape();
        return;
      }
      if (e.key !== 'Tab') return;
      const focusable = ref.current.querySelectorAll<HTMLElement>(
        'button, input, textarea, select, [tabindex]:not([tabindex="-1"])',
      );
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    },
    [onEscape],
  );

  useEffect(() => {
    const panel = ref.current;
    if (!panel) return;
    panel.addEventListener('keydown', handleKeyDown);
    return () => panel.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return ref;
}
