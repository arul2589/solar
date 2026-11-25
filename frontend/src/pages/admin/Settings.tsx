import { useEffect, useState } from "react";
import { api } from "../../api";
import { useRole } from "./AdminLayout";

const COMPANY_FIELDS: [string, string][] = [
  ["name", "Company name"], ["contact_person", "Contact person"], ["address", "Address"], ["phone", "Phone"],
  ["email", "Email"], ["gstin", "GSTIN"], ["website", "Website"], ["signatory", "Signatory line"],
  ["bank_account_name", "Bank account name"], ["bank_name", "Bank name"], ["bank_branch", "Branch"],
  ["bank_ifsc", "IFSC"], ["upi_id", "UPI ID"], ["services_text", "Services text (quotation footer)"],
];

const CALC_HELP: Record<string, string> = {
  cuf_tnerc: "TNERC CUF used for network charges (0.21 = 21%)",
  realistic_yield_low: "Realistic yield low, kWh/kW/day (customer savings) - PLACEHOLDER",
  realistic_yield_high: "Realistic yield high, kWh/kW/day - PLACEHOLDER",
  sizing_yield_basis: "realistic_mid | realistic_low | cuf",
  nominal_kw_rounding: "floor | round ('sold as' kW)",
  network_pct_domestic_upto_10kw: "Network charge % allowed, domestic ≤10 kW (0.20)",
  network_pct_other: "Network charge % for others - PLACEHOLDER",
  network_gst_pct: "GST on network charges %",
  commercial_flat_rate: "Flat tariff ₹/unit when no slabs - PLACEHOLDER",
  single_phase_max_kw: "Single-phase limit kW - PLACEHOLDER",
};

export default function Settings() {
  const role = useRole();
  const isAdmin = role === "admin";
  const [s, setS] = useState<any>(null);
  const [tab, setTab] = useState("placeholders");
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [tplText, setTplText] = useState("");
  const [logo, setLogo] = useState<File | null>(null);

  const load = () => api("/api/admin/settings").then((r) => { setS(r); setTplText(JSON.stringify(r.templates || {}, null, 2)); }).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);

  const save = async (section: string, value: any) => {
    setErr(""); setMsg("");
    try { await api(`/api/admin/settings/${section}`, { method: "PUT", json: value }); setMsg(`Saved ${section}.`); load(); }
    catch (e: any) { setErr(e.message); }
  };
  const confirm = async (key: string, confirmed: boolean) => {
    const r = await api("/api/admin/settings/placeholders", { method: "POST", json: { key, confirmed } });
    setS({ ...s, placeholders: r.placeholders });
  };
  const uploadLogo = async () => {
    if (!logo) return;
    const fd = new FormData(); fd.append("file", logo);
    try { await api("/api/admin/settings/logo", { method: "POST", body: fd }); setMsg("Logo uploaded."); load(); }
    catch (e: any) { setErr(e.message); }
  };

  if (!s) return <p>{err || "Loading..."}</p>;
  const open = s.placeholders.filter((p: any) => !p.confirmed);
  const upd = (section: string, k: string, v: any) => setS({ ...s, [section]: { ...s[section], [k]: v } });

  return (
    <div>
      <h1>Settings</h1>
      {open.length > 0 && <div className="note"><strong>{open.length} placeholder value(s) - owner must confirm.</strong> Calculations use these defaults until changed. See the Placeholders tab.</div>}
      {err && <div className="err">{err}</div>}
      {msg && <div className="ok">{msg}</div>}
      <div className="tabs">
        {["placeholders", "company", "calculation", "tariff", "quotation", "email", "templates", "features"].map((t) => (
          <button key={t} className={tab === t ? "active" : ""} onClick={() => setTab(t)}>{t[0].toUpperCase() + t.slice(1)}</button>
        ))}
      </div>

      {tab === "placeholders" && (
        <div className="card">
          <h2>Placeholder values - owner must confirm</h2>
          <p className="muted small">These come from SPEC items marked VERIFY or from seeded examples. Edit the value in its tab, then mark it confirmed.</p>
          <table><tbody>
            {s.placeholders.map((p: any) => (
              <tr key={p.key}>
                <td>{p.confirmed ? <span className="pill green">confirmed</span> : <span className="placeholder-tag">placeholder - owner must confirm</span>}</td>
                <td><code className="small">{p.key}</code><div>{p.message}</div></td>
                <td>{isAdmin && <button className="small secondary" onClick={() => confirm(p.key, !p.confirmed)}>{p.confirmed ? "Reopen" : "Mark confirmed"}</button>}</td>
              </tr>
            ))}
          </tbody></table>
        </div>
      )}

      {tab === "company" && (
        <div className="card">
          <h2>Company & branding {!s.placeholders.find((p: any) => p.key === "company.branding")?.confirmed && <span className="placeholder-tag">placeholder - owner must confirm</span>}</h2>
          <p className="muted small">Bank account numbers and government IDs are not stored. The quotation footer shows bank name, IFSC and UPI only.</p>
          <div className="grid2">
            {COMPANY_FIELDS.map(([k, l]) => (
              <div key={k}><label>{l}</label>
                {k === "services_text" || k === "address" ? <textarea value={s.company[k] || ""} onChange={(e) => upd("company", k, e.target.value)} disabled={!isAdmin} />
                  : <input value={s.company[k] || ""} onChange={(e) => upd("company", k, e.target.value)} disabled={!isAdmin} />}
              </div>
            ))}
          </div>
          {isAdmin && <button style={{ marginTop: 12 }} onClick={() => save("company", s.company)}>Save company</button>}
          {isAdmin && (
            <div className="row" style={{ marginTop: 16 }}>
              <div><label>Logo (JPEG/PNG)</label><input type="file" accept="image/*" onChange={(e) => setLogo(e.target.files?.[0] || null)} /></div>
              <button style={{ flex: "0 0 auto" }} onClick={uploadLogo} disabled={!logo}>Upload logo</button>
            </div>
          )}
        </div>
      )}

      {tab === "calculation" && (
        <div className="card">
          <h2>Calculation settings</h2>
          <p className="muted small">Every rate, yield and design assumption used by the engine. Lists and tables are JSON.</p>
          <div className="grid3">
            {Object.entries(s.calc).map(([k, v]) => (
              <div key={k}>
                <label title={CALC_HELP[k] || k}>{k.replace(/_/g, " ")} {CALC_HELP[k]?.includes("PLACEHOLDER") && <span className="placeholder-tag">placeholder</span>}</label>
                <input disabled={!isAdmin} value={typeof v === "object" ? JSON.stringify(v) : String(v)}
                  onChange={(e) => {
                    let val: any = e.target.value;
                    if (typeof v === "number") val = val === "" ? "" : Number(val);
                    else if (typeof v === "boolean") val = val === "true";
                    else if (typeof v === "object") { try { val = JSON.parse(val); } catch { val = e.target.value; } }
                    upd("calc", k, val);
                  }} />
                {CALC_HELP[k] && <div className="muted small">{CALC_HELP[k]}</div>}
              </div>
            ))}
          </div>
          {isAdmin && <button style={{ marginTop: 12 }} onClick={() => save("calc", s.calc)}>Save calculation settings</button>}
          <p className="muted small">Network-charge rates by effective date are edited under Price list & catalogue → Network rates.</p>
        </div>
      )}

      {tab === "tariff" && (
        <div className="card">
          <h2>Tariff slabs (per 2-month bill) <span className="placeholder-tag">placeholder - owner must confirm</span></h2>
          {Object.entries(s.tariff_slabs).map(([cat, slabs]: any) => (
            <div key={cat} style={{ marginBottom: 14 }}>
              <h3>{cat}</h3>
              <table><thead><tr><th>Up to units (blank = above)</th><th>₹ / unit</th><th></th></tr></thead><tbody>
                {slabs.map((row: any, i: number) => (
                  <tr key={i}>
                    <td><input value={row[0] ?? ""} disabled={!isAdmin} onChange={(e) => { const n = [...slabs]; n[i] = [e.target.value === "" ? null : Number(e.target.value), row[1]]; setS({ ...s, tariff_slabs: { ...s.tariff_slabs, [cat]: n } }); }} /></td>
                    <td><input value={row[1]} disabled={!isAdmin} onChange={(e) => { const n = [...slabs]; n[i] = [row[0], e.target.value]; setS({ ...s, tariff_slabs: { ...s.tariff_slabs, [cat]: n } }); }} /></td>
                    <td>{isAdmin && <button className="ghost" onClick={() => { const n = slabs.filter((_: any, j: number) => j !== i); setS({ ...s, tariff_slabs: { ...s.tariff_slabs, [cat]: n } }); }}>✕</button>}</td>
                  </tr>
                ))}
              </tbody></table>
              {isAdmin && <button className="small secondary" style={{ marginTop: 6 }} onClick={() => setS({ ...s, tariff_slabs: { ...s.tariff_slabs, [cat]: [...slabs, [null, "0"]] } })}>Add slab</button>}
              {slabs.length === 0 && <p className="muted small">No slabs: the flat commercial rate setting is used.</p>}
            </div>
          ))}
          {isAdmin && <button onClick={() => save("tariff_slabs", s.tariff_slabs)}>Save tariff slabs</button>}
        </div>
      )}

      {tab === "quotation" && (
        <div className="card">
          <h2>Quotation text</h2>
          <label>Validity (days)</label>
          <input value={s.quotation.validity_days} disabled={!isAdmin} onChange={(e) => upd("quotation", "validity_days", Number(e.target.value))} />
          {["terms_text", "scope_text", "warranty_text", "closing_text", "disclaimer_en", "disclaimer_ta"].map((k) => (
            <div key={k}><label>{k.replace(/_/g, " ")}</label><textarea rows={6} value={s.quotation[k] || ""} disabled={!isAdmin} onChange={(e) => upd("quotation", k, e.target.value)} /></div>
          ))}
          {isAdmin && <button style={{ marginTop: 12 }} onClick={() => save("quotation", s.quotation)}>Save quotation text</button>}
        </div>
      )}

      {tab === "email" && (
        <div className="card">
          <h2>Email sender</h2>
          <p className="muted small">Provider (Resend / Brevo) and API key are set on the server (.env). Switch From to the company domain after adding SPF/DKIM records.</p>
          {[["from_address", "From address"], ["from_name", "From name"], ["reply_to", "Reply-To"], ["staff_notify", "Staff notification address"]].map(([k, l]) => (
            <div key={k}><label>{l}</label><input value={s.email[k] || ""} disabled={!isAdmin} onChange={(e) => upd("email", k, e.target.value)} /></div>
          ))}
          {isAdmin && <button style={{ marginTop: 12 }} onClick={() => save("email", s.email)}>Save email settings</button>}
        </div>
      )}

      {tab === "templates" && isAdmin && (
        <div className="card">
          <h2>Email templates (English and Tamil)</h2>
          <p className="muted small">Placeholders like {"{reference}"}, {"{customer_name}"}, {"{status_url}"}, {"{quote_url}"} are filled in automatically. Never include prices in the acknowledgement.</p>
          <textarea style={{ minHeight: 420, fontFamily: "monospace", fontSize: 13 }} value={tplText} onChange={(e) => setTplText(e.target.value)} />
          <button style={{ marginTop: 10 }} onClick={() => { try { save("templates", JSON.parse(tplText)); } catch { setErr("Templates are not valid JSON"); } }}>Save templates</button>
        </div>
      )}

      {tab === "features" && (
        <div className="card">
          <h2>Features</h2>
          <label className="inline"><input type="checkbox" disabled={!isAdmin} checked={!!s.features.require_phone_otp} onChange={(e) => upd("features", "require_phone_otp", e.target.checked)} />
            Require phone OTP on the request form <span className="placeholder-tag">needs an SMS provider</span></label>
          <label className="inline"><input type="checkbox" disabled={!isAdmin} checked={!!s.features.bill_reading_enabled} onChange={(e) => upd("features", "bill_reading_enabled", e.target.checked)} />
            Bill-photo reading with a vision model (staff confirm the values)</label>
          {isAdmin && <button style={{ marginTop: 12 }} onClick={() => save("features", s.features)}>Save features</button>}
        </div>
      )}
    </div>
  );
}
