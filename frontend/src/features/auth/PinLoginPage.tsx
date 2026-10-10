import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../lib/auth";
import { ApiError } from "../../lib/api";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";

const DASHBOARD = "/dashboard";

export default function PinLoginPage() {
  const { t } = useTranslation();
  const { pinLogin } = useAuth();
  const navigate = useNavigate();
  const [pin, setPin] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function append(digit: string) {
    if (pin.length < 6) setPin((p) => p + digit);
  }

  async function submit() {
    if (pin.length !== 6) return;
    setLoading(true);
    setError("");
    try {
      await pinLogin(pin);
      navigate(DASHBOARD, { replace: true });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Invalid PIN");
      setPin("");
    } finally {
      setLoading(false);
    }
  }

  const KEYS = [["1","2","3"],["4","5","6"],["7","8","9"],["x","0","ok"]];

  return (
    <Card className="w-full max-w-xs">
      <h2 className="text-xl font-semibold text-gray-900 mb-4 text-center">{t("pin")}</h2>
      <div className="flex justify-center gap-2 mb-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-10 w-8 border-b-2 border-gray-400 flex items-end justify-center text-xl font-bold text-gray-700">
            {pin[i] ? "o" : ""}
          </div>
        ))}
      </div>
      {error && <p className="text-sm text-red-600 text-center mb-2">{error}</p>}
      <div className="grid gap-2">
        {KEYS.map((row, ri) => (
          <div key={ri} className="grid grid-cols-3 gap-2">
            {row.map((key) => (
              <Button key={key} variant="secondary" onClick={() => {
                if (key === "x") setPin((p) => p.slice(0, -1));
                else if (key === "ok") submit();
                else append(key);
              }} disabled={loading} className="h-12 text-lg">{key}</Button>
            ))}
          </div>
        ))}
      </div>
      <div className="mt-4 text-center">
        <Link to="/login" className="text-sm text-brand-700 hover:underline">{t("loginWith", { method: "Password" })}</Link>
      </div>
    </Card>
  );
}