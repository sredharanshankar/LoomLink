import { createContext, useContext, useState } from "react";
import { clsx } from "clsx";

interface TabsContextValue { active: string; setActive: (v: string) => void; }
const TabsContext = createContext<TabsContextValue>({ active: "", setActive: () => {} });

export function Tabs({ defaultValue, children }: { defaultValue: string; children: React.ReactNode }) {
  const [active, setActive] = useState(defaultValue);
  return <TabsContext.Provider value={{ active, setActive }}>{children}</TabsContext.Provider>;
}

export function TabList({ children }: { children: React.ReactNode }) {
  return <div className="flex border-b border-gray-200 gap-0">{children}</div>;
}

export function Tab({ value, children }: { value: string; children: React.ReactNode }) {
  const { active, setActive } = useContext(TabsContext);
  return (
    <button
      className={clsx(
        "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors",
        active === value ? "border-brand-700 text-brand-700" : "border-transparent text-gray-500 hover:text-gray-700"
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
  return <div className="py-4">{children}</div>;
}
