import React, { useState } from 'react';
import type { Candidate } from '../types';
import { CandidateDetailModal } from './CandidateDetailModal'; // <-- Import the modal

interface Props {
  candidates: Candidate[];
}

export const CandidateTable: React.FC<Props> = ({ candidates }) => {
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null); // <-- Add state

  if (candidates.length === 0) return null;
  const sortedCandidates = [...candidates].sort((a, b) => b.overall_fit_score - a.overall_fit_score);

  return (
    <>
      <div className="mt-8 overflow-x-auto rounded-xl border border-[#213548] bg-[#081b2a] shadow-[0_0_20px_rgba(15,23,42,0.45)]">
        <table className="min-w-full divide-y divide-[#213548] text-sm">
          <thead className="bg-[#0d2134] font-semibold text-slate-200">
            <tr>
              <th className="px-6 py-4 text-left">Rank</th>
              <th className="px-6 py-4 text-left">Candidate Info</th>
              <th className="px-6 py-4 text-center">Fit Score</th>
              <th className="px-6 py-4 text-left">Matched Skills</th>
              <th className="w-1/3 px-6 py-4 text-left">AI Insight</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#213548]">
            {sortedCandidates.map((candidate, index) => (
              <tr 
                key={candidate.id} 
                onClick={() => setSelectedCandidate(candidate)}
                className="cursor-pointer transition hover:bg-[#10293d]"
              >
                <td className="px-6 py-4 text-lg font-bold text-slate-400">#{index + 1}</td>
                <td className="px-6 py-4">
                  <div className="font-bold text-white">{candidate.name || 'Anonymous'}</div>
                  <div className="mt-1 text-xs text-slate-400">{candidate.email}</div>
                </td>
                <td className="px-6 py-4 text-center">
                  <span className={`rounded-full border px-3 py-1.5 text-sm font-bold ${
                    candidate.overall_fit_score >= 75 ? 'border-[#1f5f4a] bg-[#173b2f] text-[#8beec2]' :
                    candidate.overall_fit_score >= 50 ? 'border-[#7b5b27] bg-[#3b2c1d] text-[#f7d77d]' : 
                    'border-[#6a2f39] bg-[#2a1d2a] text-[#ff9aa5]'
                  }`}>
                    {candidate.overall_fit_score}%
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="flex flex-wrap gap-1.5">
                    {candidate.extracted_skills?.slice(0, 4).map((skill, i) => (
                      <span key={i} className="rounded border border-[#27465c] bg-[#10293d] px-2 py-0.5 text-xs font-medium text-slate-200">
                        {skill}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="max-w-xs truncate px-6 py-4 text-slate-300">
                  {candidate.one_line_summary}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedCandidate && (
        <CandidateDetailModal 
          candidate={selectedCandidate} 
          onClose={() => setSelectedCandidate(null)} 
        />
      )}
    </>
  );
};