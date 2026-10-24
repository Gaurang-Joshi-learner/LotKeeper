import { useEffect } from "react";
import { useNow } from "../hooks/useNow";
import { formatCountdown } from "../lib/format";

const HOLD_SECONDS = 10 * 60; // matches the backend default; only used to scale the bar

export function HoldTimer({ expiresAt, onExpire }: { expiresAt: string; onExpire: () => void }) {
  const now = useNow(1000);
  const remaining = (new Date(expiresAt).getTime() - now) / 1000;

  useEffect(() => {
    if (remaining <= 0) onExpire();
  }, [remaining <= 0]); // eslint-disable-line react-hooks/exhaustive-deps

  const pct = Math.min(100, Math.max(0, (remaining / HOLD_SECONDS) * 100));
  const urgent = remaining < 60;
  return (
    <div className="w-full" aria-live="off">
      <div className="mb-1 flex justify-between text-xs font-semibold">
        <span>Held for you</span>
        <span className={urgent ? "text-brake" : ""}>{formatCountdown(remaining)}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-line">
        <div className={`h-full transition-[width] duration-1000 ease-linear ${urgent ? "bg-brake" : "bg-enamel"}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
