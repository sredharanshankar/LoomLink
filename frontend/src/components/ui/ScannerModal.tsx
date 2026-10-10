import { useEffect, useRef, useState, useCallback } from "react";
import { Html5Qrcode } from "html5-qrcode";
import Button from "./Button";

interface Props {
  open: boolean;
  onClose: () => void;
  onScan: (code: string) => void;
}

function beep() {
  try {
    const ctx = new AudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.frequency.value = 880;
    gain.gain.setValueAtTime(0.1, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.15);
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + 0.15);
    ctx.close();
  } catch { /* AudioContext unavailable */ }
}

function parseCode(raw: string): string {
  try {
    const url = new URL(raw);
    const parts = url.pathname.split("/").filter(Boolean);
    if (parts[0] === "s" && parts[1]) return parts[1];
  } catch { /* not a URL */ }
  return raw;
}

const DEBOUNCE_MS = 1500;
const QR_ELEMENT_ID = "scanner-modal-qr";

export default function ScannerModal({ open, onClose, onScan }: Props) {
  const qrRef = useRef<Html5Qrcode | null>(null);
  const lastRef = useRef<{ code: string; ts: number } | null>(null);
  const [torchOn, setTorchOn] = useState(false);
  const [torchSupported, setTorchSupported] = useState(false);
  const [permDenied, setPermDenied] = useState(false);
  const [cameraReady, setCameraReady] = useState(false);
  const [manual, setManual] = useState("");

  const dispatch = useCallback(
    (raw: string) => {
      const code = parseCode(raw.trim());
      if (!code) return;
      const now = Date.now();
      if (lastRef.current?.code === code && now - lastRef.current.ts < DEBOUNCE_MS) return;
      lastRef.current = { code, ts: now };
      try { navigator.vibrate?.(200); } catch { /* not supported */ }
      beep();
      onScan(code);
    },
    [onScan]
  );

  useEffect(() => {
    if (!open) return;
    setPermDenied(false);
    setCameraReady(false);
    setTorchSupported(false);
    setTorchOn(false);

    const qr = new Html5Qrcode(QR_ELEMENT_ID);
    qrRef.current = qr;

    qr.start(
      { facingMode: "environment" },
      { fps: 10, qrbox: { width: 250, height: 250 } },
      dispatch,
      undefined
    )
      .then(() => {
        setCameraReady(true);
        try {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const caps = (qr as any).getRunningTrackCapabilities?.() as MediaTrackCapabilities | undefined;
          if (typeof (caps as Record<string, unknown> | undefined)?.torch !== "undefined") {
            setTorchSupported(true);
          }
        } catch { /* torch detection failed */ }
      })
      .catch((err: unknown) => {
        const msg = String(err).toLowerCase();
        if (msg.includes("permission") || msg.includes("notallowed") || msg.includes("denied")) {
          setPermDenied(true);
        }
      });

    return () => {
      qr.isScanning && qr.stop().catch(() => {});
      qrRef.current = null;
    };
  }, [open, dispatch]);

  async function toggleTorch() {
    const qr = qrRef.current;
    if (!qr) return;
    const next = !torchOn;
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      await (qr as any).applyVideoConstraints({ advanced: [{ torch: next }] });
      setTorchOn(next);
    } catch { /* torch not writable */ }
  }

  function submitManual() {
    const v = manual.trim();
    if (!v) return;
    dispatch(v);
    setManual("");
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex flex-col bg-black/95"
      role="dialog"
      aria-modal="true"
      aria-label="QR / Barcode Scanner"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 text-white shrink-0">
        <span className="font-semibold text-lg">Scan QR / Barcode</span>
        <button
          onClick={onClose}
          className="text-white/70 hover:text-white text-2xl leading-none w-10 h-10 flex items-center justify-center rounded-full hover:bg-white/10"
          aria-label="Close scanner"
        >
          ✕
        </button>
      </div>

      {permDenied ? (
        <div className="flex-1 flex flex-col items-center justify-center gap-4 px-6 text-center text-white">
          <p className="text-5xl">📷</p>
          <p className="text-xl font-semibold">Camera access denied</p>
          <p className="text-sm text-white/70 max-w-xs">
            Allow camera access in your browser or system settings, then reload the page and try again.
          </p>
          <Button variant="secondary" onClick={onClose}>Close</Button>
        </div>
      ) : (
        <>
          <div className="flex-1 flex items-center justify-center overflow-hidden">
            <div id={QR_ELEMENT_ID} className="w-full max-w-sm" />
          </div>

          <div className="shrink-0 px-4 pb-8 pt-3 space-y-3 bg-gradient-to-t from-black to-transparent">
            {torchSupported && cameraReady && (
              <Button variant="secondary" className="w-full" onClick={toggleTorch}>
                {torchOn ? "🔦 Torch Off" : "🔦 Torch On"}
              </Button>
            )}
            <div className="flex gap-2">
              <input
                type="text"
                value={manual}
                onChange={(e) => setManual(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && submitManual()}
                placeholder="Enter code manually…"
                className="flex-1 rounded-md border border-gray-600 bg-gray-800 text-white px-3 py-2 text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-brand-500"
                aria-label="Manual code entry"
              />
              <Button onClick={submitManual} disabled={!manual.trim()}>
                Go
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
