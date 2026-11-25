# Progress

## Status
| Phase | State |
|---|---|
| 1 — Foundation | **Done**: tests passing, smoke test passing |
| 2 — Quotation and diagrams | Not started |
| 3 — Project pack and extras | Not started |
| 4 — Later (subsidy, WhatsApp, payments, reports, onboarding) | Out of scope |

## Phase 1: what is done
- Multi-tenant schema (Alembic migration), mandatory tenant filter, tenant-isolation tests.
- Staff auth (Argon2 passwords, JWT, optional TOTP 2FA) and roles: admin, sales, engineer, technician, platform owner.
- Public site (English/Tamil): landing page, mobile-first request form (OTP verify, honeypot, rate limit, uploads), confirmation with reference number, status page, customer sign-in by email magic link or phone OTP.
- Calculation engine `backend/solarcalc` (pure library): sizing, panel count, roof space (rule of thumb + row geometry), network charges, strings/inverter, cables/protection, cost, savings, off-grid formulas.
- Auto-analysis on submit; admin pipeline (kanban + list + filters), request review screen with photos, analysis panel, live recalculation on input overrides, notes, assignment, site-visit scheduling, activity log.
- Settings per installer (company, calculation constants, tariff slabs, network-rate table, quotation text, email templates) with placeholder tracking; price list and catalogue editor; users; email log; platform-owner installer management.
- Acknowledgement email (EN/TA) through the outbox; no price in any customer response.

## How to run
```bash
docker compose -p solar up -d --build        # http://localhost:8088
```
- Public site: http://localhost:8088/s/demo
- Staff: http://localhost:8088/admin/login → installer `demo`, `admin@example.com` / `ChangeMe-2026!`
  (dev staff accounts `sales@demo.local`, `engineer@demo.local`, `technician@demo.local`, same password)
- Platform owner: installer `platform`, `platform@example.com` / `ChangeMe-2026!`
- Change seed credentials with `SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD`, `SEED_PLATFORM_EMAIL` in `.env` before first start.

### Tests
```bash
# all backend tests (SQLite) inside the API image
docker compose -p solar run --rm --no-deps -v "$PWD/backend:/app" api python -m pytest -q
# against Postgres
docker compose -p solar exec db psql -U solar -c "CREATE DATABASE solar_test"   # once
docker compose -p solar run --rm --no-deps -v "$PWD/backend:/app" -e DATABASE_URL=postgresql+psycopg://solar:solar-dev-password@db:5432/solar_test api python -m pytest -q
# end-to-end smoke test through the web proxy
docker compose -p solar run --rm --no-deps -v "$PWD/backend:/app" api python scripts/smoke.py --base http://web --phase 1
```
(On Windows Git Bash prefix with `MSYS_NO_PATHCONV=1` and use `$(pwd -W)`.)

## Next
Phase 2: price master → quotation builder, PDF, send-quotation email, customer accept flow, single-line diagram and roof layout.
