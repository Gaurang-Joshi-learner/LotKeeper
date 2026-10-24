# Lotkeeper — Car Dealership Inventory System

A full-stack dealership inventory app: FastAPI + PostgreSQL backend, React + Tailwind frontend, built test-first.

**Live demo:** _add your Vercel/Render link here_

## What makes it more than CRUD

| Feature | Why it matters |
|---|---|
| **Race-safe purchasing** | Stock changes are single conditional `UPDATE … WHERE quantity - reserved > 0` statements, plus DB `CHECK` constraints. A test fires 20 simultaneous buyers at 5 cars and asserts exactly 5 succeed. |
| **10-minute holds with live countdown** | Shoppers can reserve a unit. Holds reduce *available* stock, expire automatically (background sweeper + lazy expiry), and are consumed by the purchase. |
| **Per-user orders** | Every purchase creates an `orders` row owned by the buyer (price and car snapshotted). `GET /api/orders/mine` only ever returns the caller's own orders; admins get `/api/admin/orders`. The UI clears its cache on sign-out so accounts never leak into each other. |
| **Audit trail** | Every create/update/delete/purchase/restock/hold writes an event in the same transaction. Admins see a live activity feed; history survives deleted vehicles. |
| **Admin insights** | Inventory value, units sold, revenue, value by category, 14-day sales chart, low-stock list. |
| **Shareable filters** | Search/category/price/sort live in the URL. Debounced search, optimistic purchase with rollback, compare tray (up to 3 cars), dark mode, `/` to focus search. |

## Architecture

```
backend/app
  api/            thin FastAPI routers (HTTP only)
  services/       business rules: Auth, Vehicle, Inventory, Analytics (one transaction per call)
  repositories/   all SQL for vehicle search
  models.py       SQLAlchemy models + CHECK constraints
  core/           config, DB engine, JWT/bcrypt
frontend/src
  pages/ components/ hooks/ (React Query) auth/ lib/
```

Routers depend on services; services depend on repositories/models — never the reverse (Dependency Inversion via FastAPI `Depends`). Domain errors (`ConflictError`, `NotFoundError`, …) are mapped to HTTP in one place.

### API

| Method | Path | Access |
|---|---|---|
| POST | `/api/auth/register`, `/api/auth/login` | public |
| GET | `/api/auth/me` | user |
| POST/GET | `/api/vehicles` | user (`VEHICLE_WRITE_ADMIN_ONLY=true` makes POST/PUT admin-only) |
| GET | `/api/vehicles/search?make&model&category&q&min_price&max_price&in_stock&sort&limit&offset` | user |
| GET/PUT | `/api/vehicles/{id}` | user |
| DELETE | `/api/vehicles/{id}` | **admin** |
| POST | `/api/vehicles/{id}/purchase` | user |
| POST | `/api/vehicles/{id}/restock` | **admin** |
| POST/DELETE | `/api/vehicles/{id}/hold` · GET `/api/holds/mine` | user |
| GET | `/api/orders/mine` | user (own orders only) |
| GET | `/api/admin/events`, `/api/admin/analytics`, `/api/admin/orders` | **admin** |

Interactive docs at `http://localhost:8000/docs`.

## Run it

### Option A — Docker (one command)
```bash
docker compose up --build
# app: http://localhost:8080   api docs: http://localhost:8000/docs
```
Demo accounts (seeded): `admin@demo.com / admin12345` and `shopper@demo.com / shopper12345`.

### Option B — local dev
**macOS / Linux**
```bash
# backend (SQLite file by default; set DATABASE_URL for Postgres)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m app.seed                                      # demo admin, shopper and 16 cars
uvicorn app.main:app --reload                           # http://localhost:8000

# frontend (new terminal)
cd frontend
npm install
npm run dev                                             # http://localhost:5173 (proxies /api)
```

**Windows (PowerShell)**
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m app.seed
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

# second window
cd frontend
npm install
npm run dev
```

**Reset the database** (stop the server first): delete `backend/lotkeeper.db*` and run the seed again. The seed never modifies an existing account, so credentials only change after a reset. Always start the backend from the `backend` folder, otherwise a second empty database is created elsewhere.

### Tests
```bash
cd backend && pytest            # 83 tests, coverage report
cd frontend && npm test         # 10 tests
```

## Test report

Backend (`pytest`, SQLite file DB, real HTTP through `TestClient`):

```
83 passed
TOTAL  781 statements  40 missed  95% coverage
```
Covers: auth & JWT edge cases, validation, every endpoint's authorization (401/403), search filters, purchase/restock, holds & expiry, **concurrency**, audit log, analytics, seeding.
Uncovered lines are the DB-engine bootstrap, startup/sweeper loop, and the `__main__` seed entrypoint.

Frontend (`vitest`): 10 passed — formatting helpers and `VehicleCard` behaviour (Purchase disabled at zero stock, held-unit purchase, etc.).

_Re-run both and paste your own output here before submitting._

### Starting with an empty lot
Demo cars are optional: set `SEED_DEMO_VEHICLES=false` to seed only the admin/shopper accounts, then add inventory in **Back office**.

## Screenshots
_Add: sign-in, the lot (with a hold countdown), compare tray, back office table, activity feed, insights, dark mode._

## Design decisions & trade-offs
- **Money** is `NUMERIC(12,2)` in the DB; the API exposes floats for simplicity (cents-as-integers would be the next step).
- **Schema** is created with `create_all` at startup; a production system would use Alembic migrations.
- **Spec ambiguity:** only DELETE and restock are admin-only in the brief, so create/update are open to any signed-in user by default; one env flag locks them to admins.
- Registration always creates role `user`; the admin is seeded (no self-service privilege escalation).
- Tokens are stored in `localStorage` for simplicity; httpOnly cookies would be safer against XSS.

## My AI Usage
> **Write this yourself, honestly.** The kata grades it and you will be asked about it. Cover:
> 1. **Which tools** you used (e.g. Claude for design/boilerplate, Copilot for completions).
> 2. **How** — what you asked for, what you accepted, what you rewrote or rejected, and where the AI was wrong.
> 3. **Reflection** — how it changed your workflow, what you'd do differently.
>
> Be specific (e.g. "AI generated the first version of `InventoryService`; I replaced its read-then-write purchase logic after reasoning about races").
