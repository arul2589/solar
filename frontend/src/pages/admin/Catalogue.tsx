import { useEffect, useState } from "react";
import { api } from "../../api";
import { useRole } from "./AdminLayout";

type Col = { k: string; l: string; w?: number; type?: "bool" | "text" };

const TABLES: Record<string, { path: string; title: string; cols: Col[]; blank: any }> = {
  price: {
    path: "price-items", title: "Price master",
    cols: [{ k: "sort_order", l: "#", w: 50 }, { k: "code", l: "Code", w: 120 }, { k: "name", l: "Name", w: 260 }, { k: "details", l: "Details", w: 200 },
      { k: "hsn", l: "HSN", w: 90 }, { k: "unit", l: "Unit", w: 80 }, { k: "unit_price", l: "Price ₹", w: 90 }, { k: "cost_price", l: "Cost ₹", w: 90 },
      { k: "gst_pct", l: "GST %", w: 60 }, { k: "qty_rule", l: "Qty rule", w: 110 }, { k: "qty_factor", l: "× factor", w: 70 },
      { k: "phase", l: "Phase", w: 60 }, { k: "system_kind", l: "Kind", w: 90 }, { k: "min_kw", l: "Min kW", w: 70 }, { k: "max_kw", l: "Max kW", w: 70 },
      { k: "requires_la", l: "LA only", type: "bool" }, { k: "is_placeholder", l: "Placeholder", type: "bool" }, { k: "active", l: "Active", type: "bool" }],
    blank: { code: "", name: "", unit: "No", unit_price: "0", gst_pct: "18", qty_rule: "fixed", qty_factor: "1", sort_order: 100, active: true },
  },
  panels: {
    path: "panels", title: "Panel catalogue",
    cols: [{ k: "make", l: "Make", w: 90 }, { k: "model", l: "Model", w: 220 }, { k: "wp", l: "Wp", w: 60 }, { k: "voc", l: "Voc", w: 60 }, { k: "vmp", l: "Vmp", w: 60 },
      { k: "isc", l: "Isc", w: 60 }, { k: "imp", l: "Imp", w: 60 }, { k: "temp_coeff_voc_pct", l: "β Voc %/°C", w: 70 }, { k: "temp_coeff_pmax_pct", l: "γ Pmax %/°C", w: 70 },
      { k: "length_mm", l: "L mm", w: 70 }, { k: "width_mm", l: "W mm", w: 70 }, { k: "price", l: "Price ₹", w: 90 }, { k: "hsn", l: "HSN", w: 90 }, { k: "gst_pct", l: "GST %", w: 60 },
      { k: "warranty_text", l: "Warranty", w: 200 }, { k: "is_default", l: "Default", type: "bool" }, { k: "is_placeholder", l: "Placeholder", type: "bool" }, { k: "active", l: "Active", type: "bool" }],
    blank: { make: "", model: "", wp: 0, voc: 0, vmp: 0, isc: 0, imp: 0, temp_coeff_voc_pct: -0.27, temp_coeff_pmax_pct: -0.3, length_mm: 0, width_mm: 0, gst_pct: "5", active: true },
  },
  inverters: {
    path: "inverters", title: "Inverter catalogue",
    cols: [{ k: "make", l: "Make", w: 90 }, { k: "model", l: "Model", w: 220 }, { k: "kind", l: "Kind", w: 90 }, { k: "ac_kw", l: "AC kW", w: 60 }, { k: "phase", l: "Ph", w: 40 },
      { k: "max_dc_voltage", l: "Max DC V", w: 70 }, { k: "mppt_min_v", l: "MPPT min", w: 70 }, { k: "mppt_max_v", l: "MPPT max", w: 70 }, { k: "num_mppt", l: "MPPTs", w: 50 },
      { k: "max_input_current_per_mppt", l: "Max A/MPPT", w: 70 }, { k: "ac_max_current", l: "AC max A", w: 70 }, { k: "battery_voltage", l: "Batt V", w: 60 },
      { k: "price", l: "Price ₹", w: 90 }, { k: "hsn", l: "HSN", w: 70 }, { k: "gst_pct", l: "GST %", w: 60 }, { k: "warranty_text", l: "Warranty", w: 160 },
      { k: "is_placeholder", l: "Placeholder", type: "bool" }, { k: "active", l: "Active", type: "bool" }],
    blank: { make: "", model: "", kind: "on_grid", ac_kw: 0, phase: 1, max_dc_voltage: 0, mppt_min_v: 0, mppt_max_v: 0, num_mppt: 1, max_input_current_per_mppt: 0, ac_max_current: 0, gst_pct: "5", active: true },
  },
  rates: {
    path: "network-rates", title: "Network-charge rates (by effective date)",
    cols: [{ k: "effective_from", l: "Effective from (YYYY-MM-DD)", w: 160 }, { k: "rate", l: "₹ per generated unit", w: 120 }, { k: "note", l: "Note", w: 320 }],
    blank: { effective_from: "", rate: "", note: "" },
  },
};

export default function Catalogue() {
  const role = useRole();
  const [tab, setTab] = useState("price");
  return (
    <div>
      <h1>Price list & catalogue</h1>
      <div className="note">Prices, GST rates and catalogue specs were seeded from sample quotation #276 and typical values. Rows marked <span className="placeholder-tag">placeholder</span> must be confirmed by the owner.</div>
      <div className="tabs">
        {Object.entries(TABLES).map(([k, v]) => <button key={k} className={tab === k ? "active" : ""} onClick={() => setTab(k)}>{v.title}</button>)}
      </div>
      <EditableTable key={tab} cfg={TABLES[tab]} canEdit={role === "admin"} />
      {tab === "price" && (
        <div className="card small muted">
          <strong>Qty rules:</strong> fixed (1 × factor) · per_kw (nominal kW) · per_kwp · per_panel · panel (panel model price) · inverter (inverter model price) ·
          dc_cable_m · ac_cable_m · earth_pits · la_cable_m · per_string · per_mppt. Filters: phase, kind (on_grid/hybrid), min/max kWp, LA only.
          Name/details for panel and inverter rows can use {"{model}"}, {"{wp}"}, {"{panel_count}"}, {"{dc_wp}"}, {"{nominal_kw}"}.
        </div>
      )}
    </div>
  );
}

function EditableTable({ cfg, canEdit }: { cfg: any; canEdit: boolean }) {
  const [rows, setRows] = useState<any[]>([]);
  const [dirty, setDirty] = useState<Set<number>>(new Set());
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const load = () => api(`/api/admin/${cfg.path}`).then((r) => { setRows(r); setDirty(new Set()); }).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, [cfg.path]);

  const set = (i: number, k: string, v: any) => {
    const n = [...rows]; n[i] = { ...n[i], [k]: v }; setRows(n);
    setDirty(new Set(dirty).add(i));
  };
  const saveRow = async (i: number) => {
    setErr(""); setMsg("");
    const r = rows[i];
    try {
      if (r.id) await api(`/api/admin/${cfg.path}/${r.id}`, { method: "PUT", json: r });
      else await api(`/api/admin/${cfg.path}`, { method: "POST", json: r });
      setMsg("Saved."); load();
    } catch (e: any) { setErr(e.message); }
  };
  const del = async (i: number) => {
    const r = rows[i];
    if (!r.id) { setRows(rows.filter((_, j) => j !== i)); return; }
    if (!window.confirm("Deactivate / delete this row?")) return;
    await api(`/api/admin/${cfg.path}/${r.id}`, { method: "DELETE" });
    load();
  };

  return (
    <div className="card" style={{ padding: 0 }}>
      {err && <div className="err">{err}</div>}
      {msg && <div className="ok">{msg}</div>}
      <div className="table-wrap inline-edit">
        <table>
          <thead><tr>{cfg.cols.map((c: Col) => <th key={c.k}>{c.l}</th>)}<th></th></tr></thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={r.id || `new${i}`} style={r.active === false ? { opacity: 0.5 } : {}}>
                {cfg.cols.map((c: Col) => (
                  <td key={c.k}>
                    {c.type === "bool"
                      ? <input type="checkbox" checked={!!r[c.k]} disabled={!canEdit} onChange={(e) => set(i, c.k, e.target.checked)} />
                      : <input style={{ minWidth: c.w || 80 }} value={r[c.k] ?? ""} disabled={!canEdit} onChange={(e) => set(i, c.k, e.target.value)} />}
                  </td>
                ))}
                <td style={{ whiteSpace: "nowrap" }}>
                  {canEdit && dirty.has(i) && <button className="small" onClick={() => saveRow(i)}>Save</button>}
                  {canEdit && <button className="ghost" onClick={() => del(i)} title="Delete">✕</button>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {canEdit && <div style={{ padding: 12 }}><button className="secondary" onClick={() => { setRows([...rows, { ...cfg.blank }]); setDirty(new Set(dirty).add(rows.length)); }}>Add row</button></div>}
    </div>
  );
}
