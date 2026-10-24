import { Link } from "react-router-dom";
import { CarSilhouette } from "../components/CarSilhouette";
import { useOrders } from "../hooks/queries";
import { formatPrice, timeAgo } from "../lib/format";

/** The signed-in user's own purchases. The server only ever returns the caller's orders. */
export default function OrdersPage() {
  const { data: orders = [], isLoading, isError, error } = useOrders();
  const total = orders.reduce((sum, o) => sum + o.price, 0);

  return (
    <main className="mx-auto max-w-4xl px-4 py-6">
      <div className="mb-5 flex flex-wrap items-end justify-between gap-2">
        <h1 className="text-4xl font-extrabold">My orders</h1>
        {orders.length > 0 && (
          <p className="text-sm text-muted">
            {orders.length} purchase{orders.length === 1 ? "" : "s"} · {formatPrice(total)} total
          </p>
        )}
      </div>

      {isError && <p role="alert" className="rounded border border-brake/40 bg-brake/10 p-4 text-sm text-brake">Could not load your orders: {(error as Error).message}</p>}
      {isLoading && <div className="h-28 animate-pulse rounded-lg border border-line bg-surface" aria-hidden />}

      {!isLoading && !isError && orders.length === 0 && (
        <div className="rounded-lg border border-dashed border-line p-10 text-center">
          <p className="text-xl font-bold">You haven&apos;t bought anything yet.</p>
          <p className="mt-1 text-sm text-muted">Hold a car for 10 minutes, or buy one straight away.</p>
          <Link to="/" className="btn-primary mt-4">Browse the lot</Link>
        </div>
      )}

      <ul className="space-y-3">
        {orders.map((o) => (
          <li key={o.id} className="flex items-center gap-4 rounded-lg border border-line bg-surface p-3">
            <div className="h-16 w-28 shrink-0 rounded bg-ink/[0.06] px-2 pt-2"><CarSilhouette color={o.color} category={o.category ?? "Sedan"} /></div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-lg font-bold">{o.vehicle_label}</p>
              <p className="text-sm text-muted">
                Order #{o.id} · <time dateTime={o.created_at}>{timeAgo(o.created_at)}</time>
                {o.from_hold && " · bought from a hold"}
              </p>
            </div>
            <p className="font-display text-xl font-extrabold">{formatPrice(o.price)}</p>
          </li>
        ))}
      </ul>
    </main>
  );
}
