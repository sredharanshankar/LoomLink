import { lazy } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import PublicShell from "./components/layout/PublicShell";
import { useAuth } from "./lib/auth";

const LoginPage = lazy(() => import("./features/auth/LoginPage"));
const PinLoginPage = lazy(() => import("./features/auth/PinLoginPage"));
const ScanResolverPage = lazy(() => import("./features/scan/ScanResolverPage"));
const DashboardPage = lazy(() => import("./features/dashboard/DashboardPage"));
const TrackPage = lazy(() => import("./features/buyer/TrackPage"));

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="flex items-center justify-center h-64 text-gray-400 text-xl">
      {title} - coming soon
    </div>
  );
}

export default function AppRouter() {
  return (
    <Routes>
      <Route element={<PublicShell />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/pin" element={<PinLoginPage />} />
        <Route path="/track/:tracking_token" element={<TrackPage />} />
        <Route path="/s/:code" element={<ScanResolverPage />} />
      </Route>
      <Route element={<RequireAuth><AppShell /></RequireAuth>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/inventory/*" element={<PlaceholderPage title="Inventory" />} />
        <Route path="/orders/*" element={<PlaceholderPage title="Orders" />} />
        <Route path="/production/*" element={<PlaceholderPage title="Production" />} />
        <Route path="/quality/*" element={<PlaceholderPage title="Quality" />} />
        <Route path="/dispatch/*" element={<PlaceholderPage title="Dispatch" />} />
        <Route path="/workers/*" element={<PlaceholderPage title="Workers" />} />
        <Route path="/finance/*" element={<PlaceholderPage title="Finance" />} />
        <Route path="/ripple/*" element={<PlaceholderPage title="Ripple" />} />
        <Route path="/admin/*" element={<PlaceholderPage title="Admin" />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}