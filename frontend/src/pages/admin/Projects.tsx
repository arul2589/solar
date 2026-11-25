import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, fmtDate, staffSession } from "../../api";
import { useRole } from "./AdminLayout";

const STATUS: Record<string, string> = { planned: "Planned", in_progress: "In progress", net_metering: "Net metering", done: "Completed" };

export function Projects() {
  const [rows, setRows] = useState<any[]>([]);
  const [err, setErr] = useState("");
  useEffect(() => { api("/api/admin/projects").then(setRows).catch((e) => setErr(e.message)); }, []);
  return (
    <div>
      <h1>Projects</h1>
      {err && <div className="err">{err}</div>}
      {rows.length === 0 && <p className="muted">No projects yet. A project is created when a customer accepts a quotation.</p>}
      {rows.map((p) => (
        <Link key={p.id} to={`/admin/projects/${p.id}`} className="card" style={{ display: "block", textDecoration: "none", color: "inherit" }}>
          <strong>{p.reference}</strong> · {p.customer_name} <span className="pill">{STATUS[p.status]}</span> <span className="pill green">{p.progress}</span>
          <div className="muted small">{p.system_summary}</div>
          <div className="muted small">{p.address} {p.district}</div>
        </Link>
      ))}
    </div>
  );
}

export function ProjectDetail() {
  const { id } = useParams();
  const role = useRole();
  const [d, setD] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [tab, setTab] = useState("checklist");
  const [ta, setTa] = useState(false);
  const [rd, setRd] = useState<any>({ kind: "voc", label: "String 1", value: "" });
  const [err, setErr] = useState("");
  const [svgs, setSvgs] = useState<Record<string, string>>({});
  const manager = role !== "technician";

  const load = () => api(`/api/admin/projects/${id}`).then(setD).catch((e) => setErr(e.message));
  useEffect(() => { load(); if (manager) api("/api/admin/users").then(setUsers).catch(() => {}); }, [id]);
  useEffect(() => {
    const aid = d?.pack?.analysis_run_id;
    if (tab === "drawings" && aid) for (const k of ["sld", "roof", "schedule"]) api(`/api/admin/analysis/${aid}/diagram/${k}`).then((r) => setSvgs((s) => ({ ...s, [k]: r.svg })));
  }, [tab, d?.pack?.analysis_run_id]);

  const patchItem = async (item: any, body: any) => {
    setErr("");
    try { await api(`/api/admin/projects/${id}/checklist/${item.id}`, { method: "PATCH", json: body }); load(); }
    catch (e: any) { setErr(e.message); }
  };
  const togglePoint = (item: any, i: number) => {
    const pts = item.points.map((p: any, j: number) => (j === i ? { ...p, done: !p.done } : p));
    patchItem(item, { points: pts, done: pts.every((p: any) => p.done) || undefined });
  };
  const addReading = async () => {
    setErr("");
    try { await api(`/api/admin/projects/${id}/readings`, { method: "POST", json: { ...rd, value: Number(rd.value) } }); setRd({ ...rd, value: "" }); load(); }
    catch (e: any) { setErr(e.message); }
  };
  const uploadPhoto = async (f: File) => {
    const fd = new FormData(); fd.append("file", f);
    try { await api(`/api/admin/projects/${id}/photos`, { method: "POST", body: fd }); load(); } catch (e: any) { setErr(e.message); }
  };
  const patch = async (body: any) => {
    try { setD(await api(`/api/admin/projects/${id}`, { method: "PATCH", json: body })); } catch (e: any) { setErr(e.message); }
  };
  const openPdf = async () => {
    const res = await fetch(`/api/admin/projects/${id}/pack.pdf`, { headers: { Authorization: `Bearer ${staffSession()?.token}` } });
    if (!res.ok) { setErr("PDF failed"); return; }
    window.open(URL.createObjectURL(await res.blob()), "_blank");
  };

  if (!d) return <p>{err || "Loading..."}</p>;
  return (
    <div style={{ maxWidth: 900 }}>
      <Link className="small" to="/admin/projects">← Projects</Link>
      <h1 style={{ margin: "4px 0" }}>{d.reference} · {d.customer_name}</h1>
      <p className="muted small">{d.system_summary}<br />{d.address} {d.district} · <a href={`tel:${d.customer_phone}`}>{d.customer_phone}</a></p>
      <div className="row" style={{ marginBottom: 10 }}>
        <span className="pill blue" style={{ flex: "0 0 auto" }}>{STATUS[d.status]} · {d.progress}</span>
        <button className="secondary small" style={{ flex: "0 0 auto" }} onClick={openPdf}>Project pack PDF</button>
        <button className="ghost small" style={{ flex: "0 0 auto" }} onClick={() => setTa(!ta)}>{ta ? "English" : "தமிழ்"}</button>
        {manager && (<>
          <select style={{ flex: "0 0 200px" }} value={d.technician_user_id || ""} onChange={(e) => patch({ technician_user_id: Number(e.target.value) || 0 })}>
            <option value="">Assign technician...</option>
            {users.filter((u) => u.active).map((u) => <option key={u.id} value={u.id}>{u.name} ({u.role})</option>)}
          </select>
          <select style={{ flex: "0 0 170px" }} value={d.status} onChange={(e) => patch({ status: e.target.value })}>
            {Object.entries(STATUS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <Link className="btn small secondary" style={{ flex: "0 0 auto" }} to={`/admin/requests/${d.request_id}`}>Request</Link>
        </>)}
      </div>
      {err && <div className="err">{err}</div>}
      <div className="tabs">
        {["checklist", "readings", "photos", "materials", "drawings", "net metering"].map((t) => <button key={t} className={tab === t ? "active" : ""} onClick={() => setTab(t)}>{t[0].toUpperCase() + t.slice(1)}</button>)}
      </div>

      {tab === "checklist" && d.checklist.map((item: any) => (
        <div className="card" key={item.id} style={{ padding: 12 }}>
          <label className="inline" style={{ fontSize: "1.05rem", margin: 0 }}>
            <input type="checkbox" style={{ width: 22, height: 22 }} checked={item.done} onChange={() => patchItem(item, { done: !item.done })} />
            <span><strong>{item.step_no}. {ta && item.title_ta ? item.title_ta : item.title}</strong>{item.done_at && <span className="muted small"> · {fmtDate(item.done_at)}</span>}</span>
          </label>
          <div style={{ marginLeft: 30 }}>
            {item.points.map((pt: any, i: number) => (
              <label key={i} className="inline" style={{ margin: "6px 0" }}>
                <input type="checkbox" style={{ width: 18, height: 18 }} checked={pt.done} onChange={() => togglePoint(item, i)} /> <span>{pt.text}</span>
              </label>
            ))}
            <input placeholder="Notes" defaultValue={item.notes} onBlur={(e) => e.target.value !== item.notes && patchItem(item, { notes: e.target.value })} />
          </div>
        </div>
      ))}

      {tab === "readings" && (
        <div className="card">
          <h2>Test readings</h2>
          <p className="muted small">Expected max string Voc (cold design): {d.pack.expected?.string_voc_cold_max ?? "-"} V · earth resistance &lt; 5 Ω per pit.</p>
          <div className="row">
            <div><label>Test</label><select value={rd.kind} onChange={(e) => setRd({ ...rd, kind: e.target.value })}>
              <option value="voc">Voc (V)</option><option value="isc">Isc (A)</option><option value="earth_resistance">Earth resistance (Ω)</option>
              <option value="insulation">Insulation (MΩ)</option><option value="ac_voltage">AC voltage (V)</option><option value="other">Other</option></select></div>
            <div><label>Label</label><input value={rd.label} onChange={(e) => setRd({ ...rd, label: e.target.value })} placeholder="String 1 / Pit 2" /></div>
            <div><label>Value</label><input value={rd.value} onChange={(e) => setRd({ ...rd, value: e.target.value })} inputMode="decimal" /></div>
            <button style={{ flex: "0 0 auto" }} disabled={rd.value === ""} onClick={addReading}>Save</button>
          </div>
          <table style={{ marginTop: 12 }}><thead><tr><th>Test</th><th>Label</th><th className="num">Value</th><th>Expected</th><th>Result</th></tr></thead>
            <tbody>{d.readings.map((r: any) => (
              <tr key={r.id}><td>{r.kind}</td><td>{r.label}</td><td className="num">{r.value} {r.unit}</td><td>{r.expected || "-"}</td>
                <td>{r.ok === null ? "-" : r.ok ? <span className="pill green">OK</span> : <span className="pill red">CHECK</span>}</td></tr>))}</tbody></table>
        </div>
      )}

      {tab === "photos" && (
        <div className="card">
          <h2>Site photos</h2>
          <input type="file" accept="image/*" capture="environment" onChange={(e) => e.target.files?.[0] && uploadPhoto(e.target.files[0])} />
          <div className="photos" style={{ marginTop: 10 }}>{d.photos.map((p: any) => <a key={p.id} href={p.url} target="_blank" rel="noreferrer"><img src={p.url} alt="" /></a>)}</div>
        </div>
      )}

      {tab === "materials" && (
        <>
          <div className="card"><h2>Bill of materials</h2>
            <table><tbody>{d.pack.bom.map((l: any, i: number) => <tr key={i}><td>{l.description}<div className="muted small">{l.details}</div></td><td className="num">{Number(l.qty)} {l.unit}</td></tr>)}</tbody></table></div>
          <div className="card"><h2>String plan</h2>{d.pack.strings.map((s: any, i: number) => <div key={i}>String {i + 1}: {s.modules} modules · {s.inverter ? `inverter ${s.inverter} · ` : ""}MPPT {s.mppt}</div>)}</div>
          <div className="card"><h2>Tools</h2><ul>{d.pack.tools.map((t: string) => <li key={t}>{t}</li>)}</ul></div>
        </>
      )}

      {tab === "drawings" && ["sld", "roof", "schedule"].map((k) => (
        <div className="card" key={k}><div className="svgbox" dangerouslySetInnerHTML={{ __html: svgs[k] || "Loading..." }} /></div>
      ))}

      {tab === "net metering" && (
        <div className="card"><h2>TANGEDCO net-metering documents</h2><ul>{d.pack.net_metering_docs.map((t: string) => <li key={t}>{t}</li>)}</ul></div>
      )}
    </div>
  );
}
