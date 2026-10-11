/**
 * Parse VITE_MOCK_MODULES to determine which API modules are mocked.
 *
 * VITE_MOCK_MODULES=inventory,orders  → only those modules are intercepted
 * VITE_MOCK_MODULES=           (empty) → ALL modules are real (passthrough)
 * VITE_MOCK_MODULES unset             → ALL modules are mocked (default dev mode)
 */
const raw = import.meta.env.VITE_MOCK_MODULES as string | undefined;

// When the variable is not defined, mock everything.
const ALL_MOCKED = raw === undefined;
const MOCKED_SET = ALL_MOCKED ? null : new Set(
  (raw ?? "").split(",").map((s) => s.trim()).filter(Boolean)
);

export function isMocked(module: string): boolean {
  if (ALL_MOCKED) return true;
  return MOCKED_SET?.has(module) ?? false;
}
