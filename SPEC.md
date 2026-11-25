# Solar Platform — Product Spec (for Claude Code)

Owner: Arul. Company: Sri Vinayaka-style rooftop solar installer, Tamil Nadu, India.
Goal: a website where customers request solar installations, and an admin panel where staff review, calculate, quote and plan each project. Later it will be sold to other installers, so it is **multi-tenant from day one**.

Reference material (read before writing calculation code): `reference/` — quotation sample, network-charge sheets, formula posters, installation checklist, TANGEDCO net-metering memo, panel/inverter datasheets. Section 6 summarises the rules taken from them; where a number looks inconsistent it is marked **VERIFY**.

---

## 1. Scope

### In scope (v1)
1. Public website: landing page, request form, request status page.
2. Admin panel: request pipeline, review, calculations, price list, quotation/estimate PDF, project pack, users and roles.
3. Calculation engine: system size, panel count, roof space, string design, inverter, cables, protection, network charges, cost and payback.
4. Auto-generated diagrams: single-line wiring diagram, roof layout, cable/protection schedule.
5. Email: automatic acknowledgement; quotation email sent only after admin approval.
6. Multi-tenant data model, per-installer settings and branding.
7. English and Tamil UI.

### Out of scope (v1) — leave extension points only
- Government subsidy application (PM Surya Ghar). Model a `subsidy_case` table/status placeholder but build nothing else.
- Online payments, GST e-invoicing, WhatsApp sending, customer mobile app, IoT monitoring.

### Key product rules
- **Customers never see a price automatically.** After submitting, they get an acknowledgement. Staff review the analysis, then press **Send quotation**.
- Online numbers are approximate until a site visit. Show a disclaimer on every customer-facing estimate.
- All rates, prices, GST, yield and standards are **settings per installer**, never hard-coded.

---

## 2. Users and roles

| Role | Can do |
|---|---|
| Customer | Submit requests, upload photos, view own request status and quotation. Login by phone OTP or email magic link. |
| Technician | See assigned projects, checklist, wiring sheet, upload site photos. No prices. |
| Engineer | Edit survey data, run/adjust calculations, edit diagrams. |
| Sales | Review requests, edit quotation, send quotation. |
| Admin (installer owner) | Everything for their installer: users, price list, settings, branding. |
| Platform owner | Create/manage installers (tenants). |

Every row in every table carries `installer_id`. All queries are scoped by it (use row-level security or a mandatory query filter, plus tests proving one installer cannot read another's data).

---

## 3. Suggested stack

React (Vite or Next.js) frontend; Python FastAPI backend; PostgreSQL; SQLAlchemy + Alembic migrations; Pydantic for validation. Background jobs (email, PDF) via a simple queue (RQ/Celery/arq). Docker Compose for deployment on a VPS, behind HTTPS (Caddy/Traefik/Nginx). Transactional email through Resend or Brevo (not direct SMTP from a personal mailbox). File storage: local volume or S3-compatible bucket. PDF: server-side HTML → PDF (WeasyPrint or Playwright). Diagrams: generate SVG in code, embed into PDFs.

Deploy to a subdomain of the owner's existing domain (e.g. `solar.<domain>`). Keep tenant resolution ready for `<installer>.<domain>` later.

Alternative stacks are fine if Claude Code has a strong reason; keep multi-tenancy, settings-driven calculations and tests non-negotiable.

---

## 4. Customer side

### 4.1 Request form (mobile-first)
- Contact: name, phone (OTP verify), email (optional), preferred language.
- Site: address, pincode/district, home or industry/commercial.
- Electricity: EB consumer number (optional), tariff (e.g. LA1A), phase (1 or 3), sanction load (kW), average monthly units **or** monthly bill amount.
- Roof: type (RCC / sheet / tile), approximate free area (sq ft or sq m), direction, shade (none/some/heavy), floors.
- Goal: reduce bill / backup (off-grid or hybrid) / industrial; budget range (optional).
- Uploads: EB bill photo, roof photos (up to 6).
- Consent checkbox for contact and data use.

### 4.2 After submit
- Show confirmation with reference number.
- Send acknowledgement email (template below). No price.
- Request status page: Received → Under review → Quotation ready → Site visit → Accepted → Installation → Completed.

### 4.3 Quotation view
When staff send a quotation, the customer gets an email with a secure link to view/download the PDF and **Accept** or **Ask a question**. Accept moves the project to the next stage and notifies staff.

---

## 5. Admin panel

### 5.1 Pipeline (kanban + list)
Stages: New → Analysed → Quoted → Site visit → Accepted → Installation → Net metering → Completed (+ Lost/On hold). Filters by stage, owner, district, kW, date. Activity log per request (who changed what).

### 5.2 Request review screen
- Customer data and uploaded photos side by side.
- **Auto-analysis panel** (runs on submit; re-run on edit): suggested kW, panel count, roof space needed vs available, inverter, estimated generation, rough cost range, rough savings/payback, warnings (small roof, shade, phase mismatch).
- Staff can override any input and see recalculated outputs immediately.
- Notes, assignments, site-visit scheduling.

### 5.3 Quotation / estimate builder
- Line items from the installer's price master (panel, inverter, structure, DC cable, AC cable, DCDB, ACDB, earthing, lightning arrester, MC4, cable tray/conduit, labour, transport, net-meter charges…).
- Per-line HSN, quantity, unit price, GST%. Totals computed server-side.
- Warranty and terms text per template.
- Output: PDF quotation (installer logo/branding, quote number sequence per installer, validity date) and an internal estimate with margin visible only to Admin/Sales.

### 5.4 Project pack (generated when quotation is accepted)
- Bill of materials with quantities.
- Tools list (see `TOOLS SOLAR POWER INSTALLATION.pdf`).
- 12-step installation checklist: site survey → design → structure → panel mounting → DC wiring → inverter → protection → earthing/testing → pre-commissioning tests → commissioning → net-metering and handover (see checklist image).
- Wiring diagram, roof layout, cable and protection schedule.
- Net-metering document checklist (see TANGEDCO memo).
- Technician mobile view: tick steps, upload photos, record Voc/Isc/earth-resistance readings.

### 5.5 Settings (per installer)
Company details, logo, GSTIN, bank details for quotation footer, email sender/reply-to, tax rates, network-charge rate table with effective dates, yield/CUF assumptions, panel catalogue (Wp, Voc, Vmp, Isc, Imp, dimensions, price), inverter catalogue (rating, phase, MPPT range, max DC voltage, max input current, price), standard cable sizes, templates for emails and quotation text.

---

## 6. Calculation engine

Implement as a pure, well-tested library (no web code) with unit tests using the worked examples below. Every constant comes from installer settings.

### 6.1 Sizing
- Generation per kW per day = 24 × CUF. With CUF 21%: 5.04 units/kW/day (matches the institute's 5 kW → 25.2 units/day example).
- Monthly units needed ÷ (units per kW per month) → kW needed, rounded up to the nearest panel count.
- Keep **two** yield settings: (a) *TNERC/CUF figure* used for network-charge calculation, default 21%; (b) *realistic yield* used for customer savings estimates, chosen by the owner. **VERIFY** the realistic default with real plant data.
- Also cap by sanction load and by available roof area.

### 6.2 Panel count and DC capacity
- Panels = ceil(target Wp ÷ panel Wp). Example from sample quotation #276: 5 × 615 W = 3,075 Wp → sold as "3 kW".

### 6.3 Roof space
- Rule of thumb from the institute's 1 kW guideline: minimum about 7.5 m² per kW, recommended 9–10 m² per kW. Also compute from actual panel dimensions + row spacing + tilt (shadow spacing using the trigonometry sheet: row spacing from module height × sin(tilt) and sun-elevation assumption, configurable).
- Tilt default ~10–15° in Tamil Nadu, south-facing, shade-free 9:00–16:00 (from the institute's checklist).
- Report: required area, available area, fit / does not fit.

### 6.4 String design and inverter
- Modules per string: Voc_cold × N ≤ inverter max DC voltage; Vmp_hot × N ≥ MPPT minimum; Isc × strings ≤ MPPT max current. Temperature coefficients and design temperatures are settings.
- Inverter: choose from catalogue by AC rating, phase, DC/AC ratio (default 1.0–1.3, configurable), and MPPT compatibility. Sample items seen: UTL 3.3 kW single-phase on-grid, UTL GT-5K.
- Off-grid/hybrid: battery capacity from daily load (see appliance load chart and `CALCULATIONS AND FORMULA BATTERY, INVERTER,CHARGER CONTROLLER SELECTION.pdf`), battery voltage, charge-controller current = array power ÷ battery voltage × safety factor.

### 6.5 Cables and protection
- DC cable: default 4 or 6 sq mm (from checklist), chosen by current and voltage-drop limit; AC cable by inverter output current. Voltage-drop limits are settings.
- DCDB: SPD + isolator/MCB. ACDB: MCB + SPD. Earthing: minimum 2 pits, target earth resistance < 5 Ω. Lightning arrester optional.
- Use basic electrical formulas: P = V × I, series (voltages add), parallel (currents add).

### 6.6 Network charges (Tamil Nadu)
From the network-charge sheets in the folder:
- Generated units = PV kW × 24 × CUF × days.
- Network charge = generated units × network rate × percentage allowed. For domestic consumers up to 10 kW, percentage allowed = 20%.
- GST on network charges = 18% (9% CGST + 9% SGST) per the sheet.
- Rate table by effective date: 1.27 (before 10.09.2022), 1.48 (from 10.09.2022), 1.53 (from 01.07.2023), 1.59 (from 01.07.2024). Store as a dated table.
- **VERIFY**: sample sheets use 1.56 and 1.6, which are not in the printed table, and billed amounts differ slightly from recomputed ones. Check the latest TNERC order and ask the owner before shipping.
- Worked example (test case): 5 kW, 65 days, CUF 21% → 1,638 units.

### 6.7 Costing, savings, payback
- Cost from price master + labour. GST per line.
- Savings = generated units × applicable tariff slab (tariff slabs are a setting, **VERIFY**) minus network charges.
- Payback = net cost ÷ annual savings. Show ranges, not single numbers, on anything customer-facing.
- Subsidy: not computed in v1. Keep a nullable `subsidy_amount` field so it can be added later.

### 6.8 Warnings the engine must raise
Roof too small, heavy shade, phase/sanction-load mismatch, string voltage out of range, inverter oversized or undersized, missing catalogue data.

---

## 7. Diagrams (generated, not drawn by hand)

1. **Single-line diagram (SVG → PDF):** panels → strings → DCDB (SPD, isolator) → inverter → ACDB (MCB, SPD) → net meter → grid, with earthing, labels for cable sizes, string counts and ratings. Off-grid/hybrid variants add charge controller and battery bank.
2. **Roof layout:** rectangle (or polygon) of the roof from entered dimensions, panels placed in rows with spacing, tilt and orientation noted, count shown. Warn if panels do not fit.
3. **Cable and protection schedule:** table of every cable run (from, to, size, length, type) and each protective device (rating).
Keep diagram generation as a separate module returning SVG so it can be reused in the admin UI and PDFs. Add snapshot tests.

---

## 8. Email

- Provider: Resend or Brevo via API. **From** address is a configurable setting; for now set **Reply-To** to `arulmurugan08@outlook.com`. Later switch From to the company domain and add SPF/DKIM DNS records.
- Templates (English and Tamil), editable per installer:
  1. **Acknowledgement** (automatic on submit): reference number, what happens next, no price.
  2. **Quotation ready** (manual send): link to PDF, validity, accept/ask-question links.
  3. **Status updates** (optional): site visit scheduled, installation started, completed.
- Log every email (to, template, time, provider id, delivery status). Retry failures. Rate-limit and honeypot the public form to stop spam.

---

## 9. Data model (starting point)

`installer`, `user`, `role`, `customer`, `site`, `request`, `request_file`, `analysis_run`, `quotation`, `quotation_line`, `price_item`, `panel_model`, `inverter_model`, `network_rate`, `setting`, `project`, `checklist_item`, `project_reading`, `diagram`, `email_log`, `activity_log`, `subsidy_case` (placeholder).
Keep analysis runs immutable (store inputs, settings snapshot, outputs) so an old quotation can always be explained.

---

## 10. Security, privacy, quality

- HTTPS only; password hashing for staff (Argon2/bcrypt); optional 2FA for Admin.
- Customer data (phone, address, EB consumer number) is personal data: restrict by role, no logging of full values, backups encrypted, delete-on-request.
- **Do not store bank account numbers or any government ID.**
- Uploaded files: type and size limits, virus-scan or at least re-encode images, private storage with signed URLs.
- Tests: unit tests for the calculation engine (worked examples above), API tests, tenant-isolation tests. CI runs them.
- Audit log for quotation edits and sends.

---

## 11. Phases and acceptance

**Phase 1 — Foundation:** auth and roles, multi-tenant schema, customer request form, admin request list/detail, calculation engine for sizing/space/network charge, acknowledgement email.
*Done when:* a test customer submits a request, receives the email, and staff see the analysis; tenant isolation tests pass.

**Phase 2 — Quotation and diagrams:** price master, quotation builder and PDF, send-quotation email, customer accept flow, single-line diagram and roof layout.
*Done when:* staff can produce and send a correct PDF quotation for a 3 kW and a 5 kW home example, matching a hand calculation.

**Phase 3 — Project pack and extras:** project pack, technician mobile checklist, bill-photo reading (use a vision model to extract units, sanction load, tariff — staff confirm), industrial/3-phase handling, Tamil templates.

**Phase 4 — Later:** subsidy workflow, WhatsApp, payments/invoices, reports, onboarding other installers.

---

## 12. Open questions for the owner
1. Realistic yield setting and tariff slabs for savings estimates.
2. Latest TNERC network-charge rate and the 1.56 / 1.6 discrepancy.
3. GST rates per item for the quotation template (sample quotation shows 5% on panels, inverter and structure).
4. Hosting details (VPS access, subdomain name).
5. Company branding, GSTIN, quotation terms and warranty wording.
6. Which panel and inverter models and prices to preload.
