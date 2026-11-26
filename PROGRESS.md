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
docker compose -p solar run --rm --no-deps -v "$PWD/backend:/app" -e TEST_DATABASE_URL=postgresql+psycopg://solar:solar-dev-password@db:5432/solar_test api python -m pytest -q
# sample demo data through the normal app flow (5 requests, sent quote, accepted project)
docker compose -p solar run --rm --no-deps -v "$PWD/backend:/app" -w /app/scripts api python demo_data.py --base http://web
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

## Update 2026-11-26 (evening): full marketing site — 8 public pages
Theme changed to navy + sun-gold for the public site only (`.site-root` scope; admin unchanged).
- Pages (EN/TA): Home (redesigned: hero, solution cards, savings calculator, steps, benefits, recent projects, FAQ, CTA),
  `/residential`, `/commercial`, `/industrial` (one `SolutionPage` component), `/products` (on-grid/hybrid/off-grid,
  components, comparison table), `/calculator`, `/how-it-works` (animated roadmap + solar flow), `/projects` (filterable gallery).
- New header with Solutions dropdown, mobile menu, phone pill and CTA; new 4-column footer. About / request / status pages
  keep their layout inside the new shell and pick up the navy theme through the shared CSS variables.
- Copy: `frontend/src/siteContent.ts` (all new text, EN + TA). Styles: `frontend/src/site.css`. Icons: `components/Icon.tsx`.
- Images: `frontend/public/img/` (residential, commercial, industrial, hybrid-battery).
- Savings calculator: new backend endpoint `POST /api/public/{slug}/estimate` (`app/services/estimate.py`). It runs the
  normal engine with the installer's own settings and returns size, roof area, generation and a savings range only;
  cost, price lines and payback are stripped (tests in `tests/test_public_estimate.py`).
- Projects: entries in `siteContent.ts` → `projects.items`. The four entries there are `sample: true` and show only in
  `npm run dev`; the live build hides them until real projects are added.
- Checked: `tsc` passes; pages rendered server-side and screenshotted at desktop and mobile widths.
  Not yet run: `vite build` and the backend tests (run them in Docker, see "Tests" above).

## Update 2026-11-26 (night): document knowledge base (RAG, OpenAI)
- Admin → **Knowledge (AI)**: upload PDFs/images (or bulk import with `backend/scripts/kb_import.py`), indexing status,
  "Ask the documents" with answers citing document + page (click a citation to open the PDF at that page).
- Request → Review tab → **Design notes (AI)**: the engine's design (strings, cables, protection, earthing, structure,
  approvals, battery) is checked against the documents with citations and OK / CHECK / CONFLICT verdicts.
  It never changes calculations; quotations still come only from the tested engine. No prices are sent to the model.
- Indexing (worker thread): text PDFs read directly (pypdfium2); scanned pages and images are transcribed by the
  OpenAI vision model (diagrams described). Chunks + `text-embedding-3-small` (512 dims) stored in Postgres
  (`kb_document`, `kb_chunk`, migration `c41f7a2be9d0`). Search = cosine similarity + keyword boost, per installer.
- Config (.env): `OPENAI_API_KEY` (required), optional `OPENAI_CHAT_MODEL` / `OPENAI_VISION_MODEL` (default
  `gpt-5.4-mini`), `OPENAI_EMBED_MODEL`. Without a key, uploads wait as "pending".
- Roles: everyone on staff can ask; admin + engineer upload/re-index; admin deletes. Tests: `tests/test_knowledge.py`
  (fake OpenAI client; tests never call OpenAI).

## Update 2026-11-27: quotation by email/WhatsApp, "normal" staff role
- Request form: "Send my quotation by" WhatsApp / Email / Both (default WhatsApp, same as mobile unless changed).
  At least an email or a WhatsApp number is required, and the chosen channel must be filled (checked on the server).
- Send quotation: email goes only if the customer chose email/both; for WhatsApp the response includes a
  click-to-chat link (`services/whatsapp.py`, https://wa.me/...) with the message ready in the customer's language.
  Staff press "Send on WhatsApp" and then Send in their own WhatsApp Business app. No API, no cost.
- New role "normal": read-only pipeline, request review, designs, diagrams, design notes and knowledge base.
  Customer name, phone, email, WhatsApp, address, EB number, EB bill file, status link and quotations are removed
  on the server; no prices; cannot edit, add notes, quote, see activity, projects or email log.
- Migration `d7a3c5e1f2b4` (customer.whatsapp, customer.contact_pref). Tests: `tests/test_contact_roles.py`.

## Update 2026-11-27: Tamil admin (technicians), RAG wired into planning and quotations
- Admin sidebar has English / தமிழ். Technician screens (projects, checklist, readings, photos, materials, drawings,
  net-metering docs, design explanation) are fully EN/TA (`frontend/src/adminI18n.ts`, incl. Tamil for the default
  checklist points, tools and TANGEDCO documents). Other admin pages still English.
- Design check (`design_review` table, migration e5c2a9d4b7f1): structured OK / CHECK / CONFLICT / NOT_COVERED per topic
  with citations. When the knowledge base is ready, a quotation cannot be sent until the check has been run for its
  analysis and any CONFLICT is acknowledged with a reason (admin can send anyway with a logged reason).
  A CONFLICT must cite a document, otherwise it is downgraded to CHECK.
- Settings -> Placeholders -> "Suggest from documents" (admin): proposes values with references for yield, network %,
  commercial tariff, single-phase limit (and text-only guidance for network rate, tariff slabs, panel datasheet).
  "Apply values" changes only those fields (range-checked) and logs the sources; the admin then marks it confirmed.
- Project -> "Design explanation" tab: plain-language why-this-design in English or Tamil with citations; included in
  the project pack PDF (`?lang=ta`).
- Tests: tests/test_kb_features.py (fake AI).

## Deployment (Hostinger VPS behind Traefik)
The VPS already runs Traefik on 80/443 for other sites, so this project joins it instead of binding ports:
```bash
git clone https://github.com/arul2589/solar.git /opt/solar && cd /opt/solar
# .env: ENVIRONMENT=production, SECRET_KEY, POSTGRES_PASSWORD, PUBLIC_BASE_URL=https://solar.jujutech.tech,
#       SOLAR_DOMAIN=solar.jujutech.tech, SEED_ADMIN_PASSWORD, SEED_DEMO_STAFF=0, OPENAI_API_KEY
docker compose -p solar -f docker-compose.yml -f docker-compose.traefik.yml up -d --build
```
Update: `git pull && docker compose -p solar -f docker-compose.yml -f docker-compose.traefik.yml up -d --build`
