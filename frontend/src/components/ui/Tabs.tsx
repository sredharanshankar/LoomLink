import { createContext, useContext, useState } from "react";
import { clsx } from "clsx";

interface TabsContextValue { active: string; setActive: (v: string) => void; }
const TabsContext = createContext<TabsContextValue>({ active: "", setActive: () => {} });

export function Tabs({ defaultValue, children }: { defaultValue: string; children: React.ReactNode }) {
  const [active, setActive] = useState(defaultValue);
  return <TabsContext.Provider value={{ active, setActive }}>{children}</TabsContext.Provider>;
}

export function TabList({ children }: { children: React.ReactNode }) {
  return <div role="tablist" className="flex gap-1 border-b border-gray-200">{children}</div>;
}

export function Tab({ value, children }: { value: string; children: React.ReactNode }) {
  const { active, setActive } = useContext(TabsContext);
  const selected = active === value;
  return (
    <button
      role="tab"
      aria-selected={selected}
      className={clsx(
        "-mb-px border-b-2 px-3.5 py-2.5 text-sm font-medium transition-colors",
        selected ? "border-brand-600 text-brand-700" : "border-transparent text-gray-500 hover:text-gray-800",
      )}
      onClick={() => setActive(value)}
    >
      {children}
    </button>
  );
}

export function TabPanel({ value, children }: { value: string; children: React.ReactNode }) {
  const { active } = useContext(TabsContext);
  if (active !== value) return null;
  return <div role="tabpanel" className="animate-fade-in py-4">{children}</div>;
}
