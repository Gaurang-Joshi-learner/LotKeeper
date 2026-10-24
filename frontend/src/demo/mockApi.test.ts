import { describe, expect, it } from "vitest";
import { installMockApi } from "./mockApi";

describe("demo mock API", () => {
  it("supports sign-in, hold, purchase from hold and admin-only analytics", async () => {
    installMockApi();
    const call = async (method: string, path: string, token?: string, body?: unknown) => {
      const res = await fetch(`/api${path}`, { method, headers: token ? { Authorization: `Bearer ${token}` } : {}, body: body ? JSON.stringify(body) : undefined });
      return { status: res.status, data: res.status === 204 ? null : await res.json() };
    };
    const login = await call("POST", "/auth/login", undefined, { email: "shopper@demo.com", password: "shopper12345" });
    const t = login.data.access_token;
    expect((await call("POST", "/auth/login", undefined, { email: "shopper@demo.com", password: "nope" })).status).toBe(401);
    expect((await call("GET", "/vehicles", t)).data).toHaveLength(16);
    expect((await call("POST", "/vehicles/4/hold", t)).status).toBe(201); // last BMW
    const bought = await call("POST", "/vehicles/4/purchase", t);
    expect(bought.data).toMatchObject({ quantity: 0, reserved: 0, available: 0 });
    expect((await call("POST", "/vehicles/4/purchase", t)).status).toBe(409);
    const mine = (await call("GET", "/orders/mine", t)).data;
    expect(mine).toHaveLength(1);
    expect(mine[0]).toMatchObject({ vehicle_label: "2024 BMW M340i", from_hold: true });
    expect((await call("GET", "/admin/analytics", t)).status).toBe(403);
    const admin = (await call("POST", "/auth/login", undefined, { email: "admin@demo.com", password: "admin12345" })).data.access_token;
    expect((await call("GET", "/admin/analytics", admin)).data.units_sold).toBeGreaterThan(10);
    expect((await call("GET", "/orders/mine", admin)).data).toEqual([]); // the admin never sees the shopper's order
  });
});
