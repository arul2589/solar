import { NavLink, Navigate, Outlet, useNavigate } from "react-router-dom";
import { STAFF_KEY, staffSession } from "../../api";

const LINKS: { to: string; label: string; roles: string[] }[] = [
  { to: "/admin", label: "Pipeline", roles: ["admin", "sales", "engineer", "normal"] },
  { to: "/admin/calculator", label: "Calculator", roles: ["admin", "sales", "engineer"] },
  { to: "/admin/projects", label: "Projects", roles: ["admin", "sales", "engineer", "technician"] },
  { to: "/admin/knowledge", label: "Knowledge (AI)", roles: ["admin", "sales", "engineer", "technician", "normal"] },
  { to: "/admin/catalogue", label: "Price list & catalogue", roles: ["admin", "sales", "engineer"] },
  { to: "/admin/settings", label: "Settings", roles: ["admin", "sales", "engineer"] },
  { to: "/admin/users", label: "Users", roles: ["admin"] },
  { to: "/admin/emails", label: "Email log", roles: ["admin", "sales"] },
  { to: "/admin/platform", label: "Installers", roles: ["platform_owner"] },
];

export default function AdminLayout() {
  const s = staffSession();
  const nav = useNavigate();
  if (!s) return <Navigate to="/admin/login" replace />;
  const role = s.user.role;
  return (
    <div className="admin">
      <nav className="sidebar">
        <div className="brand">☀ {s.user.installer.name}</div>
        {LINKS.filter((l) => l.roles.includes(role)).map((l) => (
          <NavLink key={l.to} to={l.to} end={l.to === "/admin"}>{l.label}</NavLink>
        ))}
        <div className="who">
          {s.user.name} · {role}
          <br />
          <a href="#" onClick={(e) => { e.preventDefault(); localStorage.removeItem(STAFF_KEY); nav("/admin/login"); }}>Sign out</a>
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
