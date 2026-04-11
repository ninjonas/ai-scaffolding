import {
  useState,
  useCallback,
  useEffect,
  type RefObject,
  type ChangeEvent,
  type KeyboardEvent,
} from 'react';
import { listKnowledgeFiles, type KnowledgeCatalogEntry } from '../api/knowledge';
import {
  MAX_DROPDOWN_ITEMS,
  fuzzyMatch,
  stripMentionsFromText,
  removeMentionByName,
  collapseSpaces,
  findMentionAtCursor,
  shortenName,
} from './mentionUtils';

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
    setCatalog([]);
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
    const mention = `@${shortenName(entry.name)}`;
    const trailing = after.startsWith(' ') ? after : ` ${after}`;
    setMessage(before + mention + trailing);
    closeMention();
    if (!attachedFiles.find((f) => f.id === entry.id)) {
      setAttachedFiles((prev) => [...prev, entry]);
    }
    setTimeout(() => {
      const ta = textareaRef.current;
      if (!ta) return;
      ta.focus();
      ta.setSelectionRange(before.length + mention.length + 1, before.length + mention.length + 1);
    }, 0);
  };

  const handleTextChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    let val = e.target.value;
    const pos = e.target.selectionStart ?? 0;

    const broken = attachedFiles.filter((f) => !val.includes(`@${shortenName(f.name)}`));
    if (broken.length > 0) {
      for (const f of broken) {
        const escaped = shortenName(f.name).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        val = val.replace(new RegExp(`@${escaped}\\S*`, 'g'), '');
      }
      val = val.replace(/  +/g, ' ');
      setAttachedFiles((prev) => prev.filter((f) => val.includes(`@${shortenName(f.name)}`)));
    }

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

  const handleMentionKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>): boolean => {
    if (e.key !== 'Backspace' && e.key !== 'Delete') return false;
    if (attachedFiles.length === 0) return false;
    const ta = textareaRef.current;
    if (!ta || ta.selectionStart !== ta.selectionEnd) return false;
    const dir = e.key === 'Backspace' ? 'backspace' : 'delete';
    const hit = findMentionAtCursor(ta.selectionStart, message, attachedFiles, dir);
    if (!hit) return false;
    e.preventDefault();
    const before = message.slice(0, hit.start);
    const after = message.slice(hit.end);
    setMessage(collapseSpaces(before, after));
    setAttachedFiles((prev) => prev.filter((x) => x.id !== hit.file.id));
    setTimeout(() => ta.setSelectionRange(hit.start, hit.start), 0);
    return true;
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

  const removeMentionFromText = (name: string) => {
    setMessage((prev) => removeMentionByName(prev, name));
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
    handleMentionKeyDown,
    handleDropdownKeyDown,
    removeMentionFromText,
    stripMentions: (text: string) => stripMentionsFromText(text, attachedFiles),
    resetMention,
  };
}
