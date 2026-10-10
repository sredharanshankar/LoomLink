import { WifiOff } from "lucide-react";
import { useLiveStatus } from "../../lib/live-status";

export default function OfflineBanner() {
  const status = useLiveStatus();
  if (status === "connected") return null;
  return (
    <div
      role="alert"
      aria-live="assertive"
      className="fixed top-0 inset-x-0 z-50 flex items-center justify-center gap-2 bg-red-600 text-white text-sm px-4 py-2"
    >
      <WifiOff className="h-4 w-4 shrink-0" />
      <span>
        {status === "offline"
          ? "You're offline. Some actions are disabled."
          : "Reconnecting to server…"}
      </span>
    </div>
  );
}
