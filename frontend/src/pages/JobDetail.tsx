import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Briefcase, FileText, Cpu, Users, Pencil, Trash2 } from 'lucide-react';
import { apiClient } from '../api/client';
import type { Job, Candidate } from '../types';
import { ResumeUploader } from '../components/ResumeUploader';
import { CandidateTable } from '../components/CandidateTable';
import { JobFormModal } from '../components/JobFormModal';

export const JobDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [job, setJob] = useState<Job | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

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

  if (loading) return <div className="p-20 text-center text-slate-300 font-medium">Loading Job Profile...</div>;
  if (!job) return <div className="p-20 text-center text-red-400 font-medium">Error 404: Job not found.</div>;

  return (
    <div className="mx-auto max-w-7xl px-6 py-8 text-slate-100">
      <Link 
        to={`/?portal=${job.role_type === 'non_technical' ? 'non_technical' : 'technical'}`} 
        className="mb-6 inline-flex items-center gap-2 font-semibold text-slate-300 transition hover:text-[#7ef0be]"
      >
        <ArrowLeft className="w-4 h-4" /> Back to {job.role_type === 'non_technical' ? 'Non-Technical' : 'Technical'} Portal
      </Link>

      <div className="mb-8 rounded-2xl border border-[#213548] bg-[#081b2a] p-8 shadow-[0_0_24px_rgba(15,23,42,0.45)]">
        <div className="mb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <h1 className="text-3xl font-extrabold text-white">{job.title}</h1>

          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={() => setIsEditModalOpen(true)}
              className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800/80 px-3.5 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-700 hover:text-white transition cursor-pointer"
            >
              <Pencil className="w-3.5 h-3.5" />
              Edit Role
            </button>
            <button
              type="button"
              onClick={async () => {
                const confirmed = window.confirm(
                  `Are you sure you want to delete "${job.title}"?\n\nAll candidate evaluations for this role will be permanently removed.`
                );
                if (!confirmed) return;
                try {
                  await apiClient.delete(`/jobs/${job.id}`);
                  navigate(`/?portal=${job.role_type === 'non_technical' ? 'non_technical' : 'technical'}`);
                } catch (err) {
                  console.error('Failed to delete job:', err);
                  alert('Failed to delete job. Check if backend is reachable.');
                }
              }}
              className="flex items-center gap-1.5 rounded-lg border border-red-900/50 bg-red-950/40 px-3.5 py-2 text-xs font-semibold text-red-300 hover:bg-red-900/60 hover:text-red-100 transition cursor-pointer"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Delete Role
            </button>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <span className="rounded-md border border-[#24534a] bg-[#12382f] px-3 py-1 text-sm font-bold uppercase tracking-wide text-[#8beec2]">
            {job.department || 'General'}
          </span>
          <span className={`inline-flex items-center gap-1.5 rounded-md border px-3 py-1 text-sm font-semibold ${
            job.role_type === 'non_technical'
              ? 'border-sky-500/30 bg-sky-950/40 text-sky-300'
              : 'border-[#2ad38a]/30 bg-[#162923] text-[#7ef0be]'
          }`}>
            {job.role_type === 'non_technical' ? (
              <>
                <Users className="w-4 h-4" /> Non-Technical Track (40% Skills • 20% Seniority • 40% Domain)
              </>
            ) : (
              <>
                <Cpu className="w-4 h-4" /> Technical Track (50% Skills • 30% Seniority • 20% Domain)
              </>
            )}
          </span>
          <button
            type="button"
            onClick={async () => {
              const newRole = job.role_type === 'non_technical' ? 'technical' : 'non_technical';
              try {
                await apiClient.patch(`/jobs/${job.id}`, { role_type: newRole });
                await fetchJobData();
              } catch (err) {
                console.error('Failed to switch track:', err);
              }
            }}
            className="rounded-md border border-slate-700 bg-slate-800/80 px-2.5 py-1 text-xs font-medium text-slate-300 hover:bg-slate-700 hover:text-white transition cursor-pointer"
          >
            Switch to {job.role_type === 'non_technical' ? 'Technical' : 'Non-Technical'}
          </button>
        </div>
        
        <div className="mt-8 grid grid-cols-1 gap-8 border-t border-[#1d3040] pt-8 md:grid-cols-2">
          <div>
            <h3 className="mb-3 flex items-center gap-2 text-lg font-bold text-white">
              <Briefcase className="w-5 h-5 text-[#7ef0be]" /> Role Description
            </h3>
            <p className="leading-relaxed text-slate-300">{job.description}</p>
          </div>
          <div>
            <h3 className="mb-3 flex items-center gap-2 text-lg font-bold text-white">
              <FileText className="w-5 h-5 text-[#7ef0be]" /> Core Requirements
            </h3>
            <p className="leading-relaxed text-slate-300">{job.requirements}</p>
          </div>
        </div>
      </div>

      <div className="mb-12">
        <h2 className="mb-6 text-2xl font-bold text-white">Screen Candidates</h2>
        <ResumeUploader jobId={id} onUploadSuccess={fetchJobData} />
      </div>
      
      {candidates.length > 0 && (
        <div className="mb-12">
          <h2 className="mb-2 text-2xl font-bold text-white">Ranked Shortlist</h2>
          <p className="mb-6 text-slate-300">Candidates autonomously evaluated against job requirements by AI.</p>
          <CandidateTable candidates={candidates} />
        </div>
      )}

      {/* --- EDIT JOB MODAL --- */}
      {isEditModalOpen && (
        <JobFormModal 
          onClose={() => setIsEditModalOpen(false)} 
          onSuccess={fetchJobData} 
          jobToEdit={job}
          initialRoleType={job.role_type || 'technical'}
        />
      )}
    </div>
  );
};