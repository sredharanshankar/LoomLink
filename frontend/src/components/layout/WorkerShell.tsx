import { Outlet } from "react-router-dom";

export default function WorkerShell() {
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <Outlet />
    </div>
  );
}