import { NavLink, Navigate, Outlet, useNavigate } from "react-router-dom";
import { STAFF_KEY, staffSession } from "../../api";
import { useAdminI18n, type AKey } from "../../adminI18n";

const LINKS: { to: string; label: AKey; roles: string[] }[] = [
  { to: "/admin", label: "nav_pipeline", roles: ["admin", "sales", "engineer", "normal"] },
  { to: "/admin/calculator", label: "nav_calculator", roles: ["admin", "sales", "engineer"] },
  { to: "/admin/projects", label: "nav_projects", roles: ["admin", "sales", "engineer", "technician"] },
  { to: "/admin/knowledge", label: "nav_knowledge", roles: ["admin", "sales", "engineer", "technician", "normal"] },
  { to: "/admin/catalogue", label: "nav_catalogue", roles: ["admin", "sales", "engineer"] },
  { to: "/admin/settings", label: "nav_settings", roles: ["admin", "sales", "engineer"] },
  { to: "/admin/users", label: "nav_users", roles: ["admin"] },
  { to: "/admin/emails", label: "nav_emails", roles: ["admin", "sales"] },
  { to: "/admin/platform", label: "nav_platform", roles: ["platform_owner"] },
];

export default function AdminLayout() {
  const s = staffSession();
  const nav = useNavigate();
  const { lang, setLang, at } = useAdminI18n();
  if (!s) return <Navigate to="/admin/login" replace />;
  const role = s.user.role;
  return (
    <div className="admin">
      <nav className="sidebar">
        <div className="brand">☀ {s.user.installer.name}</div>
        {LINKS.filter((l) => l.roles.includes(role)).map((l) => (
          <NavLink key={l.to} to={l.to} end={l.to === "/admin"}>{at(l.label)}</NavLink>
        ))}
        <div className="who">
          {s.user.name} · {role}
          <br />
          <a href="#" onClick={(e) => { e.preventDefault(); localStorage.removeItem(STAFF_KEY); nav("/admin/login"); }}>{at("sign_out")}</a>
          <div className="admin-lang">
            <button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")}>English</button>
            <button className={lang === "ta" ? "on" : ""} onClick={() => setLang("ta")}>தமிழ்</button>
          </div>
        </div>
      </nav>
      <div className="content">
        <Outlet />
      </div>
    </div>
  );
}

export function useRole() {
  return staffSession()?.user.role || "";
}
