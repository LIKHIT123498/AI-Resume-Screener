import React, { useState } from 'react'; // <-- Fixed typo here
import { apiClient } from '../api/client'; // <-- Fixed import here

interface Props {
  onLoginSuccess: () => void;
}

export const Login: React.FC<Props> = ({ onLoginSuccess }) => {
  const [isLoginMode, setIsLoginMode] = useState(true); 
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      if (!isLoginMode) {
        // --- SIGN UP FLOW ---
        // Updated to use apiClient
        await apiClient.post(`/auth/register?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`);
      }

      // --- LOGIN FLOW ---
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      // Updated to use apiClient
      const response = await apiClient.post('/auth/token', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });

      localStorage.setItem('token', response.data.access_token);
      onLoginSuccess();
      
    } catch (err: any) {
      if (err.response?.status === 400 && !isLoginMode) {
        setError('An account with this email already exists.');
      } else {
        setError(isLoginMode ? 'Invalid email or password. Please try again.' : 'Failed to create account. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#020b14] p-4">
      <div className="w-full max-w-md rounded-2xl border border-[#1f3343] bg-[#0a1725] p-8 shadow-[0_0_32px_rgba(15,23,42,0.7)]">
        
        <h2 className="mb-2 text-3xl font-black tracking-tight text-white">
          {isLoginMode ? 'Welcome Back' : 'Create an Account'}
        </h2>
        <p className="mb-6 text-slate-300">
          {isLoginMode ? 'Log in to access your recruitment dashboard.' : 'Sign up to start screening resumes with AI.'}
        </p>

        {error && (
          <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-200">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-semibold text-slate-200">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full rounded-xl border border-[#2d4256] bg-[#091c2d] px-4 py-2.5 text-white placeholder:text-slate-400 focus:border-[#2ad38a] focus:outline-none focus:ring-2 focus:ring-[#2ad38a]/40"
              placeholder="recruiter@company.com"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-semibold text-slate-200">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              className="w-full rounded-xl border border-[#2d4256] bg-[#091c2d] px-4 py-2.5 text-white placeholder:text-slate-400 focus:border-[#2ad38a] focus:outline-none focus:ring-2 focus:ring-[#2ad38a]/40"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full rounded-xl bg-[#2ad38a] py-3 font-bold text-[#03150d] transition hover:bg-[#42df98] disabled:opacity-50"
          >
            {isLoading ? 'Processing...' : (isLoginMode ? 'Sign In' : 'Sign Up')}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-slate-300">
          {isLoginMode ? "Don't have an account? " : "Already have an account? "}
          <button 
            type="button"
            onClick={() => {
              setIsLoginMode(!isLoginMode);
              setError('');
            }}
            className="font-bold text-[#7ef0be] hover:underline focus:outline-none"
          >
            {isLoginMode ? 'Sign Up' : 'Sign In'}
          </button>
        </div>

      </div>
    </div>
  );
};