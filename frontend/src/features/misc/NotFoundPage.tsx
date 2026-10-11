import { Link } from "react-router-dom";
import { useAuth } from "../../lib/auth";

export default function NotFoundPage() {
  const { user } = useAuth();
  const home = user ? "/app/dashboard" : "/login";
  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8 text-center bg-gray-50">
      <p className="text-7xl font-bold text-brand-700 mb-4">404</p>
      <h1 className="text-2xl font-semibold text-gray-900 mb-2">Page not found</h1>
      <p className="text-gray-500 mb-8 max-w-sm">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <Link
        to={home}
        className="px-5 py-2.5 bg-brand-700 text-white rounded-md hover:bg-brand-800 transition-colors text-sm font-medium"
      >
        Go to dashboard
      </Link>
    </div>
  );
}
