# Bringing this into your repo with an honest Red → Green → Refactor history

The reviewers read your git log. Don't commit everything at once. For each slice below:

1. Add **only the test file(s)**, run `pytest`, watch them **fail** (red), commit with `test:`.
2. Add the implementation files, run `pytest`, watch them **pass** (green), commit with `feat:`.
3. Make any cleanup you'd genuinely do, re-run tests, commit with `refactor:`.

Read each file before you commit it. Change things you'd do differently — you need to defend every line in the interview.
Add the trailer to every AI-assisted commit (two blank lines, then):

    Co-authored-by: Claude <noreply@anthropic.com>

(The kata only requires "AI Tool Name <AI@users.noreply.github.com>" style; any clear tool name is fine.)

| Slice | Red (tests first) | Green (implementation) |
|---|---|---|
| 0 Scaffold | — | `.gitignore`, `docker-compose.yml`, `.github/`, `backend/requirements*.txt`, `pytest.ini`, `app/core/*`, `app/models.py` |
| 1 Security | `tests/test_security.py` | `app/core/security.py` (already in 0 — move it here to keep the history honest) |
| 2 Auth | `tests/conftest.py`, `tests/test_auth.py` | `schemas.py` (auth part), `services/errors.py`, `services/base.py`, `services/auth_service.py`, `api/deps.py`, `api/auth.py`, `main.py` |
| 3 Vehicles CRUD | `tests/test_vehicles.py` | `repositories/vehicle_repository.py`, `services/vehicle_service.py`, `api/vehicles.py` (CRUD routes) |
| 4 Search | `tests/test_search.py` | search params + `/search` route |
| 5 Purchase + restock | `tests/test_inventory.py` | `services/inventory_service.py` (purchase, restock) |
| 6 Holds | `tests/test_holds.py` | hold methods, `api/account.py`, expiry sweeper in `main.py` |
| 7 Concurrency | `tests/test_concurrency.py` | (should already pass — a good "characterisation" commit; say so in the message) |
| 8 Audit + analytics | `tests/test_audit_and_analytics.py` | `services/analytics_service.py`, `api/admin.py` |
| 8b Orders | `tests/test_orders.py` | `Order` model, `services/order_service.py`, `api/orders.py`, order write in `purchase` |
| 9 Seed | `tests/test_seed.py` | `app/seed.py` |
| 10 Frontend | `src/lib/format.test.ts`, `VehicleCard.test.tsx` | everything under `frontend/src` |
| 11 Docs | — | `README.md`, screenshots, `PROMPTS.md` |

Tip: if you want a *truer* TDD story, delete the implementation of one slice, rewrite it yourself from the test, and commit that.
