import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { AlertCircle, BadgeCheck, Delete, KeyRound, Lock, User } from "lucide-react";
import { clsx } from "clsx";
import { useAuth, useAuthStore } from "../../lib/auth";
import { ApiError } from "../../lib/api";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";

function redirectForRole(role: string | undefined): string {
  if (role === "worker") return "/w";
  if (role === "buyer") return "/app/buyer-portal";
  return "/app/dashboard";
}

function getRedirect(): string {
  return redirectForRole(useAuthStore.getState().user?.role);
}

function ErrorNote({ message }: { message: string }) {
  return (
    <div role="alert" className="flex items-start gap-2 rounded-lg bg-red-50 px-3 py-2.5 text-sm text-red-700 ring-1 ring-inset ring-red-600/15">
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
      {message}
    </div>
  );
}

// ─── Password tab ────────────────────────────────────────────────────────────
function PasswordForm() {
  const { t } = useTranslation();
  const { login } = useAuth();
  const navigate = useNavigate();
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!code || !password) { setError("All fields are required."); return; }
    setError(""); setLoading(true);
    try {
      await login(code, password);
      navigate(getRedirect(), { replace: true });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input
        label={t("employee_code")}
        icon={User}
        autoComplete="username"
        placeholder="e.g. MGR-001"
        value={code}
        onChange={(e) => setCode(e.target.value)}
      />
      <Input
        label={t("password")}
        icon={Lock}
        type="password"
        autoComplete="current-password"
        placeholder="••••••••"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      {error && <ErrorNote message={error} />}
      <Button type="submit" size="lg" loading={loading} className="w-full">
        {t("login")}
      </Button>
    </form>
  );
}

// ─── PIN tab ──────────────────────────────────────────────────────────────────
function PinForm() {
  const { pinLogin } = useAuth();
  const navigate = useNavigate();
  const [employeeCode, setEmployeeCode] = useState("");
  const [pin, setPin] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // With employee code → 4-digit PIN; without (management) → 6-digit PIN
  const pinLength = employeeCode.trim() ? 4 : 6;

  async function submit(currentPin: string) {
    if (currentPin.length !== pinLength) return;
    setError(""); setLoading(true);
    try {
      await pinLogin(currentPin, employeeCode.trim().toUpperCase() || undefined);
      navigate(getRedirect(), { replace: true });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Invalid PIN");
      setPin("");
    } finally {
      setLoading(false);
    }
  }

  function append(digit: string) {
    if (pin.length >= pinLength || loading) return;
    const next = pin + digit;
    setPin(next);
    if (next.length === pinLength) submit(next);
  }

  const KEYS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "", "0", "⌫"];

  return (
    <div className="space-y-5">
      <Input
        label="Employee code (floor workers)"
        icon={BadgeCheck}
        value={employeeCode}
        onChange={(e) => { setEmployeeCode(e.target.value); setPin(""); }}
        placeholder="e.g. EMP-001"
        disabled={loading}
        className="font-mono uppercase"
        hint={employeeCode.trim() ? "Enter your 4-digit PIN below." : "Management: leave blank and use your 6-digit PIN."}
      />

      <div className="flex justify-center gap-2.5" aria-label={`${pin.length} of ${pinLength} digits entered`}>
        {Array.from({ length: pinLength }).map((_, i) => (
          <span
            key={i}
            className={clsx(
              "h-3 w-3 rounded-full transition-all duration-150",
              pin[i] ? "scale-110 bg-brand-600" : "bg-gray-200",
            )}
          />
        ))}
      </div>

      {error && <ErrorNote message={error} />}

      <div className="grid grid-cols-3 gap-2.5">
        {KEYS.map((key, i) => {
          if (key === "") return <div key={`empty-${i}`} />;
          const isDelete = key === "⌫";
          return (
            <button
              key={key}
              type="button"
              disabled={loading}
              aria-label={isDelete ? "Delete digit" : key}
              onClick={() => (isDelete ? setPin((p) => p.slice(0, -1)) : append(key))}
              className={clsx(
                "flex h-14 items-center justify-center rounded-xl text-xl font-medium transition-all active:scale-95 disabled:opacity-50",
                isDelete
                  ? "text-gray-500 hover:bg-gray-100"
                  : "border border-gray-200 bg-white text-gray-900 shadow-sm hover:border-gray-300 hover:bg-gray-50",
              )}
            >
              {isDelete ? <Delete className="h-5 w-5" /> : key}
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ─── Unified Login Page ───────────────────────────────────────────────────────
export default function LoginPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"password" | "pin">("password");

  const tabs = [
    { id: "password" as const, label: t("password"), icon: Lock },
    { id: "pin" as const, label: t("pin"), icon: KeyRound },
  ];

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight text-gray-900">Welcome back</h1>
      <p className="mt-1.5 text-sm text-gray-500">Sign in to manage the mill floor.</p>

      <div role="tablist" className="mt-8 grid grid-cols-2 gap-1 rounded-xl bg-gray-100 p-1">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={tab === id}
            onClick={() => setTab(id)}
            className={clsx(
              "flex items-center justify-center gap-2 rounded-lg py-2 text-sm font-medium transition-all",
              tab === id ? "bg-white text-gray-900 shadow-sm ring-1 ring-gray-900/5" : "text-gray-500 hover:text-gray-800",
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      <div className="mt-6">{tab === "password" ? <PasswordForm /> : <PinForm />}</div>
    </div>
  );
}
