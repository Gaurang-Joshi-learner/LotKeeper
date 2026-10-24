import { useState, type FormEvent } from "react";
import type { Vehicle, VehicleInput } from "../lib/types";
import { Modal } from "./Modal";

interface Props {
  vehicle?: Vehicle;
  onClose: () => void;
  onSubmit: (data: VehicleInput) => Promise<unknown>;
}

export function VehicleFormModal({ vehicle, onClose, onSubmit }: Props) {
  const [f, setF] = useState({
    make: vehicle?.make ?? "",
    model: vehicle?.model ?? "",
    category: vehicle?.category ?? "",
    price: vehicle ? String(vehicle.price) : "",
    quantity: vehicle ? String(vehicle.quantity) : "1",
    year: vehicle?.year ? String(vehicle.year) : "",
    color: vehicle?.color ?? "#2f5d50",
  });
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      await onSubmit({
        make: f.make.trim(),
        model: f.model.trim(),
        category: f.category.trim(),
        price: Number(f.price),
        quantity: Number(f.quantity),
        year: f.year ? Number(f.year) : null,
        color: f.color,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save the vehicle");
    } finally {
      setSaving(false);
    }
  }

  const input = (label: string, key: keyof typeof f, props: React.InputHTMLAttributes<HTMLInputElement> = {}) => (
    <label className="block text-sm font-semibold">
      {label}
      <input className="field mt-1 font-normal" value={f[key]} onChange={set(key)} {...props} />
    </label>
  );

  return (
    <Modal title={vehicle ? `Edit ${vehicle.make} ${vehicle.model}` : "Add a vehicle"} onClose={onClose}>
      <form onSubmit={submit} className="grid grid-cols-2 gap-3">
        {input("Make", "make", { required: true, maxLength: 60, autoFocus: true })}
        {input("Model", "model", { required: true, maxLength: 60 })}
        {input("Category", "category", { required: true, maxLength: 60, list: "categories", placeholder: "Sedan, SUV, Truck…" })}
        {input("Model year", "year", { type: "number", min: 1900, max: 2100 })}
        {input("Price (USD)", "price", { type: "number", min: 1, step: "0.01", required: true })}
        {input("Units on the lot", "quantity", { type: "number", min: 0, step: 1, required: true })}
        <label className="col-span-2 flex items-center gap-3 text-sm font-semibold">
          Paint colour
          <input type="color" value={f.color} onChange={set("color")} className="h-9 w-14 cursor-pointer rounded border border-line bg-transparent" />
        </label>
        {error && <p role="alert" className="col-span-2 rounded border border-brake/40 bg-brake/10 px-3 py-2 text-sm text-brake">{error}</p>}
        <div className="col-span-2 mt-2 flex justify-end gap-2">
          <button type="button" className="btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn-primary" disabled={saving}>{saving ? "Saving…" : vehicle ? "Save changes" : "Add vehicle"}</button>
        </div>
      </form>
    </Modal>
  );
}
