import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useNavigate, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../lib/auth";
import { ApiError } from "../../lib/api";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Card from "../../components/ui/Card";

const schema = z.object({
  employee_code: z.string().min(1, "Required"),
  password: z.string().min(1, "Required"),
});
type FormValues = z.infer<typeof schema>;

const DASHBOARD = "/app/dashboard";

export default function LoginPage() {
  const { t } = useTranslation();
  const { login } = useAuth();
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(data: FormValues) {
    try {
      await login(data.employee_code, data.password);
      navigate(DASHBOARD, { replace: true });
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : "Login failed";
      setError("root", { message: msg });
    }
  }

  return (
    <Card className="w-full max-w-sm">
      <h2 className="text-xl font-semibold text-gray-900 mb-6">{t("login")}</h2>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Input label={t("employee_code")} autoComplete="username" {...register("employee_code")} error={errors.employee_code?.message} />
        <Input label={t("password")} type="password" autoComplete="current-password" {...register("password")} error={errors.password?.message} />
        {errors.root && <p className="text-sm text-red-600">{errors.root.message}</p>}
        <Button type="submit" loading={isSubmitting} className="w-full">{t("login")}</Button>
      </form>
      <div className="mt-4 text-center">
        <Link to="/pin" className="text-sm text-brand-700 hover:underline">{t("loginWith", { method: "PIN" })}</Link>
      </div>
    </Card>
  );
}
