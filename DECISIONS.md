# Decisions and assumptions

Built autonomously per CLAUDE.md "Autonomous mode". Every placeholder below is also listed
in **Admin → Settings → Placeholders** with a "placeholder - owner must confirm" tag, and
stays flagged until the owner presses *Mark confirmed*.

## Placeholders the owner must confirm (SPEC VERIFY items)

| Key (Settings → Placeholders) | Placeholder used | Why / source |
|---|---|---|
| `calc.realistic_yield` | 3.8–4.4 kWh/kW/day (sizing uses the mid value 4.1) | SPEC 6.1 VERIFY. Institute poster says 4–5 units/day per kW; CUF 21% gives 5.04 (used only for network charges). |
| `network_rate.latest` | Dated table 1.27 / 1.48 (10.09.2022) / 1.53 (01.07.2023) / 1.59 (01.07.2024) | SPEC 6.6 VERIFY. Sample bills used 1.56 and 1.6, not in the printed table. Rates are editable rows with effective dates. |
| `calc.network_pct_other` | 100% for non-domestic or > 10 kW | Only the domestic ≤ 10 kW rule (20%) is in the sheets. |
| `tariff_slabs.domestic` | Bi-monthly telescopic slabs: 0–100 free, 101–200 ₹2.35, 201–400 ₹4.70, 401–500 ₹6.30, 501–600 ₹8.40, 601–800 ₹9.45, 801–1000 ₹10.50, >1000 ₹11.55 | SPEC 6.7 VERIFY. Used for savings and to turn a bill amount into units. |
| `calc.commercial_flat_rate` | ₹9.00/unit | No commercial/industrial slabs given. |
| `price_items.gst` | 5% panels and inverter, 18% BOS, 0% services/charges | Copied from quotation #276 (SPEC 12 Q3). |
| `price_items.prices` | All prices from quotation #276 (June 2026); 3-phase ACDB ₹4,500, battery ₹18,000/kWh and hybrid/10 kW inverter prices are guesses | SPEC 12 Q6. |
| `catalogue.panel_specs` | 615 Wp TOPCon: Voc 52.6, Vmp 44.0, Isc 14.75, Imp 13.98, βVoc −0.25 %/°C, γ −0.29 %/°C, 2382 × 1134 mm | No datasheet in `reference/` for the quoted Adani 615 W panel. The Waaree 710 W row is from its datasheet. |
| `catalogue.inverter_specs` | UTL 3.3 kW: 550 V max, MPPT 80–500 V, 16 A. 10 kW 3-ph and 5 kW hybrid are generic | Only the UTL GT-5K nameplate photo was available (550 V, MPPT 250–500 V, 20 A, 25 A AC) and is used as-is. |
| `company.branding` | Neutral "Demo Rooftop Solar", no GSTIN, no bank details | See "Branding" below (SPEC 12 Q5). |
| `calc.single_phase_max_kw` | 5 kW | Above this on a 3-phase supply the engine prefers a 3-phase inverter. Quotation #276 put a 1-ph 3.3 kW inverter on a 3-ph supply, so small 1-ph inverters stay allowed. |
| `calc.cost_range_band_pct` | ±10% | Width of the rough cost range shown on the analysis panel. |
| `email.from_address` | `onboarding@resend.dev` (provider sandbox), Reply-To `arulmurugan08@outlook.com` | SPEC 8: switch to the company domain after SPF/DKIM. |
| `features.require_phone_otp` | Off | No SMS provider credentials yet. The OTP flow is built and tested (codes go to the server log; in development they are shown on screen). |

Other design defaults (editable in Settings → Calculation, not flagged): tilt 12°, design sun elevation 30° for row spacing, 0.3 m edge clearance and min row gap (institute 1 kW guideline), cell temperature 10 °C / 70 °C for string limits, DC/AC ratio 1.0–1.3, 1.25 current safety factor, DC voltage drop ≤ 1.5%, AC ≤ 2%, DC run 15 m one way, AC run 15 m, earthing = 2 pits minimum + 1 dedicated LA pit (matches the 3 pits in #276), 2-month billing cycle, network units floored (the Nov-2025 sheet shows 1572.48 → 1572).

## Branding
`reference/` contains Sri Vinayaka Solar's quotation, including GSTIN and bank account. SPEC says the owner's company is "Sri Vinayaka-*style*", so I did not copy that company's name, GSTIN or bank details into the product. The seed installer is a neutral **Demo Rooftop Solar** (slug `demo`). The owner enters real details in Settings → Company. Prices, items, HSN codes and terms wording from #276 *are* used as the starting price list.

## Privacy rules
- **Bank account numbers are never stored.** The quotation footer has bank account name, bank, branch, IFSC and UPI ID only. The settings API rejects `bank_account_number` / `account_number` / `aadhaar` / `pan` keys.
- No government IDs are collected. The subsidy flow is a placeholder table (`subsidy_case`) and a `subsidy_amount` nullable column.
- Phone numbers are masked in logs and list views; email addresses are masked in the email log view.
- Admins can delete a customer's personal data (anonymise) from the API (`POST /api/admin/requests/{id}/anonymise`).
- Uploaded images are re-encoded to JPEG (drops EXIF/GPS and hidden payloads); only JPEG/PNG/WEBP (and PDF for bills) up to 8 MB; files live in a private volume and are served only through short-lived HMAC-signed URLs.

## Architecture choices
- **Stack as SPEC §3**: FastAPI + SQLAlchemy 2 + Alembic + Pydantic, PostgreSQL 16, React + Vite (TypeScript), Docker Compose, Caddy (static files + reverse proxy + automatic HTTPS), WeasyPrint for HTML → PDF, diagrams as SVG generated in Python.
- **Tenant isolation**: every tenant table inherits `TenantMixin` (`installer_id` NOT NULL, indexed). A SQLAlchemy `do_orm_execute` hook adds `WHERE installer_id = :tenant` to every ORM SELECT/UPDATE/DELETE via `with_loader_criteria`; a `before_flush` hook stamps/validates `installer_id` on writes. A session without a tenant that touches a tenant table raises `TenantError`. Only platform-owner code uses an explicit bypass. Postgres row-level security was not added on top (would need a per-request `SET` and a non-owner DB role); the ORM filter plus tests is the "mandatory query filter" option from SPEC §2.
- **Tenant resolution**: public URLs are `/s/<installer-slug>/...`, and the API takes the slug in the path. Staff tokens carry the installer id. This works unchanged when `<installer>.<domain>` subdomains are added later (map host → slug in Caddy or the frontend).
- **Queue**: a database outbox (`email_log`) instead of Redis/RQ. The API sends right after the request (FastAPI background task) and the `worker` container retries failed sends every 15 s with exponential back-off (max 5 attempts, then `dead`). Fewer moving parts on a single VPS; swappable later.
- **Email providers**: `log` (default; nothing leaves the server, message stored and marked sent with id `log-N`), `resend`, `brevo` — choose with `EMAIL_PROVIDER` and the API key in `.env`.
- **Analysis runs are immutable**: each stores inputs, a full settings + catalogue snapshot and outputs. Updating or deleting one raises an error. Staff overrides create a new run.
- **Customer status links** use a stable HMAC of a per-request random salt (no token stored in clear, and links in earlier emails keep working).
- **Rate limiting** of the public form is in-process (one API process). If the API is scaled to several processes, move it to Redis or Caddy.
- **Sizing basis**: SPEC 6.1 says kW needed = monthly units ÷ units per kW per month. The yield used is a setting (`sizing_yield_basis`: realistic mid (default), realistic low, or CUF).
- **"Sold as" kW**: the nominal kW label is the DC kWp rounded down (5 × 615 W = 3.075 kWp → "3 kW", as in #276); per-kW price lines (structure, labour) use this nominal kW. Setting `nominal_kw_rounding`.
- **Savings** use bill-before minus bill-after on the slab tariff per billing cycle, minus network charges incl. GST, so generation above consumption earns nothing (TANGEDCO caps export credit). Low/high yield give the range; payback = estimated cost ÷ annual saving.
- **ACDB vs net meter phase**: price items can filter on supply phase (`phase`, e.g. net meter) or inverter phase (`inverter_phase`, e.g. ACDB). Quotation #276 had a 3-phase supply, a 1-phase inverter, a 1-phase ACDB and a 3-phase net meter.
- **Quotation editing**: only drafts are editable. A sent quotation is locked; *Revise* copies it to a new draft with the next number, and sending it supersedes the older one. Lines sent by the browser are re-totalled on the server; client totals are ignored.
- **Labour quantity**: #276 charged labour for 2 kW on a 3 kW system. The price rule uses the nominal kW (3), so the 3 kW example is ₹3,500 + other small cable-length differences above #276. Staff can edit any line.
- **Customer PDF language**: the quotation PDF body is English (as in #276); the disclaimer is shown in the customer's language plus English. Emails and the web quotation page follow the customer's language.
- **Bill reading model**: `claude-opus-5-5` (configurable via `BILL_READER_MODEL`), low effort, JSON-schema output, server-side refusal fallback (`fallbacks: "default"`). Monthly units = units in the bill ÷ billing-period months (default 2). Results are stored on the file as suggestions with `confirmed: false`; they never change inputs automatically. The bill image is sent to Anthropic's API, so this is off unless an API key is configured and can be turned off in Settings → Features.
- **Large plants**: when no single inverter fits the DC/AC range, the engine tries up to `max_inverters` (10) identical units and picks the fewest that fit. Above 112 kW it warns that LT net metering does not apply.
- **Project checklist** is copied from the institute's 12-step checklist poster; tools from the tools poster; net-metering documents from the TANGEDCO memo and its forms.
- **Local development** runs in Docker: this Windows machine's Application Control policy blocks native Python extension DLLs in a local virtualenv, so tests run in the API container.
- **Tamil text** was written by me; a native speaker should review the UI strings (`frontend/src/i18n.tsx`) and email templates (Settings → Templates) before launch. The same applies to the Home/About copy in `frontend/src/content.ts`.
- **Home/About copy** (`frontend/src/content.ts`) is generic marketing text shared by all installers: it makes no claims about years in business, installation counts or certifications. Per-installer editable page copy is a possible later feature. The "9 to 10 sq m per kW" roof guide matches the default `roof_recommended_m2_per_kw` (9.5).

## 2026-11-26 marketing pages
- The calculator and the Residential/Commercial pages show **no installation cost, price range or payback**, even though
  the reference designs did, because CLAUDE.md says customers never see a price automatically. The pages show
  savings and say the price comes from the engineer. To change this, the owner must decide; the engine already has `cost.range_low/high`.
- No testimonials, installation counts, MW totals or "years of experience" were added (the reference design had them);
  the owner should add only real, verifiable facts.
- Typical size bands on the solution pages (e.g. "2 – 3 kW for ~150–350 units") are generic guidance text, not calculation inputs.
- Images with other companies' logos (uniforms, vests, shirts) from the reference set were not used.

## 2026-11-26 knowledge base (RAG)
- Owner asked for OpenAI. Bill reading still uses Anthropic (unchanged); the knowledge base uses OpenAI only.
- RAG is advisory: it explains and cross-checks with citations; it does not feed numbers into analyses or quotations.
- Vectors stored as JSON in Postgres (no pgvector) - fine for a few thousand passages; revisit if the library grows large.
- PDF library: pypdfium2 (Apache/BSD) instead of PyMuPDF (AGPL) for a commercial deployment.
- Videos are not indexed (would need audio transcription).

## 2026-11-26 security review
Fixed:
- Staff login: max 8 failed attempts per account and 30 per IP in 15 minutes (429); unknown accounts take the same
  time as real ones (no email probing by timing); a successful login clears the account's counter.
- Turning off 2FA now needs a current 2FA code.
- Developer helpers (OTP code in API response, magic link in response, API docs/OpenAPI) only run on a local
  address; a real domain never gets them, even if ENVIRONMENT is left as development.
- ENVIRONMENT=production refuses to start with a default SECRET_KEY, default POSTGRES_PASSWORD or non-https
  PUBLIC_BASE_URL.
- Web server headers: Content-Security-Policy (own scripts only), HSTS, Permissions-Policy, COOP.
- Knowledge-base prompts treat document text as data (prompt-injection guard).
Checked and OK: tenant isolation (tests), role checks on every admin route, signed short-lived file links,
path-traversal guard in storage, upload type sniffing + image re-encoding, size limits, Argon2 passwords,
OTP attempt limits, HTML escaping in emails/PDF/SVG, no secrets in git history, .env ignored, API container runs
as non-root, database not exposed on a host port.
Known / accepted for now:
- Staff tokens live 12 h in browser storage and are not revoked on password change (disabled users are blocked).
- Magic sign-in links can be reused until they expire (30 min).
- Rate limits are in-process (one API container); use a shared store if the API is scaled out.
- OTP codes are written to the server log until a real SMS provider is configured.

## 2026-11-27 WhatsApp and roles
- Owner wants no running cost for WhatsApp: using official click-to-chat links (staff press Send), not the paid
  WhatsApp Cloud API and not unofficial WhatsApp Web bots (Hermes/Baileys-style bridges risk a number ban).
  n8n not used: it would add a server without removing any work. Automating later = Cloud API behind
  `services/whatsapp.py` (about Rs 0.12 + GST per utility message from Oct 2026).
- "normal" role = read-only without customer personal data; masking is done in the API, not just the UI.
