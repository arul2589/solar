import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, fmtDate } from "../../api";

export const STAGE_LABEL: Record<string, string> = {
  new: "New", analysed: "Analysed", quoted: "Quoted", site_visit: "Site visit", accepted: "Accepted",
  installation: "Installation", net_metering: "Net metering", completed: "Completed", lost: "Lost", on_hold: "On hold",
};

export default function Pipeline() {
  const nav = useNavigate();
  const [data, setData] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [view, setView] = useState<"kanban" | "list">((localStorage.getItem("solar.pipelineView") as any) || "kanban");
  const [flt, setFlt] = useState<any>({ stage: "", owner: "", district: "", kw_min: "", kw_max: "", date_from: "", date_to: "", q: "" });
  const [err, setErr] = useState("");

  const load = () => {
    const qs = new URLSearchParams(Object.entries(flt).filter(([, v]) => v !== "") as any).toString();
    api(`/api/admin/requests?${qs}`).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, []);
  useEffect(() => { api("/api/admin/users").then(setUsers).catch(() => {}); }, []);
  const setV = (v: "kanban" | "list") => { setView(v); localStorage.setItem("solar.pipelineView", v); };
  const set = (k: string) => (e: any) => setFlt({ ...flt, [k]: e.target.value });

  const items: any[] = data?.items || [];
  const uname = (id: number) => users.find((u) => u.id === id)?.name || "";
  return (
    <div>
      <div className="topbar">
        <h1>Request pipeline</h1>
        <div className="row" style={{ flex: "0 0 auto" }}>
          <button className={view === "kanban" ? "" : "secondary"} onClick={() => setV("kanban")}>Kanban</button>
          <button className={view === "list" ? "" : "secondary"} onClick={() => setV("list")}>List</button>
        </div>
      </div>
      <div className="card filters">
        <div className="row">
          <div><label>Search</label><input value={flt.q} onChange={set("q")} placeholder="Ref, name, phone" /></div>
          <div><label>Stage</label>
            <select value={flt.stage} onChange={set("stage")}><option value="">All</option>
              {Object.entries(STAGE_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></div>
          <div><label>Owner</label>
            <select value={flt.owner} onChange={set("owner")}><option value="">Anyone</option>
              {users.map((u) => <option key={u.id} value={u.id}>{u.name}</option>)}</select></div>
          <div><label>District</label><input value={flt.district} onChange={set("district")} /></div>
          <div><label>kW from</label><input value={flt.kw_min} onChange={set("kw_min")} inputMode="decimal" /></div>
          <div><label>kW to</label><input value={flt.kw_max} onChange={set("kw_max")} inputMode="decimal" /></div>
          <div><label>From</label><input type="date" value={flt.date_from} onChange={set("date_from")} /></div>
          <div><label>To</label><input type="date" value={flt.date_to} onChange={set("date_to")} /></div>
          <button style={{ flex: "0 0 auto" }} onClick={load}>Filter</button>
        </div>
      </div>
      {err && <div className="err">{err}</div>}
      {view === "kanban" ? (
        <div className="kanban">
          {(data?.stages || []).map((s: string) => {
            const col = items.filter((i) => i.stage === s);
            return (
              <div className="kcol" key={s}>
                <h4>{STAGE_LABEL[s]} <span>{col.length}</span></h4>
                {col.map((i) => (
                  <div className="kcard" key={i.id} onClick={() => nav(`/admin/requests/${i.id}`)}>
                    <strong>{i.reference}</strong> {i.warnings > 0 && <span className="pill amber">⚠ {i.warnings}</span>}
                    <div>{i.customer_name}</div>
                    <div className="muted small">{i.district || "-"} · {i.kw ? `${i.kw} kWp` : "-"} · {i.phase}-ph</div>
                    {i.owner_user_id && <div className="muted small">Owner: {uname(i.owner_user_id)}</div>}
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="table-wrap card" style={{ padding: 0 }}>
          <table>
            <thead><tr><th>Ref</th><th>Customer</th><th>Phone</th><th>District</th><th>Type</th><th className="num">kWp</th><th>Stage</th><th>Owner</th><th>Received</th></tr></thead>
            <tbody>
              {items.map((i) => (
                <tr key={i.id} onClick={() => nav(`/admin/requests/${i.id}`)} style={{ cursor: "pointer" }}>
                  <td><strong>{i.reference}</strong></td><td>{i.customer_name}</td><td>{i.phone_masked}</td>
                  <td>{i.district}</td><td>{i.site_type} · {i.phase}-ph</td><td className="num">{i.kw ?? "-"}</td>
                  <td><span className="pill">{STAGE_LABEL[i.stage]}</span></td><td>{uname(i.owner_user_id)}</td>
                  <td className="small">{fmtDate(i.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
