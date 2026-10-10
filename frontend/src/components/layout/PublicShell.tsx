import { Outlet } from "react-router-dom";

export default function PublicShell() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-50 to-brand-100 flex flex-col items-center justify-center p-4">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-brand-900">LoomLink</h1>
        <p className="text-brand-600 text-sm mt-1">Everest Textile Mills</p>
      </div>
      <Outlet />
    </div>
  );
}