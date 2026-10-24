import { formatPrice, vehicleTitle } from "../lib/format";
import type { Hold, Vehicle } from "../lib/types";
import { CarSilhouette } from "./CarSilhouette";
import { HoldTimer } from "./HoldTimer";
import { NumberPlate } from "./NumberPlate";

interface Props {
  vehicle: Vehicle;
  hold?: Hold;
  compared: boolean;
  compareDisabled: boolean;
  onToggleCompare: () => void;
  onPurchase: () => void;
  onHold: () => void;
  onRelease: () => void;
  onHoldExpired: () => void;
  busy: boolean;
}

export function VehicleCard({ vehicle: v, hold, compared, compareDisabled, onToggleCompare, onPurchase, onHold, onRelease, onHoldExpired, busy }: Props) {
  const soldOut = v.quantity === 0;
  // A shopper can buy if a unit is free OR they hold one themselves.
  const canBuy = !soldOut && (v.available > 0 || !!hold);
  const buyLabel = soldOut ? "Sold out" : canBuy ? (hold ? "Buy held car" : "Purchase") : "All units on hold";

  return (
    <article className={`flex flex-col overflow-hidden rounded-lg border bg-surface transition ${hold ? "border-enamel ring-2 ring-enamel/40" : "border-line"} ${soldOut ? "opacity-80" : ""}`}>
      <div className="relative bg-ink/[0.06] px-4 pb-1 pt-4">
        <div className="absolute left-3 top-3 rounded bg-surface/90 px-2 py-0.5 text-xs font-semibold text-muted">{v.category}</div>
        <div className="absolute right-3 top-3"><NumberPlate available={v.available} held={v.reserved} /></div>
        <div className="mx-auto mt-6 h-24 max-w-[15rem]"><CarSilhouette color={v.color} category={v.category} /></div>
      </div>

      <div className="flex flex-1 flex-col gap-3 p-4">
        <div>
          <h3 className="text-xl font-bold leading-tight">{v.make} {v.model}</h3>
          <p className="text-sm text-muted">{v.year ?? "Model year n/a"}</p>
        </div>
        <p className="font-display text-2xl font-extrabold">{formatPrice(v.price)}</p>

        {hold && <HoldTimer expiresAt={hold.expires_at} onExpire={onHoldExpired} />}

        <div className="mt-auto flex flex-wrap gap-2 pt-1">
          <button className="btn-primary flex-1" disabled={!canBuy || busy} onClick={onPurchase} aria-label={`${buyLabel}: ${vehicleTitle(v)}`}>
            {buyLabel}
          </button>
          {hold ? (
            <button className="btn-ghost" disabled={busy} onClick={onRelease}>Release</button>
          ) : (
            <button className="btn-ghost" disabled={v.available <= 0 || busy} onClick={onHold} title="Reserve one unit for 10 minutes">
              Hold 10 min
            </button>
          )}
        </div>

        <label className={`flex items-center gap-2 text-xs text-muted ${compareDisabled && !compared ? "opacity-50" : "cursor-pointer"}`}>
          <input type="checkbox" checked={compared} disabled={compareDisabled && !compared} onChange={onToggleCompare} />
          Compare
        </label>
      </div>
    </article>
  );
}

export function VehicleCardSkeleton() {
  return <div className="h-80 animate-pulse rounded-lg border border-line bg-surface" aria-hidden />;
}
