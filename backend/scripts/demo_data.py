"""Create sample demo data through the normal app API (public form + staff actions).

    docker compose -p solar run --rm --no-deps -v "$PWD/backend:/app" api python scripts/demo_data.py --base http://web

Five requests at different pipeline stages: new, site visit scheduled, quotation draft,
quotation sent, and one accepted project with a technician and some progress.
All names, phones and emails are made up (example.com).
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone

from smoke import PASSWORD, Client, jpeg, multipart

BASE_FIELDS = {"roof_type": "rcc", "roof_area_unit": "sqft", "direction": "south", "shade": "none",
               "goal": "reduce_bill", "consent": True, "language": "en"}

CUSTOMERS = [
    dict(key="new", name="Lakshmi Narayanan", phone="9800000101", email="lakshmi.demo@example.com",
         address="14 Anna Nagar 2nd Street", pincode="641012", district="Coimbatore", site_type="home",
         phase=1, sanction_load_kw=4, monthly_units=320, roof_area=450),
    dict(key="visit", name="முருகன் செல்வம் (Murugan Selvam)", phone="9800000102", email="murugan.demo@example.com",
         language="ta", address="7 Bypass Road, K.K. Nagar", pincode="625020", district="Madurai", site_type="home",
         phase=1, sanction_load_kw=5, monthly_bill=4500, roof_area=600, shade="some"),
    dict(key="draft", name="Sri Ganesh Textiles Showroom", phone="9800000103", email="ganesh.demo@example.com",
         address="22 Kumaran Road", pincode="641601", district="Tiruppur", site_type="commercial",
         phase=3, sanction_load_kw=20, monthly_units=1500, roof_area=1800),
    dict(key="sent", name="Sathish Kumar", phone="9800000104", email="sathish.demo@example.com",
         address="3 Five Roads, Fairlands", pincode="636016", district="Salem", site_type="home",
         phase=3, sanction_load_kw=8, monthly_units=700, roof_area=900),
    dict(key="project", name="Kaveri Rice Mill", phone="9800000105", email="kaveri.demo@example.com",
         address="SIDCO Industrial Estate, Plot 9", pincode="638052", district="Erode", site_type="industry",
         phase=3, sanction_load_kw=60, monthly_units=4200, roof_area=4500, direction="south_east"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://web")
    ap.add_argument("--slug", default="demo")
    a = ap.parse_args()
    c = Client(a.base)
    c.token = c.req("POST", "/api/auth/login", {"installer": a.slug, "email": "admin@example.com", "password": PASSWORD})["token"]
    users = {u["role"]: u["id"] for u in c.req("GET", "/api/admin/users")}

    rid = {}
    for cust in CUSTOMERS:
        data = BASE_FIELDS | {k: v for k, v in cust.items() if k != "key"}
        body, h = multipart({"data": json.dumps(data)},
                            [("eb_bill", "bill.jpg", jpeg(), "image/jpeg"), ("roof_photos", "roof.jpg", jpeg(), "image/jpeg")])
        sub = c.req("POST", f"/api/public/{a.slug}/requests", body, h, auth=False)
        items = c.req("GET", "/api/admin/requests")["items"]
        rid[cust["key"]] = next(i["id"] for i in items if i["reference"] == sub["reference"])
        print(f"  request {sub['reference']}  {cust['name']}  ({cust['key']})")

    c.req("POST", f"/api/admin/requests/{rid['new']}/notes", {"text": "Customer prefers a call after 6 pm."})

    visit = (datetime.now(timezone.utc) + timedelta(days=3)).replace(hour=5, minute=0, second=0, microsecond=0)
    c.req("PATCH", f"/api/admin/requests/{rid['visit']}",
          {"owner_user_id": users["sales"], "engineer_user_id": users["engineer"], "site_visit_at": visit.isoformat()})
    print("  site visit scheduled")

    q = c.req("POST", f"/api/admin/requests/{rid['draft']}/quotations")
    print(f"  quotation #{q['number']} drafted (not sent)")

    q = c.req("POST", f"/api/admin/requests/{rid['sent']}/quotations")
    c.req("POST", f"/api/admin/quotations/{q['id']}/send", {})
    print(f"  quotation #{q['number']} sent")

    q = c.req("POST", f"/api/admin/requests/{rid['project']}/quotations")
    sent = c.req("POST", f"/api/admin/quotations/{q['id']}/send", {})
    token = sent["dev_quote_url"].split("/q/")[1]
    c.req("POST", f"/api/public/{a.slug}/quotations/{token}/accept", {}, auth=False)
    print(f"  quotation #{q['number']} sent and accepted by the customer")

    proj = next(p for p in c.req("GET", "/api/admin/projects") if p["request_id"] == rid["project"])
    c.req("PATCH", f"/api/admin/projects/{proj['id']}", {"technician_user_id": users["technician"]})
    d = c.req("GET", f"/api/admin/projects/{proj['id']}")
    for item in d["checklist"][:2]:
        c.req("PATCH", f"/api/admin/projects/{proj['id']}/checklist/{item['id']}", {"done": True})
    for label, val in (("Pit 1", 1.8), ("Pit 2", 2.3)):
        c.req("POST", f"/api/admin/projects/{proj['id']}/readings", {"kind": "earth_resistance", "label": label, "value": val})
    print(f"  project {proj['reference']}: technician assigned, 2 steps done, 2 earth readings")


if __name__ == "__main__":
    main()
