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
    success: "bg-emerald-500",
    error: "bg-red-500",
    warning: "bg-amber-500",
    info: "bg-brand-500",
  };

  return (
    <ToastContext.Provider value={{ show }}>
      {children}
      <div className="fixed bottom-4 right-4 z-[100] space-y-2" aria-live="polite">
        {toasts.map((t) => (
          <div
            key={t.id}
            className="theme-light flex animate-fade-up items-center gap-3 rounded-xl bg-gray-900 py-3 pl-3 pr-4 text-sm text-white shadow-pop"
          >
            <span className={clsx("h-8 w-1 rounded-full", COLOR[t.type])} />
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
