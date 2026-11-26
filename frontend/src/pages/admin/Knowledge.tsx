// Admin: knowledge base (RAG). Upload reference documents, watch indexing, ask cited questions.
import { Fragment, useCallback, useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { api, fmtDate, STAFF_KEY } from "../../api";
import { useRole } from "./AdminLayout";

export type Source = { n: number; document_id: number; title: string; page: number; score: number; snippet: string };
type Doc = {
  id: number; title: string; filename: string; content_type: string; size: number; status: string; error?: string | null;
  pages: number; vision_pages: number; chunk_count: number; created_at: string; updated_at?: string | null;
};
type Status = { configured: boolean; chat_model: string; embed_model: string; documents: Record<string, number>; chunks: number };

const STATUS_PILL: Record<string, string> = { ready: "green", pending: "amber", processing: "blue", error: "red" };

/** Open a stored document (auth header needed, so fetch as a blob), jumping to the page for PDFs. */
export async function openDocument(id: number, page?: number) {
  const t = JSON.parse(localStorage.getItem(STAFF_KEY) || "null")?.token;
  const w = window.open("", "_blank");
  const res = await fetch(`/api/admin/kb/documents/${id}/file`, { headers: t ? { Authorization: `Bearer ${t}` } : {} });
  if (!res.ok) { w?.close(); alert("Could not open the document"); return; }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob) + (blob.type === "application/pdf" && page ? `#page=${page}` : "");
  if (w) w.location.href = url; else window.open(url, "_blank");
}

/** Turn LaTeX-style formulas into readable plain text (models sometimes ignore the instruction). */
export function plainMath(text: string): string {
  let t = text.replace(/\\\[|\\\]|\\\(|\\\)/g, "").replace(/\$\$/g, "");
  for (let i = 0; i < 4; i++) {
    t = t.replace(/\\(?:d|t)?frac\{([^{}]*)\}\{([^{}]*)\}/g, "($1) / ($2)")
         .replace(/\\(?:text|mathrm|mathbf|textbf|operatorname)\{([^{}]*)\}/g, "$1");
  }
  return t.replace(/\\times/g, "×").replace(/\\cdot/g, "·").replace(/\\approx/g, "≈").replace(/\\le(q)?/g, "≤")
    .replace(/\\ge(q)?/g, "≥").replace(/\\%/g, "%").replace(/\\,|\\;|\\!/g, " ").replace(/\\([a-zA-Z]+)/g, "$1")
    .replace(/[{}]/g, "").replace(/ {2,}/g, " ");
}

/** Minimal, safe renderer for model answers: headings, bullets, **bold** and [n] citations. */
export function AnswerText({ text, sources }: { text: string; sources: Source[] }) {
  const byN = new Map(sources.map((s) => [s.n, s]));
  const inline = (line: string): ReactNode[] =>
    line.split(/(\[\d+(?:\s*,\s*\d+)*\]|\*\*[^*]+\*\*)/g).map((part, i) => {
      const cite = part.match(/^\[(\d+(?:\s*,\s*\d+)*)\]$/);
      if (cite) {
        return (
          <Fragment key={i}>
            {cite[1].split(/\s*,\s*/).map((n) => {
              const s = byN.get(Number(n));
              return (
                <sup key={n}>
                  <a href="#" className="cite" title={s ? `${s.title}, page ${s.page}` : ""}
                    onClick={(e) => { e.preventDefault(); if (s) openDocument(s.document_id, s.page); }}>[{n}]</a>
                </sup>
              );
            })}
          </Fragment>
        );
      }
      if (/^\*\*[^*]+\*\*$/.test(part)) return <strong key={i}>{part.slice(2, -2)}</strong>;
      return <Fragment key={i}>{part}</Fragment>;
    });
  const out: ReactNode[] = [];
  let list: ReactNode[] = [];
  const flush = () => { if (list.length) { out.push(<ul key={`u${out.length}`}>{list}</ul>); list = []; } };
  plainMath(text).split("\n").forEach((raw, i) => {
    const line = raw.trimEnd();
    const bullet = line.match(/^\s*(?:[-*•]|\d+[.)])\s+(.*)$/);
    const head = line.match(/^#{1,4}\s+(.*)$/);
    if (bullet) { list.push(<li key={i}>{inline(bullet[1])}</li>); return; }
    flush();
    if (head) out.push(<h4 key={i}>{inline(head[1])}</h4>);
    else if (line.trim()) out.push(<p key={i}>{inline(line)}</p>);
  });
  flush();
  return <div className="answer">{out}</div>;
}

export function SourceList({ sources }: { sources: Source[] }) {
  if (!sources.length) return null;
  return (
    <details className="sources" open>
      <summary>Sources ({sources.length})</summary>
      <ol>
        {sources.map((s) => (
          <li key={s.n} value={s.n}>
            <a href="#" onClick={(e) => { e.preventDefault(); openDocument(s.document_id, s.page); }}>{s.title}</a>
            <span className="muted small"> · page {s.page}</span>
            <div className="muted small snippet">{s.snippet}</div>
          </li>
        ))}
      </ol>
    </details>
  );
}

export default function Knowledge() {
  const role = useRole();
  const canEdit = ["admin", "engineer"].includes(role);
  const [docs, setDocs] = useState<Doc[]>([]);
  const [st, setSt] = useState<Status | null>(null);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);
  const [q, setQ] = useState("");
  const [asking, setAsking] = useState(false);
  const [ans, setAns] = useState<{ q: string; answer: string; sources: Source[] } | null>(null);
  const [filter, setFilter] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const load = useCallback(() => {
    api<{ items: Doc[] }>("/api/admin/kb/documents").then((r) => setDocs(r.items)).catch((e) => setErr(e.message));
    api<Status>("/api/admin/kb/status").then(setSt).catch(() => {});
  }, []);
  useEffect(load, [load]);
  const working = docs.some((d) => d.status === "pending" || d.status === "processing");
  useEffect(() => {
    if (!working) return;
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [working, load]);

  async function upload(files: FileList | null) {
    if (!files?.length) return;
    setBusy(true); setErr(""); setMsg("");
    try {
      const all = Array.from(files);
      let added = 0; const skipped: string[] = [];
      for (let i = 0; i < all.length; i += 20) {
        const fd = new FormData();
        all.slice(i, i + 20).forEach((f) => fd.append("files", f, f.name));
        const r = await api<{ added: Doc[]; skipped: { filename: string; reason: string }[] }>("/api/admin/kb/documents", { method: "POST", body: fd });
        added += r.added.length;
        r.skipped.forEach((s) => skipped.push(`${s.filename}: ${s.reason}`));
      }
      setMsg(`${added} file(s) added; indexing runs in the background (scanned pages take a few seconds each).` +
        (skipped.length ? ` Skipped ${skipped.length}: ${skipped.slice(0, 5).join("; ")}${skipped.length > 5 ? "…" : ""}` : ""));
      load();
    } catch (e: any) { setErr(e.message); } finally { setBusy(false); if (fileRef.current) fileRef.current.value = ""; }
  }

  async function ask(e: FormEvent) {
    e.preventDefault();
    if (q.trim().length < 3) return;
    setAsking(true); setErr("");
    try {
      const r = await api<{ answer: string; sources: Source[] }>("/api/admin/kb/ask", { method: "POST", json: { question: q } });
      setAns({ q, ...r });
    } catch (e: any) { setErr(e.message); } finally { setAsking(false); }
  }

  async function act(d: Doc, kind: "reindex" | "delete") {
    if (kind === "delete" && !confirm(`Delete "${d.title}" from the knowledge base? This cannot be undone.`)) return;
    try {
      if (kind === "delete") await api(`/api/admin/kb/documents/${d.id}`, { method: "DELETE" });
      else await api(`/api/admin/kb/documents/${d.id}/reindex`, { method: "POST" });
      load();
    } catch (e: any) { setErr(e.message); }
  }

  const shown = docs.filter((d) => !filter || (d.title + d.filename).toLowerCase().includes(filter.toLowerCase()));
  const counts = st?.documents || {};

  return (
    <div>
      <div className="topbar">
        <div>
          <h1 style={{ margin: 0 }}>Knowledge base</h1>
          <p className="muted small" style={{ margin: "4px 0 0" }}>
            Ask questions about your reference documents (calculations, wiring, protection, TANGEDCO rules). Answers cite the document and page.
            Quotation numbers always come from the calculation engine, not from here.
          </p>
        </div>
        {canEdit && (
          <div className="row" style={{ flex: "0 0 auto" }}>
            <input ref={fileRef} type="file" multiple accept="application/pdf,image/jpeg,image/png,image/webp" style={{ display: "none" }}
              onChange={(e) => upload(e.target.files)} />
            <button disabled={busy} onClick={() => fileRef.current?.click()}>{busy ? "Uploading…" : "Upload documents"}</button>
          </div>
        )}
      </div>

      {st && !st.configured && (
        <div className="note">The assistant is not configured yet. Add <code>OPENAI_API_KEY=…</code> to the <code>.env</code> file next to
          docker-compose.yml, then run <code>docker compose -p solar up -d</code>. Documents can be uploaded now and will be indexed once the key is set.</div>
      )}
      {err && <div className="err">{err}</div>}
      {msg && <div className="ok">{msg}</div>}

      <div className="card">
        <form onSubmit={ask} className="row" style={{ alignItems: "flex-end" }}>
          <label style={{ flex: "1 1 400px", margin: 0 }}>Ask the documents
            <input value={q} onChange={(e) => setQ(e.target.value)} maxLength={2000}
              placeholder="e.g. How do I size the DC cable and string fuse for 2 strings of 8 × 540 W panels?" />
          </label>
          <button style={{ flex: "0 0 auto" }} disabled={asking || !st?.configured}>{asking ? "Thinking…" : "Ask"}</button>
        </form>
        <div className="row small" style={{ marginTop: 8, gap: 6 }}>
          {["Formula for battery Ah for a backup load", "Earthing pit resistance limit and how to test it",
            "Documents needed for TANGEDCO net metering", "How is the network charge calculated?"].map((s) => (
            <button key={s} type="button" className="ghost small" style={{ flex: "0 0 auto" }} onClick={() => setQ(s)}>{s}</button>
          ))}
        </div>
        {ans && (
          <div className="answer-box">
            <div className="muted small">Q: {ans.q}</div>
            <AnswerText text={ans.answer} sources={ans.sources} />
            <SourceList sources={ans.sources} />
          </div>
        )}
      </div>

      <div className="card">
        <div className="topbar" style={{ marginBottom: 8 }}>
          <h2 style={{ margin: 0 }}>Documents ({docs.length})</h2>
          <div className="small muted">
            {counts.ready || 0} ready · {(counts.pending || 0) + (counts.processing || 0)} indexing · {counts.error || 0} errors · {st?.chunks || 0} passages
          </div>
          <input style={{ maxWidth: 240 }} placeholder="Filter…" value={filter} onChange={(e) => setFilter(e.target.value)} />
        </div>
        {!docs.length ? (
          <p className="muted">No documents yet. {canEdit ? "Upload the PDFs and images from your reference folder (you can select many at once)." : "Ask an admin or engineer to upload documents."}</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Document</th><th>Status</th><th className="num">Pages</th><th className="num">Scanned</th><th className="num">Passages</th><th>Added</th><th /></tr></thead>
              <tbody>
                {shown.map((d) => (
                  <tr key={d.id}>
                    <td>
                      <a href="#" onClick={(e) => { e.preventDefault(); openDocument(d.id); }}>{d.title}</a>
                      <div className="muted small">{d.filename} · {(d.size / 1024 / 1024).toFixed(1)} MB</div>
                      {d.error && <div className="warn error small">{d.error}</div>}
                    </td>
                    <td><span className={`pill ${STATUS_PILL[d.status] || ""}`}>{d.status}</span></td>
                    <td className="num">{d.pages || "-"}</td>
                    <td className="num">{d.vision_pages || "-"}</td>
                    <td className="num">{d.chunk_count || "-"}</td>
                    <td className="small">{fmtDate(d.created_at)}</td>
                    <td className="num" style={{ whiteSpace: "nowrap" }}>
                      {canEdit && d.status !== "processing" && <button className="ghost small" onClick={() => act(d, "reindex")}>Re-index</button>}
                      {role === "admin" && <button className="ghost small" style={{ color: "var(--red)" }} onClick={() => act(d, "delete")}>Delete</button>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

/** "Design notes (AI)" panel for a request: checks the engine's design against the documents. */
export function DesignNotes({ requestId, analysisId }: { requestId: number; analysisId?: number }) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [res, setRes] = useState<{ notes: string; sources: Source[]; summary: string; analysis_id: number } | null>(null);
  async function run() {
    setBusy(true); setErr("");
    try {
      setRes(await api(`/api/admin/requests/${requestId}/design-notes`, { method: "POST", json: { analysis_id: analysisId } }));
    } catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  }
  return (
    <div className="card">
      <div className="topbar" style={{ marginBottom: 6 }}>
        <div>
          <h2 style={{ margin: 0 }}>Design notes (AI, from your documents)</h2>
          <p className="muted small" style={{ margin: "4px 0 0" }}>Checks strings, cables, protection, earthing, structure and approvals against the knowledge base. It does not change any calculation.</p>
        </div>
        <button disabled={busy || !analysisId} onClick={run}>{busy ? "Reviewing…" : res ? "Run again" : "Generate design notes"}</button>
      </div>
      {err && <div className="err">{err}</div>}
      {res && (
        <>
          <details className="small"><summary>Design summary sent for review</summary><pre className="pre-wrap">{res.summary}</pre></details>
          <AnswerText text={res.notes} sources={res.sources} />
          <SourceList sources={res.sources} />
        </>
      )}
    </div>
  );
}
