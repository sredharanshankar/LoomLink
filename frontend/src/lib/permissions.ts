import type { UserRole } from "./auth";

type Permission =
  | "inventory:read" | "inventory:write"
  | "orders:read" | "orders:write"
  | "production:read" | "production:write"
  | "quality:read" | "quality:write"
  | "dispatch:read" | "dispatch:write"
  | "workers:read" | "workers:write"
  | "finance:read" | "finance:write"
  | "ripple:read"
  | "admin:read" | "admin:write";

const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  owner: ["inventory:read","inventory:write","orders:read","orders:write","production:read","production:write","quality:read","quality:write","dispatch:read","dispatch:write","workers:read","workers:write","finance:read","finance:write","ripple:read","admin:read","admin:write"],
  manager: ["inventory:read","inventory:write","orders:read","orders:write","production:read","production:write","quality:read","quality:write","dispatch:read","dispatch:write","workers:read","workers:write","finance:read","ripple:read","admin:read"],
  storekeeper: ["inventory:read","inventory:write","production:read","ripple:read"],
  operator: ["production:read","production:write","ripple:read"],
  qc_inspector: ["quality:read","quality:write","production:read","ripple:read"],
  dispatch: ["dispatch:read","dispatch:write","orders:read","ripple:read"],
  accounts: ["finance:read","finance:write","orders:read","ripple:read"],
  buyer: ["orders:read"],
};

export function can(role: UserRole | undefined, permission: Permission): boolean {
  if (!role) return false;
  return ROLE_PERMISSIONS[role]?.includes(permission) ?? false;
}