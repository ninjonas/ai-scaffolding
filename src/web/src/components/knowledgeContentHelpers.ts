const PLACEHOLDER: Record<string, string> = {
  md: 'Start writing markdown...',
  txt: 'Start writing...',
  json: 'Paste JSON here...',
  yml: 'Paste YAML here...',
  yaml: 'Paste YAML here...',
};

export function getContentPlaceholder(name: string): string {
  const ext = name.split('.').pop()?.toLowerCase() ?? '';
  return PLACEHOLDER[ext] ?? 'Start writing...';
}

export function isMonoFileType(name: string): boolean {
  const ext = name.split('.').pop()?.toLowerCase() ?? '';
  return ext === 'json' || ext === 'yml' || ext === 'yaml';
}
