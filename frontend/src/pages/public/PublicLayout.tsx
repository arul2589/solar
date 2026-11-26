import { createContext, useContext, useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation, useParams } from "react-router-dom";
import Icon from "../../components/Icon";
import { content } from "../../content";
import { api } from "../../api";
import { useI18n } from "../../i18n";
import { site } from "../../siteContent";

export type InstallerInfo = {
  slug: string; name: string; phone?: string; email?: string; address?: string; logo_url?: string | null;
  languages: string[]; require_phone_otp: boolean; disclaimer_en: string; disclaimer_ta: string;
};

const Ctx = createContext<InstallerInfo | null>(null);
export const useInstaller = () => useContext(Ctx);

// Marketing pages use the full-width site layout; forms and status pages stay narrow.
const MARKETING = /^\/s\/[^/]+\/?(residential|commercial|industrial|products|calculator|how-it-works|projects)?\/?$/;
const ABOUT = /^\/s\/[^/]+\/about\/?$/;
// hover-to-open only for the desktop menu; on phones/tablets a tap toggles it
const canHover = () => window.matchMedia("(hover: hover) and (min-width: 1101px)").matches;

export default function PublicLayout() {
  const { slug } = useParams();
  const [info, setInfo] = useState<InstallerInfo | null>(null);
  const [err, setErr] = useState("");
  const [menu, setMenu] = useState(false);
  const [solOpen, setSolOpen] = useState(false);
  const { lang, setLang, t } = useI18n();
  const { pathname } = useLocation();
  const n = site[lang].nav;
  const f = site[lang].footer;
  const oldNav = content[lang].nav;
  const marketing = MARKETING.test(pathname);
  const base = `/s/${slug}`;

  useEffect(() => {
    api<InstallerInfo>(`/api/public/${slug}`).then((i) => {
      setInfo(i);
      document.title = i.name;
    }).catch((e) => setErr(e.message));
  }, [slug]);

  // close menus and go to the top on navigation
  useEffect(() => {
    setMenu(false);
    setSolOpen(false);
    window.scrollTo(0, 0);
  }, [pathname]);

  const solutions = [
    { to: "residential", label: n.residential, icon: "home" },
    { to: "commercial", label: n.commercial, icon: "building" },
    { to: "industrial", label: n.industrial, icon: "factory" },
    { to: "products", label: n.products, icon: "battery" },
  ];
  const solActive = solutions.some((s) => pathname.startsWith(`${base}/${s.to}`));
  const tel = info?.phone?.replace(/\s/g, "");

  return (
    <div className="site-root">
      <header className="site-header">
        <div className="site-header-inner">
          <Link to={base} className="brand">
            {info?.logo_url ? <img src={info.logo_url} alt="" /> : <span className="brand-sun"><Icon name="sun" size={26} /></span>}
            <span className="brand-name">{info?.name || ""}</span>
          </Link>

          <button className="menu-btn" aria-expanded={menu} aria-label={n.menu} onClick={() => setMenu(!menu)}>
            <Icon name={menu ? "close" : "menu"} />
          </button>

          <nav className={`site-nav${menu ? " open" : ""}`} aria-label="Main">
            <NavLink end to={base}>{oldNav.home}</NavLink>
            <div className={`dd${solOpen ? " open" : ""}`} onMouseLeave={() => { if (canHover()) setSolOpen(false); }}>
              <button className={`dd-btn${solActive ? " active" : ""}`} aria-expanded={solOpen}
                onClick={() => setSolOpen(!solOpen)} onMouseEnter={() => { if (canHover()) setSolOpen(true); }}>
                {n.solutions} <Icon name="chevron" size={16} />
              </button>
              <div className="dd-menu">
                {solutions.map((s) => (
                  <NavLink key={s.to} to={`${base}/${s.to}`}><Icon name={s.icon} size={18} /> {s.label}</NavLink>
                ))}
              </div>
            </div>
            <NavLink to={`${base}/calculator`}>{n.calculator}</NavLink>
            <NavLink to={`${base}/how-it-works`}>{n.how}</NavLink>
            <NavLink to={`${base}/projects`}>{n.projects}</NavLink>
            <NavLink to={`${base}/about`}>{n.about}</NavLink>
            <div className="nav-extra">
              {tel && <a className="phone-pill" href={`tel:${tel}`}><Icon name="phone" size={16} /> {info?.phone}</a>}
              <Link className="btn btn-sun" to={`${base}/request`}>{n.quote}</Link>
              <div className="lang-switch">
                <button className={lang === "en" ? "active" : ""} onClick={() => setLang("en")}>EN</button>
                <button className={lang === "ta" ? "active" : ""} onClick={() => setLang("ta")}>தமிழ்</button>
              </div>
            </div>
          </nav>
        </div>
      </header>

      <main className={marketing ? "site-main" : `pub-main${ABOUT.test(pathname) ? " wide" : ""}`}>
        {err && <div className="err">{err}</div>}
        {info && (
          <Ctx.Provider value={info}>
            <Outlet />
          </Ctx.Provider>
        )}
      </main>

      {info && (
        <footer className="site-footer">
          <div className="site-footer-inner">
            <div>
              <div className="brand footer-brand">
                <span className="brand-sun"><Icon name="sun" size={24} /></span>
                <span className="brand-name">{info.name}</span>
              </div>
              <p>{f.tagline}</p>
            </div>
            <div>
              <h4>{n.solutions}</h4>
              {solutions.map((s) => <Link key={s.to} to={`${base}/${s.to}`}>{s.label}</Link>)}
            </div>
            <div>
              <h4>{f.explore}</h4>
              <Link to={`${base}/calculator`}>{n.calculator}</Link>
              <Link to={`${base}/how-it-works`}>{n.how}</Link>
              <Link to={`${base}/projects`}>{n.projects}</Link>
              <Link to={`${base}/about`}>{n.about}</Link>
              <Link to={`${base}/login`}>{t("my_requests")}</Link>
            </div>
            <div>
              <h4>{f.contact}</h4>
              {info.address && <p className="f-line"><Icon name="pin" size={16} /> <span>{info.address}</span></p>}
              {tel && <a className="f-line" href={`tel:${tel}`}><Icon name="phone" size={16} /> {info.phone}</a>}
              {info.email && <a className="f-line" href={`mailto:${info.email}`}><Icon name="doc" size={16} /> {info.email}</a>}
              <Link className="btn btn-sun" style={{ marginTop: 10 }} to={`${base}/request`}>{n.quote}</Link>
            </div>
          </div>
          <div className="site-footer-bottom">© {new Date().getFullYear()} {info.name}. {f.rights}</div>
        </footer>
      )}
    </div>
  );
}
