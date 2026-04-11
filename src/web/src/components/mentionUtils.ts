import type { KnowledgeCatalogEntry } from '../api/knowledge';

export const MAX_DROPDOWN_ITEMS = 8;

export function shortenName(name: string): string {
  const words = name.split(/\s+/);
  if (words.length <= 2) return name;
  return `${words[0]}...${words[words.length - 1]}`;
}

export function fuzzyMatch(query: string, entry: KnowledgeCatalogEntry): boolean {
  const q = query.toLowerCase();
  return (
    entry.name.toLowerCase().includes(q) ||
    entry.description.toLowerCase().includes(q) ||
    entry.tags.some((t) => t.toLowerCase().includes(q))
  );
}

export function stripMentionsFromText(text: string, files: KnowledgeCatalogEntry[]): string {
  let cleaned = text;
  for (const f of files) {
    cleaned = cleaned.replace(`@${shortenName(f.name)}`, '').replace(/  +/g, ' ');
  }
  return cleaned.trim();
}

export function removeMentionByName(text: string, name: string): string {
  return text
    .replace(`@${shortenName(name)}`, '')
    .replace(/  +/g, ' ')
    .trim();
}

export function collapseSpaces(before: string, after: string): string {
  return before.endsWith(' ') && after.startsWith(' ') ? before + after.slice(1) : before + after;
}

/** Find the earliest @mention in text; used by MentionHighlight. */
export function findEarliestMention(
  text: string,
  files: KnowledgeCatalogEntry[],
): { file: KnowledgeCatalogEntry; index: number; text: string } | null {
  let earliest = -1;
  let matched: KnowledgeCatalogEntry | null = null;
  for (const f of files) {
    const idx = text.indexOf(`@${shortenName(f.name)}`);
    if (idx !== -1 && (earliest === -1 || idx < earliest)) {
      earliest = idx;
      matched = f;
    }
  }
  if (earliest === -1 || !matched) return null;
  return { file: matched, index: earliest, text: `@${shortenName(matched.name)}` };
}

/** Find if cursor is inside a mention; returns the file or null. */
export function findMentionAtCursor(
  pos: number,
  message: string,
  files: KnowledgeCatalogEntry[],
  direction: 'backspace' | 'delete',
): { file: KnowledgeCatalogEntry; start: number; end: number } | null {
  for (const f of files) {
    const mention = `@${shortenName(f.name)}`;
    const idx = message.indexOf(mention);
    if (idx === -1) continue;
    const end = idx + mention.length;
    const inside = direction === 'backspace' ? pos > idx && pos <= end : pos >= idx && pos < end;
    if (inside) return { file: f, start: idx, end };
  }
  return null;
}
