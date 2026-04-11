import { useState } from 'react';

export interface AttachedImage {
  dataUrl: string;
  filename: string;
}

const MAX_IMAGE_SIZE = 10 * 1024 * 1024;

export function useImageAttachments() {
  const [images, setImages] = useState<AttachedImage[]>([]);

  const addFiles = (files: FileList) => {
    Array.from(files).forEach((file) => {
      if (file.size > MAX_IMAGE_SIZE) return;
      const reader = new FileReader();
      reader.onload = () =>
        setImages((prev) => [...prev, { dataUrl: reader.result as string, filename: file.name }]);
      reader.readAsDataURL(file);
    });
  };

  const clearImages = () => setImages([]);
  const removeImage = (index: number) => setImages((p) => p.filter((_, j) => j !== index));

  return { images, addFiles, clearImages, removeImage };
}
