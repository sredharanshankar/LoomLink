// Indian grouping: lakh/crore separators for amounts ≥ 1000

function indianGrouping(intPart: string): string {
  if (intPart.length <= 3) return intPart;
  const last3 = intPart.slice(-3);
  const rest = intPart.slice(0, -3);
  const grouped = rest.replace(/\B(?=(\d{2})+(?!\d))/g, ",");
  return `${grouped},${last3}`;
}

export function formatPaise(paise: number, { showPaise = false } = {}): string {
  const rupees = Math.floor(Math.abs(paise) / 100);
  const paiseRemainder = Math.abs(paise) % 100;
  const sign = paise < 0 ? "-" : "";
  const intStr = indianGrouping(String(rupees));
  if (showPaise) {
    return `${sign}₹${intStr}.${String(paiseRemainder).padStart(2, "0")}`;
  }
  return `${sign}₹${intStr}`;
}

export function formatGrams(grams: number): string {
  if (grams >= 1_000_000) return `${(grams / 1_000_000).toFixed(2)} t`;
  if (grams >= 1_000) return `${(grams / 1_000).toFixed(2)} kg`;
  return `${grams} g`;
}

export function formatCm(cm: number): string {
  if (cm >= 100_000) return `${(cm / 100_000).toFixed(2)} km`;
  if (cm >= 100) return `${(cm / 100).toFixed(2)} m`;
  return `${cm} cm`;
}

export function formatMinutes(minutes: number): string {
  if (minutes < 60) return `${minutes}m`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (m === 0) return `${h}h`;
  return `${h}h ${m}m`;
}

const IST = "Asia/Kolkata";

export function formatDateTime(utcIso: string | null | undefined): string {
  if (!utcIso) return "—";
  const d = new Date(utcIso);
  if (isNaN(d.getTime())) return "—";
  return d.toLocaleString("en-IN", { timeZone: IST, hour12: false });
}

export function formatDate(utcIso: string | null | undefined): string {
  if (!utcIso) return "—";
  const d = new Date(utcIso);
  if (isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("en-IN", { timeZone: IST });
}