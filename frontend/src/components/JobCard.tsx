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
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition duration-200 flex flex-col h-full">
      <div className="flex-grow">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-lg font-bold text-gray-900">{job.title}</h3>
            <span className="inline-block bg-blue-50 text-blue-700 text-xs font-semibold px-2.5 py-1 rounded-full mt-2">
              {job.department || 'General'}
            </span>
          </div>
        </div>
        <p className="text-gray-600 text-sm mb-6 line-clamp-3">
          {job.description}
        </p>
      </div>
      
      <div className="flex items-center gap-4 text-sm text-gray-500 mb-6">
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
        className="block w-full text-center bg-gray-50 hover:bg-gray-100 text-gray-700 font-semibold py-2.5 rounded-md border border-gray-200 transition"
      >
        View & Screen Candidates
      </Link>
    </div>
  );
};