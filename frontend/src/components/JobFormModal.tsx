import React, { useState } from 'react';
import { X, Loader2 } from 'lucide-react';
import { apiClient } from '../api/client';

interface Props {
  onClose: () => void;
  onSuccess: () => void;
}

export const JobFormModal: React.FC<Props> = ({ onClose, onSuccess }) => {
  const [title, setTitle] = useState('');
  const [department, setDepartment] = useState('');
  const [description, setDescription] = useState('');
  const [requirements, setRequirements] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      await apiClient.post('/jobs/', {
        title,
        department,
        description,
        requirements,
      });
      onSuccess(); // Triggers the dashboard to fetch the updated list
      onClose();   // Closes the modal
    } catch (error) {
      console.error("Failed to create job:", error);
      alert("Failed to create job. Check if your FastAPI server is running.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="flex max-h-[90vh] w-full max-w-2xl flex-col overflow-hidden rounded-2xl border border-[#24384b] bg-[#081b2a] shadow-[0_0_32px_rgba(15,23,42,0.7)]">
        
        <div className="flex items-center justify-between border-b border-[#1b2f3d] bg-[#0f2537] p-6">
          <h2 className="text-xl font-bold text-white">Create New Job Role</h2>
          <button onClick={onClose} className="rounded-full p-2 transition hover:bg-[#162f43]">
            <X className="w-5 h-5 text-slate-300" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="overflow-y-auto p-6">
          <div className="mb-4 grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1 block text-sm font-semibold text-slate-200">Job Title *</label>
              <input 
                type="text" 
                required 
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full rounded-lg border border-[#2d4256] bg-[#0d2134] p-2.5 text-white placeholder:text-slate-400 focus:border-[#2ad38a] focus:outline-none focus:ring-2 focus:ring-[#2ad38a]/40"
                placeholder="e.g. Senior Frontend Engineer"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-semibold text-slate-200">Department</label>
              <input 
                type="text" 
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="w-full rounded-lg border border-[#2d4256] bg-[#0d2134] p-2.5 text-white placeholder:text-slate-400 focus:border-[#2ad38a] focus:outline-none focus:ring-2 focus:ring-[#2ad38a]/40"
                placeholder="e.g. Engineering"
              />
            </div>
          </div>

          <div className="mb-4">
            <label className="mb-1 block text-sm font-semibold text-slate-200">Role Description *</label>
            <textarea 
              required 
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full resize-none rounded-lg border border-[#2d4256] bg-[#0d2134] p-2.5 text-white placeholder:text-slate-400 focus:border-[#2ad38a] focus:outline-none focus:ring-2 focus:ring-[#2ad38a]/40"
              placeholder="Briefly describe the day-to-day responsibilities."
            />
          </div>

          <div className="mb-6">
            <label className="mb-1 block text-sm font-semibold text-slate-200">Core Requirements *</label>
            <textarea 
              required 
              rows={4}
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              className="w-full resize-none rounded-lg border border-[#2d4256] bg-[#0d2134] p-2.5 text-white placeholder:text-slate-400 focus:border-[#2ad38a] focus:outline-none focus:ring-2 focus:ring-[#2ad38a]/40"
              placeholder="List the mandatory skills, years of experience, and technical stack. (The AI will heavily weigh these constraints)."
            />
          </div>

          <div className="flex justify-end gap-3 border-t border-[#1b2f3d] pt-4">
            <button 
              type="button" 
              onClick={onClose}
              className="rounded-lg px-5 py-2.5 font-medium text-slate-200 transition hover:bg-[#122b3d]"
            >
              Cancel
            </button>
            <button 
              type="submit" 
              disabled={isSubmitting}
              className="flex items-center justify-center gap-2 rounded-lg bg-[#2ad38a] px-6 py-2.5 font-medium text-[#03150d] transition hover:bg-[#42df98] disabled:bg-[#3f8d68]"
            >
              {isSubmitting ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Create Job'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};