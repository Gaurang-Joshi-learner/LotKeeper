import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { Hold, Vehicle } from "../lib/types";
import { VehicleCard } from "./VehicleCard";

const base: Vehicle = { id: 1, make: "Toyota", model: "Corolla", category: "Sedan", price: 21500, quantity: 3, reserved: 0, available: 3, year: 2025, color: "#c9ccd1" };

function setup(vehicle: Vehicle, hold?: Hold) {
  const handlers = { onPurchase: vi.fn(), onHold: vi.fn(), onRelease: vi.fn(), onToggleCompare: vi.fn(), onHoldExpired: vi.fn() };
  render(<VehicleCard vehicle={vehicle} hold={hold} compared={false} compareDisabled={false} busy={false} {...handlers} />);
  return handlers;
}

describe("VehicleCard", () => {
  it("lets a shopper purchase an in-stock car", async () => {
    const h = setup(base);
    const buy = screen.getByRole("button", { name: /purchase: 2025 toyota corolla/i });
    expect(buy).toBeEnabled();
    await userEvent.click(buy);
    expect(h.onPurchase).toHaveBeenCalledOnce();
  });

  it("disables Purchase and Hold when quantity is zero", () => {
    setup({ ...base, quantity: 0, available: 0 });
    expect(screen.getByRole("button", { name: /sold out/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /hold 10 min/i })).toBeDisabled();
  });

  it("disables Purchase when every unit is held by other shoppers", () => {
    setup({ ...base, quantity: 2, reserved: 2, available: 0 });
    expect(screen.getByRole("button", { name: /all units on hold/i })).toBeDisabled();
  });

  it("lets the holder buy their own held unit even though none are free", () => {
    const hold: Hold = { id: 9, vehicle_id: 1, status: "active", created_at: new Date().toISOString(), expires_at: new Date(Date.now() + 5 * 60_000).toISOString() };
    setup({ ...base, quantity: 1, reserved: 1, available: 0 }, hold);
    expect(screen.getByRole("button", { name: /buy held car/i })).toBeEnabled();
    expect(screen.getByRole("button", { name: /release/i })).toBeInTheDocument();
    expect(screen.getByText(/held for you/i)).toBeInTheDocument();
  });

  it("shows stock on the number plate", () => {
    setup(base);
    expect(screen.getByLabelText("3 available")).toBeInTheDocument();
  });
});
