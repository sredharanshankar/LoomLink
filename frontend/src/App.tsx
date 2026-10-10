import { Suspense } from "react";
import AppRouter from "./router";
import { AuthProvider } from "./lib/auth";

export default function App() {
  return (
    <AuthProvider>
      <Suspense fallback={<div className="flex items-center justify-center h-screen">Loading…</div>}>
        <AppRouter />
      </Suspense>
    </AuthProvider>
  );
}