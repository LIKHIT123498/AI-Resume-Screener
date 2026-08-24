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
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Job Dashboard</h1>
          <p className="text-gray-600 mt-1">Manage your active roles and AI screenings.</p>
        </div>
        
        {/* Update the button to open the modal */}
        <button 
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg font-medium transition shadow-sm"
        >
          <Plus className="w-5 h-5" />
          Create New Job
        </button>
      </div>

      {jobs.length === 0 ? (
        <div className="text-center bg-white p-16 rounded-xl border border-dashed border-gray-300">
          <p className="text-gray-500 font-medium">No jobs found. Create one to get started.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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