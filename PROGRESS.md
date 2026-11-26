# Progress

## Status
| Phase | State |
|---|---|
| 1 — Foundation | **Done**: tests passing, smoke test passing |
| 2 — Quotation and diagrams | **Done**: tests passing, smoke test passing |
| 3 — Project pack and extras | **Done**: tests passing (84), smoke test passing |
| 4 — Later (subsidy, WhatsApp, payments, reports, onboarding) | Out of scope |

## Phase 1: what is done
- Multi-tenant schema (Alembic migration), mandatory tenant filter, tenant-isolation tests.
- Staff auth (Argon2 passwords, JWT, optional TOTP 2FA) and roles: admin, sales, engineer, technician, platform owner.
- Public site (English/Tamil): landing page, mobile-first request form (OTP verify, honeypot, rate limit, uploads), confirmation with reference number, status page, customer sign-in by email magic link or phone OTP.
- Calculation engine `backend/solarcalc` (pure library): sizing, panel count, roof space (rule of thumb + row geometry), network charges, strings/inverter, cables/protection, cost, savings, off-grid formulas.
- Auto-analysis on submit; admin pipeline (kanban + list + filters), request review screen with photos, analysis panel, live recalculation on input overrides, notes, assignment, site-visit scheduling, activity log.
- Settings per installer (company, calculation constants, tariff slabs, network-rate table, quotation text, email templates) with placeholder tracking; price list and catalogue editor; users; email log; platform-owner installer management.
- Acknowledgement email (EN/TA) through the outbox; no price in any customer response.

## Phase 2: what is done
- Price master with quantity rules (per kW, per panel, cable metres, earth pits, per MPPT, phase / inverter-phase / kind / kW filters) seeded from quotation #276.
- Quotation builder: drafted from the latest analysis run, editable lines (add from price list, reorder, edit qty/rate/GST/HSN/cost), totals always recomputed server-side with Decimal half-up rounding, per-installer quote number sequence (starts at 277), validity date, terms/scope/warranty text, revise-to-new-number, audit log of every edit and send.
- PDF quotation (WeasyPrint): installer branding and logo, customer and TNEB details, line table with HSN/qty/price/tax/total, totals in Indian grouping and in words, disclaimer, terms, payment instructions (no account number), scope, warranty, single-line diagram and roof layout pages. Internal estimate PDF with cost and margin for Admin/Sales only.
- Send quotation: stores the PDF, emails a secure link (EN/TA template), marks older sent quotes superseded, moves the request to Quoted.
- Customer quotation page (by emailed link or status page): view, download PDF, Accept (moves to Accepted and notifies staff), Ask a question (logged + staff email).
- Diagrams module `backend/diagrams/svg.py`: single-line diagram (incl. hybrid battery), roof layout with fit warning, cable and protection schedule; SVG snapshot tests.
- Acceptance tests: 3 kW (₹2,08,120.48) and 5 kW (₹3,23,476.48) home examples match line-by-line hand calculations in `tests/test_phase2.py`, and the totals appear in the PDF text.

## Phase 3: what is done
- Project created automatically when a customer accepts: bill of materials (quantities only, no prices), tools list, 12-step checklist (English + Tamil titles), string plan, cable/protection schedule, expected test values, TANGEDCO net-metering document checklist. Defaults editable in Settings → Project.
- Technician mobile view (Projects): sees only assigned projects; tick steps and sub-points, notes, record Voc/Isc/earth resistance/insulation readings with automatic OK/CHECK against the design, camera photo upload, drawings, materials. Project status drives the request stage (installation → net metering → completed) and customer status emails.
- Project pack PDF with diagrams.
- Bill-photo reading: staff press "Read bill (AI)" on an EB bill upload; Claude (`claude-opus-5-5`, JSON-schema structured output, image or PDF input, server-side refusal fallback) extracts consumer no., tariff, phase, sanction load, units, period and amount. Values are shown as suggestions; staff click Apply and then Save, so nothing changes without confirmation. Needs `ANTHROPIC_API_KEY` in `.env`; without it the button returns a clear "not configured" message.
- Industrial / 3-phase: several identical inverters for large plants (e.g. 30 kW → 3 × 10 kW three-phase), per-inverter AC runs and MCBs, outgoing MCCB, CEIG inspection notice ≥ 10 kW, HT/EHT notice > 112 kW, non-domestic network-charge percentage and tariff.
- Tamil: all customer emails (acknowledgement, quotation ready, status updates, sign-in link) and the public UI in Tamil; Tamil checklist titles for technicians.

## Not done / known gaps
- Visual browser check of the UI was not possible in this session (Chrome extension not connected); all flows were exercised through the API smoke test and backend tests, and the frontend type-checks and builds.
- Tamil text was written without native-speaker review.
- No real SMS provider (OTP codes go to the server log); email uses the `log` provider until a Resend/Brevo key is set.
- Phase 4 items (subsidy workflow, WhatsApp, payments/invoices, reports, self-service onboarding) are not built; `subsidy_case` and `quotation.subsidy_amount` are placeholders.

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
docker compose -p solar run --rm --no-deps -v "$PWD/backend:/app" api python scripts/smoke.py --base http://web --phase 3
```
(On Windows Git Bash prefix with `MSYS_NO_PATHCONV=1` and use `$(pwd -W)`.)

## Next
Owner to review Settings → Placeholders and confirm each value; then deploy (set `.env` from `.env.example`, `SITE_ADDRESS=solar.<domain>`, point DNS, `docker compose -p solar up -d --build`). Phase 4 after that.

## Update 2026-11-26: Home and About pages (added outside Claude Code)
Changed only in `frontend/src` (no backend changes). Built with `npm run build` and checked in desktop, mobile and Tamil.
- New: `src/content.ts` (all Home/About copy in English + Tamil; edit text here), `src/components/SolarFlow.tsx` (sun -> panels -> inverter -> building -> grid illustration), `src/pages/public/About.tsx`.
- Rewritten: `src/pages/public/Landing.tsx` (hero, what is solar, benefits, system types, who it is for, savings factors, how it works, FAQ, CTA, contact). It also exports `IconCards`, which About reuses.
- Edited: `src/pages/public/PublicLayout.tsx` (header nav Home / About us / Get a quotation, wide layout only for Home and About, footer links), `src/App.tsx` (route `/s/:slug/about`), `src/styles.css` (new styles appended at the end; language buttons now side by side).
- About text is generic: it names no years of experience, installation counts or certifications. The owner should add real company facts in `content.ts`.
- Tamil text for these pages has not been reviewed by a native speaker.
- To see it: `docker compose -p solar up -d --build web`, then open http://localhost:8088/s/demo and /s/demo/about.
- Please do not revert these files. Keep the existing i18n for the request form and status pages.
