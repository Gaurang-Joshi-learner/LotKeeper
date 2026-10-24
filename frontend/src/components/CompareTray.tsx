import { formatPrice, vehicleTitle } from "../lib/format";
import type { Vehicle } from "../lib/types";

export function CompareTray({ vehicles, onRemove, onClear }: { vehicles: Vehicle[]; onRemove: (id: number) => void; onClear: () => void }) {
  const rows: { label: string; value: (v: Vehicle) => string }[] = [
    { label: "Price", value: (v) => formatPrice(v.price) },
    { label: "Category", value: (v) => v.category },
    { label: "Year", value: (v) => String(v.year ?? "—") },
    { label: "Available", value: (v) => (v.available > 0 ? `${v.available} of ${v.quantity}` : "None") },
  ];
  const cheapest = Math.min(...vehicles.map((v) => v.price));

  return (
    <aside
      className={`fixed inset-x-0 bottom-0 z-30 border-t border-line bg-surface shadow-[0_-8px_24px_rgb(0_0_0/0.12)] transition-transform duration-300 ${vehicles.length ? "translate-y-0" : "translate-y-full"}`}
      aria-label="Compare vehicles"
      aria-hidden={vehicles.length === 0}
    >
      <div className="mx-auto max-w-7xl overflow-x-auto px-4 py-3">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-lg font-bold">Comparing {vehicles.length} of 3</h2>
          <button className="btn-ghost !py-1" onClick={onClear}>Clear</button>
        </div>
        <table className="w-full min-w-[32rem] text-left text-sm">
          <thead>
            <tr>
              <th className="w-24" />
              {vehicles.map((v) => (
                <th key={v.id} className="pb-1 pr-4 align-top font-semibold">
                  {vehicleTitle(v)}
                  <button className="ml-2 text-xs font-normal text-muted underline" onClick={() => onRemove(v.id)}>remove</button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.label} className="border-t border-line">
                <td className="py-1.5 pr-2 text-muted">{r.label}</td>
                {vehicles.map((v) => (
                  <td key={v.id} className={`py-1.5 pr-4 ${r.label === "Price" && vehicles.length > 1 && v.price === cheapest ? "font-bold text-enamel" : ""}`}>
                    {r.value(v)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </aside>
  );
}
