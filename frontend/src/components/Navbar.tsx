import React from 'react';
import { Briefcase } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Navbar = () => {
  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
      <Link to="/" className="flex items-center gap-2">
        <Briefcase className="text-blue-600 w-6 h-6" />
        <span className="text-xl font-bold text-gray-900">AI Recruiter</span>
      </Link>
    </nav>
  );
};