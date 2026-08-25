import  { useEffect, useState } from 'react';
import type { Job } from '../types';
import { apiClient } from '../api/client';
import { JobCard } from '../components/JobCard';
import { JobFormModal } from '../components/JobFormModal'; // <-- Import the new modal
import { Plus } from 'lucide-react';

export const Dashboard = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false); // <-- Add state for the modal

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await apiClient.get('/jobs/');
      setJobs(response.data);
    } catch (error) {
      console.error("Failed to fetch jobs:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64 text-gray-500 font-medium">
        Loading jobs...
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 text-slate-100">
      <div className="mb-8 flex items-center justify-between gap-4">
        <div>
          <h1 className="text-4xl font-black tracking-tight text-white">Job Dashboard</h1>
          <p className="mt-2 text-lg text-slate-300">Manage your active roles and AI screenings.</p>
        </div>
        
        <button 
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 rounded-xl bg-[#2ad38a] px-5 py-3 font-semibold text-[#041510] shadow-[0_0_24px_rgba(42,211,138,0.35)] transition hover:bg-[#42df98]"
        >
          <Plus className="w-5 h-5" />
          Create New Job
        </button>
      </div>

      {jobs.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-[#224154] bg-[#081b2a] p-16 text-center">
          <p className="text-slate-300 font-medium">No jobs found. Create one to get started.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
          {jobs.map((job) => (
            <JobCard key={job.id} job={job} />
          ))}
        </div>
      )}

      {/* Render the modal when isModalOpen is true */}
      {isModalOpen && (
        <JobFormModal 
          onClose={() => setIsModalOpen(false)} 
          onSuccess={fetchJobs} 
        />
      )}
    </div>
  );
};