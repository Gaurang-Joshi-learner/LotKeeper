/**
 * Demo-only: replaces fetch() for /api/* with an in-browser fake of the FastAPI backend,
 * so the real UI can be explored without a server. Not bundled into the normal build.
 */
type Row = Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any
type Car = { id: number; make: string; model: string; category: string; price: number; quantity: number; reserved: number; year: number | null; color: string | null };

const SEED: [string, string, string, number, number, number, string][] = [
  ["Toyota", "Corolla", "Sedan", 21500, 6, 2025, "#C9CCD1"], ["Honda", "Civic", "Sedan", 24800, 4, 2025, "#9B1C20"],
  ["Tesla", "Model 3", "Sedan", 41990, 3, 2025, "#E7E9EC"], ["BMW", "M340i", "Sedan", 62500, 1, 2024, "#1F3A5F"],
  ["Toyota", "RAV4", "SUV", 33900, 5, 2025, "#2F5D50"], ["Hyundai", "Tucson", "SUV", 31200, 4, 2025, "#B8C2CC"],
  ["Volvo", "XC90", "SUV", 58900, 2, 2024, "#3B4B59"], ["Land Rover", "Defender 110", "SUV", 71500, 1, 2025, "#4E5B3A"],
  ["Ford", "F-150", "Truck", 44900, 3, 2025, "#B5521B"], ["Rivian", "R1T", "Truck", 73000, 0, 2024, "#E0A526"],
  ["Mazda", "MX-5 Miata", "Convertible", 31700, 2, 2025, "#C23B22"], ["Porsche", "911 Carrera", "Coupe", 118000, 1, 2024, "#202428"],
  ["Chevrolet", "Corvette", "Coupe", 69900, 0, 2024, "#E4C21F"], ["Kia", "EV6", "Hatchback", 44500, 3, 2025, "#6C7A89"],
  ["Volkswagen", "Golf GTI", "Hatchback", 33400, 2, 2025, "#0E3B7A"], ["Chrysler", "Pacifica", "Van", 41200, 2, 2024, "#7A8793"],
];
const USERS: Record<string, { id: number; email: string; role: string; password: string }> = {
  "admin@demo.com": { id: 1, email: "admin@demo.com", role: "admin", password: "admin12345" },
  "shopper@demo.com": { id: 2, email: "shopper@demo.com", role: "user", password: "shopper12345" },
};
const HOLD_MS = 10 * 60_000;
const HISTORY = [0, 1, 0, 2, 1, 0, 3, 1, 2, 0, 1, 2, 1]; // fake sales for the 13 days before today

export function installMockApi() {
  const cars: Car[] = SEED.map(([make, model, category, price, quantity, year, color], i) => ({ id: i + 1, make, model, category, price, quantity, reserved: 0, year, color }));
  const holds: Row[] = [];
  const events: Row[] = [];
  const orders: Row[] = [];
  let nextId = 100;
  const ago = (min: number) => new Date(Date.now() - min * 60_000).toISOString();
  const label = (c: Car) => [c.year, c.make, c.model].filter(Boolean).join(" ");
  const log = (type: string, c: Car | null, who: string, delta = 0, amount: number | null = null, detail: string | null = null, at = new Date().toISOString()) =>
    events.unshift({ id: nextId++, type, vehicle_id: c?.id ?? null, vehicle_label: c ? label(c) : null, user_email: who, delta, amount, detail, created_at: at });
  log("vehicle_created", cars[11], "admin@demo.com", 1, null, null, ago(240));
  log("purchase", cars[0], "shopper@demo.com", -1, 21500, null, ago(95));
  log("restock", cars[4], "admin@demo.com", 3, null, null, ago(30));

  const view = (c: Car) => ({ ...c, available: c.quantity - c.reserved });
  const reply = (body: unknown, status = 200) => new Response(status === 204 ? null : JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
  const fail = (status: number, detail: string) => reply({ detail }, status);
  const sweep = () => {
    for (const h of holds) if (h.status === "active" && Date.parse(h.expires_at) <= Date.now()) {
      h.status = "expired";
      const c = cars.find((x) => x.id === h.vehicle_id);
      if (c) { c.reserved--; log("hold_expired", c, h.user); }
    }
  };

  const real = window.fetch.bind(window);
  window.fetch = async (input, init = {}) => {
    const url = new URL(typeof input === "string" ? input : input instanceof URL ? input.href : input.url, location.origin);
    if (!url.pathname.startsWith("/api/")) return real(input, init);
    await new Promise((r) => setTimeout(r, 120));
    sweep();

    const path = url.pathname.slice(4);
    const method = (init.method ?? "GET").toUpperCase();
    const body: Row = init.body ? JSON.parse(String(init.body)) : {};
    const token = new Headers(init.headers).get("Authorization")?.replace("Bearer ", "");
    const me = token?.startsWith("demo:") ? USERS[token.slice(5)] ?? { id: nextId++, email: token.slice(5), role: "user", password: "" } : undefined;
    const q = url.searchParams;
    const m = (re: RegExp) => path.match(re);
    const issue = (u: { id: number; email: string; role: string }) => reply({ access_token: `demo:${u.email}`, token_type: "bearer", user: { id: u.id, email: u.email, role: u.role } });

    if (method === "POST" && path === "/auth/login") {
      const u = USERS[String(body.email).toLowerCase()];
      return u && u.password === body.password ? issue(u) : fail(401, "Incorrect email or password");
    }
    if (method === "POST" && path === "/auth/register") {
      const email = String(body.email).toLowerCase();
      if (USERS[email]) return fail(409, "An account with this email already exists");
      USERS[email] = { id: nextId++, email, role: "user", password: body.password };
      return issue(USERS[email]);
    }
    if (!me) return fail(401, "Not authenticated");
    const admin = me.role === "admin";

    if (path === "/auth/me") return reply({ id: me.id, email: me.email, role: me.role });
    if (method === "GET" && path === "/vehicles") return reply([...cars].reverse().map(view));
    if (method === "GET" && path === "/vehicles/search") {
      const text = (q.get("q") ?? "").toLowerCase(), cat = (q.get("category") ?? "").toLowerCase();
      const lo = q.get("min_price") ? Number(q.get("min_price")) : 0, hi = q.get("max_price") ? Number(q.get("max_price")) : Infinity;
      const sort = q.get("sort") ?? "newest";
      const out = cars.filter((c) => (!text || [c.make, c.model, c.category].some((s) => s.toLowerCase().includes(text))) && (!cat || c.category.toLowerCase().includes(cat)) && c.price >= lo && c.price <= hi && (q.get("in_stock") !== "true" || c.quantity - c.reserved > 0));
      out.sort((a, b) => sort === "price_asc" ? a.price - b.price : sort === "price_desc" ? b.price - a.price : sort === "name" ? (a.make + a.model).localeCompare(b.make + b.model) : b.id - a.id);
      return reply(out.map(view));
    }
    if (method === "POST" && path === "/vehicles") {
      const c = { year: null, color: null, ...body, id: nextId++, reserved: 0 } as Car;
      cars.push(c); log("vehicle_created", c, me.email, c.quantity);
      return reply(view(c), 201);
    }
    if (method === "GET" && path === "/orders/mine") return reply(orders.filter((o) => o.user === me.email).map(({ user: _u, ...o }) => o).reverse());
    if (method === "GET" && path === "/holds/mine") return reply(holds.filter((h) => h.status === "active" && h.user === me.email).map(({ user: _u, ...h }) => h));
    if (path === "/admin/events") return admin ? reply(events.slice(0, 60)) : fail(403, "Admin access required");
    if (path === "/admin/analytics") {
      if (!admin) return fail(403, "Admin access required");
      const sales = events.filter((e) => e.type === "purchase" && Date.parse(e.created_at) > Date.now() - 864e5);
      const today = sales.length;
      const byCat = new Map<string, { units: number; value: number }>();
      cars.forEach((c) => { const x = byCat.get(c.category) ?? { units: 0, value: 0 }; x.units += c.quantity; x.value += c.quantity * c.price; byCat.set(c.category, x); });
      return reply({
        vehicle_count: cars.length, units_in_stock: cars.reduce((n, c) => n + c.quantity, 0), units_reserved: cars.reduce((n, c) => n + c.reserved, 0),
        inventory_value: cars.reduce((n, c) => n + c.quantity * c.price, 0),
        units_sold: HISTORY.reduce((a, b) => a + b, 0) + today, revenue: HISTORY.reduce((a, b) => a + b, 0) * 38000 + events.filter((e) => e.type === "purchase").reduce((n, e) => n + e.amount, 0),
        by_category: [...byCat].map(([category, v]) => ({ category, ...v })).sort((a, b) => b.value - a.value),
        purchases_by_day: [...HISTORY, today].map((purchases, i, a) => ({ date: new Date(Date.now() - (a.length - 1 - i) * 864e5).toISOString().slice(0, 10), purchases, revenue: purchases * 38000 })),
        low_stock: cars.filter((c) => c.quantity - c.reserved <= 2).map((c) => ({ id: c.id, label: label(c), available: c.quantity - c.reserved })).sort((a, b) => a.available - b.available),
      });
    }

    const id = Number(m(/^\/vehicles\/(\d+)/)?.[1]);
    const car = cars.find((c) => c.id === id);
    if (!id) return fail(404, "Not found");
    if (!car) return fail(404, "Vehicle not found");
    const mine = holds.find((h) => h.status === "active" && h.vehicle_id === id && h.user === me.email);

    if (method === "PUT" && path === `/vehicles/${id}`) {
      if (body.quantity != null && body.quantity < car.reserved) return fail(409, `Quantity cannot be lower than the ${car.reserved} unit(s) currently on hold`);
      Object.assign(car, body); log("vehicle_updated", car, me.email, 0, null, Object.keys(body).join(", "));
      return reply(view(car));
    }
    if (method === "DELETE" && path === `/vehicles/${id}`) {
      if (!admin) return fail(403, "Admin access required");
      cars.splice(cars.indexOf(car), 1); log("vehicle_deleted", car, me.email, -car.quantity);
      return reply(null, 204);
    }
    if (method === "POST" && path.endsWith("/restock")) {
      if (!admin) return fail(403, "Admin access required");
      car.quantity += body.quantity; log("restock", car, me.email, body.quantity);
      return reply(view(car));
    }
    if (method === "POST" && path.endsWith("/hold")) {
      if (mine) return fail(409, "You already have a hold on this vehicle");
      if (car.quantity - car.reserved <= 0) return fail(409, "No unit is available to hold");
      car.reserved++;
      const h = { id: nextId++, vehicle_id: id, user: me.email, status: "active", created_at: new Date().toISOString(), expires_at: new Date(Date.now() + HOLD_MS).toISOString() };
      holds.push(h); log("hold_placed", car, me.email, 0, null, "10 min");
      const { user: _u, ...out } = h;
      return reply(out, 201);
    }
    if (method === "DELETE" && path.endsWith("/hold")) {
      if (!mine) return fail(404, "You have no active hold on this vehicle");
      mine.status = "released"; car.reserved--; log("hold_released", car, me.email);
      return reply(null, 204);
    }
    if (method === "POST" && path.endsWith("/purchase")) {
      if (mine) { mine.status = "converted"; car.reserved--; }
      else if (car.quantity - car.reserved <= 0) return fail(409, "This vehicle is out of stock");
      car.quantity--;
      orders.push({ id: nextId++, user: me.email, vehicle_id: car.id, vehicle_label: label(car), category: car.category, color: car.color, price: car.price, from_hold: !!mine, created_at: new Date().toISOString() });
      log("purchase", car, me.email, -1, car.price, mine ? "from hold" : null);
      return reply(view(car));
    }
    return fail(404, "Not found");
  };
}
