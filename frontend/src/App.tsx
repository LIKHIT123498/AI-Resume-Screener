import  { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Dashboard } from './pages/Dashboard';
import { JobDetail } from './pages/JobDetail';
import { Login } from './components/Login'; // <-- Import the new Login component

function App() {
  // Check local storage on initial load to see if a token exists
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(
    !!localStorage.getItem('token')
  );

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50 font-sans text-gray-900">
        
        {/* Only render the Navbar if the user is actually logged in */}
        {isAuthenticated && <Navbar />}
        
        <main>
          <Routes>
            {/* --- PUBLIC ROUTE --- */}
            <Route 
              path="/login" 
              element={
                isAuthenticated ? (
                  // If they are already logged in, send them to the dashboard
                  <Navigate to="/" replace /> 
                ) : (
                  <Login onLoginSuccess={() => setIsAuthenticated(true)} />
                )
              } 
            />

            {/* --- PROTECTED ROUTES --- */}
            <Route 
              path="/" 
              element={
                isAuthenticated ? <Dashboard /> : <Navigate to="/login" replace />
              } 
            />
            
            <Route 
              path="/jobs/:id" 
              element={
                isAuthenticated ? <JobDetail /> : <Navigate to="/login" replace />
              } 
            />
            
            {/* Catch-all route: redirect unknown URLs to the dashboard (or login) */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;