import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./hooks/useAuth";
import AppLayout from "./layouts/AppLayout";

import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import IdentitiesPage from "./pages/IdentitiesPage";
import IdentityProfilePage from "./pages/IdentityProfilePage";
import VerificationPage from "./pages/VerificationPage";
import DocumentsPage from "./pages/DocumentsPage";
import DeepfakePage from "./pages/DeepfakePage";
import VoicePage from "./pages/VoicePage";
import FraudPage from "./pages/FraudPage";
import AlertsPage from "./pages/AlertsPage";
import GraphPage from "./pages/GraphPage";
import CopilotPage from "./pages/CopilotPage";
import AuditPage from "./pages/AuditPage";
import SettingsPage from "./pages/SettingsPage";

function PrivateRoute({ children }: { children: React.ReactElement }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen flex items-center justify-center text-slate-500">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <PrivateRoute>
                <AppLayout />
              </PrivateRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="identities" element={<IdentitiesPage />} />
            <Route path="identities/:id" element={<IdentityProfilePage />} />
            <Route path="verification" element={<VerificationPage />} />
            <Route path="documents" element={<DocumentsPage />} />
            <Route path="deepfake" element={<DeepfakePage />} />
            <Route path="voice" element={<VoicePage />} />
            <Route path="fraud" element={<FraudPage />} />
            <Route path="alerts" element={<AlertsPage />} />
            <Route path="graph" element={<GraphPage />} />
            <Route path="copilot" element={<CopilotPage />} />
            <Route path="audit" element={<AuditPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
