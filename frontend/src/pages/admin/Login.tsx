import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, defaultSlug, STAFF_KEY } from "../../api";

export default function Login() {
  const nav = useNavigate();
  const [installer, setInstaller] = useState(localStorage.getItem("solar.lastInstaller") || defaultSlug());
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [needOtp, setNeedOtp] = useState(false);
  const [err, setErr] = useState("");

  async function submit(e: FormEvent) {
    e.preventDefault();
    setErr("");
    try {
      const r = await api("/api/auth/login", { method: "POST", auth: "none", json: { installer, email, password, otp: otp || null } });
      localStorage.setItem(STAFF_KEY, JSON.stringify(r));
      localStorage.setItem("solar.lastInstaller", installer);
      const role = r.user.role;
      nav(role === "platform_owner" ? "/admin/platform" : role === "technician" ? "/admin/projects" : "/admin");
    } catch (e: any) {
      if (e.message.includes("Two-factor")) setNeedOtp(true);
      setErr(e.message);
    }
  }

  return (
    <div style={{ maxWidth: 380, margin: "8vh auto", padding: 16 }}>
      <form className="card" onSubmit={submit}>
        <h1>Staff sign in</h1>
        <label>Installer</label>
        <input value={installer} onChange={(e) => setInstaller(e.target.value)} autoCapitalize="none" />
        <label>Email</label>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" />
        <label>Password</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" />
        {needOtp && (<><label>Two-factor code</label><input value={otp} onChange={(e) => setOtp(e.target.value)} inputMode="numeric" /></>)}
        {err && <div className="err">{err}</div>}
        <button type="submit" style={{ width: "100%", marginTop: 14 }}>Sign in</button>
      </form>
    </div>
  );
}
