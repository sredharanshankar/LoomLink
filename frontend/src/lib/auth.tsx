import { createContext, useContext, useEffect, useRef } from "react";
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { api, ApiError } from "./api";

export type UserRole =
  | "owner" | "manager" | "storekeeper" | "operator"
  | "qc_inspector" | "dispatch" | "accounts" | "buyer";

export interface AuthUser {
  id: string;
  employee_code: string;
  full_name: string;
  role: UserRole;
  language: string;
}

interface AuthStore {
  user: AuthUser | null;
  accessToken: string | null;
  setToken: (access: string) => void;
  setUser: (u: AuthUser) => void;
  logout: () => void;
}

// Access token + user in sessionStorage only; refresh token is never stored
// (backend sets httpOnly ll_refresh cookie on login, sent automatically)
export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      setToken: (access) => set({ accessToken: access }),
      setUser: (u) => set({ user: u }),
      logout: () => set({ user: null, accessToken: null }),
    }),
    {
      name: "loomlink-auth",
      storage: createJSONStorage(() => sessionStorage),
      partialize: (s) => ({ accessToken: s.accessToken, user: s.user }),
    }
  )
);

interface AuthContextValue {
  user: AuthUser | null;
  login: (employeeCode: string, password: string) => Promise<void>;
  pinLogin: (pin: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const store = useAuthStore();
  const hydratedRef = useRef(false);

  useEffect(() => {
    if (hydratedRef.current || !store.accessToken) return;
    hydratedRef.current = true;
    api.get<AuthUser>("/auth/me").then(store.setUser).catch(() => store.logout());
  }, []);

  async function login(employee_code: string, password: string) {
    const data = await api.post<{ access_token: string; user: AuthUser }>(
      "/auth/login",
      { employee_code, password },
      { skipAuth: true } as Parameters<typeof api.post>[2]
    );
    store.setToken(data.access_token);
    store.setUser(data.user);
  }

  async function pinLogin(pin: string) {
    const data = await api.post<{ access_token: string; user: AuthUser }>(
      "/auth/pin-login",
      { pin },
      { skipAuth: true } as Parameters<typeof api.post>[2]
    );
    store.setToken(data.access_token);
    store.setUser(data.user);
  }

  async function logout() {
    try {
      await api.post("/auth/logout");
    } catch (e) {
      if (!(e instanceof ApiError)) throw e;
    } finally {
      store.logout();
    }
  }

  return (
    <AuthContext.Provider value={{ user: store.user, login, pinLogin, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
