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
      className={`border-2 border-dashed rounded-xl p-12 text-center transition duration-200 ${
        isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white hover:border-gray-400'
      }`}
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
    >
      {isUploading ? (
        <div className="flex flex-col items-center text-blue-600">
          <Loader2 className="w-12 h-12 animate-spin mb-4" />
          <h3 className="text-lg font-bold">AI is analyzing resumes...</h3>
          <p className="text-sm mt-2 text-gray-500">Extracting text and calculating fit scores. This may take a moment.</p>
        </div>
      ) : (
        <div className="flex flex-col items-center">
          <Upload className="w-12 h-12 text-gray-400 mb-4" />
          <h3 className="text-xl font-bold text-gray-800">Drag & Drop Resumes Here</h3>
          <p className="text-gray-500 text-sm mt-2 mb-6">Batch upload supported. PDF format only.</p>
          <button 
            onClick={() => fileInputRef.current?.click()}
            className="bg-gray-900 hover:bg-gray-800 text-white px-6 py-2.5 rounded-lg font-medium transition shadow-sm"
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