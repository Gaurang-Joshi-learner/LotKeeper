import { useState } from "react";
import { VehicleFormModal } from "../components/VehicleFormModal";
import { useAdminActions, useAllVehicles, useAnalytics, useEvents } from "../hooks/queries";
import { EVENT_LABELS, formatPrice, timeAgo, vehicleTitle } from "../lib/format";
import type { Vehicle } from "../lib/types";

type Tab = "vehicles" | "activity" | "insights";
const TABS: { id: Tab; label: string }[] = [
  { id: "vehicles", label: "Vehicles" },
  { id: "activity", label: "Activity" },
  { id: "insights", label: "Insights" },
];

export default function AdminPage() {
  const [tab, setTab] = useState<Tab>("vehicles");
  return (
    <main className="mx-auto max-w-7xl px-4 py-6">
      <h1 className="mb-4 text-4xl font-extrabold">Back office</h1>
      <div role="tablist" className="mb-6 flex gap-1 border-b border-line">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={`-mb-px border-b-2 px-4 py-2 text-sm font-semibold ${tab === t.id ? "border-enamel text-ink" : "border-transparent text-muted hover:text-ink"}`}
          >
            {t.label}
          </button>
        ))}
      </div>
      {tab === "vehicles" && <VehicleManager />}
      {tab === "activity" && <ActivityFeed />}
      {tab === "insights" && <Insights />}
    </main>
  );
}

function VehicleManager() {
  const { data: vehicles = [], isLoading } = useAllVehicles();
  const admin = useAdminActions();
  const [editing, setEditing] = useState<Vehicle | "new" | null>(null);
  const [confirmId, setConfirmId] = useState<number | null>(null);
  const [restockQty, setRestockQty] = useState<Record<number, string>>({});

  return (
    <section>
      <div className="mb-3 flex items-center justify-between">
        <p className="text-sm text-muted">{vehicles.length} vehicles on the lot</p>
        <button className="btn-primary" onClick={() => setEditing("new")}>Add vehicle</button>
      </div>

      <div className="overflow-x-auto rounded-lg border border-line bg-surface">
        <table className="w-full min-w-[46rem] text-left text-sm">
          <thead className="border-b border-line text-muted">
            <tr>
              <th className="p-3 font-semibold">Vehicle</th>
              <th className="p-3 font-semibold">Category</th>
              <th className="p-3 font-semibold">Price</th>
              <th className="p-3 font-semibold">On lot</th>
              <th className="p-3 font-semibold">On hold</th>
              <th className="p-3 font-semibold">Restock</th>
              <th className="p-3" />
            </tr>
          </thead>
          <tbody>
            {isLoading && <tr><td colSpan={7} className="p-6 text-center text-muted">Loading…</td></tr>}
            {vehicles.map((v) => (
              <tr key={v.id} className="border-b border-line last:border-0">
                <td className="p-3">
                  <span className="mr-2 inline-block h-3 w-3 rounded-full border border-ink/30 align-middle" style={{ background: v.color ?? "#7a8793" }} />
                  <span className="font-semibold">{vehicleTitle(v)}</span>
                </td>
                <td className="p-3">{v.category}</td>
                <td className="p-3">{formatPrice(v.price)}</td>
                <td className={`p-3 font-semibold ${v.quantity === 0 ? "text-brake" : ""}`}>{v.quantity}</td>
                <td className="p-3">{v.reserved}</td>
                <td className="p-3">
                  <form
                    className="flex gap-1"
                    onSubmit={(e) => {
                      e.preventDefault();
                      const qty = Number(restockQty[v.id] ?? "5");
                      if (qty > 0) admin.restock.mutate({ v, qty }, { onSuccess: () => setRestockQty((s) => ({ ...s, [v.id]: "" })) });
                    }}
                  >
                    <input className="field !w-16 !py-1" type="number" min={1} aria-label={`Units to add to ${vehicleTitle(v)}`} placeholder="5" value={restockQty[v.id] ?? ""} onChange={(e) => setRestockQty((s) => ({ ...s, [v.id]: e.target.value }))} />
                    <button className="btn-ghost !px-2 !py-1">Add</button>
                  </form>
                </td>
                <td className="whitespace-nowrap p-3 text-right">
                  <button className="btn-ghost !py-1" onClick={() => setEditing(v)}>Edit</button>{" "}
                  {confirmId === v.id ? (
                    <>
                      <button className="btn-danger !py-1" onClick={() => { admin.remove.mutate(v); setConfirmId(null); }}>Confirm delete</button>{" "}
                      <button className="btn-ghost !py-1" onClick={() => setConfirmId(null)}>Keep</button>
                    </>
                  ) : (
                    <button className="btn-ghost !py-1 text-brake" onClick={() => setConfirmId(v.id)}>Delete</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editing && (
        <VehicleFormModal
          vehicle={editing === "new" ? undefined : editing}
          onClose={() => setEditing(null)}
          onSubmit={(data) => (editing === "new" ? admin.create.mutateAsync(data) : admin.update.mutateAsync({ id: editing.id, data }))}
        />
      )}
    </section>
  );
}

function ActivityFeed() {
  const { data = [], isLoading } = useEvents();
  const tone = (t: string) => (t === "purchase" ? "bg-enamel" : t === "restock" ? "bg-plate" : t.includes("hold") ? "bg-muted" : t === "vehicle_deleted" ? "bg-brake" : "bg-ink");
  return (
    <section>
      <p className="mb-3 text-sm text-muted">Every stock change, newest first. Refreshes every few seconds.</p>
      <ol className="divide-y divide-line rounded-lg border border-line bg-surface">
        {isLoading && <li className="p-6 text-center text-muted">Loading…</li>}
        {!isLoading && data.length === 0 && <li className="p-6 text-center text-muted">No activity yet. Add a vehicle or make a purchase.</li>}
        {data.map((e) => (
          <li key={e.id} className="flex items-center gap-3 p-3 text-sm">
            <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${tone(e.type)}`} aria-hidden />
            <div className="min-w-0 flex-1">
              <p className="truncate">
                <span className="font-semibold">{EVENT_LABELS[e.type] ?? e.type}</span> · {e.vehicle_label ?? "Unknown vehicle"}
                {e.amount != null && <span className="text-muted"> · {formatPrice(e.amount)}</span>}
              </p>
              <p className="truncate text-xs text-muted">{e.user_email ?? "system"}{e.detail ? ` · ${e.detail}` : ""}</p>
            </div>
            {e.delta !== 0 && <span className={`font-semibold ${e.delta > 0 ? "text-enamel" : "text-brake"}`}>{e.delta > 0 ? `+${e.delta}` : e.delta}</span>}
            <time className="w-16 shrink-0 text-right text-xs text-muted" dateTime={e.created_at}>{timeAgo(e.created_at)}</time>
          </li>
        ))}
      </ol>
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-line bg-surface p-4">
      <p className="text-sm text-muted">{label}</p>
      <p className="mt-1 font-display text-3xl font-extrabold">{value}</p>
    </div>
  );
}

function Insights() {
  const { data, isLoading } = useAnalytics();
  if (isLoading || !data) return <p className="text-muted">Loading…</p>;
  const maxValue = Math.max(1, ...data.by_category.map((c) => c.value));
  const maxDay = Math.max(1, ...data.purchases_by_day.map((d) => d.purchases));

  return (
    <section className="space-y-6">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label="Inventory value" value={formatPrice(data.inventory_value)} />
        <Stat label="Units on the lot" value={String(data.units_in_stock)} />
        <Stat label="Units sold" value={String(data.units_sold)} />
        <Stat label="Revenue" value={formatPrice(data.revenue)} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-line bg-surface p-4">
          <h2 className="mb-3 text-xl font-bold">Value by category</h2>
          <ul className="space-y-2">
            {data.by_category.map((c) => (
              <li key={c.category} className="text-sm">
                <div className="mb-0.5 flex justify-between"><span className="font-semibold">{c.category}</span><span className="text-muted">{c.units} units · {formatPrice(c.value)}</span></div>
                <div className="h-2.5 rounded bg-line"><div className="h-full rounded bg-enamel" style={{ width: `${(c.value / maxValue) * 100}%` }} /></div>
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-lg border border-line bg-surface p-4">
          <h2 className="mb-3 text-xl font-bold">Sales, last 14 days</h2>
          <div className="flex h-36 items-end gap-1" role="img" aria-label="Purchases per day">
            {data.purchases_by_day.map((d) => (
              <div key={d.date} className="group flex flex-1 flex-col items-center justify-end" title={`${d.date}: ${d.purchases} sold`}>
                <div className={`w-full rounded-t ${d.purchases ? "bg-plate" : "bg-line"}`} style={{ height: `${d.purchases ? Math.max(8, (d.purchases / maxDay) * 100) : 3}%` }} />
              </div>
            ))}
          </div>
          <div className="mt-1 flex justify-between text-xs text-muted"><span>{data.purchases_by_day[0]?.date.slice(5)}</span><span>today</span></div>
        </div>
      </div>

      <div className="rounded-lg border border-line bg-surface p-4">
        <h2 className="mb-3 text-xl font-bold">Running low</h2>
        {data.low_stock.length === 0 ? (
          <p className="text-sm text-muted">Every vehicle has more than 2 units free.</p>
        ) : (
          <ul className="flex flex-wrap gap-2">
            {data.low_stock.map((i) => (
              <li key={i.id} className={`rounded-full border px-3 py-1 text-sm ${i.available === 0 ? "border-brake text-brake" : "border-line"}`}>
                {i.label} · <strong>{i.available === 0 ? "none free" : `${i.available} free`}</strong>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
