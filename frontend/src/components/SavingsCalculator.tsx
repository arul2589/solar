// Website savings calculator. Calls POST /api/public/{slug}/estimate, which runs the real
// engine with this installer's settings and returns size + savings only (never a price).
import { useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { useI18n } from "../i18n";
import { site } from "../siteContent";
import Icon from "./Icon";

type SiteType = "home" | "commercial" | "industry";

export type Estimate = {
  ok: boolean;
  monthly_units?: number | null;
  monthly_units_source?: string | null;
  system?: { nominal_kw: number; dc_kwp: number; panel_count: number; panel_wp: number; kind: string };
  roof?: { min_m2: number | null; recommended_m2: number | null };
  generation?: { per_month_low: number | null; per_month_high: number | null };
  savings?: { annual_low: number | null; annual_high: number | null; monthly_low: number | null; monthly_high: number | null };
  notes?: string[];
};

const inr = (n?: number | null) => (n == null ? "–" : `₹${Math.round(n).toLocaleString("en-IN")}`);
const num = (n?: number | null) => (n == null ? "–" : Math.round(n).toLocaleString("en-IN"));
const range = (lo?: number | null, hi?: number | null, f = inr) =>
  lo == null && hi == null ? "–" : lo === hi || hi == null ? f(lo) : `${f(lo)} – ${f(hi)}`;

export default function SavingsCalculator({ defaultType = "home", compact = false }: { defaultType?: SiteType; compact?: boolean }) {
  const { slug } = useParams();
  const { lang } = useI18n();
  const c = site[lang].calc;
  const [mode, setMode] = useState<"bill" | "units">("bill");
  const [value, setValue] = useState(defaultType === "home" ? "4000" : defaultType === "commercial" ? "40000" : "250000");
  const [siteType, setSiteType] = useState<SiteType>(defaultType);
  const [phase, setPhase] = useState<1 | 3>(defaultType === "home" ? 1 : 3);
  const [goal, setGoal] = useState<"reduce_bill" | "backup">("reduce_bill");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [res, setRes] = useState<Estimate | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    const v = Number(value);
    if (!v || v <= 0) return;
    setBusy(true);
    setErr("");
    try {
      const body = { [mode === "bill" ? "monthly_bill" : "monthly_units"]: v, site_type: siteType, phase, goal };
      const r = await api<Estimate>(`/api/public/${slug}/estimate`, { method: "POST", json: body });
      setRes(r);
      if (!r.ok) setErr(c.error);
    } catch {
      setErr(c.error);
      setRes(null);
    } finally {
      setBusy(false);
    }
  }

  const s = res?.ok ? res : null;
  const sqft = (m2?: number | null) => (m2 == null ? "" : ` (~${num(m2 * 10.764)} sq ft)`);

  return (
    <div className={`calc${compact ? " calc-compact" : ""}`}>
      <form className="calc-form" onSubmit={submit}>
        <div className="calc-form-head">
          <span className="calc-icon"><Icon name="calc" size={26} /></span>
          <div>
            <h3>{c.eyebrow}</h3>
            {!compact && <p>{c.lead}</p>}
          </div>
        </div>
        <div className="seg-toggle" role="group">
          <button type="button" className={mode === "bill" ? "on" : ""} onClick={() => setMode("bill")}>{c.byBill}</button>
          <button type="button" className={mode === "units" ? "on" : ""} onClick={() => setMode("units")}>{c.byUnits}</button>
        </div>
        <div className="calc-grid">
          <label>
            {mode === "bill" ? c.billLabel : c.unitsLabel}
            <input inputMode="numeric" type="number" min={1} step="any" required value={value} onChange={(e) => setValue(e.target.value)} />
          </label>
          <label>
            {c.siteType}
            <select value={siteType} onChange={(e) => { const t = e.target.value as SiteType; setSiteType(t); if (t !== "home") setPhase(3); }}>
              <option value="home">{c.home}</option>
              <option value="commercial">{c.commercial}</option>
              <option value="industry">{c.industry}</option>
            </select>
          </label>
          <label>
            {c.phase}
            <select value={phase} onChange={(e) => setPhase(Number(e.target.value) as 1 | 3)}>
              <option value={1}>{c.single}</option>
              <option value={3}>{c.three}</option>
            </select>
          </label>
          <label>
            {c.system}
            <select value={goal} onChange={(e) => setGoal(e.target.value as "reduce_bill" | "backup")}>
              <option value="reduce_bill">{c.onGrid}</option>
              <option value="backup">{c.hybrid}</option>
            </select>
          </label>
        </div>
        <button className="btn btn-sun" disabled={busy}>{busy ? c.working : c.submit}</button>
      </form>

      <div className="calc-out" aria-live="polite">
        <div className="calc-out-head"><Icon name="leaf" /> <h3>{c.resultsTitle}</h3></div>
        {err && <div className="err">{err}</div>}
        {!s && !err && <p className="muted">{c.emptyHint}</p>}
        {s && (
          <>
            <div className="calc-big">
              <div><strong>{range(s.savings?.monthly_low, s.savings?.monthly_high)}</strong><span>{c.monthlySaving}</span></div>
              <div><strong>{range(s.savings?.annual_low, s.savings?.annual_high)}</strong><span>{c.annualSaving}</span></div>
            </div>
            <div className="calc-sys">
              <Icon name="panel" size={34} />
              <div>
                <div className="calc-sys-title">{c.size}: <strong>{s.system?.nominal_kw} kW</strong></div>
                <div className="small muted">
                  {s.system?.panel_count} × {s.system?.panel_wp} Wp {c.panels} ({s.system?.dc_kwp} kWp)
                  {" · "}{c.roof}: ~{num(s.roof?.recommended_m2)} m²{sqft(s.roof?.recommended_m2)}
                  {" · "}{c.generation}: {range(s.generation?.per_month_low, s.generation?.per_month_high, num)} {c.unitsMonth}
                </div>
              </div>
            </div>
            {s.monthly_units_source === "bill_amount" && s.monthly_units != null && (
              <p className="small muted">{c.unitsFromBill.replace("{u}", num(s.monthly_units))}</p>
            )}
            {(s.notes ?? []).map((n) => c.notes[n] && <div className="warn info" key={n}>{c.notes[n]}</div>)}
            <p className="small muted">{c.note}</p>
            <Link className="btn btn-sun" to={`/s/${slug}/request`}>{c.cta} <Icon name="arrow" size={18} /></Link>
          </>
        )}
      </div>
    </div>
  );
}
