import { forwardRef } from "react";
import type { Filters } from "../lib/types";

interface Props {
  text: string;
  onText: (v: string) => void;
  filters: Filters;
  categories: string[];
  onChange: (patch: Partial<Filters>) => void;
  onReset: () => void;
  dirty: boolean;
}

export const FilterPanel = forwardRef<HTMLInputElement, Props>(function FilterPanel({ text, onText, filters, categories, onChange, onReset, dirty }, ref) {
  return (
    <section className="space-y-5 rounded-lg border border-line bg-surface p-4" aria-label="Search and filters">
      <div>
        <label htmlFor="search" className="mb-1 block text-sm font-semibold">Search</label>
        <input id="search" ref={ref} className="field" placeholder="Make, model or category  (press /)" value={text} onChange={(e) => onText(e.target.value)} />
      </div>

      <div>
        <p className="mb-1.5 text-sm font-semibold">Category</p>
        <div className="flex flex-wrap gap-1.5">
          {["", ...categories].map((c) => (
            <button
              key={c || "all"}
              onClick={() => onChange({ category: c })}
              aria-pressed={filters.category === c}
              className={`rounded-full border px-3 py-1 text-xs font-semibold transition ${filters.category === c ? "border-enamel bg-enamel text-white dark:text-floor" : "border-line hover:border-ink"}`}
            >
              {c || "All"}
            </button>
          ))}
        </div>
      </div>

      <div>
        <p className="mb-1.5 text-sm font-semibold">Price range</p>
        <div className="flex items-center gap-2">
          <input className="field" type="number" min={0} inputMode="numeric" placeholder="Min" aria-label="Minimum price" value={filters.minPrice} onChange={(e) => onChange({ minPrice: e.target.value })} />
          <span className="text-muted">to</span>
          <input className="field" type="number" min={0} inputMode="numeric" placeholder="Max" aria-label="Maximum price" value={filters.maxPrice} onChange={(e) => onChange({ maxPrice: e.target.value })} />
        </div>
      </div>

      <div className="flex items-center justify-between gap-3">
        <label className="flex cursor-pointer items-center gap-2 text-sm">
          <input type="checkbox" checked={filters.inStock} onChange={(e) => onChange({ inStock: e.target.checked })} /> In stock only
        </label>
        <select className="field !w-auto" aria-label="Sort" value={filters.sort} onChange={(e) => onChange({ sort: e.target.value as Filters["sort"] })}>
          <option value="newest">Newest</option>
          <option value="price_asc">Price: low to high</option>
          <option value="price_desc">Price: high to low</option>
          <option value="name">Name</option>
        </select>
      </div>

      {dirty && <button className="btn-ghost w-full" onClick={onReset}>Clear all filters</button>}
    </section>
  );
});
