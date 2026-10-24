import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { CompareTray } from "../components/CompareTray";
import { FilterPanel } from "../components/FilterPanel";
import { VehicleCard, VehicleCardSkeleton } from "../components/VehicleCard";
import { useAllVehicles, useHoldActions, useHolds, usePurchase, useSearch } from "../hooks/queries";
import type { Filters } from "../lib/types";

const DEFAULTS: Filters = { q: "", category: "", minPrice: "", maxPrice: "", inStock: false, sort: "newest" };

/** Filters live in the URL, so any search is a shareable link and survives refresh. */
function useUrlFilters() {
  const [params, setParams] = useSearchParams();
  const filters: Filters = {
    q: params.get("q") ?? "",
    category: params.get("category") ?? "",
    minPrice: params.get("min") ?? "",
    maxPrice: params.get("max") ?? "",
    inStock: params.get("stock") === "1",
    sort: (params.get("sort") as Filters["sort"]) ?? "newest",
  };
  const write = (f: Filters) => {
    const p = new URLSearchParams();
    if (f.q) p.set("q", f.q);
    if (f.category) p.set("category", f.category);
    if (f.minPrice) p.set("min", f.minPrice);
    if (f.maxPrice) p.set("max", f.maxPrice);
    if (f.inStock) p.set("stock", "1");
    if (f.sort !== "newest") p.set("sort", f.sort);
    setParams(p, { replace: true });
  };
  return { filters, update: (patch: Partial<Filters>) => write({ ...filters, ...patch }), reset: () => write(DEFAULTS) };
}

export default function InventoryPage() {
  const { filters, update, reset } = useUrlFilters();
  const [text, setText] = useState(filters.q);
  const searchRef = useRef<HTMLInputElement>(null);
  const [compareIds, setCompareIds] = useState<number[]>([]);

  const all = useAllVehicles();
  const results = useSearch(filters);
  const holds = useHolds();
  const purchase = usePurchase();
  const { hold, release, refresh } = useHoldActions();

  // Debounce typing into the URL so we don't query on every keystroke.
  useEffect(() => {
    if (text === filters.q) return;
    const t = setTimeout(() => update({ q: text }), 250);
    return () => clearTimeout(t);
  }, [text]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { setText(filters.q); }, [filters.q]);

  // "/" jumps to search, like on GitHub.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (e.key === "/" && tag !== "INPUT" && tag !== "SELECT" && tag !== "TEXTAREA") {
        e.preventDefault();
        searchRef.current?.focus();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const categories = useMemo(() => [...new Set((all.data ?? []).map((v) => v.category))].sort(), [all.data]);
  const holdByVehicle = useMemo(() => new Map((holds.data ?? []).map((h) => [h.vehicle_id, h])), [holds.data]);
  const compared = useMemo(() => (all.data ?? []).filter((v) => compareIds.includes(v.id)), [all.data, compareIds]);
  const dirty = JSON.stringify(filters) !== JSON.stringify(DEFAULTS);
  const list = results.data ?? [];

  const toggleCompare = (id: number) =>
    setCompareIds((ids) => (ids.includes(id) ? ids.filter((x) => x !== id) : ids.length < 3 ? [...ids, id] : ids));

  return (
    <main className={`mx-auto max-w-7xl px-4 py-6 ${compared.length ? "pb-72" : "pb-12"}`}>
      <div className="mb-5 flex flex-wrap items-end justify-between gap-2">
        <h1 className="text-4xl font-extrabold">The lot</h1>
        <p className="text-sm text-muted" aria-live="polite">
          {results.isLoading ? "Loading…" : `${list.length} vehicle${list.length === 1 ? "" : "s"}${dirty ? " match your filters" : ""}`}
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[18rem_1fr]">
        <div className="lg:sticky lg:top-20 lg:self-start">
          <FilterPanel ref={searchRef} text={text} onText={setText} filters={filters} categories={categories} onChange={update} onReset={reset} dirty={dirty} />
        </div>

        <div>
          {results.isError && (
            <p role="alert" className="rounded border border-brake/40 bg-brake/10 p-4 text-sm text-brake">
              Could not load vehicles: {(results.error as Error).message}
            </p>
          )}

          {results.isLoading ? (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{Array.from({ length: 6 }, (_, i) => <VehicleCardSkeleton key={i} />)}</div>
          ) : list.length === 0 && !results.isError ? (
            <div className="rounded-lg border border-dashed border-line p-10 text-center">
              <p className="text-xl font-bold">Nothing on the lot matches that.</p>
              <p className="mt-1 text-sm text-muted">Widen the price range or clear a filter.</p>
              {dirty && <button className="btn-primary mt-4" onClick={reset}>Clear all filters</button>}
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {list.map((v) => (
                <VehicleCard
                  key={v.id}
                  vehicle={v}
                  hold={holdByVehicle.get(v.id)}
                  compared={compareIds.includes(v.id)}
                  compareDisabled={compareIds.length >= 3}
                  onToggleCompare={() => toggleCompare(v.id)}
                  onPurchase={() => purchase.mutate(v)}
                  onHold={() => hold.mutate(v)}
                  onRelease={() => release.mutate(v)}
                  onHoldExpired={refresh}
                  busy={purchase.isPending || hold.isPending || release.isPending}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      <CompareTray vehicles={compared} onRemove={toggleCompare} onClear={() => setCompareIds([])} />
    </main>
  );
}
