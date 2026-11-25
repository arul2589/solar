import { useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api, CUSTOMER_KEY } from "../../api";
import { Key, useI18n } from "../../i18n";

export default function CustomerLogin() {
  const { slug } = useParams();
  const [sp] = useSearchParams();
  const nav = useNavigate();
  const { t } = useI18n();
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [items, setItems] = useState<any[] | null>(null);

  const loadMine = () => api("/api/customer/requests").then(setItems).catch(() => { localStorage.removeItem(CUSTOMER_KEY); setItems(null); });

  useEffect(() => {
    const magic = sp.get("magic");
    if (magic) {
      api(`/api/public/${slug}/customer/session`, { method: "POST", json: { token: magic } })
        .then((r) => { localStorage.setItem(CUSTOMER_KEY, JSON.stringify(r)); nav(`/s/${slug}/login`, { replace: true }); loadMine(); })
        .catch((e) => setErr(e.message));
    } else if (localStorage.getItem(CUSTOMER_KEY)) {
      loadMine();
    }
  }, []);

  async function sendLink() {
    setErr(""); setMsg("");
    try {
      const r = await api(`/api/public/${slug}/customer/magic-link`, { method: "POST", json: { email } });
      setMsg(r.dev_link ? `Sent. (dev) ${r.dev_link}` : "Sent. Check your email.");
    } catch (e: any) { setErr(e.message); }
  }
  async function sendOtp() {
    setErr("");
    try {
      const r = await api(`/api/public/${slug}/otp/request`, { method: "POST", json: { phone, purpose: "login" } });
      setOtpSent(true);
      if (r.dev_code) setMsg(`dev code: ${r.dev_code}`);
    } catch (e: any) { setErr(e.message); }
  }
  async function otpLogin() {
    setErr("");
    try {
      const r = await api(`/api/public/${slug}/customer/otp-login`, { method: "POST", json: { phone, code } });
      localStorage.setItem(CUSTOMER_KEY, JSON.stringify(r));
      loadMine();
    } catch (e: any) { setErr(e.message); }
  }

  if (items) {
    return (
      <div>
        <div className="topbar"><h1>{t("my_requests")}</h1>
          <button className="secondary small" onClick={() => { localStorage.removeItem(CUSTOMER_KEY); setItems(null); }}>{t("logout")}</button></div>
        {items.map((r) => (
          <div className="card" key={r.reference}>
            <strong>{r.reference}</strong> <span className="pill">{t(r.status as Key)}</span>
            <p className="muted small">{r.address}</p>
            <Link to={`/s/${slug}/status/${r.reference}?t=${r.status_token}`}>{t("status_link")}</Link>
          </div>
        ))}
      </div>
    );
  }
  return (
    <div>
      <h1>{t("login_title")}</h1>
      {err && <div className="err">{err}</div>}
      {msg && <div className="ok" style={{ wordBreak: "break-all" }}>{msg}</div>}
      <div className="card">
        <h2>{t("login_email")}</h2>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
        <button style={{ marginTop: 10 }} onClick={sendLink} disabled={!email}>{t("send")}</button>
      </div>
      <div className="card">
        <h2>{t("login_phone")}</h2>
        <input value={phone} onChange={(e) => setPhone(e.target.value)} inputMode="tel" placeholder="98765 43210" />
        {!otpSent ? <button style={{ marginTop: 10 }} onClick={sendOtp} disabled={phone.replace(/\D/g, "").length < 10}>{t("send_otp")}</button> : (
          <div className="row" style={{ marginTop: 10 }}>
            <input value={code} onChange={(e) => setCode(e.target.value)} inputMode="numeric" maxLength={6} placeholder={t("otp")} />
            <button onClick={otpLogin} style={{ flex: "0 0 auto" }}>{t("verify")}</button>
          </div>
        )}
      </div>
    </div>
  );
}
