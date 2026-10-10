import { useAuthStore } from "./auth";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status: number,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = "ApiError";
  }
}

let refreshPromise: Promise<string> | null = null;

async function refreshTokens(): Promise<string> {
  const store = useAuthStore.getState();
  // Backend sets httpOnly ll_refresh cookie; send it via credentials:'include'
  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    store.logout();
    throw new ApiError("UNAUTHENTICATED", "Session expired", 401);
  }
  const data = await res.json();
  store.setToken(data.access_token);
  return data.access_token as string;
}

async function request<T>(
  path: string,
  options: RequestInit & { skipAuth?: boolean } = {}
): Promise<T> {
  const store = useAuthStore.getState();
  const { skipAuth, ...init } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };

  if (!skipAuth && store.accessToken) {
    headers["Authorization"] = `Bearer ${store.accessToken}`;
  }

  let res = await fetch(`${API_BASE}${path}`, { ...init, headers });

  if (res.status === 401 && !skipAuth) {
    if (!refreshPromise) {
      refreshPromise = refreshTokens().finally(() => {
        refreshPromise = null;
      });
    }
    const newToken = await refreshPromise;
    headers["Authorization"] = `Bearer ${newToken}`;
    res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  }

  if (!res.ok) {
    let body: { error?: { code: string; message: string; details?: Record<string, unknown> } } = {};
    try {
      body = await res.json();
    } catch { /* empty body */ }
    const err = body.error;
    throw new ApiError(err?.code ?? "HTTP_ERROR", err?.message ?? res.statusText, res.status, err?.details);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string, opts?: RequestInit) => request<T>(path, { ...opts, method: "GET" }),
  post: <T>(path: string, body?: unknown, opts?: RequestInit) =>
    request<T>(path, { ...opts, method: "POST", body: body ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: unknown, opts?: RequestInit) =>
    request<T>(path, { ...opts, method: "PUT", body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown, opts?: RequestInit) =>
    request<T>(path, { ...opts, method: "PATCH", body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string, opts?: RequestInit) => request<T>(path, { ...opts, method: "DELETE" }),
};
