import { FormEvent, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../../api";
import { Key, useI18n } from "../../i18n";
import { useInstaller } from "./PublicLayout";

type Opt = { v: string | number; k: Key };

function Seg({ name, value, opts, onChange }: { name: string; value: any; opts: Opt[]; onChange: (v: any) => void }) {
  const { t } = useI18n();
  return (
    <div className="seg" role="radiogroup">
      {opts.map((o) => (
        <label key={String(o.v)} className={value === o.v ? "on" : ""}>
          <input type="radio" name={name} checked={value === o.v} onChange={() => onChange(o.v)} />
          {t(o.k)}
        </label>
      ))}
    </div>
  );
}

export default function RequestForm() {
  const { slug } = useParams();
  const { t, lang } = useI18n();
  const info = useInstaller()!;
  const [f, setF] = useState<any>({
    name: "", phone: "", email: "", address: "", pincode: "", district: "", site_type: "home",
    eb_consumer_no: "", tariff: "", phase: 1, sanction_load_kw: "", monthly_units: "", monthly_bill: "",
    roof_type: "rcc", roof_area: "", roof_area_unit: "sqft", direction: "south", shade: "none", floors: "",
    goal: "reduce_bill", backup_load_w: "", budget_range: "", consent: false, website: "",
  });
  const [ebBill, setEbBill] = useState<File | null>(null);
  const [roofPhotos, setRoofPhotos] = useState<File[]>([]);
  const [otpSent, setOtpSent] = useState(false);
  const [otp, setOtp] = useState("");
  const [devCode, setDevCode] = useState("");
  const [phoneToken, setPhoneToken] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [done, setDone] = useState<any>(null);

  const set = (k: string) => (e: any) => setF({ ...f, [k]: e?.target ? (e.target.type === "checkbox" ? e.target.checked : e.target.value) : e });

  async function sendOtp() {
    setErr("");
    try {
      const r = await api(`/api/public/${slug}/otp/request`, { method: "POST", json: { phone: f.phone } });
      setOtpSent(true);
      if (r.dev_code) setDevCode(r.dev_code);
    } catch (e: any) { setErr(e.message); }
  }
  async function verifyOtp() {
    setErr("");
    try {
      const r = await api(`/api/public/${slug}/otp/verify`, { method: "POST", json: { phone: f.phone, code: otp } });
      setPhoneToken(r.phone_token);
    } catch (e: any) { setErr(e.message); }
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setErr("");
    if (!f.monthly_units && !f.monthly_bill) { setErr(t("units_or_bill") + " - " + t("required")); return; }
    if (!f.consent) { setErr(t("consent")); return; }
    const num = (v: any) => (v === "" || v === null ? null : Number(v));
    const data = {
      ...f, language: lang, email: f.email || null, phase: Number(f.phase), sanction_load_kw: num(f.sanction_load_kw),
      monthly_units: num(f.monthly_units), monthly_bill: num(f.monthly_bill), roof_area: num(f.roof_area),
      floors: num(f.floors), backup_load_w: num(f.backup_load_w), phone_token: phoneToken || null,
      pincode: f.pincode || null, district: f.district || null, eb_consumer_no: f.eb_consumer_no || null,
      tariff: f.tariff || null, budget_range: f.budget_range || null,
    };
    const fd = new FormData();
    fd.append("data", JSON.stringify(data));
    if (ebBill) fd.append("eb_bill", ebBill);
    roofPhotos.slice(0, 6).forEach((p) => fd.append("roof_photos", p));
    setBusy(true);
    try {
      const r = await api(`/api/public/${slug}/requests`, { method: "POST", body: fd });
      setDone(r);
      window.scrollTo(0, 0);
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return (
      <div className="card">
        <h1>{t("thanks")}</h1>
        <p>{t("reference")}: <strong style={{ fontSize: "1.3rem" }}>{done.reference}</strong></p>
        <p>{done.email_sent ? t("ack_note") : t("ack_no_email")}</p>
        <Link className="btn" to={`/s/${slug}/status/${done.reference}?t=${done.status_token}`}>{t("status_link")}</Link>
      </div>
    );
  }

  const needOtp = info.require_phone_otp && !phoneToken;
  return (
    <form onSubmit={submit} noValidate>
      <h1>{t("form_title")}</h1>
      <div className="card">
        <h2>{t("contact")}</h2>
        <label>{t("name")} *</label>
        <input value={f.name} onChange={set("name")} required autoComplete="name" />
        <label>{t("phone")} *</label>
        <div className="row">
          <input value={f.phone} onChange={set("phone")} inputMode="tel" autoComplete="tel" required placeholder="98765 43210" />
          {!phoneToken ? (
            <button type="button" className="secondary" style={{ flex: "0 0 auto" }} onClick={sendOtp} disabled={f.phone.replace(/\D/g, "").length < 10}>
              {t("send_otp")}
            </button>
          ) : <span className="pill green" style={{ flex: "0 0 auto" }}>{t("verified")}</span>}
        </div>
        {otpSent && !phoneToken && (
          <div className="row">
            <div><label>{t("otp")}</label><input value={otp} onChange={(e) => setOtp(e.target.value)} inputMode="numeric" maxLength={6} /></div>
            <button type="button" style={{ flex: "0 0 auto" }} onClick={verifyOtp}>{t("verify")}</button>
            {devCode && <span className="muted small">dev code: {devCode}</span>}
          </div>
        )}
        <label>{t("email")}</label>
        <input type="email" value={f.email} onChange={set("email")} autoComplete="email" />
        <input className="hp" tabIndex={-1} autoComplete="off" value={f.website} onChange={set("website")} aria-hidden="true" />
      </div>

      <div className="card">
        <h2>{t("site")}</h2>
        <label>{t("address")} *</label>
        <textarea value={f.address} onChange={set("address")} required autoComplete="street-address" />
        <div className="row">
          <div><label>{t("pincode")}</label><input value={f.pincode} onChange={set("pincode")} inputMode="numeric" maxLength={6} /></div>
          <div><label>{t("district")}</label><input value={f.district} onChange={set("district")} /></div>
        </div>
        <label>{t("site_type")}</label>
        <Seg name="site_type" value={f.site_type} onChange={set("site_type")} opts={[{ v: "home", k: "home" }, { v: "commercial", k: "commercial" }, { v: "industry", k: "industry" }]} />
      </div>

      <div className="card">
        <h2>{t("electricity")}</h2>
        <div className="row">
          <div><label>{t("eb_no")}</label><input value={f.eb_consumer_no} onChange={set("eb_consumer_no")} /></div>
          <div><label>{t("tariff")}</label><input value={f.tariff} onChange={set("tariff")} placeholder="LA1A" /></div>
        </div>
        <label>{t("phase")}</label>
        <Seg name="phase" value={Number(f.phase)} onChange={(v) => setF({ ...f, phase: v })} opts={[{ v: 1, k: "single" }, { v: 3, k: "three" }]} />
        <label>{t("sanction_load")}</label>
        <input value={f.sanction_load_kw} onChange={set("sanction_load_kw")} inputMode="decimal" />
        <p className="muted small" style={{ marginBottom: 0 }}>{t("units_or_bill")} *</p>
        <div className="row">
          <div><label>{t("monthly_units")}</label><input value={f.monthly_units} onChange={set("monthly_units")} inputMode="decimal" /></div>
          <div><label>{t("monthly_bill")}</label><input value={f.monthly_bill} onChange={set("monthly_bill")} inputMode="decimal" /></div>
        </div>
      </div>

      <div className="card">
        <h2>{t("roof")}</h2>
        <label>{t("roof_type")}</label>
        <Seg name="roof_type" value={f.roof_type} onChange={set("roof_type")} opts={[{ v: "rcc", k: "rcc" }, { v: "sheet", k: "sheet" }, { v: "tile", k: "tile" }]} />
        <label>{t("roof_area")}</label>
        <div className="row">
          <input value={f.roof_area} onChange={set("roof_area")} inputMode="decimal" />
          <select value={f.roof_area_unit} onChange={set("roof_area_unit")} style={{ flex: "0 0 110px" }}>
            <option value="sqft">{t("sqft")}</option>
            <option value="sqm">{t("sqm")}</option>
          </select>
        </div>
        <label>{t("direction")}</label>
        <select value={f.direction} onChange={set("direction")}>
          {(["south", "south_east", "south_west", "east", "west", "north", "flat", "unknown"] as Key[]).map((d) => <option key={d} value={d}>{t(d)}</option>)}
        </select>
        <label>{t("shade")}</label>
        <Seg name="shade" value={f.shade} onChange={set("shade")} opts={[{ v: "none", k: "none" }, { v: "some", k: "some" }, { v: "heavy", k: "heavy" }]} />
        <label>{t("floors")}</label>
        <input value={f.floors} onChange={set("floors")} inputMode="numeric" />
      </div>

      <div className="card">
        <h2>{t("goal")}</h2>
        <Seg name="goal" value={f.goal} onChange={set("goal")} opts={[{ v: "reduce_bill", k: "reduce_bill" }, { v: "backup", k: "backup" }, { v: "industrial", k: "industrial" }]} />
        {f.goal === "backup" && (<><label>{t("backup_load")}</label><input value={f.backup_load_w} onChange={set("backup_load_w")} inputMode="numeric" /></>)}
        <label>{t("budget")}</label>
        <input value={f.budget_range} onChange={set("budget_range")} />
      </div>

      <div className="card">
        <h2>{t("uploads")}</h2>
        <label>{t("eb_bill")}</label>
        <input type="file" accept="image/*,application/pdf" capture="environment" onChange={(e) => setEbBill(e.target.files?.[0] || null)} />
        <label>{t("roof_photos")}</label>
        <input type="file" accept="image/*" multiple onChange={(e) => setRoofPhotos(Array.from(e.target.files || []).slice(0, 6))} />
        {roofPhotos.length > 0 && <p className="muted small">{roofPhotos.length} / 6</p>}
      </div>

      <div className="card">
        <label className="inline"><input type="checkbox" checked={f.consent} onChange={set("consent")} /> <span>{t("consent")}</span></label>
        {err && <div className="err">{err}</div>}
        <button type="submit" disabled={busy || needOtp} style={{ width: "100%", marginTop: 10 }}>{busy ? t("submitting") : t("submit")}</button>
        <p className="muted small">{lang === "ta" ? info.disclaimer_ta : info.disclaimer_en}</p>
      </div>
    </form>
  );
}
