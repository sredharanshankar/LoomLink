import { useEffect, useState } from "react";

export type LiveStatus = "connected" | "reconnecting" | "offline";

export function useLiveStatus(): LiveStatus {
  const [status, setStatus] = useState<LiveStatus>(
    navigator.onLine ? "connected" : "offline"
  );

  useEffect(() => {
    const onOnline = () => setStatus("connected");
    const onOffline = () => setStatus("offline");
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    return () => {
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
    };
  }, []);

  return status;
}
