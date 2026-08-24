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
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-8 border border-gray-100">
        
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          {isLoginMode ? 'Welcome Back' : 'Create an Account'}
        </h2>
        <p className="text-gray-500 mb-6">
          {isLoginMode ? 'Log in to access your recruitment dashboard.' : 'Sign up to start screening resumes with AI.'}
        </p>

        {error && (
          <div className="bg-red-50 border border-red-100 text-red-700 p-3 rounded-lg mb-4 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
              placeholder="recruiter@company.com"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 rounded-lg transition disabled:opacity-50"
          >
            {isLoading ? 'Processing...' : (isLoginMode ? 'Sign In' : 'Sign Up')}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-gray-600">
          {isLoginMode ? "Don't have an account? " : "Already have an account? "}
          <button 
            type="button"
            onClick={() => {
              setIsLoginMode(!isLoginMode);
              setError('');
            }}
            className="text-blue-600 font-bold hover:underline focus:outline-none"
          >
            {isLoginMode ? 'Sign Up' : 'Sign In'}
          </button>
        </div>

      </div>
    </div>
  );
};