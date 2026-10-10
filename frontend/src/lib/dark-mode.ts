import { useEffect, useState } from "react";

function getStored(): boolean | null {
  try {
    const v = localStorage.getItem("ll-dark");
    if (v === "true") return true;
    if (v === "false") return false;
  } catch { /* private browsing */ }
  return null;
}

function applyClass(dark: boolean) {
  document.documentElement.classList.toggle("dark", dark);
}

export function useDarkMode() {
  const [dark, setDark] = useState<boolean>(() => {
    const stored = getStored();
    if (stored !== null) return stored;
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  });

  useEffect(() => {
    applyClass(dark);
    try { localStorage.setItem("ll-dark", String(dark)); } catch { /* ignore */ }
  }, [dark]);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const handle = (e: MediaQueryListEvent) => {
      if (getStored() === null) setDark(e.matches);
    };
    mq.addEventListener("change", handle);
    return () => mq.removeEventListener("change", handle);
  }, []);

  return { dark, toggle: () => setDark((d) => !d) };
}

// Apply immediately to prevent flash
(function () {
  const stored = getStored();
  const dark = stored !== null ? stored : window.matchMedia("(prefers-color-scheme: dark)").matches;
  applyClass(dark);
})();
