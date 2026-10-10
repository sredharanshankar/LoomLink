import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Html5Qrcode } from "html5-qrcode";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";

export default function ScanResolverPage() {
  const { code } = useParams<{ code?: string }>();
  const navigate = useNavigate();
  const [scanning, setScanning] = useState(!code);
  const [error, setError] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (code) { resolve(code); return; }
    if (!containerRef.current) return;
    const qr = new Html5Qrcode("qr-reader");
    qr.start(
      { facingMode: "environment" },
      { fps: 10, qrbox: { width: 250, height: 250 } },
      (decoded) => { qr.stop().then(() => resolve(decoded)).catch(() => {}); },
      undefined
    ).catch((err) => setError(String(err)));
    return () => { qr.isScanning && qr.stop().catch(() => {}); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code]);

  function resolve(raw: string) {
    setScanning(false);
    try {
      const url = new URL(raw);
      const parts = url.pathname.split("/");
      const prefix = parts[1];
      const id = parts[2];
      if (prefix === "rolls") navigate("/quality/rolls/" + id);
      else if (prefix === "jobs") navigate("/production/jobs/" + id);
      else if (prefix === "orders") navigate("/orders/" + id);
      else navigate("/dashboard");
    } catch { navigate("/dashboard"); }
  }

  return (
    <div className="flex items-center justify-center min-h-screen p-4">
      <Card className="w-full max-w-sm text-center">
        <h2 className="text-xl font-semibold mb-4">Scan QR Code</h2>
        {scanning ? (
          <><div id="qr-reader" ref={containerRef} className="w-full" />{error && <p className="text-sm text-red-600 mt-2">{error}</p>}</>
        ) : <Spinner className="mx-auto" />}
        <Button variant="ghost" onClick={() => navigate(-1)} className="mt-4">Cancel</Button>
      </Card>
    </div>
  );
}