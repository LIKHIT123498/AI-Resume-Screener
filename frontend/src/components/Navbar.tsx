
import { Briefcase, LogOut, Cpu, Users } from 'lucide-react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';

export const Navbar = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const currentPortal = searchParams.get('portal') === 'non_technical' ? 'non_technical' : 'technical';

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
    window.location.reload();
  };

  const switchPortal = (p: 'technical' | 'non_technical') => {
    navigate(`/?portal=${p}`);
  };

  return (
    <nav className="sticky top-0 z-40 border-b border-[#1a2d3b] bg-[#07131e]/90 px-6 py-3.5 backdrop-blur-sm flex items-center justify-between gap-4">
      <Link to="/" className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-[#1c352d] text-[#7ef0be] shadow-[0_0_18px_rgba(126,240,190,0.25)]">
          <Briefcase className="w-5 h-5" />
        </div>
        <span className="text-xl font-bold tracking-tight text-white hidden sm:inline">AI Recruiter</span>
      </Link>

      {/* --- QUICK PORTAL SWITCHER IN NAVBAR --- */}
      <div className="flex items-center rounded-xl bg-[#0b1b28] border border-[#1e3447] p-1">
        <button
          onClick={() => switchPortal('technical')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
            currentPortal === 'technical'
              ? 'bg-[#2ad38a] text-[#041510] shadow-[0_0_12px_rgba(42,211,138,0.25)]'
              : 'text-slate-300 hover:text-white hover:bg-[#12283a]'
          }`}
        >
          <Cpu className="w-3.5 h-3.5" />
          <span>Technical Portal</span>
        </button>

        <button
          onClick={() => switchPortal('non_technical')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
            currentPortal === 'non_technical'
              ? 'bg-[#38bdf8] text-[#02131d] shadow-[0_0_12px_rgba(56,189,248,0.25)]'
              : 'text-slate-300 hover:text-white hover:bg-[#12283a]'
          }`}
        >
          <Users className="w-3.5 h-3.5" />
          <span>Non-Technical Portal</span>
        </button>
      </div>

      <button 
        onClick={handleLogout}
        className="flex items-center gap-2 text-sm font-semibold text-slate-200 transition-colors hover:text-[#7ef0be] cursor-pointer"
      >
        <LogOut className="w-4 h-4" />
        <span className="hidden sm:inline">Sign Out</span>
      </button>
    </nav>
  );
};