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
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        <div className="flex justify-between items-center p-6 border-b border-gray-100 bg-gray-50/50">
          <h2 className="text-xl font-bold text-gray-900">Create New Job Role</h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-200 rounded-full transition">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto">
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Job Title *</label>
              <input 
                type="text" 
                required 
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                placeholder="e.g. Senior Frontend Engineer"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Department</label>
              <input 
                type="text" 
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                placeholder="e.g. Engineering"
              />
            </div>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-semibold text-gray-700 mb-1">Role Description *</label>
            <textarea 
              required 
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none"
              placeholder="Briefly describe the day-to-day responsibilities."
            />
          </div>

          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-700 mb-1">Core Requirements *</label>
            <textarea 
              required 
              rows={4}
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none"
              placeholder="List the mandatory skills, years of experience, and technical stack. (The AI will heavily weigh these constraints)."
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <button 
              type="button" 
              onClick={onClose}
              className="px-5 py-2.5 text-gray-700 font-medium hover:bg-gray-100 rounded-lg transition"
            >
              Cancel
            </button>
            <button 
              type="submit" 
              disabled={isSubmitting}
              className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-lg font-medium transition disabled:bg-blue-400"
            >
              {isSubmitting ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Create Job'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};