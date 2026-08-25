
import { Briefcase, LogOut } from 'lucide-react'; // <-- Added LogOut icon
import { Link } from 'react-router-dom';
import { useNavigate } from 'react-router-dom';
export const Navbar = () => {
  const navigate = useNavigate();
  // 1. Logic goes ABOVE the return statement
 const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login'); // Cleanly tells React Router to go to login
    window.location.reload(); // Optional: clears any cached app state
  };

  return (
    <nav className="sticky top-0 z-40 border-b border-[#1a2d3b] bg-[#07131e]/90 px-6 py-4 backdrop-blur-sm flex items-center justify-between">
      <Link to="/" className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-[#1c352d] text-[#7ef0be] shadow-[0_0_18px_rgba(126,240,190,0.25)]">
          <Briefcase className="w-5 h-5" />
        </div>
        <span className="text-2xl font-bold tracking-tight text-white">AI Recruiter</span>
      </Link>

      <button 
        onClick={handleLogout}
        className="flex items-center gap-2 text-sm font-semibold text-slate-200 transition-colors hover:text-[#7ef0be]"
      >
        <LogOut className="w-5 h-5" />
        Sign Out
      </button>
    </nav>
  );
};