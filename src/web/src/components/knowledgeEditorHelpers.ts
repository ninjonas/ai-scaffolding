import type { KnowledgeCatalogEntry } from '../api/knowledge';

export function toCatalogEntry(f: {
  id: string;
  name: string;
  description: string;
  tags: string[];
  fileType: string;
  scope: string;
}): KnowledgeCatalogEntry {
  return {
    id: f.id,
    name: f.name,
    description: f.description,
    tags: f.tags,
    fileType: f.fileType,
    scope: f.scope,
  };
}
