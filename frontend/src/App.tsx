import { Suspense } from "react";
import AppRouter from "./router";
import { AuthProvider } from "./lib/auth";
import OfflineBanner from "./components/ui/OfflineBanner";

export default function App() {
  return (
    <AuthProvider>
      <OfflineBanner />
      <Suspense fallback={<div className="flex items-center justify-center h-screen">Loading…</div>}>
        <AppRouter />
      </Suspense>
    </AuthProvider>
  );
}