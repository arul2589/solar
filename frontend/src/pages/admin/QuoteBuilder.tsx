import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, fmtDate, inr, staffSession } from "../../api";
import { useRole } from "./AdminLayout";

const r2 = (n: number) => Math.round(n * 100) / 100;

export default function QuoteBuilder() {
  const { id } = useParams();
  const nav = useNavigate();
  const role = useRole();
  const [q, setQ] = useState<any>(null);
  const [lines, setLines] = useState<any[]>([]);
  const [texts, setTexts] = useState<any>({});
  const [prices, setPrices] = useState<any[]>([]);
  const [dirty, setDirty] = useState(false);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  const load = () => api(`/api/admin/quotations/${id}`).then((r) => {
    setQ(r); setLines(r.lines.map((l: any) => ({ ...l })));
    setTexts({ system_summary: r.system_summary, valid_until: r.valid_until, terms_text: r.terms_text, scope_text: r.scope_text, warranty_text: r.warranty_text, notes: r.notes });
    setDirty(false);
  }).catch((e) => setErr(e.message));
  useEffect(() => { load(); api("/api/admin/price-items").then(setPrices).catch(() => {}); }, [id]);

  const editable = q?.status === "draft" && ["admin", "sales"].includes(role);
  const showCost = ["admin", "sales"].includes(role);
  const setLine = (i: number, k: string, v: any) => { const n = [...lines]; n[i] = { ...n[i], [k]: v }; setLines(n); setDirty(true); };
  const move = (i: number, d: number) => { const n = [...lines]; const [x] = n.splice(i, 1); n.splice(i + d, 0, x); setLines(n); setDirty(true); };
  const addFromPrice = (pid: string) => {
    const p = prices.find((x) => String(x.id) === pid);
    if (!p) return;
    setLines([...lines, { code: p.code, description: p.name.replace(/\{.*?\}/g, "").trim() || p.code, details: p.details?.includes("{") ? "" : p.details, hsn: p.hsn, qty: "1", unit: p.unit, unit_price: p.unit_price, gst_pct: p.gst_pct, cost_price: p.cost_price }]);
    setDirty(true);
  };
  // client-side preview only; the server recomputes on save
  const calc = lines.reduce((acc, l) => {
    const amt = r2(Number(l.qty) * Number(l.unit_price)); const tax = r2(amt * Number(l.gst_pct) / 100);
    return { sub: acc.sub + amt, tax: acc.tax + tax };
  }, { sub: 0, tax: 0 });

  const save = async () => {
    setErr(""); setMsg(""); setBusy(true);
    try {
      const body = { ...texts, lines: lines.map((l) => ({ code: l.code || "", description: l.description, details: l.details || "", hsn: l.hsn || "", qty: Number(l.qty), unit: l.unit || "No", unit_price: Number(l.unit_price), gst_pct: Number(l.gst_pct), cost_price: l.cost_price === "" || l.cost_price == null ? null : Number(l.cost_price) })) };
      const r = await api(`/api/admin/quotations/${id}`, { method: "PUT", json: body });
      setQ(r); setLines(r.lines); setDirty(false); setMsg("Saved. Totals recalculated by the server.");
    } catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  };
  const openPdf = async (internal = false) => {
    setErr("");
    const s = staffSession();
    const res = await fetch(`/api/admin/quotations/${id}/pdf${internal ? "?internal=true" : ""}`, { headers: { Authorization: `Bearer ${s?.token}` } });
    if (!res.ok) { setErr(`PDF failed (${res.status})`); return; }
    const url = URL.createObjectURL(await res.blob());
    window.open(url, "_blank");
  };
  const [wa, setWa] = useState<{ number: string; url: string; text: string } | null>(null);
  const send = async () => {
    if (dirty) { setErr("Save changes before sending."); return; }
    const pref = q.request.contact_pref || "email";
    const via = [pref !== "whatsapp" && q.request.customer_email ? `email ${q.request.customer_email}` : "",
                 pref !== "email" && q.request.customer_whatsapp ? `WhatsApp ${q.request.customer_whatsapp}` : ""].filter(Boolean).join(" and ");
    if (!window.confirm(`Send quotation #${q.number} (${inr(q.grand_total)}) by ${via || "a link you share yourself"}?`)) return;
    setBusy(true); setErr(""); setWa(null);
    try {
      const r = await api(`/api/admin/quotations/${id}/send`, { method: "POST" });
      const parts = [r.email_status === "queued" ? "Email queued." : r.email_status === "not_requested" ? "Customer chose WhatsApp (no email sent)." : "No email on file."];
      if (r.whatsapp) parts.push("Press \"Send on WhatsApp\" to message the customer.");
      setMsg(`Sent. ${parts.join(" ")} Customer link: ${r.customer_url}`);
      setWa(r.whatsapp || null);
      load();
    } catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  };
  const revise = async () => {
    const r = await api(`/api/admin/quotations/${id}/revise`, { method: "POST" });
    nav(`/admin/quotations/${r.id}`);
  };

  if (!q) return <p>{err || "Loading..."}</p>;
  return (
    <div>
      <div className="topbar">
        <div>
          <Link className="small" to={`/admin/requests/${q.request.id}`}>← {q.request.reference} · {q.request.customer_name}</Link>
          <h1 style={{ margin: "4px 0" }}>Quotation #{q.number} <span className="pill">{q.status}</span></h1>
          <span className="muted small">Date {q.quote_date} · valid until {q.valid_until} · sent {fmtDate(q.sent_at)} · accepted {fmtDate(q.accepted_at)}</span>
        </div>
        <div className="row" style={{ flex: "0 0 auto" }}>
          <button className="secondary" onClick={() => openPdf(false)}>PDF preview</button>
          {showCost && <button className="secondary" onClick={() => openPdf(true)}>Internal estimate</button>}
          {editable && <button onClick={save} disabled={busy || !dirty}>Save</button>}
          {["admin", "sales"].includes(role) && ["draft", "sent"].includes(q.status) && <button onClick={send} disabled={busy}>{q.status === "sent" ? "Re-send" : "Send quotation"}</button>}
          {["admin", "sales"].includes(role) && q.status !== "draft" && <button className="secondary" onClick={revise}>Revise (new number)</button>}
        </div>
      </div>
      {err && <div className="err">{err}</div>}
      {msg && <div className="ok" style={{ wordBreak: "break-all" }}>{msg}</div>}
      {wa && (
        <div className="card wa-card">
          <div>
            <strong>WhatsApp {wa.number}</strong>
            <div className="small muted">Opens WhatsApp with this message ready; press Send there. Free — uses your own WhatsApp Business number.</div>
            <pre className="pre-wrap" style={{ marginTop: 8 }}>{wa.text}</pre>
          </div>
          <a className="btn wa-btn" href={wa.url} target="_blank" rel="noreferrer">Send on WhatsApp</a>
        </div>
      )}
      {!editable && q.status !== "draft" && <div className="note">This quotation is {q.status} and locked. Use Revise to make a new version.</div>}

      <div className="card">
        <label>System summary (shown in email and PDF)</label>
        <input value={texts.system_summary || ""} disabled={!editable} onChange={(e) => { setTexts({ ...texts, system_summary: e.target.value }); setDirty(true); }} />
        <div className="row">
          <div><label>Valid until</label><input type="date" value={texts.valid_until || ""} disabled={!editable} onChange={(e) => { setTexts({ ...texts, valid_until: e.target.value }); setDirty(true); }} /></div>
        </div>
      </div>

      <div className="card" style={{ padding: 0 }}>
        <div className="table-wrap inline-edit">
          <table>
            <thead><tr><th>#</th><th>Description / details</th><th>HSN</th><th className="num">Qty</th><th>Unit</th><th className="num">Rate ₹</th><th className="num">GST %</th>{showCost && <th className="num">Cost ₹</th>}<th className="num">Tax</th><th className="num">Total</th><th></th></tr></thead>
            <tbody>
              {lines.map((l, i) => {
                const amt = r2(Number(l.qty) * Number(l.unit_price)); const tax = r2(amt * Number(l.gst_pct) / 100);
                return (
                  <tr key={i}>
                    <td>{i + 1}</td>
                    <td style={{ minWidth: 280 }}>
                      <input value={l.description} disabled={!editable} onChange={(e) => setLine(i, "description", e.target.value)} />
                      <textarea style={{ minHeight: 34, marginTop: 4 }} value={l.details || ""} disabled={!editable} onChange={(e) => setLine(i, "details", e.target.value)} />
                    </td>
                    <td><input style={{ width: 90 }} value={l.hsn || ""} disabled={!editable} onChange={(e) => setLine(i, "hsn", e.target.value)} /></td>
                    <td><input style={{ width: 70 }} value={l.qty} disabled={!editable} onChange={(e) => setLine(i, "qty", e.target.value)} /></td>
                    <td><input style={{ width: 80 }} value={l.unit || ""} disabled={!editable} onChange={(e) => setLine(i, "unit", e.target.value)} /></td>
                    <td><input style={{ width: 95 }} value={l.unit_price} disabled={!editable} onChange={(e) => setLine(i, "unit_price", e.target.value)} /></td>
                    <td><input style={{ width: 60 }} value={l.gst_pct} disabled={!editable} onChange={(e) => setLine(i, "gst_pct", e.target.value)} /></td>
                    {showCost && <td><input style={{ width: 90 }} value={l.cost_price ?? ""} disabled={!editable} onChange={(e) => setLine(i, "cost_price", e.target.value)} /></td>}
                    <td className="num">{inr(tax)}</td>
                    <td className="num">{inr(amt + tax)}</td>
                    <td style={{ whiteSpace: "nowrap" }}>{editable && (<>
                      <button className="ghost" disabled={i === 0} onClick={() => move(i, -1)}>↑</button>
                      <button className="ghost" disabled={i === lines.length - 1} onClick={() => move(i, 1)}>↓</button>
                      <button className="ghost" onClick={() => { setLines(lines.filter((_, j) => j !== i)); setDirty(true); }}>✕</button></>)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {editable && (
          <div className="row" style={{ padding: 12 }}>
            <select onChange={(e) => { addFromPrice(e.target.value); e.target.value = ""; }} defaultValue="">
              <option value="">+ Add line from price list...</option>
              {prices.filter((p) => p.active).map((p) => <option key={p.id} value={p.id}>{p.code} - {p.name} ({inr(p.unit_price)})</option>)}
            </select>
            <button className="secondary" style={{ flex: "0 0 auto" }} onClick={() => { setLines([...lines, { description: "New item", qty: "1", unit: "No", unit_price: "0", gst_pct: "18" }]); setDirty(true); }}>+ Blank line</button>
          </div>
        )}
        <div style={{ padding: "8px 16px 16px", textAlign: "right" }}>
          {dirty && <div className="muted small">Unsaved preview: subtotal {inr(calc.sub)} · tax {inr(calc.tax)} · total {inr(calc.sub + calc.tax)}</div>}
          <div>Sub total <strong>{inr(q.subtotal)}</strong> · Tax <strong>{inr(q.tax)}</strong></div>
          <div style={{ fontSize: "1.3rem" }}>Grand total <strong>{inr(q.grand_total)}</strong></div>
          <div className="muted small">{q.in_words}</div>
          {q.margin && <div className="small">Cost {inr(q.cost_total)} · margin before tax {inr(q.margin)}</div>}
        </div>
      </div>

      <div className="grid2">
        {[["terms_text", "Terms & conditions"], ["scope_text", "Scope"], ["warranty_text", "Warranty"], ["notes", "Notes"]].map(([k, l]) => (
          <div className="card" key={k}><label>{l}</label>
            <textarea rows={8} value={texts[k] || ""} disabled={!editable} onChange={(e) => { setTexts({ ...texts, [k]: e.target.value }); setDirty(true); }} /></div>
        ))}
      </div>
    </div>
  );
}
