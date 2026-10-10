import { lazy, Suspense } from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import WorkerShell from "./components/layout/WorkerShell";
import PublicShell from "./components/layout/PublicShell";
import ErrorBoundary from "./components/ui/ErrorBoundary";
import { useAuth } from "./lib/auth";
import Spinner from "./components/ui/Spinner";
import { rippleRoutes } from "./features/ripple/index";
import { buyerLineRoutes } from "./features/buyer-line/index";

const LoginPage = lazy(() => import("./features/auth/LoginPage"));
const PinLoginPage = lazy(() => import("./features/auth/PinLoginPage"));
const ScanResolverPage = lazy(() => import("./features/scan/ScanResolverPage"));
const TrackPage = lazy(() => import("./features/buyer/TrackPage"));
const BuyerPortalPage = lazy(() => import("./features/buyer/BuyerPortalPage"));
const BuyerOrderFormPage = lazy(() => import("./features/buyer/BuyerOrderFormPage"));

// Console (/app/*)
const DashboardPage = lazy(() => import("./features/dashboard/DashboardPage"));
const FloorPage = lazy(() => import("./features/dashboard/FloorPage"));
const OrdersPage = lazy(() => import("./features/orders/OrdersPage"));
const NewOrderPage = lazy(() => import("./features/orders/NewOrderPage"));
const OrderDetailPage = lazy(() => import("./features/orders/OrderDetailPage"));
const BuyersPage = lazy(() => import("./features/orders/BuyersPage"));
const BuyerDetailPage = lazy(() => import("./features/orders/BuyerDetailPage"));
const InventoryPage = lazy(() => import("./features/inventory/InventoryPage"));
const BatchDetailPage = lazy(() => import("./features/inventory/BatchDetailPage"));
const ReceiveYarnPage = lazy(() => import("./features/inventory/ReceiveYarnPage"));
const SuppliersPage = lazy(() => import("./features/inventory/SuppliersPage"));
const PurchaseOrdersPage = lazy(() => import("./features/inventory/PurchaseOrdersPage"));
const ProductionPage = lazy(() => import("./features/production/ProductionPage"));
const MachinesPage = lazy(() => import("./features/production/MachinesPage"));
const MachineDetailPage = lazy(() => import("./features/production/MachineDetailPage"));
const QualityPage = lazy(() => import("./features/quality/QualityPage"));
const RollDetailPage = lazy(() => import("./features/quality/RollDetailPage"));
const RollPassportPage = lazy(() => import("./features/quality/RollPassportPage"));
const DispatchPage = lazy(() => import("./features/dispatch/DispatchPage"));
const DispatchDetailPage = lazy(() => import("./features/dispatch/DispatchDetailPage"));
const WorkersPage = lazy(() => import("./features/workers/WorkersPage"));
const AttendancePage = lazy(() => import("./features/workers/AttendancePage"));
const PayrollPage = lazy(() => import("./features/workers/PayrollPage"));
const PayrollRunPage = lazy(() => import("./features/workers/PayrollRunPage"));
const FinancePage = lazy(() => import("./features/finance/FinancePage"));
const MonthClosePage = lazy(() => import("./features/finance/MonthClosePage"));
const InvoiceDetailPage = lazy(() => import("./features/finance/InvoiceDetailPage"));
const PaymentsPage = lazy(() => import("./features/finance/PaymentsPage"));
const SupplierBillsPage = lazy(() => import("./features/finance/SupplierBillsPage"));
const ExpensesPage = lazy(() => import("./features/finance/ExpensesPage"));
const SettingsPage = lazy(() => import("./features/admin/SettingsPage"));
const UsersPage = lazy(() => import("./features/admin/UsersPage"));
const AuditPage = lazy(() => import("./features/admin/AuditPage"));

const NotFoundPage = lazy(() => import("./features/misc/NotFoundPage"));

// Worker app (/w/*)
const WorkerHomePage = lazy(() => import("./features/workers/app/WorkerHomePage"));
const WorkerScanPage = lazy(() => import("./features/workers/app/WorkerScanPage"));
const WorkerJobsPage = lazy(() => import("./features/workers/app/WorkerJobsPage"));
const WorkerAlertsPage = lazy(() => import("./features/workers/app/WorkerAlertsPage"));
const WorkerAttendancePage = lazy(() => import("./features/workers/app/WorkerAttendancePage"));
const WorkerMachinePage = lazy(() => import("./features/workers/app/WorkerMachinePage"));
const WorkerJobPage = lazy(() => import("./features/workers/app/WorkerJobPage"));
const WorkerBatchPage = lazy(() => import("./features/workers/app/WorkerBatchPage"));
const WorkerReceivePage = lazy(() => import("./features/workers/app/WorkerReceivePage"));
const WorkerRollPage = lazy(() => import("./features/workers/app/WorkerRollPage"));
const WorkerQcPage = lazy(() => import("./features/workers/app/WorkerQcPage"));
const WorkerDispatchPage = lazy(() => import("./features/workers/app/WorkerDispatchPage"));
const WorkerMePage = lazy(() => import("./features/workers/app/WorkerMePage"));

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function Lazy({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation();
  return (
    <ErrorBoundary key={pathname}>
      <Suspense fallback={<div className="flex h-full items-center justify-center p-12"><Spinner /></div>}>
        {children}
      </Suspense>
    </ErrorBoundary>
  );
}

export default function AppRouter() {
  return (
    <Routes>
      {/* Public */}
      <Route element={<PublicShell />}>
        <Route path="/login" element={<Lazy><LoginPage /></Lazy>} />
        <Route path="/pin" element={<Navigate to="/login" replace />} />
        <Route path="/track/:tracking_token" element={<Lazy><TrackPage /></Lazy>} />
        <Route path="/s/:code" element={<Lazy><ScanResolverPage /></Lazy>} />
      </Route>

      {/* Worker app */}
      <Route path="/w" element={<RequireAuth><WorkerShell /></RequireAuth>}>
        <Route index element={<Lazy><WorkerHomePage /></Lazy>} />
        <Route path="scan" element={<Lazy><WorkerScanPage /></Lazy>} />
        <Route path="jobs" element={<Lazy><WorkerJobsPage /></Lazy>} />
        <Route path="alerts" element={<Lazy><WorkerAlertsPage /></Lazy>} />
        <Route path="attendance" element={<Lazy><WorkerAttendancePage /></Lazy>} />
        <Route path="machine/:id" element={<Lazy><WorkerMachinePage /></Lazy>} />
        <Route path="job/:id" element={<Lazy><WorkerJobPage /></Lazy>} />
        <Route path="batch/:id" element={<Lazy><WorkerBatchPage /></Lazy>} />
        <Route path="receive" element={<Lazy><WorkerReceivePage /></Lazy>} />
        <Route path="roll/:id" element={<Lazy><WorkerRollPage /></Lazy>} />
        <Route path="qc" element={<Lazy><WorkerQcPage /></Lazy>} />
        <Route path="dispatch/:id" element={<Lazy><WorkerDispatchPage /></Lazy>} />
        <Route path="me" element={<Lazy><WorkerMePage /></Lazy>} />
      </Route>

      {/* Console app */}
      <Route path="/app" element={<RequireAuth><AppShell /></RequireAuth>}>
        <Route index element={<Navigate to="/app/dashboard" replace />} />
        <Route path="dashboard" element={<Lazy><DashboardPage /></Lazy>} />
        <Route path="floor" element={<Lazy><FloorPage /></Lazy>} />
        <Route path="orders" element={<Lazy><OrdersPage /></Lazy>} />
        <Route path="orders/new" element={<Lazy><NewOrderPage /></Lazy>} />
        <Route path="orders/:id" element={<Lazy><OrderDetailPage /></Lazy>} />
        <Route path="buyers" element={<Lazy><BuyersPage /></Lazy>} />
        <Route path="buyers/:id" element={<Lazy><BuyerDetailPage /></Lazy>} />
        <Route path="buyer-portal" element={<Lazy><BuyerPortalPage /></Lazy>} />
        <Route path="buyer-portal/new" element={<Lazy><BuyerOrderFormPage /></Lazy>} />
        <Route path="inventory" element={<Lazy><InventoryPage /></Lazy>} />
        <Route path="inventory/batches/:id" element={<Lazy><BatchDetailPage /></Lazy>} />
        <Route path="inventory/receive" element={<Lazy><ReceiveYarnPage /></Lazy>} />
        <Route path="suppliers" element={<Lazy><SuppliersPage /></Lazy>} />
        <Route path="purchase-orders" element={<Lazy><PurchaseOrdersPage /></Lazy>} />
        <Route path="production" element={<Lazy><ProductionPage /></Lazy>} />
        <Route path="machines" element={<Lazy><MachinesPage /></Lazy>} />
        <Route path="machines/:id" element={<Lazy><MachineDetailPage /></Lazy>} />
        <Route path="quality" element={<Lazy><QualityPage /></Lazy>} />
        <Route path="rolls/:id" element={<Lazy><RollDetailPage /></Lazy>} />
        <Route path="rolls/:id/passport" element={<Lazy><RollPassportPage /></Lazy>} />
        <Route path="dispatch" element={<Lazy><DispatchPage /></Lazy>} />
        <Route path="dispatch/:id" element={<Lazy><DispatchDetailPage /></Lazy>} />
        <Route path="workers" element={<Lazy><WorkersPage /></Lazy>} />
        <Route path="attendance" element={<Lazy><AttendancePage /></Lazy>} />
        <Route path="payroll" element={<Lazy><PayrollPage /></Lazy>} />
        <Route path="payroll/:id" element={<Lazy><PayrollRunPage /></Lazy>} />
        <Route path="finance" element={<Lazy><FinancePage /></Lazy>} />
        <Route path="finance/month-close" element={<Lazy><MonthClosePage /></Lazy>} />
        <Route path="invoices/:id" element={<Lazy><InvoiceDetailPage /></Lazy>} />
        <Route path="payments" element={<Lazy><PaymentsPage /></Lazy>} />
        <Route path="supplier-bills" element={<Lazy><SupplierBillsPage /></Lazy>} />
        <Route path="expenses" element={<Lazy><ExpensesPage /></Lazy>} />
        <Route path="settings" element={<Lazy><SettingsPage /></Lazy>} />
        <Route path="users" element={<Lazy><UsersPage /></Lazy>} />
        <Route path="audit" element={<Lazy><AuditPage /></Lazy>} />
        {/* Lane B: Ripple routes under /app */}
        {rippleRoutes.map((r) => (
          <Route key={String(r.path)} path={String(r.path)} element={r.element} />
        ))}
      </Route>

      {/* Lane B: Buyer Line portal at /buyer-line */}
      <Route path="/buyer-line">
        {buyerLineRoutes.map((r) => (
          <Route key={String(r.path ?? "index")} index={!r.path} path={r.path ? String(r.path) : undefined} element={r.element} />
        ))}
      </Route>

      <Route path="/" element={<Navigate to="/app/dashboard" replace />} />
      <Route path="*" element={<Lazy><NotFoundPage /></Lazy>} />
    </Routes>
  );
}
