// Small fetch wrapper. Staff and customer tokens live in localStorage under separate keys.
export const STAFF_KEY = "solar.staff";
export const CUSTOMER_KEY = "solar.customer";

export type StaffSession = {
  token: string;
  user: { id: number; name: string; email: string; role: string; installer: { id: number; slug: string; name: string; is_platform: boolean } };
};

export function staffSession(): StaffSession | null {
  try {
    return JSON.parse(localStorage.getItem(STAFF_KEY) || "null");
  } catch {
    return null;
  }
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function detailMessage(body: any): string {
  if (!body) return "Request failed";
  const d = body.detail ?? body;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map((e) => (e.loc ? `${e.loc[e.loc.length - 1]}: ${e.msg}` : e.msg || String(e))).join("; ");
  return JSON.stringify(d);
}

export async function api<T = any>(path: string, opts: RequestInit & { auth?: "staff" | "customer" | "none"; json?: any } = {}): Promise<T> {
  const headers: Record<string, string> = { ...(opts.headers as any) };
  const auth = opts.auth ?? (path.startsWith("/api/public") ? "none" : path.startsWith("/api/customer") ? "customer" : "staff");
  if (auth === "staff") {
    const s = staffSession();
    if (s) headers["Authorization"] = `Bearer ${s.token}`;
  } else if (auth === "customer") {
    const t = localStorage.getItem(CUSTOMER_KEY);
    if (t) headers["Authorization"] = `Bearer ${JSON.parse(t).token}`;
  }
  let body = opts.body;
  if (opts.json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.json);
  }
  const res = await fetch(path, { ...opts, headers, body });
  const text = await res.text();
  let parsed: any = null;
  try {
    parsed = text ? JSON.parse(text) : null;
  } catch {
    parsed = text;
  }
  if (!res.ok) {
    if (res.status === 401 && auth === "staff" && !path.startsWith("/api/auth/login")) {
      localStorage.removeItem(STAFF_KEY);
      if (!location.pathname.startsWith("/admin/login")) location.href = "/admin/login";
    }
    throw new ApiError(res.status, detailMessage(parsed));
  }
  return parsed as T;
}

export const inr = (v: any) => {
  if (v === null || v === undefined || v === "") return "-";
  const n = Number(v);
  return "₹" + n.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

export const inr0 = (v: any) => {
  if (v === null || v === undefined || v === "") return "-";
  return "₹" + Math.round(Number(v)).toLocaleString("en-IN");
};

export const fmtDate = (s?: string | null) => (s ? new Date(s).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" }) : "-");

export function defaultSlug(): string {
  // Subdomain tenant resolution ready for <installer>.<domain>; falls back to the configured default.
  const env = (import.meta as any).env?.VITE_DEFAULT_INSTALLER;
  return env || "demo";
}
