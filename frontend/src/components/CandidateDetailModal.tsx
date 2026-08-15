import React from 'react';
import { X, AlertTriangle, CheckCircle, BarChart3 } from 'lucide-react';
import type { Candidate } from '../types';

interface Props {
  candidate: Candidate;
  onClose: () => void;
}

export const CandidateDetailModal: React.FC<Props> = ({ candidate, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-100 bg-gray-50/50">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{candidate.name || 'Anonymous Candidate'}</h2>
            <p className="text-gray-500 mt-1">{candidate.email} • {candidate.phone}</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-200 rounded-full transition">
            <X className="w-6 h-6 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto">
          <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 mb-6">
            <p className="text-blue-900 font-medium">"{candidate.one_line_summary}"</p>
          </div>

          <div className="grid grid-cols-3 gap-4 mb-8">
            <ScoreCard title="Skills Match" score={candidate.skills_score} />
            <ScoreCard title="Seniority Fit" score={candidate.seniority_score} />
            <ScoreCard title="Domain Exp." score={candidate.domain_score} />
          </div>

          {/* Red Flags Section */}
          <div className="mb-6">
            <h3 className="flex items-center gap-2 font-bold text-gray-900 mb-3 text-lg">
              <AlertTriangle className="w-5 h-5 text-amber-500" /> Detected Red Flags
            </h3>
            {candidate.red_flags.length > 0 ? (
              <ul className="space-y-2">
                {candidate.red_flags.map((flag, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-red-700 bg-red-50 p-3 rounded-lg border border-red-100">
                    <span className="mt-0.5">•</span>
                    <span>{flag}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-emerald-700 bg-emerald-50 p-3 rounded-lg border border-emerald-100 flex items-center gap-2">
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
  <div className="bg-white border border-gray-200 rounded-xl p-4 text-center shadow-sm">
    <div className="text-gray-500 text-sm font-semibold mb-1">{title}</div>
    <div className={`text-3xl font-black ${score >= 75 ? 'text-emerald-600' : score >= 50 ? 'text-amber-500' : 'text-red-500'}`}>
      {score}%
    </div>
  </div>
);