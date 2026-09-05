'use client';

import { FileText, UploadCloud, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { useCallback, useRef, useState } from 'react';
import { useWorkspaceStore } from '@/store/workspace';

export function FileDropzone() {
  const { activeBusinessId } = useWorkspaceStore();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  const uploadFile = async (file: File) => {
    if (!file) return;

    setIsUploading(true);
    setUploadStatus('idle');
    setErrorMessage('');

    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const formData = new FormData();
      formData.append('file', file);
      if (activeBusinessId) {
        formData.append('business_id', activeBusinessId);
      }

      const response = await fetch(`${backendUrl}/knowledge/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed with status ${response.status}`);
      }

      setUploadStatus('success');
    } catch (err: any) {
      console.error('Failed to upload knowledge document:', err);
      setErrorMessage(err.message || 'Failed to upload document');
      setUploadStatus('error');
    } finally {
      setIsUploading(false);
    }
  };

  const onDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        uploadFile(e.dataTransfer.files[0]);
      }
    },
    [activeBusinessId]
  );

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      uploadFile(e.target.files[0]);
    }
  };

  return (
    <div
      onClick={() => fileInputRef.current?.click()}
      onDragOver={(e) => e.preventDefault()}
      onDrop={onDrop}
      className="max-w-xl mx-auto mt-8 border-2 border-dashed border-slate-custom rounded-2xl p-12 text-center hover:bg-paper/50 transition-colors cursor-pointer group relative"
    >
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept=".pdf,.txt,.docx"
        className="hidden"
      />

      <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center mx-auto mb-4 border border-slate-custom group-hover:scale-105 transition-transform">
        {isUploading ? (
          <Loader2 className="w-8 h-8 text-confirm-green animate-spin" />
        ) : uploadStatus === 'success' ? (
          <CheckCircle className="w-8 h-8 text-confirm-green" />
        ) : uploadStatus === 'error' ? (
          <AlertCircle className="w-8 h-8 text-red-500" />
        ) : (
          <UploadCloud className="w-8 h-8 text-confirm-green" />
        )}
      </div>

      <h3 className="text-lg font-medium text-ink mb-1">
        {isUploading
          ? 'Uploading PDF...'
          : uploadStatus === 'success'
          ? 'Document Uploaded Successfully!'
          : 'Drag and drop PDFs here'}
      </h3>

      <p className="text-slate text-sm flex items-center justify-center gap-2">
        <FileText className="w-4 h-4" />{' '}
        {uploadStatus === 'error'
          ? errorMessage
          : 'or click to browse your files (.pdf, .txt, .docx)'}
      </p>
    </div>
  );
}