import { BracesIcon, FileCodeIcon, FileTextIcon } from './KnowledgeIcons';

export function getFileIcon(fileType: string) {
  if (fileType === 'json') return <BracesIcon />;
  if (fileType === 'yml' || fileType === 'yaml') return <FileCodeIcon />;
  return <FileTextIcon />;
}
