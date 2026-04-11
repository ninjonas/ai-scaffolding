const ICON_PROPS = {
  fill: 'none' as const,
  stroke: 'currentColor' as const,
  strokeWidth: 2,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
  'aria-hidden': true,
};

export const TrashIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" {...ICON_PROPS}>
    <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
  </svg>
);

export const CloseIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" {...ICON_PROPS}>
    <path d="M18 6 6 18M6 6l12 12" />
  </svg>
);

export const PlusIcon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" {...ICON_PROPS} strokeWidth={2.5}>
    <path d="M12 5v14M5 12h14" />
  </svg>
);

export const DocumentIcon = () => (
  <svg width="40" height="40" viewBox="0 0 24 24" {...ICON_PROPS} strokeWidth={1.25}>
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="9" y1="13" x2="15" y2="13" />
    <line x1="9" y1="17" x2="13" y2="17" />
  </svg>
);

export const FileTextIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" {...ICON_PROPS}>
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="9" y1="13" x2="15" y2="13" />
    <line x1="9" y1="17" x2="13" y2="17" />
  </svg>
);

export const BracesIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" {...ICON_PROPS}>
    <path d="M8 3H7a2 2 0 0 0-2 2v5a2 2 0 0 1-2 2 2 2 0 0 1 2 2v5a2 2 0 0 0 2 2h1" />
    <path d="M16 21h1a2 2 0 0 0 2-2v-5a2 2 0 0 1 2-2 2 2 0 0 1-2-2V5a2 2 0 0 0-2-2h-1" />
  </svg>
);

export const FileCodeIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" {...ICON_PROPS}>
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <polyline points="10 13 8 15 10 17" />
    <polyline points="14 13 16 15 14 17" />
  </svg>
);

export const CheckIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" {...ICON_PROPS} stroke="#4ade80">
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

export const ImageIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" {...ICON_PROPS}>
    <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
    <circle cx="8.5" cy="8.5" r="1.5" />
    <polyline points="21 15 16 10 5 21" />
  </svg>
);

export const SpinnerIcon = () => (
  <svg
    width="14"
    height="14"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={2}
    strokeLinecap="round"
    aria-hidden
    style={{ animation: 'knowledge-spin 0.7s linear infinite' }}
  >
    <path d="M21 12a9 9 0 1 1-6.219-8.56" />
  </svg>
);
