import React from 'react';
import type { Job } from '../types';
import { Link } from 'react-router-dom';
import { Calendar, Users } from 'lucide-react';

interface Props {
  job: Job;
}

export const JobCard: React.FC<Props> = ({ job }) => {
  const date = new Date(job.created_at).toLocaleDateString();

  return (
    <div className="flex h-full flex-col rounded-2xl border border-[#2a3f4f] bg-[linear-gradient(180deg,#0d1b2a_0%,#0a1a26_100%)] p-6 shadow-[0_0_20px_rgba(30,58,80,0.35)] transition duration-200 hover:border-[#3ae1a0] hover:shadow-[0_0_28px_rgba(58,225,160,0.12)]">
      <div className="flex-grow">
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h3 className="text-[1.8rem] font-black leading-tight tracking-tight text-white">{job.title}</h3>
            <span className="mt-3 inline-block rounded-full border border-[#24534a] bg-[#12382f] px-3 py-1 text-xs font-bold uppercase tracking-[0.08em] text-[#8beec2]">
              {job.department || 'General'}
            </span>
          </div>
        </div>
        <p className="mb-6 text-sm leading-7 text-slate-300 line-clamp-3">
          {job.description}
        </p>
      </div>
      
      <div className="mb-6 flex items-center gap-4 text-sm text-slate-400">
        <div className="flex items-center gap-1.5">
          <Calendar className="w-4 h-4" />
          <span>{date}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Users className="w-4 h-4" />
          <span>AI Ready</span>
        </div>
      </div>

      <Link 
        to={`/jobs/${job.id}`}
        className="block w-full rounded-xl border border-[#2bd690] bg-[#2ad38a] px-4 py-3 text-center text-base font-bold text-[#02170f] transition hover:bg-[#42df98]"
      >
        View & Screen Candidates
      </Link>
    </div>
  );
};