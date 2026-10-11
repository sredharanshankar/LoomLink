interface Props {
  title: string;
  subtitle?: string;
  eyebrow?: string;
  actions?: React.ReactNode;
}

export default function PageHeader({ title, subtitle, eyebrow, actions }: Props) {
  return (
    <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        {eyebrow && (
          <p className="mb-1 text-xs font-semibold uppercase tracking-[0.14em] text-brand-600">{eyebrow}</p>
        )}
        <h1 className="truncate text-[26px] font-semibold leading-tight tracking-tight text-gray-900">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-gray-500">{subtitle}</p>}
      </div>
      {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}
