import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import ScannerModal from "../../components/ui/ScannerModal";
import { api } from "../../lib/api";
import { useAuthStore } from "../../lib/auth";

interface ScanResult {
  type: string;
  id: string;
  code: string;
}

const WORKER_ROLES = new Set(["operator", "qc_inspector", "dispatch"]);
const EMPLOYEE_ROLES = new Set(["operator"]);

function extractCode(raw: string): string {
  try {
    const url = new URL(raw);
    const parts = url.pathname.split("/").filter(Boolean);
    // /s/{code} → return the code segment
    if (parts[0] === "s" && parts[1]) return parts[1].toUpperCase();
    return (parts[parts.length - 1] || raw).toUpperCase();
  } catch {
    return raw.toUpperCase();
  }
}

function routeForResult(result: ScanResult, role: string | undefined): string {
  const isWorker = WORKER_ROLES.has(role ?? "");
  switch (result.type) {
    case "machine":
      return isWorker ? `/w/machine/${result.id}` : `/app/machines/${result.id}`;
    case "roll":
      return isWorker ? `/w/roll/${result.id}` : `/app/rolls/${result.id}`;
    case "yarn_batch":
      return `/app/inventory/batches/${result.id}`;
    case "order":
      return `/app/orders/${result.id}`;
    case "worker":
      return `/app/workers`;
    default:
      return isWorker ? "/w" : "/app/dashboard";
  }
}

function ScanResolver({ rawCode }: { rawCode: string }) {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const code = extractCode(rawCode);

  const { data, error } = useQuery({
    queryKey: ["scan-resolve", code],
    queryFn: () => api.get<ScanResult>(`/scan/${encodeURIComponent(code)}`),
    retry: false,
  });

  useEffect(() => {
    if (data) {
      navigate(routeForResult(data, user?.role), { replace: true });
    } else if (error) {
      navigate(user && WORKER_ROLES.has(user.role) ? "/w" : "/app/dashboard", { replace: true });
    }
  }, [data, error, user, navigate]);

  return (
    <div className="flex h-full items-center justify-center p-8">
      <p className="text-sm text-gray-500">Resolving {code}…</p>
    </div>
  );
}

export default function ScanResolverPage() {
  const { code } = useParams<{ code?: string }>();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const [modalOpen, setModalOpen] = useState(!code);

  // QR code link (with code) — resolve for anyone, route by role
  if (code) {
    return <ScanResolver rawCode={decodeURIComponent(code)} />;
  }

  // Camera scanner mode (no code) — employees only
  if (!user) {
    navigate("/pin", { replace: true });
    return null;
  }
  if (!EMPLOYEE_ROLES.has(user.role)) {
    navigate("/app/dashboard", { replace: true });
    return null;
  }

  function handleScan(scanned: string) {
    setModalOpen(false);
    navigate(`/s/${encodeURIComponent(extractCode(scanned))}`, { replace: true });
  }

  return (
    <ScannerModal
      open={modalOpen}
      onClose={() => navigate("/w", { replace: true })}
      onScan={handleScan}
    />
  );
}
