import { createContext, useContext, useEffect, useState } from "react";
import { Link, Outlet, useParams } from "react-router-dom";
import { api } from "../../api";
import { useI18n } from "../../i18n";

export type InstallerInfo = {
  slug: string; name: string; phone?: string; email?: string; address?: string; logo_url?: string | null;
  languages: string[]; require_phone_otp: boolean; disclaimer_en: string; disclaimer_ta: string;
};

const Ctx = createContext<InstallerInfo | null>(null);
export const useInstaller = () => useContext(Ctx);

export default function PublicLayout() {
  const { slug } = useParams();
  const [info, setInfo] = useState<InstallerInfo | null>(null);
  const [err, setErr] = useState("");
  const { lang, setLang, t } = useI18n();

  useEffect(() => {
    api<InstallerInfo>(`/api/public/${slug}`).then((i) => {
      setInfo(i);
      document.title = i.name;
    }).catch((e) => setErr(e.message));
  }, [slug]);

  return (
    <>
      <header className="pub-header">
        <div className="inner">
          <Link to={`/s/${slug}`} style={{ display: "flex", alignItems: "center", gap: 10 }}>
            {info?.logo_url && <img src={info.logo_url} alt="" />}
            <span>{info?.name || ""}</span>
          </Link>
          <div className="lang-switch row" style={{ flex: "0 0 auto", gap: 6 }}>
            <button className={lang === "en" ? "active" : ""} onClick={() => setLang("en")}>English</button>
            <button className={lang === "ta" ? "active" : ""} onClick={() => setLang("ta")}>தமிழ்</button>
          </div>
        </div>
      </header>
      <main className="pub-main">
        {err && <div className="err">{err}</div>}
        {info && (
          <Ctx.Provider value={info}>
            <Outlet />
          </Ctx.Provider>
        )}
        {info && (
          <footer className="muted small" style={{ marginTop: 40, textAlign: "center" }}>
            {info.name} {info.phone && <>· {info.phone}</>} {info.email && <>· {info.email}</>}
            <br />
            <Link to={`/s/${slug}/login`}>{t("my_requests")}</Link>
          </footer>
        )}
      </main>
    </>
  );
}
