import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { PreferencesProvider } from './context/PreferencesContext';
import { AppLayout } from './components/layout/AppLayout';
import { DashboardPage } from './pages/DashboardPage';
import { LoginPage } from './pages/LoginPage';
import { StudyAcademicPage } from './pages/StudyAcademicPage';
import { SuggestionsPage } from './pages/SuggestionsPage';
import { TasksPlannerPage } from './pages/TasksPlannerPage';
import { WealthPlannerPage } from './pages/WealthPlannerPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { SimulationPage } from './pages/SimulationPage';
import { ProfilePage } from './pages/ProfilePage';
import { SettingsPage } from './pages/SettingsPage';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin" />
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 tracking-wider uppercase">
            Loading Digital Twin...
          </span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

const PublicOnlyRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return null;
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

export function App() {
  return (
    <AuthProvider>
      <PreferencesProvider>
        <BrowserRouter>
        <Routes>
          {/* Public Auth Route */}
          <Route
            path="/login"
            element={
              <PublicOnlyRoute>
                <LoginPage />
              </PublicOnlyRoute>
            }
          />

          {/* Protected Application Routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            {/* Dashboard / Overview */}
            <Route index element={<DashboardPage />} />

            {/* Workspace Routes */}
            <Route path="tasks" element={<TasksPlannerPage />} />
            <Route path="study" element={<StudyAcademicPage />} />
            <Route path="suggestions" element={<SuggestionsPage />} />

            {/* Planning Routes */}
            <Route path="simulation" element={<SimulationPage />} />
            <Route path="wealth" element={<WealthPlannerPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />

            {/* Account Routes */}
            <Route path="profile" element={<ProfilePage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      </PreferencesProvider>
    </AuthProvider>
  );
}

export default App;
