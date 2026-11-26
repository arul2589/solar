import { useState } from "react";
import { api } from "../../api";
import { useAdminI18n } from "../../adminI18n";
import { TwoFactor } from "./Misc";

// Every signed-in staff member (any role) can change their own password here.
export default function Account() {
  const { at } = useAdminI18n();
  const [f, setF] = useState({ current: "", next: "", again: "" });
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement>) => setF({ ...f, [k]: e.target.value });

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setMsg(""); setErr("");
    if (f.next.length < 8) return setErr(at("acc_short"));
    if (f.next !== f.again) return setErr(at("acc_mismatch"));
    setBusy(true);
    try {
      await api("/api/auth/change-password", { method: "POST", json: { current_password: f.current, new_password: f.next } });
      setF({ current: "", next: "", again: "" });
      setMsg(at("acc_changed"));
    } catch (e: any) { setErr(e.message); }
    finally { setBusy(false); }
  };

  return (
    <div>
      <h1>{at("acc_title")}</h1>
      <form className="card" onSubmit={save} style={{ maxWidth: 480 }}>
        <h2>{at("acc_change_pw")}</h2>
        <label>{at("acc_current")}</label>
        <input type="password" autoComplete="current-password" value={f.current} onChange={set("current")} required />
        <label>{at("acc_new")}</label>
        <input type="password" autoComplete="new-password" minLength={8} value={f.next} onChange={set("next")} required />
        <label>{at("acc_confirm")}</label>
        <input type="password" autoComplete="new-password" minLength={8} value={f.again} onChange={set("again")} required />
        {err && <div className="err">{err}</div>}
        {msg && <div className="ok">{msg}</div>}
        <button type="submit" disabled={busy} style={{ marginTop: 12 }}>{at("acc_save")}</button>
      </form>
      <TwoFactor />
    </div>
  );
}
