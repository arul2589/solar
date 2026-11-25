"""End-to-end smoke test against a running stack (through the web proxy).

    docker compose -p solar exec api python scripts/smoke.py --base http://web --phase 3

Flow: submit request -> acknowledgement email logged -> admin sees analysis ->
quotation PDF -> send -> customer accepts -> project pack / checklist.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import urllib.request
import uuid

from PIL import Image

PASSWORD = os.environ.get("SEED_ADMIN_PASSWORD", "ChangeMe-2026!")


class Client:
    def __init__(self, base):
        self.base = base.rstrip("/")
        self.token = None

    def req(self, method, path, body=None, headers=None, raw=False, auth=True):
        h = dict(headers or {})
        data = None
        if isinstance(body, (dict, list)):
            data = json.dumps(body).encode()
            h["Content-Type"] = "application/json"
        elif isinstance(body, bytes):
            data = body
        if auth and self.token:
            h["Authorization"] = f"Bearer {self.token}"
        r = urllib.request.Request(self.base + path, data=data, headers=h, method=method)
        try:
            with urllib.request.urlopen(r, timeout=60) as resp:
                content = resp.read()
                return content if raw else json.loads(content or b"null")
        except urllib.error.HTTPError as e:
            raise SystemExit(f"FAIL {method} {path}: {e.code} {e.read()[:500]!r}")


def multipart(fields: dict, files: list[tuple[str, str, bytes, str]]):
    boundary = uuid.uuid4().hex
    out = io.BytesIO()
    for k, v in fields.items():
        out.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    for name, fname, content, ctype in files:
        out.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"; filename=\"{fname}\"\r\n"
                  f"Content-Type: {ctype}\r\n\r\n".encode())
        out.write(content + b"\r\n")
    out.write(f"--{boundary}--\r\n".encode())
    return out.getvalue(), {"Content-Type": f"multipart/form-data; boundary={boundary}"}


def jpeg():
    b = io.BytesIO()
    Image.new("RGB", (64, 48), (90, 140, 200)).save(b, "JPEG")
    return b.getvalue()


def ok(msg):
    print(f"  OK  {msg}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8088")
    ap.add_argument("--slug", default="demo")
    ap.add_argument("--phase", type=int, default=1)
    ap.add_argument("--kw", type=float, default=None, help="monthly units for the test customer")
    a = ap.parse_args()
    c = Client(a.base)
    print(f"Smoke test against {a.base} (installer {a.slug}, phase {a.phase})")

    assert c.req("GET", "/api/health")["ok"]
    ok("health")

    data = {"name": "Smoke Test Customer", "phone": "9876500001", "email": "smoke@example.com", "language": "en",
            "address": "12 Gandhi Road, Coimbatore", "pincode": "641016", "district": "Coimbatore",
            "site_type": "home", "phase": 1, "sanction_load_kw": 5, "monthly_units": a.kw or 600, "roof_type": "rcc",
            "roof_area": 700, "roof_area_unit": "sqft", "direction": "south", "shade": "none",
            "goal": "reduce_bill", "consent": True}
    body, h = multipart({"data": json.dumps(data)},
                        [("eb_bill", "bill.jpg", jpeg(), "image/jpeg"), ("roof_photos", "roof.jpg", jpeg(), "image/jpeg")])
    sub = c.req("POST", f"/api/public/{a.slug}/requests", body, h, auth=False)
    ref, tok = sub["reference"], sub["status_token"]
    assert "grand_total" not in json.dumps(sub)
    ok(f"customer submitted request {ref} (no price returned)")

    st = c.req("GET", f"/api/public/{a.slug}/requests/{ref}?t={tok}", auth=False)
    ok(f"status page: {st['status']}")

    login = c.req("POST", "/api/auth/login", {"installer": a.slug, "email": "admin@example.com", "password": PASSWORD})
    c.token = login["token"]
    ok("staff login")

    emails = c.req("GET", "/api/admin/emails")
    ack = [e for e in emails if e["template"] == "acknowledgement" and ref in e["subject"]]
    assert ack and ack[0]["status"] == "sent", ack
    ok(f"acknowledgement email logged: status={ack[0]['status']} provider_id={ack[0]['provider_id']}")

    items = c.req("GET", "/api/admin/requests")["items"]
    rid = next(i["id"] for i in items if i["reference"] == ref)
    d = c.req("GET", f"/api/admin/requests/{rid}")
    o = d["analysis"]["outputs"]
    ok(f"admin sees analysis: {o['sizing']['dc_kwp']} kWp, {o['sizing']['panel_count']} panels, "
       f"inverter {o['inverter']['inverter']['model'] if o['inverter']['inverter'] else '-'}, "
       f"warnings {[w['code'] for w in o['warnings']]}")
    if a.phase < 2:
        print("PHASE 1 SMOKE PASSED")
        return

    for k in ("sld", "roof", "schedule"):
        svg = c.req("GET", f"/api/admin/analysis/{d['analysis']['id']}/diagram/{k}")["svg"]
        assert svg.startswith("<svg")
    ok("diagrams: single-line, roof layout, cable schedule")

    q = c.req("POST", f"/api/admin/requests/{rid}/quotations")
    ok(f"quotation #{q['number']} drafted: total {q['grand_total']}")
    pdf = c.req("GET", f"/api/admin/quotations/{q['id']}/pdf", raw=True)
    assert pdf[:5] == b"%PDF-", pdf[:20]
    ok(f"quotation PDF generated ({len(pdf)} bytes)")
    sent = c.req("POST", f"/api/admin/quotations/{q['id']}/send", {})
    ok(f"quotation sent; email {sent['email_status']}")
    qtoken = sent["dev_quote_url"].split("/q/")[1]

    view = c.req("GET", f"/api/public/{a.slug}/quotations/{qtoken}", auth=False)
    assert view["grand_total"] == q["grand_total"]
    ok(f"customer views quotation #{view['number']}")
    cpdf = c.req("GET", f"/api/public/{a.slug}/quotations/{qtoken}/pdf", auth=False, raw=True)
    assert cpdf[:5] == b"%PDF-"
    ok("customer downloads PDF")
    acc = c.req("POST", f"/api/public/{a.slug}/quotations/{qtoken}/accept", {}, auth=False)
    assert acc["status"] == "accepted"
    ok("customer accepted quotation")
    st = c.req("GET", f"/api/public/{a.slug}/requests/{ref}?t={tok}", auth=False)
    assert st["status"] == "accepted", st
    ok("request moved to Accepted; staff notified")
    if a.phase < 3:
        print("PHASE 2 SMOKE PASSED")
        return

    projects = c.req("GET", "/api/admin/projects")
    p = next(p for p in projects if p["request_id"] == rid)
    pd = c.req("GET", f"/api/admin/projects/{p['id']}")
    assert len(pd["checklist"]) == 12 and pd["pack"]["bom"]
    ok(f"project pack: {len(pd['pack']['bom'])} BOM lines, {len(pd['checklist'])} checklist steps")
    c.req("PATCH", f"/api/admin/projects/{p['id']}/checklist/{pd['checklist'][0]['id']}", {"done": True})
    c.req("POST", f"/api/admin/projects/{p['id']}/readings", {"kind": "earth_resistance", "label": "Pit 1", "value": 2.1})
    ok("technician ticked step 1 and recorded earth resistance")
    pdf = c.req("GET", f"/api/admin/projects/{p['id']}/pack.pdf", raw=True)
    assert pdf[:5] == b"%PDF-"
    ok(f"project pack PDF ({len(pdf)} bytes)")
    print("PHASE 3 SMOKE PASSED")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as exc:
        print("SMOKE FAILED", exc)
        sys.exit(1)
