import React from 'react';
import { Cpu, Users } from 'lucide-react';

interface RoleTypeSelectorProps {
  selectedRoleType: 'technical' | 'non_technical';
  onSelect: (role: 'technical' | 'non_technical') => void;
}

export const RoleTypeSelector: React.FC<RoleTypeSelectorProps> = ({
  selectedRoleType,
  onSelect,
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full my-4">
      {/* Technical / Engineering Card */}
      <div
        onClick={() => onSelect('technical')}
        className={`flex flex-col justify-between p-5 rounded-2xl border transition-all duration-200 bg-[#0e1715] cursor-pointer ${
          selectedRoleType === 'technical'
            ? 'border-[#2ad38a] ring-1 ring-[#2ad38a] shadow-[0_0_20px_rgba(42,211,138,0.15)]'
            : 'border-[#1e2f2a] hover:border-[#2ad38a]/60'
        }`}
      >
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xl font-bold text-white tracking-tight">Technical</h3>
            <Cpu className="text-[#2ad38a] w-6 h-6" />
          </div>
          <p className="text-slate-400 text-xs leading-relaxed mb-4">
            Engineered for software, data, and core engineering positions. Evaluates
            candidates using a weighted formula (50% Skills, 30% Seniority, 20% Domain).
          </p>
          <div className="inline-block bg-[#162923] text-emerald-300 text-xs px-3 py-1 rounded-full mb-4 font-medium">
            Formula: 50% Skill • 30% Seniority • 20% Domain
          </div>
        </div>

        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onSelect('technical');
          }}
          className={`w-full py-2.5 px-4 rounded-xl font-medium text-sm transition cursor-pointer ${
            selectedRoleType === 'technical'
              ? 'bg-[#2ad38a] text-[#041510] font-semibold'
              : 'bg-[#1b3b30] text-[#7ef0be] hover:bg-[#254f41]'
          }`}
        >
          {selectedRoleType === 'technical' ? 'Selected' : 'Select Technical'}
        </button>
      </div>

      {/* Non-Technical / Non-Engineering Card */}
      <div
        onClick={() => onSelect('non_technical')}
        className={`flex flex-col justify-between p-5 rounded-2xl border transition-all duration-200 bg-[#0e1715] cursor-pointer ${
          selectedRoleType === 'non_technical'
            ? 'border-[#2ad38a] ring-1 ring-[#2ad38a] shadow-[0_0_20px_rgba(42,211,138,0.15)]'
            : 'border-[#1e2f2a] hover:border-[#2ad38a]/60'
        }`}
      >
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xl font-bold text-white tracking-tight">Non-Technical</h3>
            <Users className="text-[#2ad38a] w-6 h-6" />
          </div>
          <p className="text-slate-400 text-xs leading-relaxed mb-4">
            Tailored for operations, management, HR, sales, and administrative roles. Focuses on
            adaptability, organizational impact, and general domain competencies.
          </p>
          <div className="inline-block bg-[#162923] text-emerald-300 text-xs px-3 py-1 rounded-full mb-4 font-medium">
            Formula: 40% Skill • 20% Seniority • 40% Domain
          </div>
        </div>

        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onSelect('non_technical');
          }}
          className={`w-full py-2.5 px-4 rounded-xl font-medium text-sm transition cursor-pointer ${
            selectedRoleType === 'non_technical'
              ? 'bg-[#2ad38a] text-[#041510] font-semibold'
              : 'bg-[#1b3b30] text-[#7ef0be] hover:bg-[#254f41]'
          }`}
        >
          {selectedRoleType === 'non_technical' ? 'Selected' : 'Select Non-Technical'}
        </button>
      </div>
    </div>
  );
};
