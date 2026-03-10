import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import FeedView from './views/FeedView';
import DashboardView from './views/DashboardView';
import SearchView from './views/SearchView';
import AlertsView from './views/AlertsView';
import NormDetailView from './views/NormDetailView';
import DNUTrackerView from './views/DNUTrackerView';

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <Router>
      <div className="min-h-screen bg-bg-secondary flex">
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        <div className="flex-1 flex flex-col min-h-screen lg:ml-60">
          <Header onMenuToggle={() => setSidebarOpen(!sidebarOpen)} />

          <main className="flex-1 p-4 md:p-6 lg:p-8 overflow-auto">
            <Routes>
              <Route path="/" element={<Navigate to="/feed" replace />} />
              <Route path="/feed" element={<FeedView />} />
              <Route path="/dashboard" element={<DashboardView />} />
              <Route path="/search" element={<SearchView />} />
              <Route path="/alerts" element={<AlertsView />} />
              <Route path="/dnu" element={<DNUTrackerView />} />
              <Route path="/norma/:id" element={<NormDetailView />} />
              <Route path="*" element={<Navigate to="/feed" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}
