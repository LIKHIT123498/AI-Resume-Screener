import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Dashboard } from './pages/Dashboard';
import { JobDetail } from './pages/JobDetail'; // <-- Add this import

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50 font-sans text-gray-900">
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            {/* Swap out the placeholder for the real component */}
            <Route path="/jobs/:id" element={<JobDetail />} /> 
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;