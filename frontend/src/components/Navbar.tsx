
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
    <nav className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
      <Link to="/" className="flex items-center gap-2">
        <Briefcase className="text-blue-600 w-6 h-6" />
        <span className="text-xl font-bold text-gray-900">AI Recruiter</span>
      </Link>

      {/* 2. Add the UI button to trigger the function */}
      <button 
        onClick={handleLogout}
        className="flex items-center gap-2 text-sm font-semibold text-gray-500 hover:text-red-600 transition-colors"
      >
        <LogOut className="w-5 h-5" />
        Sign Out
      </button>
    </nav>
  );
};