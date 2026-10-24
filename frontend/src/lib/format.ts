const usd = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

export const formatPrice = (n: number) => usd.format(n);

/** 605 seconds -> "10:05"; negative values clamp to "0:00". */
export function formatCountdown(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

export const vehicleTitle = (v: { year: number | null; make: string; model: string }) =>
  [v.year, v.make, v.model].filter(Boolean).join(" ");

export function timeAgo(iso: string, now = Date.now()): string {
  const sec = Math.round((now - new Date(iso).getTime()) / 1000);
  if (sec < 10) return "just now";
  if (sec < 60) return `${sec}s ago`;
  if (sec < 3600) return `${Math.floor(sec / 60)}m ago`;
  if (sec < 86400) return `${Math.floor(sec / 3600)}h ago`;
  return `${Math.floor(sec / 86400)}d ago`;
}

export const EVENT_LABELS: Record<string, string> = {
  vehicle_created: "Added to lot",
  vehicle_updated: "Details changed",
  vehicle_deleted: "Removed from lot",
  purchase: "Sold",
  restock: "Restocked",
  hold_placed: "Hold placed",
  hold_released: "Hold released",
  hold_expired: "Hold expired",
};
