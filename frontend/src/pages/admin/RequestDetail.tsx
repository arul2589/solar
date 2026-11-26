import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, fmtDate, inr } from "../../api";
import { AnalysisView, cleanOverrides, OverrideForm } from "../../components/Analysis";
import { DesignNotes } from "./Knowledge";
import { useRole } from "./AdminLayout";
import { STAGE_LABEL } from "./Pipeline";

export default function RequestDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const role = useRole();
  const [d, setD] = useState<any>(null);
  const [tab, setTab] = useState("review");
  const [ov, setOv] = useState<any>({});
  const [preview, setPreview] = useState<any>(null);
  const [act, setAct] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [panels, setPanels] = useState<any[]>([]);
  const [inverters, setInverters] = useState<any[]>([]);
  const [note, setNote] = useState("");
  const [visit, setVisit] = useState("");
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const timer = useRef<any>(null);

  const load = () => api(`/api/admin/requests/${id}`).then((r) => { setD(r); setOv(r.request.overrides || {}); setPreview(null); }).catch((e) => setErr(e.message));
  const loadAct = () => api(`/api/admin/requests/${id}/activity`).then(setAct).catch(() => {});
  useEffect(() => { load(); loadAct(); }, [id]);
  useEffect(() => {
    api("/api/admin/users").then(setUsers).catch(() => {});
    api("/api/admin/panels").then(setPanels).catch(() => {});
    api("/api/admin/inverters").then(setInverters).catch(() => {});
  }, []);

  // live recalculation while staff edit inputs
  const changeOv = (v: any) => {
    setOv(v);
    clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      api(`/api/admin/requests/${id}/preview`, { method: "POST", json: { overrides: cleanOverrides(v) } })
        .then((r) => setPreview(r.outputs)).catch((e) => setErr(e.message));
    }, 350);
  };
  // overrides fully replace stored ones, so send the complete cleaned set
  const saveOverrides = async () => {
    setErr("");
    try {
      const r = await api(`/api/admin/requests/${id}`, { method: "PATCH", json: { overrides: cleanOverrides(ov) } });
      setD(r); setPreview(null); setMsg("Saved and re-analysed."); loadAct();
    } catch (e: any) { setErr(e.message); }
  };
  const patch = async (body: any) => {
    setErr("");
    try { const r = await api(`/api/admin/requests/${id}`, { method: "PATCH", json: body }); setD(r); loadAct(); }
    catch (e: any) { setErr(e.message); }
  };
  const addNote = async () => {
    if (!note.trim()) return;
    await api(`/api/admin/requests/${id}/notes`, { method: "POST", json: { text: note } });
    setNote(""); loadAct();
  };
  const newQuote = async () => {
    setErr("");
    try {
      const q = await api(`/api/admin/requests/${id}/quotations`, { method: "POST" });
      nav(`/admin/quotations/${q.id}`);
    } catch (e: any) { setErr(e.message); }
  };
  const readBill = async (fid: number) => {
    setErr(""); setMsg("Reading bill...");
    try { await api(`/api/admin/files/${fid}/read-bill`, { method: "POST" }); setMsg("Bill read. Check the values below and apply."); load(); }
    catch (e: any) { setErr(e.message); setMsg(""); }
  };
  const applyBill = (x: any) => {
    const next = { ...ov };
    if (x.monthly_units) next.monthly_units = x.monthly_units;
    if (x.sanction_load_kw) next.sanction_load_kw = x.sanction_load_kw;
    if (x.phase) next.phase = x.phase;
    changeOv(next); setTab("review");
    setMsg("Bill values copied into the inputs. Press 'Save inputs' to keep them.");
  };

  if (err && !d) return <div className="err">{err}</div>;
  if (!d) return <p>Loading...</p>;
  const r = d.request, c = d.customer, s = d.site;
  const outputs = preview || d.analysis?.outputs;
  const canQuote = ["admin", "sales"].includes(role);
  return (
    <div>
      <div className="topbar">
        <div>
          <Link to="/admin" className="small">← Pipeline</Link>
          <h1 style={{ margin: "4px 0" }}>{r.reference} · {c.name}</h1>
          <span className="pill blue">{STAGE_LABEL[r.stage]}</span> <span className="muted small">received {fmtDate(r.created_at)}</span>
        </div>
        <div className="row" style={{ flex: "0 0 auto" }}>
          {canQuote && <button onClick={newQuote}>New quotation</button>}
          <a className="btn secondary" href={r.status_url} target="_blank" rel="noreferrer">Customer status page</a>
        </div>
      </div>
      {err && <div className="err">{err}</div>}
      {msg && <div className="ok">{msg}</div>}
      <div className="tabs">
        {["review", "diagrams", "quotations", "activity"].map((t) => <button key={t} className={tab === t ? "active" : ""} onClick={() => setTab(t)}>{t[0].toUpperCase() + t.slice(1)}</button>)}
      </div>

      {tab === "review" && (
        <>
          <div className="grid2">
            <div className="card">
              <h2>Customer & site</h2>
              <dl className="kv">
                <dt>Name</dt><dd>{c.name}</dd>
                <dt>Phone</dt><dd><a href={`tel:${c.phone}`}>{c.phone}</a> {c.phone_verified && <span className="pill green">OTP verified</span>}</dd>
                <dt>Email</dt><dd>{c.email || "-"}</dd>
                <dt>Language</dt><dd>{c.language === "ta" ? "Tamil" : "English"}</dd>
                <dt>Address</dt><dd>{s.address}<br />{s.district} {s.pincode}</dd>
                <dt>Building</dt><dd>{s.site_type}{s.floors != null && `, ${s.floors} floor(s)`}</dd>
                <dt>EB no. / tariff</dt><dd>{s.eb_consumer_no || "-"} / {s.tariff || "-"}</dd>
                <dt>Supply</dt><dd>{s.phase}-phase, sanction {s.sanction_load_kw ?? "?"} kW</dd>
                <dt>Consumption</dt><dd>{r.monthly_units ? `${r.monthly_units} units/month` : ""} {r.monthly_bill ? `${inr(r.monthly_bill)}/month` : ""}</dd>
                <dt>Roof</dt><dd>{s.roof_type}, {s.roof_area_m2 ?? "?"} m², {s.direction}, shade {s.shade}</dd>
                <dt>Goal</dt><dd>{r.goal} {r.backup_load_w ? `(${r.backup_load_w} W backup)` : ""} {r.budget_range && `· budget ${r.budget_range}`}</dd>
              </dl>
            </div>
            <div className="card">
              <h2>Photos & bill</h2>
              <div className="photos">
                {d.files.map((f: any) => (
                  <div key={f.id}>
                    {f.content_type.startsWith("image/") ? <a href={f.url} target="_blank" rel="noreferrer"><img src={f.url} alt={f.kind} /></a> : <a href={f.url} target="_blank" rel="noreferrer">PDF</a>}
                    <div className="small muted">{f.kind.replace("_", " ")}</div>
                    {f.kind === "eb_bill" && (
                      <div>
                        <button className="small secondary" onClick={() => readBill(f.id)}>Read bill (AI)</button>
                        {f.extracted && !f.extracted.error && (
                          <div className="small" style={{ marginTop: 4 }}>
                            {Object.entries(f.extracted.fields || {}).filter(([, v]) => v !== null).map(([k, v]) => <div key={k}>{k}: <strong>{String(v)}</strong></div>)}
                            <button className="small" onClick={() => applyBill(f.extracted.fields || {})}>Apply (staff confirm)</button>
                          </div>
                        )}
                        {f.extracted?.error && <div className="small err">{f.extracted.error}</div>}
                      </div>
                    )}
                  </div>
                ))}
                {d.files.length === 0 && <p className="muted">No uploads.</p>}
              </div>
              <h3 style={{ marginTop: 16 }}>Assignment & visit</h3>
              <div className="row">
                <div><label>Owner (sales)</label>
                  <select value={r.owner_user_id || ""} onChange={(e) => patch({ owner_user_id: Number(e.target.value) || 0 })}>
                    <option value="">-</option>{users.map((u) => <option key={u.id} value={u.id}>{u.name} ({u.role})</option>)}</select></div>
                <div><label>Engineer</label>
                  <select value={r.engineer_user_id || ""} onChange={(e) => patch({ engineer_user_id: Number(e.target.value) || 0 })}>
                    <option value="">-</option>{users.map((u) => <option key={u.id} value={u.id}>{u.name} ({u.role})</option>)}</select></div>
              </div>
              <div className="row">
                <div><label>Site visit {r.site_visit_at && <span className="muted">({fmtDate(r.site_visit_at)})</span>}</label>
                  <input type="datetime-local" value={visit} onChange={(e) => setVisit(e.target.value)} /></div>
                <button style={{ flex: "0 0 auto" }} disabled={!visit} onClick={() => patch({ site_visit_at: new Date(visit).toISOString() })}>Schedule</button>
              </div>
              <div className="row">
                <div><label>Stage</label>
                  <select value={r.stage} onChange={(e) => patch({ stage: e.target.value })}>
                    {Object.entries(STAGE_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="topbar">
              <h2 style={{ margin: 0 }}>Auto-analysis {preview && <span className="pill amber">preview, not saved</span>}</h2>
              <span className="muted small">{d.analysis && `run #${d.analysis.id} · ${fmtDate(d.analysis.created_at)} · engine ${d.analysis.engine_version}`}</span>
            </div>
            <AnalysisView o={outputs} />
          </div>

          <DesignNotes requestId={r.id} analysisId={d.analysis?.id} />

          <div className="card">
            <h2>Override inputs</h2>
            <p className="muted small">Change any input; outputs above recalculate immediately. Save to store a new analysis run (old runs are kept).</p>
            <OverrideForm values={ov} base={d.analysis?.inputs} onChange={changeOv} panels={panels} inverters={inverters} />
            <div className="row" style={{ marginTop: 12 }}>
              <button style={{ flex: "0 0 auto" }} onClick={saveOverrides}>Save inputs & re-analyse</button>
              <button className="secondary" style={{ flex: "0 0 auto" }} onClick={() => { setOv({}); changeOv({}); }}>Clear overrides</button>
            </div>
          </div>

          <div className="card">
            <h2>Notes</h2>
            <textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="Add a note for the team" />
            <button style={{ marginTop: 8 }} onClick={addNote}>Add note</button>
            {act?.activity.filter((a: any) => a.action === "note").map((a: any) => (
              <div key={a.id} style={{ borderTop: "1px solid var(--line)", padding: "8px 0" }}>
                <div className="small muted">{a.user} · {fmtDate(a.created_at)}</div>{a.detail.text}
              </div>
            ))}
          </div>
        </>
      )}

      {tab === "diagrams" && <Diagrams analysisId={d.analysis?.id} />}

      {tab === "quotations" && (
        <div className="card">
          <h2>Quotations</h2>
          {d.quotations.length === 0 && <p className="muted">No quotations yet.</p>}
          <table>
            <thead><tr><th>No.</th><th>Status</th><th className="num">Total</th><th>Created</th><th>Sent</th></tr></thead>
            <tbody>{d.quotations.map((q: any) => (
              <tr key={q.id} onClick={() => nav(`/admin/quotations/${q.id}`)} style={{ cursor: "pointer" }}>
                <td>#{q.number}</td><td><span className="pill">{q.status}</span></td><td className="num">{inr(q.grand_total)}</td>
                <td>{fmtDate(q.created_at)}</td><td>{fmtDate(q.sent_at)}</td></tr>))}</tbody>
          </table>
          {canQuote && <button style={{ marginTop: 10 }} onClick={newQuote}>New quotation from latest analysis</button>}
        </div>
      )}

      {tab === "activity" && act && (
        <div className="grid2">
          <div className="card">
            <h2>Activity log</h2>
            {act.activity.map((a: any) => (
              <div key={a.id} style={{ borderBottom: "1px solid var(--line)", padding: "6px 0" }}>
                <div className="small muted">{fmtDate(a.created_at)} · {a.actor}{a.user ? ` · ${a.user}` : ""}</div>
                <strong>{a.action.replace(/_/g, " ")}</strong>
                {Object.keys(a.detail || {}).length > 0 && <pre className="small" style={{ whiteSpace: "pre-wrap", margin: 0 }}>{JSON.stringify(a.detail, null, 1)}</pre>}
              </div>
            ))}
          </div>
          <div className="card">
            <h2>Emails</h2>
            {act.emails.map((e: any) => (
              <div key={e.id} style={{ borderBottom: "1px solid var(--line)", padding: "6px 0" }}>
                <strong>{e.template}</strong> → {e.to} <span className={`pill ${e.status === "sent" ? "green" : e.status === "queued" ? "" : "red"}`}>{e.status}</span>
                <div className="small muted">{fmtDate(e.created_at)} · attempts {e.attempts} · {e.provider_id || ""} {e.error || ""}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Diagrams({ analysisId }: { analysisId?: number }) {
  const [svgs, setSvgs] = useState<Record<string, string>>({});
  const [err, setErr] = useState("");
  useEffect(() => {
    if (!analysisId) return;
    for (const k of ["sld", "roof", "schedule"]) {
      api(`/api/admin/analysis/${analysisId}/diagram/${k}`).then((r) => setSvgs((s) => ({ ...s, [k]: r.svg }))).catch((e) => setErr(e.message));
    }
  }, [analysisId]);
  if (!analysisId) return <p className="muted">Run an analysis first.</p>;
  return (
    <div>
      {err && <div className="err">{err}</div>}
      {[["sld", "Single-line diagram"], ["roof", "Roof layout"], ["schedule", "Cable & protection schedule"]].map(([k, l]) => (
        <div className="card" key={k}>
          <div className="topbar"><h2 style={{ margin: 0 }}>{l}</h2>
            {svgs[k] && <a className="btn small secondary" download={`${k}-${analysisId}.svg`} href={`data:image/svg+xml;charset=utf-8,${encodeURIComponent(svgs[k])}`}>Download SVG</a>}</div>
          <div className="svgbox" dangerouslySetInnerHTML={{ __html: svgs[k] || "<p>Loading...</p>" }} />
        </div>
      ))}
    </div>
  );
}
