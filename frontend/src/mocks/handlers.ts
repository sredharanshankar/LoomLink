import { http, HttpResponse } from "msw";

const BASE = "/api/v1";

const DEMO_USER = {
  id: "00000000-0000-0000-0000-000000000001",
  employee_code: "OWN-001",
  full_name: "Demo Owner",
  role: "owner",
  language: "en",
};

const DEMO_TOKEN = "demo-access-token";
const DEMO_REFRESH = "demo-refresh-token";

export const handlers = [
  http.post(BASE + "/auth/login", () =>
    HttpResponse.json({ access_token: DEMO_TOKEN, refresh_token: DEMO_REFRESH, user: DEMO_USER })
  ),
  http.post(BASE + "/auth/pin-login", () =>
    HttpResponse.json({ access_token: DEMO_TOKEN, refresh_token: DEMO_REFRESH, user: DEMO_USER })
  ),
  http.post(BASE + "/auth/refresh", () =>
    HttpResponse.json({ access_token: DEMO_TOKEN, refresh_token: DEMO_REFRESH })
  ),
  http.post(BASE + "/auth/logout", () => new HttpResponse(null, { status: 204 })),
  http.get(BASE + "/auth/me", () => HttpResponse.json(DEMO_USER)),
  http.get(BASE + "/dashboard", () =>
    HttpResponse.json({ orders_today: 0, jobs_running: 0, rolls_in_qc: 0, dispatches_today: 0 })
  ),
];