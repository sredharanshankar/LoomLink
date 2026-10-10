import { createContext, useContext, useState, useCallback } from "react";
import { clsx } from "clsx";

type ToastType = "success" | "error" | "info" | "warning";

interface Toast {
  id: number;
  message: string;
  type: ToastType;
}

interface ToastContextValue {
  show: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextValue>({ show: () => {} });

// eslint-disable-next-line react-refresh/only-export-components
export function useToast() { return useContext(ToastContext); }

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const show = useCallback((message: string, type: ToastType = "info") => {
    const id = Date.now();
    setToasts((t) => [...t, { id, message, type }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3500);
  }, []);

  const COLOR: Record<ToastType, string> = {
    success: "bg-green-700",
    error: "bg-red-700",
    warning: "bg-yellow-600",
    info: "bg-brand-700",
  };

  return (
    <ToastContext.Provider value={{ show }}>
      {children}
      <div className="fixed bottom-4 right-4 z-[100] space-y-2">
        {toasts.map((t) => (
          <div key={t.id} className={clsx("flex items-center gap-3 px-4 py-3 rounded-lg text-white text-sm shadow-lg", COLOR[t.type])}>
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
