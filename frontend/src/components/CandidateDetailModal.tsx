import React from 'react';
import { X, AlertTriangle, CheckCircle} from 'lucide-react';
import type { Candidate } from '../types';

interface Props {
  candidate: Candidate;
  onClose: () => void;
}

export const CandidateDetailModal: React.FC<Props> = ({ candidate, onClose }) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="flex max-h-[90vh] w-full max-w-2xl flex-col overflow-hidden rounded-2xl border border-[#24384b] bg-[#081b2a] shadow-[0_0_32px_rgba(15,23,42,0.7)]">
        
        <div className="flex items-center justify-between border-b border-[#1b2f3d] bg-[#0f2537] p-6">
          <div>
            <h2 className="text-2xl font-bold text-white">{candidate.name || 'Anonymous Candidate'}</h2>
            <p className="mt-1 text-slate-300">{candidate.email} • {candidate.phone}</p>
          </div>
          <button onClick={onClose} className="rounded-full p-2 transition hover:bg-[#162f43]">
            <X className="w-6 h-6 text-slate-300" />
          </button>
        </div>

        <div className="overflow-y-auto p-6">
          <div className="mb-6 rounded-xl border border-[#1f5f4a] bg-[#12382f] p-4">
            <p className="font-medium text-[#d9f8ea]">"{candidate.one_line_summary}"</p>
          </div>

          <div className="mb-6 grid grid-cols-3 gap-4">
            <ScoreCard title="Skills Match" score={candidate.skills_score} />
            <ScoreCard title="Seniority Fit" score={candidate.seniority_score} />
            <ScoreCard title="Domain Exp." score={candidate.domain_score} />
          </div>

          <div className="mb-6 flex items-center justify-between rounded-xl border border-[#213548] bg-[#0d2134] p-4">
            <div>
              <h4 className="mb-1 text-sm font-bold uppercase tracking-wider text-slate-400">Career Stints</h4>
              <p className="font-medium text-slate-100">
                Total Company Changes: <span className="font-black text-[#7ef0be]">{candidate.company_changes}</span>
              </p>
            </div>
            <div className="text-right">
              <h4 className="mb-1 text-sm font-bold uppercase tracking-wider text-slate-400">Avg Tenure (Last 3)</h4>
              <p className="font-medium text-slate-100">
                <span className="font-black text-[#7ef0be]">{candidate.avg_duration_months}</span> months
              </p>
            </div>
          </div>

          <div className="mb-6">
            <h3 className="mb-3 flex items-center gap-2 text-lg font-bold text-white">
              <AlertTriangle className="w-5 h-5 text-amber-400" /> Detected Red Flags
            </h3>
            {candidate.red_flags.length > 0 ? (
              <ul className="space-y-2">
                {candidate.red_flags.map((flag, idx) => (
                  <li key={idx} className="flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-red-100">
                    <span className="mt-0.5">•</span>
                    <span>{flag}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-emerald-100">
                <CheckCircle className="w-5 h-5" /> No critical red flags detected.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const ScoreCard = ({ title, score }: { title: string, score: number }) => (
  <div className="rounded-xl border border-[#213548] bg-[#0d2134] p-4 text-center shadow-sm">
    <div className="mb-1 text-sm font-semibold text-slate-400">{title}</div>
    <div className={`text-3xl font-black ${score >= 75 ? 'text-[#7ef0be]' : score >= 50 ? 'text-amber-300' : 'text-red-300'}`}>
      {score}%
    </div>
  </div>
);