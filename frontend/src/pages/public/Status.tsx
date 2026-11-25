import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api, fmtDate } from "../../api";
import { Key, useI18n } from "../../i18n";

export default function Status() {
  const { slug, reference } = useParams();
  const [sp] = useSearchParams();
  const token = sp.get("t") || "";
  const { t } = useI18n();
  const [st, setSt] = useState<any>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api(`/api/public/${slug}/requests/${reference}?t=${encodeURIComponent(token)}`).then(setSt).catch((e) => setErr(e.message));
  }, [slug, reference, token]);

  if (err) return <div className="err">{err}</div>;
  if (!st) return <p className="muted">...</p>;
  return (
    <div className="card">
      <h1>{t("status_title")}</h1>
      <p>{t("reference")}: <strong>{st.reference}</strong> <span className="muted small">· {fmtDate(st.submitted_at)}</span></p>
      {st.closed ? <p className="pill">{t("closed")}</p> : (
        <ul className="timeline">
          {st.steps.map((s: any) => (
            <li key={s.key} className={`${s.done ? "done" : ""} ${s.current ? "current" : ""}`}>
              {t(s.key as Key)}
              {s.key === "site_visit" && st.site_visit_at && <span className="muted small"> · {fmtDate(st.site_visit_at)}</span>}
            </li>
          ))}
        </ul>
      )}
      {st.quotation_available && (
        <p><Link className="btn" to={`/s/${slug}/status/${reference}/quotation?t=${encodeURIComponent(token)}`}>{t("view_quote")}</Link></p>
      )}
    </div>
  );
}
