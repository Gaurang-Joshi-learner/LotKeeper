import type { Analytics, Filters, Hold, InventoryEvent, Order, TokenResponse, User, Vehicle, VehicleInput } from "./types";

const TOKEN_KEY = "lotkeeper-token";

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t: string) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

/** Turn FastAPI's error shapes ({detail: string} or {detail: [{loc,msg}]}) into one readable string. */
function messageFrom(body: unknown, fallback: string): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d: { loc?: unknown[]; msg?: string }) => `${(d.loc ?? []).filter((p) => p !== "body").join(".")}: ${d.msg}`)
      .join("; ");
  }
  return fallback;
}

let onUnauthorized: () => void = () => {};
export const setUnauthorizedHandler = (fn: () => void) => { onUnauthorized = fn; };

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = tokenStore.get();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body) headers.set("Content-Type", "application/json");

  const res = await fetch(`/api${path}`, { ...init, headers });
  if (res.status === 204) return undefined as T;
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    if (res.status === 401 && token) onUnauthorized();
    throw new ApiError(res.status, messageFrom(body, res.statusText || "Request failed"));
  }
  return body as T;
}

const json = (data: unknown) => JSON.stringify(data);

export const api = {
  register: (email: string, password: string) => request<TokenResponse>("/auth/register", { method: "POST", body: json({ email, password }) }),
  login: (email: string, password: string) => request<TokenResponse>("/auth/login", { method: "POST", body: json({ email, password }) }),
  me: () => request<User>("/auth/me"),

  allVehicles: () => request<Vehicle[]>("/vehicles"),
  searchVehicles: (f: Filters) => {
    const p = new URLSearchParams({ sort: f.sort });
    if (f.q.trim()) p.set("q", f.q.trim());
    if (f.category) p.set("category", f.category);
    if (f.minPrice) p.set("min_price", f.minPrice);
    if (f.maxPrice) p.set("max_price", f.maxPrice);
    if (f.inStock) p.set("in_stock", "true");
    return request<Vehicle[]>(`/vehicles/search?${p}`);
  },
  createVehicle: (v: VehicleInput) => request<Vehicle>("/vehicles", { method: "POST", body: json(v) }),
  updateVehicle: (id: number, v: Partial<VehicleInput>) => request<Vehicle>(`/vehicles/${id}`, { method: "PUT", body: json(v) }),
  deleteVehicle: (id: number) => request<void>(`/vehicles/${id}`, { method: "DELETE" }),
  purchase: (id: number) => request<Vehicle>(`/vehicles/${id}/purchase`, { method: "POST" }),
  restock: (id: number, quantity: number) => request<Vehicle>(`/vehicles/${id}/restock`, { method: "POST", body: json({ quantity }) }),

  myOrders: () => request<Order[]>("/orders/mine"),
  myHolds: () => request<Hold[]>("/holds/mine"),
  hold: (id: number) => request<Hold>(`/vehicles/${id}/hold`, { method: "POST" }),
  release: (id: number) => request<void>(`/vehicles/${id}/hold`, { method: "DELETE" }),

  events: () => request<InventoryEvent[]>("/admin/events?limit=60"),
  analytics: () => request<Analytics>("/admin/analytics"),
};
