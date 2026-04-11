import { useState, useCallback, useRef } from 'react';

type Toast = { id: number; message: string; retry?: () => void };

export function useKnowledgeToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const counterRef = useRef(0);

  const addToast = useCallback((message: string, retry?: () => void) => {
    const id = ++counterRef.current;
    setToasts((prev) => [...prev, { id, message, retry }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), retry ? 5000 : 4000);
  }, []);

  return { toasts, addToast };
}
