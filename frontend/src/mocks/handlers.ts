import { http, HttpResponse } from "msw";
import {
  machines, yarnTypes, suppliers, fabricTypes, buyers, workers,
  routeTemplates, orders, jobs, yarnBatches, rolls, dispatches, invoices,
} from "./fixtures/index";

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

function paginate<T>(items: T[], url: URL) {
  const limit = Number(url.searchParams.get("limit") ?? 50);
  const offset = Number(url.searchParams.get("offset") ?? 0);
  return { items: items.slice(offset, offset + limit), total: items.length };
}

export const handlers = [
  // Auth
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

  // Dashboard
  http.get(BASE + "/dashboard/owner", () =>
    HttpResponse.json({
      orders_due_7d: orders.filter(o => o.status !== "closed" && o.status !== "cancelled").length,
      orders_at_risk: 1,
      today_output_cm: 15000,
      yesterday_output_cm: 18000,
      cash_in_mtd_paise: 6250000,
      receivables_paise: 5880000,
      low_stock_count: 1,
      jobs_running: jobs.filter(j => j.status === "in_progress").length,
      rolls_in_qc: rolls.filter(r => r.status === "pending_qc").length,
      dispatches_today: 0,
    })
  ),
  http.get(BASE + "/dashboard", () =>
    HttpResponse.json({
      orders_today: orders.filter(o => o.status !== "closed" && o.status !== "cancelled").length,
      jobs_running: jobs.filter(j => j.status === "in_progress").length,
      rolls_in_qc: rolls.filter(r => r.status === "pending_qc").length,
      dispatches_today: 0,
    })
  ),

  // Inventory
  http.get(BASE + "/yarn-types", ({ request }) =>
    HttpResponse.json(paginate(yarnTypes, new URL(request.url)))
  ),
  http.get(BASE + "/yarn-batches", ({ request }) =>
    HttpResponse.json(paginate(yarnBatches, new URL(request.url)))
  ),
  http.get(BASE + "/yarn-batches/:id", ({ params }) => {
    const b = yarnBatches.find(x => x.id === params.id || x.code === params.id);
    return b ? HttpResponse.json(b) : new HttpResponse(null, { status: 404 });
  }),
  http.get(BASE + "/suppliers", ({ request }) =>
    HttpResponse.json(paginate(suppliers, new URL(request.url)))
  ),
  http.get(BASE + "/purchase-orders", ({ request }) =>
    HttpResponse.json(paginate([], new URL(request.url)))
  ),

  // Orders
  http.get(BASE + "/fabric-types", ({ request }) =>
    HttpResponse.json(paginate(fabricTypes, new URL(request.url)))
  ),
  http.get(BASE + "/buyers", ({ request }) =>
    HttpResponse.json(paginate(buyers, new URL(request.url)))
  ),
  http.get(BASE + "/buyers/:id", ({ params }) => {
    const b = buyers.find(x => x.id === params.id || x.code === params.id);
    return b ? HttpResponse.json(b) : new HttpResponse(null, { status: 404 });
  }),
  http.get(BASE + "/orders", ({ request }) =>
    HttpResponse.json(paginate(orders, new URL(request.url)))
  ),
  http.get(BASE + "/orders/:id", ({ params }) => {
    const o = orders.find(x => x.id === params.id || x.code === params.id);
    return o ? HttpResponse.json(o) : new HttpResponse(null, { status: 404 });
  }),
  http.get(BASE + "/route-templates", ({ request }) =>
    HttpResponse.json(paginate(routeTemplates, new URL(request.url)))
  ),

  // Production
  http.get(BASE + "/machines", ({ request }) =>
    HttpResponse.json(paginate(machines, new URL(request.url)))
  ),
  http.get(BASE + "/machines/:id", ({ params }) => {
    const m = machines.find(x => x.id === params.id || x.code === params.id);
    return m ? HttpResponse.json(m) : new HttpResponse(null, { status: 404 });
  }),
  http.get(BASE + "/production/floor", () =>
    HttpResponse.json(machines)
  ),
  http.get(BASE + "/jobs", ({ request }) =>
    HttpResponse.json(paginate(jobs, new URL(request.url)))
  ),
  http.get(BASE + "/jobs/:id", ({ params }) => {
    const j = jobs.find(x => x.id === params.id);
    return j ? HttpResponse.json(j) : new HttpResponse(null, { status: 404 });
  }),

  // Quality
  http.get(BASE + "/rolls", ({ request }) =>
    HttpResponse.json(paginate(rolls, new URL(request.url)))
  ),
  http.get(BASE + "/rolls/:id", ({ params }) => {
    const r = rolls.find(x => x.id === params.id || x.code === params.id);
    return r ? HttpResponse.json(r) : new HttpResponse(null, { status: 404 });
  }),
  http.get(BASE + "/quality/queues", () =>
    HttpResponse.json({
      pending_qc: rolls.filter(r => r.status === "pending_qc"),
      passed: rolls.filter(r => r.status === "passed"),
      rework: rolls.filter(r => r.status === "rework"),
      rejected: rolls.filter(r => r.status === "rejected"),
    })
  ),

  // Dispatch
  http.get(BASE + "/dispatches", ({ request }) =>
    HttpResponse.json(paginate(dispatches, new URL(request.url)))
  ),
  http.get(BASE + "/dispatches/:id", ({ params }) => {
    const d = dispatches.find(x => x.id === params.id);
    return d ? HttpResponse.json(d) : new HttpResponse(null, { status: 404 });
  }),
  http.get(BASE + "/dispatch/finished-stock", () =>
    HttpResponse.json(rolls.filter(r => r.status === "passed"))
  ),

  // Workers
  http.get(BASE + "/workers", ({ request }) =>
    HttpResponse.json(paginate(workers, new URL(request.url)))
  ),
  http.get(BASE + "/workers/:id", ({ params }) => {
    const w = workers.find(x => x.id === params.id);
    return w ? HttpResponse.json(w) : new HttpResponse(null, { status: 404 });
  }),
  http.get(BASE + "/attendance", () =>
    HttpResponse.json({ items: [], total: 0 })
  ),

  // Finance
  http.get(BASE + "/invoices", ({ request }) =>
    HttpResponse.json(paginate(invoices, new URL(request.url)))
  ),
  http.get(BASE + "/invoices/:id", ({ params }) => {
    const inv = invoices.find(x => x.id === params.id);
    return inv ? HttpResponse.json(inv) : new HttpResponse(null, { status: 404 });
  }),

  // Notifications
  http.get(BASE + "/notifications", () =>
    HttpResponse.json({ items: [], total: 0 })
  ),

  // Public track
  http.get(BASE + "/public/track/:token", () =>
    HttpResponse.json({
      code: "ORD-104",
      fabric: "Blue Poplin",
      quantity_cm: 120000,
      stage: "weaving",
      pct_ready: 42,
      passed_cm: 0,
      dispatched_cm: 0,
      promised_date: "2026-10-13",
      last_updated: new Date().toISOString(),
    })
  ),

  // Mill settings
  http.get(BASE + "/settings", () =>
    HttpResponse.json({
      mill_name: "Everest Textile Mills",
      timezone: "Asia/Kolkata",
      gst_default_bp: 500,
    })
  ),
];
