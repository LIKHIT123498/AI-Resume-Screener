import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { apiClient, GOOGLE_AUTH_URL } from '../api/client';

interface Props {
  onLoginSuccess: () => void;
}

export const Login: React.FC<Props> = ({ onLoginSuccess }) => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [isLoginMode, setIsLoginMode] = useState(true); 
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Intercept Google OAuth callback redirect containing ?token=... or ?error=...
  useEffect(() => {
    const token = searchParams.get('token');
    const authError = searchParams.get('error');

    if (token) {
      localStorage.setItem('token', token);
      onLoginSuccess();
      navigate('/', { replace: true });
    } else if (authError) {
      setError(`Google Sign-In failed: ${decodeURIComponent(authError)}`);
    }
  }, [searchParams, onLoginSuccess, navigate]);

  const handleGoogleSignIn = () => {
    window.location.href = GOOGLE_AUTH_URL;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      if (!isLoginMode) {
        // --- SIGN UP FLOW ---
        await apiClient.post(`/auth/register?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`);
      }

      // --- LOGIN FLOW ---
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

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

        {/* --- GOOGLE SIGN-IN BUTTON --- */}
        <button
          type="button"
          onClick={handleGoogleSignIn}
          className="mb-5 flex w-full items-center justify-center gap-3 rounded-xl border border-[#2d4256] bg-[#0c1f31] py-2.5 font-semibold text-white shadow-sm transition hover:bg-[#132c45] active:scale-[0.99]"
        >
          <svg className="h-5 w-5" viewBox="0 0 24 24">
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
            />
          </svg>
          Continue with Google
        </button>

        <div className="relative mb-5 flex items-center justify-center">
          <div className="w-full border-t border-[#1f3343]"></div>
          <span className="bg-[#0a1725] px-3 text-xs uppercase tracking-wider text-slate-400">or with email</span>
          <div className="w-full border-t border-[#1f3343]"></div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-semibold text-slate-200">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full rounded-xl border border-[#2d4256] bg-[#091c2d] px-4 py-2.5 text-white placeholder:text-slate-400 focus:border-[#2ad38a] focus:outline-none focus:ring-2 focus:ring-[#2ad38a]/40"
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