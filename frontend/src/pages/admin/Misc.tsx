import { useEffect, useRef, useState } from "react";
import { api, fmtDate } from "../../api";
import { AnalysisView, cleanOverrides, OverrideForm } from "../../components/Analysis";

export function Users() {
  const [users, setUsers] = useState<any[]>([]);
  const [f, setF] = useState<any>({ email: "", name: "", role: "sales", phone: "", password: "", active: true });
  const [edit, setEdit] = useState<any>(null);
  const [err, setErr] = useState("");
  const load = () => api("/api/admin/users").then(setUsers).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);
  const create = async () => {
    setErr("");
    try { await api("/api/admin/users", { method: "POST", json: { ...f, phone: f.phone || null } }); setF({ ...f, email: "", name: "", password: "" }); load(); }
    catch (e: any) { setErr(e.message); }
  };
  const save = async () => {
    setErr("");
    try { await api(`/api/admin/users/${edit.id}`, { method: "PUT", json: { ...edit, password: edit.password || null } }); setEdit(null); load(); }
    catch (e: any) { setErr(e.message); }
  };
  const roles = ["admin", "sales", "engineer", "technician"];
  return (
    <div>
      <h1>Users & roles</h1>
      {err && <div className="err">{err}</div>}
      <div className="card table-wrap" style={{ padding: 0 }}>
        <table>
          <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Phone</th><th>2FA</th><th>Active</th><th></th></tr></thead>
          <tbody>{users.map((u) => edit?.id === u.id ? (
            <tr key={u.id} className="inline-edit">
              <td><input value={edit.name} onChange={(e) => setEdit({ ...edit, name: e.target.value })} /></td>
              <td><input value={edit.email} onChange={(e) => setEdit({ ...edit, email: e.target.value })} /></td>
              <td><select value={edit.role} onChange={(e) => setEdit({ ...edit, role: e.target.value })}>{roles.map((r) => <option key={r}>{r}</option>)}</select></td>
              <td><input value={edit.phone || ""} onChange={(e) => setEdit({ ...edit, phone: e.target.value })} /></td>
              <td><input placeholder="new password" type="password" value={edit.password || ""} onChange={(e) => setEdit({ ...edit, password: e.target.value })} /></td>
              <td><input type="checkbox" checked={edit.active} onChange={(e) => setEdit({ ...edit, active: e.target.checked })} /></td>
              <td><button className="small" onClick={save}>Save</button> <button className="ghost" onClick={() => setEdit(null)}>Cancel</button></td>
            </tr>) : (
            <tr key={u.id}><td>{u.name}</td><td>{u.email}</td><td>{u.role}</td><td>{u.phone}</td><td>{u.two_factor ? "on" : "-"}</td><td>{u.active ? "yes" : "no"}</td>
              <td><button className="small secondary" onClick={() => setEdit({ ...u, password: "" })}>Edit</button></td></tr>))}</tbody>
        </table>
      </div>
      <div className="card">
        <h2>Add user</h2>
        <div className="row">
          <div><label>Name</label><input value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></div>
          <div><label>Email</label><input value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /></div>
          <div><label>Role</label><select value={f.role} onChange={(e) => setF({ ...f, role: e.target.value })}>{roles.map((r) => <option key={r}>{r}</option>)}</select></div>
          <div><label>Phone</label><input value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} /></div>
          <div><label>Password (min 8)</label><input type="password" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} /></div>
          <button style={{ flex: "0 0 auto" }} onClick={create}>Add</button>
        </div>
      </div>
      <TwoFactor />
    </div>
  );
}

function TwoFactor() {
  const [setup, setSetup] = useState<any>(null);
  const [code, setCode] = useState("");
  const [msg, setMsg] = useState("");
  return (
    <div className="card">
      <h2>Two-factor sign-in (optional, for your account)</h2>
      {!setup ? <button className="secondary" onClick={() => api("/api/auth/2fa/setup", { method: "POST" }).then(setSetup)}>Set up authenticator app</button> : (
        <div>
          <p className="small">Add this secret to Google Authenticator / Authy: <code>{setup.secret}</code></p>
          <div className="row"><input value={code} onChange={(e) => setCode(e.target.value)} placeholder="6-digit code" />
            <button style={{ flex: "0 0 auto" }} onClick={() => api("/api/auth/2fa/enable", { method: "POST", json: { secret: setup.secret, code } }).then(() => setMsg("2FA enabled.")).catch((e) => setMsg(e.message))}>Enable</button></div>
        </div>
      )}
      {msg && <p>{msg}</p>}
    </div>
  );
}

export function Emails() {
  const [rows, setRows] = useState<any[]>([]);
  const load = () => api("/api/admin/emails").then(setRows);
  useEffect(() => { load(); }, []);
  return (
    <div>
      <h1>Email log</h1>
      <div className="card" style={{ padding: 0 }}>
        <div className="table-wrap"><table>
          <thead><tr><th>Time</th><th>To</th><th>Template</th><th>Subject</th><th>Status</th><th>Attempts</th><th>Provider id</th><th></th></tr></thead>
          <tbody>{rows.map((e) => (
            <tr key={e.id}><td className="small">{fmtDate(e.created_at)}</td><td>{e.to}</td><td>{e.template} ({e.language})</td><td>{e.subject}</td>
              <td><span className={`pill ${e.status === "sent" ? "green" : e.status === "queued" ? "" : "red"}`}>{e.status}</span>{e.error && <div className="small err">{e.error}</div>}</td>
              <td>{e.attempts}</td><td className="small">{e.provider} {e.provider_id}</td>
              <td>{e.status !== "sent" && <button className="small secondary" onClick={() => api(`/api/admin/emails/${e.id}/retry`, { method: "POST" }).then(load)}>Retry</button>}</td></tr>))}</tbody>
        </table></div>
      </div>
    </div>
  );
}

export function Calculator() {
  const [ov, setOv] = useState<any>({ monthly_units: 450, phase: 1 });
  const [out, setOut] = useState<any>(null);
  const [panels, setPanels] = useState<any[]>([]);
  const [inverters, setInverters] = useState<any[]>([]);
  const timer = useRef<any>(null);
  const run = (v: any) => {
    clearTimeout(timer.current);
    timer.current = setTimeout(() => api("/api/admin/analyse", { method: "POST", json: { overrides: cleanOverrides(v) } }).then((r) => setOut(r.outputs)), 300);
  };
  useEffect(() => {
    run(ov);
    api("/api/admin/panels").then(setPanels); api("/api/admin/inverters").then(setInverters);
  }, []);
  return (
    <div>
      <h1>Calculator</h1>
      <p className="muted">Quick sizing for phone or walk-in enquiries. Nothing is saved.</p>
      <div className="card"><OverrideForm values={ov} base={{}} onChange={(v) => { setOv(v); run(v); }} panels={panels} inverters={inverters} /></div>
      <div className="card"><AnalysisView o={out} /></div>
    </div>
  );
}

export function Platform() {
  const [rows, setRows] = useState<any[]>([]);
  const [f, setF] = useState<any>({ slug: "", name: "", admin_email: "", admin_password: "" });
  const [err, setErr] = useState("");
  const load = () => api("/api/platform/installers").then(setRows).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);
  return (
    <div>
      <h1>Installers (tenants)</h1>
      {err && <div className="err">{err}</div>}
      <div className="card table-wrap" style={{ padding: 0 }}>
        <table><thead><tr><th>Slug</th><th>Name</th><th>Status</th><th>Requests</th><th>Created</th><th></th></tr></thead>
          <tbody>{rows.map((i) => (
            <tr key={i.id}><td>{i.slug}</td><td>{i.name}</td><td>{i.status}</td><td>{i.requests}</td><td>{fmtDate(i.created_at)}</td>
              <td><button className="small secondary" onClick={() => api(`/api/platform/installers/${i.id}/status`, { method: "PUT", json: { status: i.status === "active" ? "suspended" : "active" } }).then(load)}>{i.status === "active" ? "Suspend" : "Activate"}</button></td></tr>))}</tbody></table>
      </div>
      <div className="card">
        <h2>New installer</h2>
        <div className="row">
          {[["slug", "Slug (subdomain)"], ["name", "Company name"], ["admin_email", "Admin email"], ["admin_password", "Admin password"]].map(([k, l]) => (
            <div key={k}><label>{l}</label><input type={k.includes("password") ? "password" : "text"} value={f[k]} onChange={(e) => setF({ ...f, [k]: e.target.value })} /></div>
          ))}
          <button style={{ flex: "0 0 auto" }} onClick={() => api("/api/platform/installers", { method: "POST", json: f }).then(() => { setF({ slug: "", name: "", admin_email: "", admin_password: "" }); load(); }).catch((e) => setErr(e.message))}>Create</button>
        </div>
      </div>
    </div>
  );
}
