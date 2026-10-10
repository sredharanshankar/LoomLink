export const qk = {
  me: () => ["me"] as const,
  dashboard: () => ["dashboard"] as const,
  inventory: {
    suppliers: () => ["suppliers"] as const,
    yarnTypes: () => ["yarn-types"] as const,
    batches: (filters?: object) => ["yarn-batches", filters] as const,
    movements: (batchId: string) => ["stock-movements", batchId] as const,
    pos: (filters?: object) => ["purchase-orders", filters] as const,
  },
  orders: {
    list: (filters?: object) => ["orders", filters] as const,
    detail: (id: string) => ["orders", id] as const,
    fabricTypes: () => ["fabric-types"] as const,
  },
  production: {
    machines: () => ["machines"] as const,
    jobs: (filters?: object) => ["jobs", filters] as const,
    job: (id: string) => ["jobs", id] as const,
  },
  quality: {
    rolls: (filters?: object) => ["rolls", filters] as const,
    roll: (id: string) => ["rolls", id] as const,
  },
  dispatch: {
    dispatches: (filters?: object) => ["dispatches", filters] as const,
  },
  workers: {
    list: () => ["workers"] as const,
    attendance: (date: string) => ["attendance", date] as const,
  },
  finance: {
    invoices: (filters?: object) => ["invoices", filters] as const,
  },
  ripple: {
    snapshots: () => ["ripple-snapshots"] as const,
  },
  settings: () => ["mill-settings"] as const,
};