import {
  useState,
  useCallback,
  useEffect,
  type RefObject,
  type ChangeEvent,
  type KeyboardEvent,
} from 'react';
import { listKnowledgeFiles, type KnowledgeCatalogEntry } from '../api/knowledge';

const MAX_DROPDOWN_ITEMS = 8;

function fuzzyMatch(query: string, entry: KnowledgeCatalogEntry): boolean {
  const q = query.toLowerCase();
  return (
    entry.name.toLowerCase().includes(q) ||
    entry.description.toLowerCase().includes(q) ||
    entry.tags.some((t) => t.toLowerCase().includes(q))
  );
}

interface UseMentionStateOptions {
  conversationId?: string;
  textareaRef: RefObject<HTMLTextAreaElement | null>;
}

export function useMentionState({ conversationId, textareaRef }: UseMentionStateOptions) {
  const [mentionQuery, setMentionQuery] = useState<string | null>(null);
  const [mentionStart, setMentionStart] = useState<number>(0);
  const [catalog, setCatalog] = useState<KnowledgeCatalogEntry[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const [dropdownVisible, setDropdownVisible] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState<KnowledgeCatalogEntry[]>([]);
  const [message, setMessage] = useState('');

  const filteredCatalog =
    mentionQuery !== null && mentionQuery.length > 0
      ? catalog.filter((e) => fuzzyMatch(mentionQuery, e)).slice(0, MAX_DROPDOWN_ITEMS)
      : catalog.slice(0, MAX_DROPDOWN_ITEMS);

  const fetchCatalog = useCallback(async () => {
    setCatalogLoading(true);
    try {
      const [project, conversation] = await Promise.all([
        listKnowledgeFiles('project'),
        conversationId ? listKnowledgeFiles('conversation', conversationId) : Promise.resolve([]),
      ]);
      setCatalog([...project, ...conversation]);
    } catch {
      setCatalog([]);
    } finally {
      setCatalogLoading(false);
    }
  }, [conversationId]);

  useEffect(() => {
    if (mentionQuery !== null && catalog.length === 0 && !catalogLoading) fetchCatalog();
  }, [mentionQuery, catalog.length, catalogLoading, fetchCatalog]);

  useEffect(() => {
    setHighlightedIndex(0);
  }, [mentionQuery]);

  const openMention = (start: number) => {
    setMentionStart(start);
    setMentionQuery('');
    setDropdownVisible(true);
    setHighlightedIndex(0);
  };

  const closeMention = () => {
    setMentionQuery(null);
    setDropdownVisible(false);
  };

  const selectFile = (entry: KnowledgeCatalogEntry, currentMessage: string) => {
    const before = currentMessage.slice(0, mentionStart - 1);
    const after = currentMessage.slice(mentionStart + (mentionQuery?.length ?? 0));
    setMessage(before + after);
    closeMention();
    if (!attachedFiles.find((f) => f.id === entry.id)) {
      setAttachedFiles((prev) => [...prev, entry]);
    }
    setTimeout(() => textareaRef.current?.focus(), 0);
  };

  const handleTextChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    const pos = e.target.selectionStart ?? 0;
    setMessage(val);
    if (mentionQuery !== null) {
      const textSinceMention = val.slice(mentionStart, pos);
      if (textSinceMention.includes(' ') || pos < mentionStart) closeMention();
      else setMentionQuery(textSinceMention);
    } else {
      const lastAt = val.lastIndexOf('@', pos - 1);
      if (lastAt !== -1 && lastAt === pos - 1) openMention(pos);
    }
  };

  const handleDropdownKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>): boolean => {
    if (!dropdownVisible || filteredCatalog.length === 0) return false;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlightedIndex((i) => Math.min(i + 1, filteredCatalog.length - 1));
      return true;
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlightedIndex((i) => Math.max(i - 1, 0));
      return true;
    }
    if (e.key === 'Enter') {
      e.preventDefault();
      const entry = filteredCatalog[highlightedIndex];
      if (entry) selectFile(entry, message);
      return true;
    }
    if (e.key === 'Escape') {
      e.preventDefault();
      closeMention();
      return true;
    }
    return false;
  };

  const resetMention = () => {
    setAttachedFiles([]);
    closeMention();
  };

  return {
    message,
    setMessage,
    attachedFiles,
    setAttachedFiles,
    filteredCatalog,
    catalogLoading,
    highlightedIndex,
    setHighlightedIndex,
    dropdownVisible,
    closeMention,
    selectFile,
    handleTextChange,
    handleDropdownKeyDown,
    resetMention,
  };
}
