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
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const fileInputRef = useRef<HTMLInputElement>(null);

  const BATCH_SIZE = 2;

  const getErrorMessage = (err: any): string => {
    if (err?.response?.data?.detail) {
      const detail = err.response.data.detail;
      return typeof detail === 'string' ? detail : JSON.stringify(detail);
    }
    if (err?.response?.status) {
      return `Server returned HTTP ${err.response.status} (${err.response.statusText || 'Error'})`;
    }
    return err?.message || 'Network request failed';
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
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

    const validExtensions = ['.pdf', '.docx'];
    const validFiles: File[] = [];
    const invalidFiles: string[] = [];

    for (const file of files) {
      const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
      if (validExtensions.includes(fileExtension)) {
        validFiles.push(file);
      } else {
        invalidFiles.push(file.name);
      }
    }

    if (invalidFiles.length > 0) {
      alert(`Skipping unsupported files (${invalidFiles.join(', ')}). Only PDF and DOCX files are supported!`);
    }

    if (validFiles.length === 0) {
      alert('Please select valid PDF or DOCX files.');
      return;
    }

    setIsUploading(true);
    setProgress({ current: 0, total: validFiles.length });

    let processedCount = 0;
    let lastError: string | null = null;

    try {
      for (let i = 0; i < validFiles.length; i += BATCH_SIZE) {
        const chunk = validFiles.slice(i, i + BATCH_SIZE);
        const formData = new FormData();
        for (const file of chunk) {
          formData.append('files', file);
        }

        let batchSucceeded = false;
        // Attempt the batch, with 1 automatic retry on failure
        for (let attempt = 0; attempt < 2; attempt++) {
          try {
            await apiClient.post(`/screening/${jobId}/upload-resumes`, formData, {
              headers: { 'Content-Type': 'multipart/form-data' },
            });
            batchSucceeded = true;
            break;
          } catch (err) {
            lastError = getErrorMessage(err);
            console.error(`Batch ${Math.floor(i / BATCH_SIZE) + 1} attempt ${attempt + 1} failed:`, err);
            if (attempt === 0) {
              // Wait 3 seconds before retrying this chunk
              await new Promise((resolve) => setTimeout(resolve, 3000));
            }
          }
        }

        if (batchSucceeded) {
          processedCount += chunk.length;
          setProgress({ current: processedCount, total: validFiles.length });
          onUploadSuccess(); // Refresh candidate table progressively after every batch!
        } else {
          // If a batch fails after retry, record failure and break to report accurately
          break;
        }

        // Small breathing delay between batches to stay within Gemini API rate limits
        if (i + BATCH_SIZE < validFiles.length) {
          await new Promise((resolve) => setTimeout(resolve, 2000));
        }
      }

      if (lastError && processedCount === 0) {
        alert(`Upload failed: ${lastError}\n\nNo resumes were saved. Please check if the server is awake and try again.`);
      } else if (lastError && processedCount < validFiles.length) {
        alert(`Partial upload: ${processedCount} of ${validFiles.length} resumes successfully screened and saved.\n\nRemaining files stopped due to: ${lastError}`);
      }
    } catch (unexpectedError) {
      console.error('Unexpected upload error:', unexpectedError);
      alert(`Unexpected error: ${getErrorMessage(unexpectedError)}`);
    } finally {
      setIsUploading(false);
      setProgress({ current: 0, total: 0 });
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const progressPercent = progress.total > 0 ? Math.round((progress.current / progress.total) * 100) : 0;

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
          <h3 className="text-lg font-bold">
            AI is analyzing resumes ({progress.current} of {progress.total})...
          </h3>
          <p className="mt-2 text-sm text-slate-300">
            Batch uploading and calculating fit scores. Live progress: {progressPercent}%
          </p>
          <div className="mt-4 h-2.5 w-72 max-w-full overflow-hidden rounded-full bg-slate-700/80">
            <div 
              className="h-full rounded-full bg-[#2ad38a] transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center">
          <Upload className="mb-4 w-12 h-12 text-slate-400" />
          <h3 className="text-xl font-bold text-white">Drag & Drop Resumes Here</h3>
          <p className="mt-2 mb-6 text-sm text-slate-300">Batch upload supported (up to 30+ resumes). PDF and DOCX formats allowed.</p>
          <button 
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="rounded-lg bg-[#2ad38a] px-6 py-2.5 font-medium text-[#041510] shadow-[0_0_20px_rgba(42,211,138,0.25)] transition hover:bg-[#42df98]"
          >
            Browse Files
          </button>
          <input 
            ref={fileInputRef}
            type="file" 
            multiple 
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" 
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>
      )}
    </div>
  );
};