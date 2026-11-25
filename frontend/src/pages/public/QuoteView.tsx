import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { api, inr } from "../../api";
import { useI18n } from "../../i18n";

// Works with the emailed link (/q/:token) or the status-page link (/status/:reference/quotation?t=...)
export default function QuoteView() {
  const { slug, token, reference } = useParams();
  const [sp] = useSearchParams();
  const t0 = sp.get("t") || "";
  const { t } = useI18n();
  const base = token ? `/api/public/${slug}/quotations/${token}` : `/api/public/${slug}/requests/${reference}/quotation`;
  const qsuf = token ? "" : `?t=${encodeURIComponent(t0)}`;
  const [q, setQ] = useState<any>(null);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [asking, setAsking] = useState(false);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);

  const load = () => api(base + qsuf).then(setQ).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, [base]);

  const accept = async () => {
    if (!window.confirm(t("accept") + "?")) return;
    setBusy(true); setErr("");
    try { await api(`${base}/accept${qsuf}`, { method: "POST" }); setMsg(t("accepted_msg")); load(); }
    catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  };
  const ask = async () => {
    setBusy(true); setErr("");
    try { await api(`${base}/question${qsuf}`, { method: "POST", json: { message: question } }); setMsg(t("question_sent")); setAsking(false); setQuestion(""); }
    catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  };

  if (err && !q) return <div className="err">{err}</div>;
  if (!q) return <p className="muted">...</p>;
  return (
    <div>
      <div className="card">
        <h1>{t("quote_title")} #{q.number}</h1>
        <p><strong>{q.system_summary}</strong></p>
        <p className="muted small">{q.customer_name} · {q.reference} · {q.quote_date} · {t("valid_until")} {q.valid_until}</p>
        {q.status === "accepted" && <div className="ok">{t("accepted_msg")}</div>}
        {q.status === "superseded" && <div className="note">A newer quotation has replaced this one.</div>}
        {q.expired && <div className="note">This quotation has expired. Please ask us for a fresh quotation.</div>}
        {msg && q.status !== "accepted" && <div className="ok">{msg}</div>}
        {err && <div className="err">{err}</div>}
        <div className="row" style={{ marginTop: 10 }}>
          <a className="btn secondary" href={`${base}/pdf${qsuf}`} target="_blank" rel="noreferrer">{t("download_pdf")}</a>
          {q.status === "sent" && !q.expired && <button onClick={accept} disabled={busy}>{t("accept")}</button>}
          {q.status !== "superseded" && <button className="secondary" onClick={() => setAsking(!asking)}>{t("ask")}</button>}
        </div>
        {asking && (
          <div style={{ marginTop: 10 }}>
            <textarea value={question} onChange={(e) => setQuestion(e.target.value)} />
            <button style={{ marginTop: 6 }} onClick={ask} disabled={busy || question.trim().length < 2}>{t("send")}</button>
          </div>
        )}
      </div>
      <div className="card" style={{ padding: 0 }}>
        <div className="table-wrap">
          <table>
            <thead><tr><th>#</th><th>Item</th><th className="num">Qty</th><th className="num">Rate</th><th className="num">GST</th><th className="num">Total</th></tr></thead>
            <tbody>{q.lines.map((l: any, i: number) => (
              <tr key={i}><td>{i + 1}</td><td><strong>{l.description}</strong>{l.details && <div className="muted small" style={{ whiteSpace: "pre-line" }}>{l.details}</div>}</td>
                <td className="num">{Number(l.qty)} {l.unit}</td><td className="num">{inr(l.unit_price)}</td><td className="num">{Number(l.gst_pct)}%</td><td className="num">{inr(l.total)}</td></tr>
            ))}</tbody>
          </table>
        </div>
        <div style={{ padding: 16, textAlign: "right" }}>
          <div>Sub total {inr(q.subtotal)} · Tax {inr(q.tax)}</div>
          <div style={{ fontSize: "1.3rem" }}><strong>{inr(q.grand_total)}</strong></div>
          <div className="muted small">{q.in_words}</div>
        </div>
      </div>
      <div className="note">{q.disclaimer}</div>
      <div className="card"><h3>Terms</h3><div className="small" style={{ whiteSpace: "pre-line" }}>{q.terms_text}</div>
        <h3 style={{ marginTop: 12 }}>Scope</h3><div className="small" style={{ whiteSpace: "pre-line" }}>{q.scope_text}</div>
        <h3 style={{ marginTop: 12 }}>Warranty</h3><div className="small" style={{ whiteSpace: "pre-line" }}>{q.warranty_text}</div></div>
    </div>
  );
}
