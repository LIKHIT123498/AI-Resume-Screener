import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import type { Job } from '../types';
import { apiClient } from '../api/client';
import { JobCard } from '../components/JobCard';
import { JobFormModal } from '../components/JobFormModal';
import { Plus, Cpu, Users, ArrowRight } from 'lucide-react';

export const Dashboard = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingJob, setEditingJob] = useState<Job | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();

  const portalParam = searchParams.get('portal');
  const portal: 'technical' | 'non_technical' = 
    portalParam === 'non_technical' ? 'non_technical' : 'technical';

  const handleSelectPortal = (selected: 'technical' | 'non_technical') => {
    setSearchParams({ portal: selected });
  };

  const handleEditJob = (job: Job) => {
    setEditingJob(job);
  };

  const handleDeleteJob = async (job: Job) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${job.title}"?\n\nThis will permanently remove this job role and all its candidate evaluations.`
    );
    if (!confirmed) return;

    try {
      await apiClient.delete(`/jobs/${job.id}`);
      await fetchJobs();
    } catch (error) {
      console.error("Failed to delete job:", error);
      alert("Failed to delete job. Check if backend is reachable.");
    }
  };

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

  const technicalJobs = jobs.filter((j) => j.role_type !== 'non_technical');
  const nonTechnicalJobs = jobs.filter((j) => j.role_type === 'non_technical');
  const displayedJobs = portal === 'technical' ? technicalJobs : nonTechnicalJobs;

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64 text-slate-400 font-medium">
        Loading portal...
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 text-slate-100">
      {/* --- PORTAL SELECTION CARDS --- */}
      <div className="mb-10">
        <div className="mb-4">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">Recruiter Portals</h2>
          <p className="text-xs text-slate-400">Switch between dedicated tracks to view roles and applied ATS weightings.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* TECHNICAL PORTAL CARD */}
          <div
            onClick={() => handleSelectPortal('technical')}
            className={`cursor-pointer relative overflow-hidden rounded-2xl border p-6 transition-all duration-200 ${
              portal === 'technical'
                ? 'border-[#2ad38a] bg-[linear-gradient(180deg,#0e241c_0%,#081611_100%)] ring-2 ring-[#2ad38a]/40 shadow-[0_0_28px_rgba(42,211,138,0.2)]'
                : 'border-[#1e303f] bg-[#091926]/70 hover:border-slate-500 hover:bg-[#0c2030]'
            }`}
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className={`p-3 rounded-xl ${
                  portal === 'technical' ? 'bg-[#2ad38a] text-[#03170e]' : 'bg-[#152e25] text-[#7ef0be]'
                }`}>
                  <Cpu className="w-6 h-6" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-xl font-bold text-white">Technical Portal</h3>
                    {portal === 'technical' && (
                      <span className="rounded-full bg-[#2ad38a]/20 border border-[#2ad38a]/50 px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-wide text-[#5bf5b0]">
                        Active
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-300">Software, Data & Core Engineering</p>
                </div>
              </div>
              <span className="rounded-full bg-[#123126] border border-[#24534a] px-3 py-1 text-xs font-bold text-[#8beec2]">
                {technicalJobs.length} {technicalJobs.length === 1 ? 'Role' : 'Roles'}
              </span>
            </div>

            <p className="text-xs text-slate-300 mb-4 leading-relaxed">
              Tailored screening pipeline with heavy emphasis on technical competencies and stack matching.
            </p>

            <div className="flex items-center justify-between border-t border-slate-700/40 pt-3">
              <span className="text-[11px] font-medium text-emerald-300/90 bg-[#162923] px-2.5 py-1 rounded-md">
                ATS: 50% Skill • 30% Seniority • 20% Domain
              </span>
              <span className={`text-xs font-semibold flex items-center gap-1 ${
                portal === 'technical' ? 'text-[#2ad38a]' : 'text-slate-400'
              }`}>
                {portal === 'technical' ? 'Currently viewing' : 'Open portal'} <ArrowRight className="w-3.5 h-3.5" />
              </span>
            </div>
          </div>

          {/* NON-TECHNICAL PORTAL CARD */}
          <div
            onClick={() => handleSelectPortal('non_technical')}
            className={`cursor-pointer relative overflow-hidden rounded-2xl border p-6 transition-all duration-200 ${
              portal === 'non_technical'
                ? 'border-[#38bdf8] bg-[linear-gradient(180deg,#0a2133_0%,#061421_100%)] ring-2 ring-[#38bdf8]/40 shadow-[0_0_28px_rgba(56,189,248,0.2)]'
                : 'border-[#1e303f] bg-[#091926]/70 hover:border-slate-500 hover:bg-[#0c2030]'
            }`}
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className={`p-3 rounded-xl ${
                  portal === 'non_technical' ? 'bg-[#38bdf8] text-[#02131d]' : 'bg-[#0f2d42] text-[#7dd3fc]'
                }`}>
                  <Users className="w-6 h-6" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-xl font-bold text-white">Non-Technical Portal</h3>
                    {portal === 'non_technical' && (
                      <span className="rounded-full bg-[#38bdf8]/20 border border-[#38bdf8]/50 px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-wide text-[#7dd3fc]">
                        Active
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-300">Operations, Business, HR & Management</p>
                </div>
              </div>
              <span className="rounded-full bg-[#0e2c40] border border-[#1e4d6e] px-3 py-1 text-xs font-bold text-[#7dd3fc]">
                {nonTechnicalJobs.length} {nonTechnicalJobs.length === 1 ? 'Role' : 'Roles'}
              </span>
            </div>

            <p className="text-xs text-slate-300 mb-4 leading-relaxed">
              Evaluates candidates with domain impact, versatility, organizational fit, and leadership tenure.
            </p>

            <div className="flex items-center justify-between border-t border-slate-700/40 pt-3">
              <span className="text-[11px] font-medium text-sky-300/90 bg-[#0e273a] px-2.5 py-1 rounded-md">
                ATS: 40% Skill • 20% Seniority • 40% Domain
              </span>
              <span className={`text-xs font-semibold flex items-center gap-1 ${
                portal === 'non_technical' ? 'text-[#38bdf8]' : 'text-slate-400'
              }`}>
                {portal === 'non_technical' ? 'Currently viewing' : 'Open portal'} <ArrowRight className="w-3.5 h-3.5" />
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* --- SECTION HEADER & ACTIONS --- */}
      <div className="mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-[#1b2f3d] pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-black tracking-tight text-white">
              {portal === 'technical' ? 'Technical Roles' : 'Non-Technical Roles'}
            </h1>
            <span className={`rounded-full px-3 py-0.5 text-xs font-bold ${
              portal === 'technical' 
                ? 'bg-[#153427] text-[#7ef0be] border border-[#27664c]' 
                : 'bg-[#0f2d42] text-[#7dd3fc] border border-[#1e4d6e]'
            }`}>
              {displayedJobs.length} {displayedJobs.length === 1 ? 'Active Role' : 'Active Roles'}
            </span>
          </div>
          <p className="mt-1.5 text-sm text-slate-300">
            {portal === 'technical'
              ? 'Screening software engineers and technical contributors using the 50/30/20 formula.'
              : 'Screening analysts, operations, and business specialists using the 40/20/40 formula.'}
          </p>
        </div>
        
        <button 
          onClick={() => setIsModalOpen(true)}
          className={`flex items-center justify-center gap-2 rounded-xl px-5 py-3 font-semibold transition cursor-pointer ${
            portal === 'technical'
              ? 'bg-[#2ad38a] text-[#041510] shadow-[0_0_24px_rgba(42,211,138,0.35)] hover:bg-[#42df98]'
              : 'bg-[#38bdf8] text-[#02131d] shadow-[0_0_24px_rgba(56,189,248,0.35)] hover:bg-[#60a5fa]'
          }`}
        >
          <Plus className="w-5 h-5" />
          {portal === 'technical' ? 'Create Technical Job' : 'Create Non-Technical Job'}
        </button>
      </div>

      {/* --- JOBS GRID --- */}
      {displayedJobs.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-[#224154] bg-[#081b2a] p-16 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-[#112738] text-slate-400">
            {portal === 'technical' ? <Cpu className="w-6 h-6" /> : <Users className="w-6 h-6" />}
          </div>
          <h3 className="text-lg font-bold text-white mb-1">
            No {portal === 'technical' ? 'technical' : 'non-technical'} roles yet
          </h3>
          <p className="text-slate-400 text-sm max-w-md mx-auto mb-6">
            {portal === 'technical'
              ? 'Create a software, data, or engineering position to begin evaluating candidate resumes.'
              : 'Create a business analyst, operations, or management position to begin evaluating candidates.'}
          </p>
          <button 
            onClick={() => setIsModalOpen(true)}
            className={`inline-flex items-center gap-2 rounded-xl px-5 py-2.5 font-semibold text-sm transition cursor-pointer ${
              portal === 'technical'
                ? 'bg-[#2ad38a] text-[#041510] hover:bg-[#42df98]'
                : 'bg-[#38bdf8] text-[#02131d] hover:bg-[#60a5fa]'
            }`}
          >
            <Plus className="w-4 h-4" />
            {portal === 'technical' ? 'Add Technical Role' : 'Add Non-Technical Role'}
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
          {displayedJobs.map((job) => (
            <JobCard 
              key={job.id} 
              job={job} 
              onEdit={handleEditJob}
              onDelete={handleDeleteJob}
            />
          ))}
        </div>
      )}

      {/* --- CREATE OR EDIT JOB MODAL --- */}
      {(isModalOpen || editingJob) && (
        <JobFormModal 
          onClose={() => {
            setIsModalOpen(false);
            setEditingJob(null);
          }} 
          onSuccess={fetchJobs} 
          initialRoleType={portal}
          jobToEdit={editingJob || undefined}
        />
      )}
    </div>
  );
};