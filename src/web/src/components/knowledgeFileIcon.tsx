import { BracesIcon, FileCodeIcon, FileTextIcon, ImageIcon } from './KnowledgeIcons';

const IMAGE_TYPES = ['png', 'jpg', 'jpeg', 'gif', 'webp'];

export function getFileIcon(fileType: string) {
  if (fileType === 'json') return <BracesIcon />;
  if (fileType === 'yml' || fileType === 'yaml') return <FileCodeIcon />;
  if (IMAGE_TYPES.includes(fileType)) return <ImageIcon />;
  return <FileTextIcon />;
}
