import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth, useAuthStore } from "../../lib/auth";
import { ApiError } from "../../lib/api";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Card from "../../components/ui/Card";

function redirectForRole(role: string | undefined): string {
  if (role === "worker") return "/w";
  if (role === "buyer") return "/app/buyer-portal";
  return "/app/dashboard";
}

function getRedirect(): string {
  return redirectForRole(useAuthStore.getState().user?.role);
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
        autoComplete="username"
        value={code}
        onChange={(e) => setCode(e.target.value)}
      />
      <Input
        label={t("password")}
        type="password"
        autoComplete="current-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      {error && <p className="text-sm text-red-600">{error}</p>}
      <Button type="submit" loading={loading} className="w-full">
        {t("login")}
      </Button>
    </form>
  );
}

// ─── PIN tab ──────────────────────────────────────────────────────────────────
function PinForm() {
  const { t } = useTranslation();
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

  const KEYS = [["1","2","3"],["4","5","6"],["7","8","9"],["⌫","0",""]];

  return (
    <div>
      {/* Optional employee code for floor workers */}
      <div className="mb-4">
        <input
          type="text"
          value={employeeCode}
          onChange={(e) => { setEmployeeCode(e.target.value); setPin(""); }}
          placeholder="Employee code (e.g. EMP-001)"
          disabled={loading}
          className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm font-mono text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:opacity-50 uppercase"
        />
        <p className="text-[11px] text-gray-400 mt-1">
          Floor workers: enter code above + 4-digit PIN &nbsp;·&nbsp; Management: leave blank + 6-digit PIN
        </p>
      </div>

      {/* PIN dots */}
      <div className="flex justify-center gap-3 mb-4">
        {Array.from({ length: pinLength }).map((_, i) => (
          <div
            key={i}
            className={`h-3 w-3 rounded-full transition-colors ${
              pin[i] ? "bg-brand-700" : "bg-gray-200"
            }`}
          />
        ))}
      </div>

      {error && <p className="text-sm text-red-600 text-center mb-3">{error}</p>}

      {/* Numpad */}
      <div className="grid gap-2">
        {KEYS.map((row, ri) => (
          <div key={ri} className="grid grid-cols-3 gap-2">
            {row.map((key) => {
              if (key === "") return <div key="empty" />;
              return (
                <button
                  key={key}
                  type="button"
                  disabled={loading}
                  onClick={() => {
                    if (key === "⌫") setPin((p) => p.slice(0, -1));
                    else append(key);
                  }}
                  className={`h-12 rounded-lg text-lg font-medium transition-colors disabled:opacity-50 ${
                    key === "⌫"
                      ? "bg-gray-100 text-gray-600 hover:bg-gray-200"
                      : "bg-gray-50 text-gray-800 hover:bg-gray-100 border border-gray-200"
                  }`}
                >
                  {key}
                </button>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Unified Login Page ───────────────────────────────────────────────────────
export default function LoginPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"password" | "pin">("password");

  return (
    <Card className="w-full max-w-sm">
      <h2 className="text-xl font-semibold text-gray-900 mb-5 text-center">
        LoomLink
      </h2>

      {/* Tab switcher */}
      <div className="flex rounded-lg border border-gray-200 p-1 mb-5 gap-1">
        <button
          type="button"
          onClick={() => setTab("password")}
          className={`flex-1 rounded-md py-1.5 text-sm font-medium transition-colors ${
            tab === "password"
              ? "bg-brand-700 text-white shadow-sm"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          {t("loginWith", { method: t("password") })}
        </button>
        <button
          type="button"
          onClick={() => setTab("pin")}
          className={`flex-1 rounded-md py-1.5 text-sm font-medium transition-colors ${
            tab === "pin"
              ? "bg-brand-700 text-white shadow-sm"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          {t("loginWith", { method: t("pin") })}
        </button>
      </div>

      {tab === "password" ? <PasswordForm /> : <PinForm />}
    </Card>
  );
}
