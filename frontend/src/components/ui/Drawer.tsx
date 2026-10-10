import { useEffect } from "react";
import { clsx } from "clsx";
import Button from "./Button";

interface Props {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  width?: "sm" | "md" | "lg";
}

const WIDTHS = { sm: "max-w-sm", md: "max-w-md", lg: "max-w-lg" };

export default function Drawer({ open, onClose, title, children, width = "md" }: Props) {
  useEffect(() => {
    if (!open) return;
    const handle = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handle);
    return () => document.removeEventListener("keydown", handle);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-static-element-interactions */}
      <div className="absolute inset-0 bg-black/40" role="presentation" onClick={onClose} onKeyDown={(e) => e.key === "Escape" && onClose()} />
      <div className={clsx("relative ml-auto h-full bg-white shadow-xl flex flex-col w-full", WIDTHS[width])}>
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200">
          {title && <h2 className="text-base font-semibold text-gray-900">{title}</h2>}
          <Button variant="ghost" size="sm" onClick={onClose} className="ml-auto">✕</Button>
        </div>
        <div className="flex-1 overflow-y-auto p-5">{children}</div>
      </div>
    </div>
  );
}
