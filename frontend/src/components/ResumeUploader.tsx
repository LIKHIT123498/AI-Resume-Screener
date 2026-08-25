import React, { useState, useRef } from 'react';
import { Upload, Loader2 } from 'lucide-react';
import { apiClient } from '../api/client';

interface Props {
  jobId: string | undefined;
  onUploadSuccess: () => void;
}

export const ResumeUploader: React.FC<Props> = ({ jobId, onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      await uploadFiles(Array.from(e.target.files));
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      await uploadFiles(Array.from(e.dataTransfer.files));
    }
  };

  const uploadFiles = async (files: File[]) => {
    if (!jobId) return;
    
    const formData = new FormData();
    files.forEach(file => {
      if (file.type === 'application/pdf') {
        formData.append('files', file);
      }
    });

    if (!formData.has('files')) {
      alert('Please upload PDF files only.');
      return;
    }

    setIsUploading(true);
    try {
      await apiClient.post(`/screening/${jobId}/upload-resumes`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      onUploadSuccess(); // Refresh the candidate table!
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Failed to process resumes. Is the FastAPI server running?');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <div 
      className={`rounded-xl border-2 border-dashed p-12 text-center transition duration-200 ${
        isDragging ? 'border-[#2ad38a] bg-[#102d24]' : 'border-[#294a5d] bg-[#081b2a] hover:border-[#3adf9a]'
      }`}
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
    >
      {isUploading ? (
        <div className="flex flex-col items-center text-[#7ef0be]">
          <Loader2 className="mb-4 w-12 h-12 animate-spin" />
          <h3 className="text-lg font-bold">AI is analyzing resumes...</h3>
          <p className="mt-2 text-sm text-slate-300">Extracting text and calculating fit scores. This may take a moment.</p>
        </div>
      ) : (
        <div className="flex flex-col items-center">
          <Upload className="mb-4 w-12 h-12 text-slate-400" />
          <h3 className="text-xl font-bold text-white">Drag & Drop Resumes Here</h3>
          <p className="mt-2 mb-6 text-sm text-slate-300">Batch upload supported. PDF format only.</p>
          <button 
            onClick={() => fileInputRef.current?.click()}
            className="rounded-lg bg-[#2ad38a] px-6 py-2.5 font-medium text-[#041510] shadow-[0_0_20px_rgba(42,211,138,0.25)] transition hover:bg-[#42df98]"
          >
            Browse Files
          </button>
          <input 
            type="file" 
            multiple 
            accept=".pdf" 
            className="hidden" 
            ref={fileInputRef}
            onChange={handleFileChange}
          />
        </div>
      )}
    </div>
  );
};