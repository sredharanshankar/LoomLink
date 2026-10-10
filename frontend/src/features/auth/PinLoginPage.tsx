import { useState, useRef } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../lib/auth";
import { ApiError } from "../../lib/api";
import Card from "../../components/ui/Card";

const PIN_LENGTH = 4;
const WORKER_APP = "/w";

export default function PinLoginPage() {
  const { t } = useTranslation();
  const { pinLogin } = useAuth();
  const navigate = useNavigate();
  const [employeeCode, setEmployeeCode] = useState("");
  const [pin, setPin] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function submit(currentPin: string) {
    if (!employeeCode.trim()) {
      setError("Enter your employee code first.");
      return;
    }
    if (currentPin.length !== PIN_LENGTH) return;
    setLoading(true);
    setError("");
    try {
      await pinLogin(currentPin, employeeCode.trim().toUpperCase());
      navigate(WORKER_APP, { replace: true });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Invalid credentials");
      setPin("");
    } finally {
      setLoading(false);
    }
  }

  function append(digit: string) {
    if (pin.length >= PIN_LENGTH || loading) return;
    const next = pin + digit;
    setPin(next);
    if (next.length === PIN_LENGTH) submit(next);
  }

  function backspace() {
    setPin((p) => p.slice(0, -1));
  }

  const KEYS = [
    ["1", "2", "3"],
    ["4", "5", "6"],
    ["7", "8", "9"],
    ["⌫", "0", ""],
  ];

  return (
    <Card className="w-full max-w-xs">
      <h2 className="text-xl font-semibold text-gray-900 mb-1 text-center">Floor Login</h2>
      <p className="text-xs text-gray-400 text-center mb-5">Employee code + 4-digit PIN</p>

      {/* Employee code input */}
      <div className="mb-4">
        <label className="block text-xs font-medium text-gray-600 mb-1 uppercase tracking-wide">
          Employee Code
        </label>
        <input
          ref={inputRef}
          type="text"
          value={employeeCode}
          onChange={(e) => setEmployeeCode(e.target.value)}
          placeholder="e.g. EMP-001"
          disabled={loading}
          className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm font-mono text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:opacity-50 uppercase"
          onKeyDown={(e) => e.key === "Enter" && inputRef.current?.blur()}
        />
      </div>

      {/* PIN dots */}
      <div className="flex justify-center gap-3 mb-4">
        {Array.from({ length: PIN_LENGTH }).map((_, i) => (
          <div
            key={i}
            className={`h-4 w-4 rounded-full border-2 transition-colors ${
              i < pin.length
                ? "bg-brand-700 border-brand-700"
                : "bg-white border-gray-300"
            }`}
          />
        ))}
      </div>

      {error && (
        <p className="text-sm text-red-600 text-center mb-3">{error}</p>
      )}

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
                    if (key === "⌫") backspace();
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

      <div className="mt-4 text-center">
        <Link to="/login" className="text-sm text-brand-700 hover:underline">
          {t("loginWith", { method: "Password" })}
        </Link>
      </div>
    </Card>
  );
}
