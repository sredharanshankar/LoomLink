import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../lib/auth";
import { ApiError } from "../../lib/api";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";

const WORKER_APP = "/w";

export default function PinLoginPage() {
  const { t } = useTranslation();
  const { pinLogin } = useAuth();
  const navigate = useNavigate();
  const [employeeCode, setEmployeeCode] = useState("");
  const [pin, setPin] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function append(digit: string) {
    if (pin.length < 6) {
      setPin((p) => p + digit);
    }
  }

  async function submit() {
    if (pin.length < 4) return;
    setLoading(true);
    setError("");
    try {
      await pinLogin(pin, employeeCode || undefined);
      navigate(WORKER_APP, { replace: true });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Invalid PIN");
      setPin("");
    } finally {
      setLoading(false);
    }
  }

  const KEYS = [["1","2","3"],["4","5","6"],["7","8","9"],["⌫","0","ok"]];

  return (
    <Card className="w-full max-w-xs">
      <div className="flex justify-center gap-2 mb-4">
        <Link
          to="/login"
          className="px-4 py-2 text-sm font-medium text-gray-600 rounded-full hover:bg-gray-100 transition"
        >
          {t("loginWith", { method: "Password" })}
        </Link>
        <span className="px-4 py-2 text-sm font-medium text-white bg-brand-600 rounded-full">
          Log in with 6-digit PIN
        </span>
      </div>

      <input
        type="text"
        value={employeeCode}
        onChange={(e) => setEmployeeCode(e.target.value.toUpperCase())}
        placeholder="EMPLOYEE CODE (E.G. EMP-001)"
        className="w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 mb-2 font-mono"
        autoComplete="username"
      />
      <p className="text-xs text-gray-400 text-center mb-3">
        Floor workers: enter code above + 4-digit PIN · Management: leave blank + 6-digit PIN
      </p>

      <div className="flex justify-center gap-2 mb-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className={`h-10 w-8 border-b-2 flex items-end justify-center text-xl font-bold ${
              pin[i] ? "border-brand-600 text-gray-700" : "border-gray-300"
            }`}
          >
            {pin[i] ? "•" : ""}
          </div>
        ))}
      </div>

      {error && <p className="text-sm text-red-600 text-center mb-2">{error}</p>}

      <div className="grid gap-2">
        {KEYS.map((row, ri) => (
          <div key={ri} className="grid grid-cols-3 gap-2">
            {row.map((key) => (
              <Button
                key={key}
                variant="secondary"
                onClick={() => {
                  if (key === "⌫") setPin((p) => p.slice(0, -1));
                  else if (key === "ok") submit();
                  else append(key);
                }}
                disabled={loading}
                className="h-12 text-lg"
              >
                {key}
              </Button>
            ))}
          </div>
        ))}
      </div>
    </Card>
  );
}
