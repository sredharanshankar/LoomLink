import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import ScannerModal from "../../components/ui/ScannerModal";

function resolveRoute(code: string): string {
  try {
    const url = new URL(code);
    const parts = url.pathname.split("/").filter(Boolean);
    return routeForParts(parts);
  } catch { /* bare code */ }
  return routeForParts([code]);
}

function routeForParts(parts: string[]): string {
  const [prefix, id] = parts;
  if (prefix === "rolls" && id) return `/app/rolls/${id}`;
  if (prefix === "jobs" && id) return `/app/production`;
  if (prefix === "orders" && id) return `/app/orders/${id}`;
  if (prefix === "batches" && id) return `/app/inventory/batches/${id}`;
  if (prefix === "machines" && id) return `/app/machines/${id}`;
  return "/app/dashboard";
}

export default function ScanResolverPage() {
  const { code } = useParams<{ code?: string }>();
  const navigate = useNavigate();
  const [modalOpen, setModalOpen] = useState(!code);

  if (code) {
    navigate(resolveRoute(decodeURIComponent(code)), { replace: true });
    return null;
  }

  function handleScan(scanned: string) {
    setModalOpen(false);
    navigate(resolveRoute(scanned), { replace: true });
  }

  return (
    <ScannerModal
      open={modalOpen}
      onClose={() => navigate(-1)}
      onScan={handleScan}
    />
  );
}
