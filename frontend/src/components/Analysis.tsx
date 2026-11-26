import { inr, inr0 } from "../api";

export function Warnings({ list }: { list: any[] }) {
  if (!list?.length) return <p className="muted small">No warnings.</p>;
  return <>{list.map((w, i) => <div key={i} className={`warn ${w.severity}`}><strong>{w.code.replace(/_/g, " ")}</strong>: {w.message}</div>)}</>;
}

// "a–b", or just "a" when both ends are the same
function range(a: any, b: any, sep = "–") {
  return String(a) === String(b) ? String(a) : `${a}${sep}${b}`;
}

function Stat({ v, l }: { v: any; l: string }) {
  return <div className="stat"><div className="v">{v}</div><div className="l">{l}</div></div>;
}

export function AnalysisView({ o }: { o: any }) {
  if (!o) return <p className="muted">No analysis yet.</p>;
  if (o.ok === false && !o.sizing) return <Warnings list={o.warnings} />;
  const sz = o.sizing || {};
  const roof = o.roof || {};
  const inv = o.inverter?.inverter;
  const st = o.inverter?.strings;
  const nc = o.network_charge;
  const sv = o.savings || {};
  const el = o.electrical;
  return (
    <div>
      <div className="grid3" style={{ marginBottom: 12 }}>
        <Stat v={`${sz.dc_kwp} kWp`} l={`Suggested system (sold as ${sz.nominal_kw} kW)`} />
        <Stat v={sz.panel_count} l={`Panels × ${sz.panel_wp} W (${o.panel?.model || ""})`} />
        <Stat v={range(o.generation?.per_month_low, o.generation?.per_month_high)} l="Units / month (realistic yield)" />
        <Stat v={roof.fits === null || roof.fits === undefined ? "?" : roof.fits ? "Fits" : "Does not fit"} l={`Roof: need ~${roof.rule_of_thumb?.min_m2}–${roof.rule_of_thumb?.recommended_m2} m², have ${roof.available_m2 ?? "?"} m²`} />
        <Stat v={inv ? `${inv.ac_kw} kW` : "-"} l={inv ? `${inv.model} (${inv.phase}-ph), DC/AC ${o.inverter.dc_ac_ratio}` : "No inverter"} />
        {o.cost && <Stat v={range(inr0(o.cost.range_low), inr0(o.cost.range_high), " – ")} l="Rough cost range (incl. GST)" />}
        {sv.low && <Stat v={range(inr0(sv.low.annual_saving), inr0(sv.high.annual_saving), " – ")} l="Annual savings (range)" />}
        {sv.low?.payback_years && <Stat v={`${range(sv.high.payback_years, sv.low.payback_years)} yrs`} l="Payback (range)" />}
      </div>
      <h3>Warnings</h3>
      <Warnings list={o.warnings} />
      <div className="grid2" style={{ marginTop: 12 }}>
        <div>
          <h3>Sizing</h3>
          <dl className="kv">
            <dt>Monthly units</dt><dd>{o.monthly_units ?? "-"} {o.monthly_units_source === "bill_amount" && <span className="muted small">(from bill amount)</span>}</dd>
            <dt>kW needed</dt><dd>{sz.kw_needed ?? "-"} (yield {sz.yield_used_kwh_per_kw_day} kWh/kW/day)</dd>
            <dt>Limited by</dt><dd>{sz.limited_by || "consumption"}</dd>
            <dt>Max by sanction</dt><dd>{sz.max_kw_by_sanction ?? "-"} kW</dd>
            <dt>Max by roof</dt><dd>{sz.max_kw_by_roof ? `${sz.max_kw_by_roof.toFixed(2)} kWp` : "-"}</dd>
            <dt>CUF generation</dt><dd>{o.generation?.per_day_cuf} units/day ({sz.cuf_units_per_kw_day}/kW)</dd>
          </dl>
          <h3 style={{ marginTop: 14 }}>Roof layout</h3>
          <dl className="kv">
            <dt>Rows × per row</dt><dd>{roof.layout?.rows} × {roof.layout?.per_row} (capacity {roof.layout?.capacity})</dd>
            <dt>Required area</dt><dd>{roof.layout?.required_area_m2} m² (geometric)</dd>
            <dt>Row pitch</dt><dd>{roof.layout?.geometry?.row_pitch_m} m (shadow gap {roof.layout?.geometry?.row_gap_m} m)</dd>
            <dt>Tilt</dt><dd>{roof.tilt_deg}° facing south</dd>
          </dl>
        </div>
        <div>
          <h3>Strings & inverter</h3>
          {st ? (
            <dl className="kv">
              <dt>Strings</dt><dd>{st.strings?.map((s: any) => `${s.modules} modules (MPPT ${s.mppt})`).join(", ") || "none"}</dd>
              <dt>Modules/string</dt><dd>{st.modules_per_string_min}–{st.modules_per_string_max}</dd>
              <dt>Voc cold (string)</dt><dd>{st.string_voc_cold_max} V (max {inv?.max_dc_voltage} V)</dd>
              <dt>Vmp hot (string)</dt><dd>{st.string_vmp_hot_min} V (MPPT min {inv?.mppt_min_v} V)</dd>
              <dt>MPPT current</dt><dd>{st.max_mppt_current} A</dd>
            </dl>
          ) : <p className="muted">-</p>}
          {el && (<>
            <h3 style={{ marginTop: 14 }}>Cables & protection</h3>
            <dl className="kv">
              <dt>DC cable</dt><dd>{el.dc_cable_mm2} mm², {el.dc_cable_total_m} m</dd>
              <dt>AC cable</dt><dd>{el.ac_cable_mm2} mm², {el.ac_cable_total_m} m</dd>
              <dt>Earthing</dt><dd>{el.earthing_pits} pits{el.lightning_arrester ? " incl. LA" : ""}</dd>
            </dl>
          </>)}
          {nc && (<>
            <h3 style={{ marginTop: 14 }}>Network charge ({nc.per})</h3>
            <dl className="kv">
              <dt>Units (CUF {nc.cuf * 100}%)</dt><dd>{nc.units}</dd>
              <dt>Rate</dt><dd>₹{nc.rate}/unit from {nc.rate_effective_from}</dd>
              <dt>Charge × {nc.percentage * 100}%</dt><dd>{inr(nc.charge)} + GST {inr(Number(nc.cgst) + Number(nc.sgst))} = {inr(nc.total)}</dd>
            </dl>
          </>)}
        </div>
      </div>
      {o.battery && (<>
        <h3 style={{ marginTop: 14 }}>Battery (hybrid / off-grid)</h3>
        <dl className="kv">
          <dt>Load × backup</dt><dd>{o.battery.load_w} W × {o.battery.backup_hours} h at {o.battery.battery_voltage} V</dd>
          <dt>Battery</dt><dd>{o.battery.battery_ah} Ah (≈{o.battery.battery_ah_rounded} Ah, {o.battery.battery_kwh} kWh)</dd>
          <dt>Inverter VA</dt><dd>{o.battery.inverter_va} VA</dd>
          <dt>Charge controller</dt><dd>{o.battery.charge_controller_a} A</dd>
        </dl>
      </>)}
      {o.cost && (
        <details style={{ marginTop: 12 }}>
          <summary><strong>Estimated bill of materials ({inr(o.cost.totals.grand_total)})</strong></summary>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Item</th><th className="num">Qty</th><th className="num">Rate</th><th className="num">GST</th><th className="num">Total</th></tr></thead>
              <tbody>
                {o.cost.lines.map((l: any, i: number) => (
                  <tr key={i}><td>{l.description}</td><td className="num">{Number(l.qty)} {l.unit}</td><td className="num">{inr(l.unit_price)}</td><td className="num">{Number(l.gst_pct)}%</td><td className="num">{inr(l.total)}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
          {o.cost.totals.margin && <p className="small">Cost {inr(o.cost.totals.cost_total)} · margin {inr(o.cost.totals.margin)}</p>}
        </details>
      )}
      {sv.low && (
        <details style={{ marginTop: 8 }}>
          <summary><strong>Savings detail</strong></summary>
          <table>
            <thead><tr><th></th><th className="num">Low yield</th><th className="num">High yield</th></tr></thead>
            <tbody>
              <tr><td>Yield kWh/kW/day</td><td className="num">{sv.low.yield_kwh_per_kw_day}</td><td className="num">{sv.high.yield_kwh_per_kw_day}</td></tr>
              <tr><td>Energy saving / {sv.cycle_months}-month bill</td><td className="num">{inr(sv.low.energy_saving_per_cycle)}</td><td className="num">{inr(sv.high.energy_saving_per_cycle)}</td></tr>
              <tr><td>Network charge / bill</td><td className="num">{inr(sv.low.network_charge_per_cycle)}</td><td className="num">{inr(sv.high.network_charge_per_cycle)}</td></tr>
              <tr><td>Annual saving</td><td className="num">{inr(sv.low.annual_saving)}</td><td className="num">{inr(sv.high.annual_saving)}</td></tr>
            </tbody>
          </table>
        </details>
      )}
    </div>
  );
}

export const OVERRIDE_FIELDS: { k: string; label: string; type?: "select"; opts?: [string, string][] }[] = [
  { k: "monthly_units", label: "Monthly units" },
  { k: "monthly_bill", label: "Monthly bill ₹" },
  { k: "phase", label: "Phase", type: "select", opts: [["1", "1"], ["3", "3"]] },
  { k: "sanction_load_kw", label: "Sanction load kW" },
  { k: "category", label: "Category", type: "select", opts: [["domestic", "Domestic"], ["commercial", "Commercial"], ["industrial", "Industrial"]] },
  { k: "goal", label: "Goal", type: "select", opts: [["reduce_bill", "Reduce bill (on-grid)"], ["backup", "Backup (hybrid)"], ["industrial", "Industrial"]] },
  { k: "roof_area_m2", label: "Roof area m²" },
  { k: "roof_length_m", label: "Roof length m (N-S)" },
  { k: "roof_width_m", label: "Roof width m (E-W)" },
  { k: "shade", label: "Shade", type: "select", opts: [["none", "None"], ["some", "Some"], ["heavy", "Heavy"]] },
  { k: "direction", label: "Direction", type: "select", opts: [["south", "South"], ["south_east", "SE"], ["south_west", "SW"], ["east", "East"], ["west", "West"], ["north", "North"], ["flat", "Flat"]] },
  { k: "target_kw", label: "Target kW (override)" },
  { k: "panel_count", label: "Panel count (override)" },
  { k: "panel_id", label: "Panel model" },
  { k: "inverter_id", label: "Inverter model" },
  { k: "dc_run_one_way_m", label: "DC run one-way m" },
  { k: "ac_run_m", label: "AC run m" },
  { k: "daily_backup_load_w", label: "Backup load W" },
  { k: "backup_hours", label: "Backup hours" },
];

const NUMERIC = new Set(["monthly_units", "monthly_bill", "phase", "sanction_load_kw", "roof_area_m2", "roof_length_m", "roof_width_m", "target_kw", "panel_count", "panel_id", "inverter_id", "dc_run_one_way_m", "ac_run_m", "daily_backup_load_w", "backup_hours"]);

export function cleanOverrides(o: Record<string, any>) {
  const out: Record<string, any> = {};
  for (const [k, v] of Object.entries(o)) {
    if (v === "" || v === null || v === undefined) continue;
    out[k] = NUMERIC.has(k) ? Number(v) : v;
  }
  return out;
}

export function OverrideForm({ values, base, onChange, panels, inverters }: { values: any; base: any; onChange: (v: any) => void; panels: any[]; inverters: any[] }) {
  return (
    <div className="grid3">
      {OVERRIDE_FIELDS.map((f) => {
        const placeholder = base?.[f.k] !== undefined && base?.[f.k] !== null ? String(base[f.k]) : "";
        const val = values[f.k] ?? "";
        const set = (v: any) => onChange({ ...values, [f.k]: v });
        let input;
        if (f.k === "panel_id" || f.k === "inverter_id") {
          const list = f.k === "panel_id" ? panels : inverters;
          input = (
            <select value={val} onChange={(e) => set(e.target.value)}>
              <option value="">Auto</option>
              {list.filter((x) => x.active).map((x) => <option key={x.id} value={x.id}>{x.make} {x.model}</option>)}
            </select>
          );
        } else if (f.type === "select") {
          input = (
            <select value={val} onChange={(e) => set(e.target.value)}>
              <option value="">{placeholder ? `(${placeholder})` : "-"}</option>
              {f.opts!.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          );
        } else {
          input = <input value={val} placeholder={placeholder} onChange={(e) => set(e.target.value)} inputMode="decimal" />;
        }
        return <div key={f.k}><label>{f.label}</label>{input}</div>;
      })}
    </div>
  );
}
