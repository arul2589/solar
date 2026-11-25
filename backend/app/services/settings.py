"""Per-installer settings with defaults, and the list of placeholder values the owner
must confirm (items marked VERIFY in SPEC.md)."""
from __future__ import annotations

import copy
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from solarcalc import CalcSettings, TariffSlab

from ..models import Setting

DEFAULT_TERMS = """1. Validity: {validity_days} days from the date of this offer.
2. Payment terms: 70% advance during material dispatch, 20% after installation and commissioning, 10% after net metering.
3. Delivery: material delivery within 1 to 3 days from the date of PO.
4. Transportation cost extra at actual where not quoted.
5. Prices are subject to variation of component prices.
6. Mode of dispatch: by road.
7. GST as shown per line (5% / 18%).
8. Online figures are approximate until a site visit."""

DEFAULT_SCOPE = """SCOPE OF INSTALLER:
1. Design, engineering, supply, installation, testing and commissioning of the solar rooftop power plant.
2. Earthing system.
3. Lightning arrester.
4. AC cables from inverter to ACDB and from ACDB to LT panel.
5. Training to customer for maintaining the solar system.

SCOPE OF CUSTOMER:
1. Civil works, inverter location, internet connection for monitoring.
2. Ladder from ground to roof, provision for solar output injection at LT panel.
3. CEIG and TANGEDCO fees (if required, additional load or miscellaneous).
4. Water and power during installation and module cleaning.
5. Roof stability certificate."""

DEFAULT_WARRANTY = """Solar panels: 12 years product warranty, 25-30 years performance warranty (as per manufacturer).
Inverter: 10 years warranty (as per manufacturer).
Workmanship: 1 year from commissioning."""

DISCLAIMER_EN = ("These figures are approximate, based on the details you gave online. Final system size, "
                 "price and savings are confirmed only after a site visit.")
DISCLAIMER_TA = ("இந்த மதிப்பீடுகள் நீங்கள் ஆன்லைனில் கொடுத்த விவரங்களின் அடிப்படையில் தோராயமானவை. "
                 "இறுதி அளவு, விலை மற்றும் சேமிப்பு தள ஆய்வுக்குப் பிறகே உறுதி செய்யப்படும்.")

EMAIL_TEMPLATES = {
    "acknowledgement": {
        "en": {
            "subject": "We received your solar request {reference}",
            "body": ("Dear {customer_name},\n\nThank you for contacting {company_name}. We have received your "
                     "rooftop solar request.\n\nReference number: {reference}\n\nWhat happens next:\n"
                     "1. Our engineer reviews your details and electricity bill.\n"
                     "2. We prepare a quotation and send it to you after review.\n"
                     "3. We arrange a site visit to confirm roof space and wiring.\n\n"
                     "You can check the status any time here: {status_url}\n\n"
                     "Regards,\n{company_name}\n{company_phone}"),
        },
        "ta": {
            "subject": "உங்கள் சோலார் கோரிக்கை {reference} பெறப்பட்டது",
            "body": ("அன்புள்ள {customer_name},\n\n{company_name} நிறுவனத்தைத் தொடர்பு கொண்டதற்கு நன்றி. உங்கள் "
                     "கூரை சோலார் கோரிக்கையைப் பெற்றுள்ளோம்.\n\nகுறிப்பு எண்: {reference}\n\nஅடுத்து என்ன நடக்கும்:\n"
                     "1. எங்கள் பொறியாளர் உங்கள் விவரங்களையும் மின் கட்டணத்தையும் பரிசீலிப்பார்.\n"
                     "2. பரிசீலனைக்குப் பிறகு விலைப்புள்ளியைத் தயாரித்து அனுப்புவோம்.\n"
                     "3. கூரை இடம் மற்றும் வயரிங்கை உறுதிசெய்ய தள ஆய்வு ஏற்பாடு செய்வோம்.\n\n"
                     "நிலையை இங்கே பார்க்கலாம்: {status_url}\n\nநன்றி,\n{company_name}\n{company_phone}"),
        },
    },
    "quotation_ready": {
        "en": {
            "subject": "Your solar quotation #{quote_number} from {company_name}",
            "body": ("Dear {customer_name},\n\nYour quotation #{quote_number} for a {system_summary} rooftop solar "
                     "system is ready.\n\nView and download: {quote_url}\nValid until: {valid_until}\n\n"
                     "On that page you can accept the quotation or ask us a question.\n\n"
                     "{disclaimer}\n\nRegards,\n{company_name}\n{company_phone}"),
        },
        "ta": {
            "subject": "{company_name} வழங்கும் உங்கள் சோலார் விலைப்புள்ளி #{quote_number}",
            "body": ("அன்புள்ள {customer_name},\n\n{system_summary} கூரை சோலார் அமைப்புக்கான உங்கள் விலைப்புள்ளி "
                     "#{quote_number} தயாராக உள்ளது.\n\nபார்க்க மற்றும் பதிவிறக்க: {quote_url}\n"
                     "செல்லுபடியாகும் நாள்: {valid_until}\n\nஅந்தப் பக்கத்தில் விலைப்புள்ளியை ஏற்கலாம் அல்லது "
                     "கேள்வி கேட்கலாம்.\n\n{disclaimer}\n\nநன்றி,\n{company_name}\n{company_phone}"),
        },
    },
    "status_update": {
        "en": {
            "subject": "Update on your solar request {reference}",
            "body": ("Dear {customer_name},\n\n{status_message}\n\nTrack your request: {status_url}\n\n"
                     "Regards,\n{company_name}"),
        },
        "ta": {
            "subject": "உங்கள் சோலார் கோரிக்கை {reference} பற்றிய தகவல்",
            "body": ("அன்புள்ள {customer_name},\n\n{status_message}\n\nஉங்கள் கோரிக்கையைப் பார்க்க: {status_url}\n\n"
                     "நன்றி,\n{company_name}"),
        },
    },
    "magic_link": {
        "en": {"subject": "Your sign-in link for {company_name}",
               "body": "Use this link to see your solar requests (valid 30 minutes):\n{login_url}"},
        "ta": {"subject": "{company_name} உள்நுழைவு இணைப்பு",
               "body": "உங்கள் சோலார் கோரிக்கைகளைப் பார்க்க இந்த இணைப்பைப் பயன்படுத்தவும் (30 நிமிடம் செல்லும்):\n{login_url}"},
    },
    "staff_notification": {
        "en": {"subject": "[{company_name}] {event} - {reference}",
               "body": "{event}\nRequest: {reference}\nCustomer: {customer_name}\n{message}\n\nOpen: {admin_url}"},
        "ta": {"subject": "[{company_name}] {event} - {reference}",
               "body": "{event}\nகோரிக்கை: {reference}\nவாடிக்கையாளர்: {customer_name}\n{message}\n\nதிற: {admin_url}"},
    },
}

STATUS_MESSAGES = {
    "site_visit": {"en": "A site visit has been scheduled{when}.", "ta": "தள ஆய்வு திட்டமிடப்பட்டுள்ளது{when}."},
    "installation": {"en": "Installation of your solar system has started.", "ta": "உங்கள் சோலார் அமைப்பின் நிறுவல் தொடங்கியது."},
    "completed": {"en": "Your solar system is installed and commissioned. Thank you!",
                  "ta": "உங்கள் சோலார் அமைப்பு நிறுவப்பட்டு இயக்கப்பட்டது. நன்றி!"},
}

# Telescopic slabs per 2-month cycle. Placeholder values (VERIFY with owner / latest TNERC order).
DEFAULT_SLABS = {
    "domestic": [[100, "0"], [200, "2.35"], [400, "4.70"], [500, "6.30"], [600, "8.40"], [800, "9.45"],
                 [1000, "10.50"], [None, "11.55"]],
    "commercial": [],     # empty -> flat rate setting
    "industrial": [],
}

DEFAULTS: dict = {
    "company": {
        # Neutral placeholders. Real branding, GSTIN and bank details are entered by the owner in Settings.
        "name": "Demo Rooftop Solar", "contact_person": "",
        "address": "Coimbatore, Tamil Nadu", "phone": "+91 00000 00000", "email": "", "gstin": "",
        "website": "", "logo_file_id": None, "signatory": "Authorised Signatory",
        # Bank details for the quotation footer. Account NUMBER is deliberately not stored (CLAUDE.md).
        "bank_account_name": "", "bank_name": "", "bank_branch": "", "bank_ifsc": "", "upi_id": "",
        "services_text": ("Residential | Commercial | Industrial rooftop solar | On-grid, off-grid and hybrid systems | "
                          "Solar water heaters | Solar water pumps"),
    },
    "email": {"from_address": "onboarding@resend.dev", "from_name": "Demo Rooftop Solar",
              "reply_to": "arulmurugan08@outlook.com", "staff_notify": "arulmurugan08@outlook.com"},
    "calc": CalcSettings().to_dict(),
    "tariff_slabs": DEFAULT_SLABS,
    "quotation": {"validity_days": 7, "terms_text": DEFAULT_TERMS, "scope_text": DEFAULT_SCOPE,
                  "warranty_text": DEFAULT_WARRANTY, "disclaimer_en": DISCLAIMER_EN, "disclaimer_ta": DISCLAIMER_TA,
                  "closing_text": "We hope you find our offer to be in line with your requirement."},
    "templates": EMAIL_TEMPLATES,
    "project": {},   # filled from services.projects.PROJECT_DEFAULTS at load time
    "features": {"require_phone_otp": False, "bill_reading_enabled": True, "languages": ["en", "ta"]},
}

# Values the owner must confirm (SPEC VERIFY items + seeded guesses). key -> explanation.
PLACEHOLDERS = {
    "calc.realistic_yield": "Realistic yield 3.8-4.4 kWh/kW/day for customer savings is a placeholder (SPEC 6.1 VERIFY). Confirm with real plant data.",
    "network_rate.latest": "Network-charge rate table (1.27/1.48/1.53/1.59) is from the printed sheet. Sample sheets used 1.56 and 1.6 (SPEC 6.6 VERIFY). Check the latest TNERC order.",
    "calc.network_pct_other": "Network-charge percentage for non-domestic or >10 kW (default 100%) is a placeholder.",
    "tariff_slabs.domestic": "Domestic tariff slabs for savings are placeholders (SPEC 6.7 VERIFY).",
    "calc.commercial_flat_rate": "Commercial/industrial flat tariff Rs 9.00/unit for savings is a placeholder.",
    "price_items.gst": "GST rates per item copied from sample quotation #276 (5% panels/inverter, 18% BOS, 0% services). Confirm (SPEC 12 Q3).",
    "price_items.prices": "Price list seeded from sample quotation #276 (June 2026). Confirm current prices.",
    "catalogue.panel_specs": "615 Wp panel electrical/mechanical values are typical TOPCon figures, not from a datasheet. Enter the real datasheet.",
    "catalogue.inverter_specs": "UTL 3.3 kW and 10 kW three-phase inverter specs are typical values; GT-5K is from the nameplate photo. Confirm.",
    "company.branding": "Company name, address, GSTIN, logo, bank details, terms and warranty wording are placeholders (SPEC 12 Q5).",
    "calc.single_phase_max_kw": "Single-phase limit of 5 kW before preferring a 3-phase inverter is a placeholder.",
    "calc.cost_range_band_pct": "Rough cost range shown to staff is +/-10% of the price-list estimate.",
    "email.from_address": "Email From address uses the provider sandbox until the company domain has SPF/DKIM (SPEC 8).",
    "features.require_phone_otp": "Phone OTP verification is off until an SMS provider is configured.",
}


def _deep_merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict) and k not in ("tariff_slabs",):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_all(db: Session) -> dict:
    stored = {row.key: row.value for row in db.scalars(select(Setting))}
    merged = {}
    for key, default in DEFAULTS.items():
        val = stored.get(key)
        if key == "tariff_slabs":
            merged[key] = val if val is not None else copy.deepcopy(default)
        else:
            merged[key] = _deep_merge(default, val or {})
    if not merged["project"]:
        from .projects import PROJECT_DEFAULTS
        merged["project"] = copy.deepcopy(PROJECT_DEFAULTS)
    merged["confirmed_placeholders"] = stored.get("confirmed_placeholders", {}).get("keys", [])
    return merged


def get_section(db: Session, key: str) -> dict:
    return load_all(db)[key]


def save_section(db: Session, key: str, value) -> None:
    row = db.scalar(select(Setting).where(Setting.key == key))
    if row is None:
        db.add(Setting(key=key, value=value))
    else:
        row.value = copy.deepcopy(value)
    db.flush()


def placeholder_status(db: Session) -> list[dict]:
    confirmed = set(load_all(db)["confirmed_placeholders"])
    return [{"key": k, "message": v, "confirmed": k in confirmed} for k, v in PLACEHOLDERS.items()]


def confirm_placeholder(db: Session, key: str, confirmed: bool = True) -> None:
    current = set(load_all(db)["confirmed_placeholders"])
    if confirmed:
        current.add(key)
    else:
        current.discard(key)
    save_section(db, "confirmed_placeholders", {"keys": sorted(current)})


def calc_settings(db: Session) -> CalcSettings:
    return CalcSettings.from_dict(get_section(db, "calc"))


def tariff_slabs(db: Session, category: str) -> list[TariffSlab]:
    slabs = get_section(db, "tariff_slabs").get(category) or []
    return [TariffSlab(None if u is None else int(u), Decimal(str(r))) for u, r in slabs]
