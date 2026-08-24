import  { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Briefcase, FileText } from 'lucide-react';
import { apiClient } from '../api/client';
import type { Job, Candidate } from '../types';
import { ResumeUploader } from '../components/ResumeUploader';
import { CandidateTable } from '../components/CandidateTable';

export const JobDetail = () => {
  const { id } = useParams<{ id: string }>();
  const [job, setJob] = useState<Job | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchJobData = async () => {
    try {
      // In a real prod app, you would create a GET /jobs/{id} endpoint
      // For speed, we are fetching all and filtering on the frontend
      const response = await apiClient.get('/jobs/');
      const foundJob = response.data.find((j: Job) => j.id === Number(id));
      
      if (foundJob) {
        setJob(foundJob);
        // Fallback to empty array if candidates aren't returned in the job schema
        setCandidates(foundJob.candidates || []); 
      }
    } catch (error) {
      console.error("Failed to fetch job", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobData();
  }, [id]);

  if (loading) return <div className="p-20 text-center text-gray-500 font-medium">Loading Job Profile...</div>;
  if (!job) return <div className="p-20 text-center text-red-500 font-medium">Error 404: Job not found.</div>;

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <Link to="/" className="inline-flex items-center gap-2 text-gray-500 hover:text-blue-600 font-semibold mb-6 transition">
        <ArrowLeft className="w-4 h-4" /> Back to Jobs
      </Link>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 mb-8">
        <h1 className="text-3xl font-extrabold text-gray-900 mb-3">{job.title}</h1>
        <span className="bg-blue-50 text-blue-700 border border-blue-200 px-3 py-1 rounded-md text-sm font-bold tracking-wide uppercase">
          {job.department || 'General'}
        </span>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-8 border-t border-gray-100 pt-8">
          <div>
            <h3 className="flex items-center gap-2 text-lg font-bold text-gray-800 mb-3">
              <Briefcase className="w-5 h-5 text-blue-500" /> Role Description
            </h3>
            <p className="text-gray-600 leading-relaxed">{job.description}</p>
          </div>
          <div>
            <h3 className="flex items-center gap-2 text-lg font-bold text-gray-800 mb-3">
              <FileText className="w-5 h-5 text-blue-500" /> Core Requirements
            </h3>
            <p className="text-gray-600 leading-relaxed">{job.requirements}</p>
          </div>
        </div>
      </div>

      <div className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Screen Candidates</h2>
        <ResumeUploader jobId={id} onUploadSuccess={fetchJobData} />
      </div>
      
      {candidates.length > 0 && (
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Ranked Shortlist</h2>
          <p className="text-gray-500 mb-6">Candidates autonomously evaluated against job requirements by AI.</p>
          <CandidateTable candidates={candidates} />
        </div>
      )}
    </div>
  );
};