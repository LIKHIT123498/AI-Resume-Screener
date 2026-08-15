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
      <div className="overflow-x-auto bg-white rounded-xl shadow-sm border border-gray-200 mt-8">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50 text-gray-700 font-semibold">
            <tr>
              <th className="py-4 px-6 text-left">Rank</th>
              <th className="py-4 px-6 text-left">Candidate Info</th>
              <th className="py-4 px-6 text-center">Fit Score</th>
              <th className="py-4 px-6 text-left">Matched Skills</th>
              <th className="py-4 px-6 text-left w-1/3">AI Insight</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {sortedCandidates.map((candidate, index) => (
              <tr 
                key={candidate.id} 
                onClick={() => setSelectedCandidate(candidate)} // <-- Make row clickable
                className="hover:bg-blue-50 transition cursor-pointer" // <-- Add pointer cursor
              >
                <td className="py-4 px-6 font-bold text-gray-400 text-lg">#{index + 1}</td>
                <td className="py-4 px-6">
                  <div className="font-bold text-gray-900">{candidate.name || 'Anonymous'}</div>
                  <div className="text-gray-500 text-xs mt-1">{candidate.email}</div>
                </td>
                <td className="py-4 px-6 text-center">
                  <span className={`px-3 py-1.5 rounded-full text-sm font-bold ${
                    candidate.overall_fit_score >= 75 ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' :
                    candidate.overall_fit_score >= 50 ? 'bg-amber-100 text-amber-800 border border-amber-200' : 
                    'bg-red-100 text-red-800 border border-red-200'
                  }`}>
                    {candidate.overall_fit_score}%
                  </span>
                </td>
                <td className="py-4 px-6">
                  <div className="flex flex-wrap gap-1.5">
                    {candidate.extracted_skills?.slice(0, 4).map((skill, i) => (
                      <span key={i} className="bg-gray-100 text-gray-700 border border-gray-200 px-2 py-0.5 rounded text-xs font-medium">
                        {skill}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="py-4 px-6 text-gray-600 truncate max-w-xs">
                  {candidate.one_line_summary}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Render the modal if a candidate is clicked */}
      {selectedCandidate && (
        <CandidateDetailModal 
          candidate={selectedCandidate} 
          onClose={() => setSelectedCandidate(null)} 
        />
      )}
    </>
  );
};