// Settings -> Placeholders: suggest a value from the knowledge base, with citations; admin applies and confirms.
import { useState } from "react";
import { api } from "../../api";
import { AnswerText, SourceList, type Source } from "./Knowledge";

type Field = { field: string; unit: string; min: number; max: number; current: any };
type Suggestion = {
  key: string; found: boolean; values: Record<string, number>; explanation: string; problems?: string[];
  cite?: number[]; sources: Source[]; fields: Field[];
};

export function SuggestButton({ k, onApplied }: { k: string; onApplied: () => void }) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [sg, setSg] = useState<Suggestion | null>(null);
  const [vals, setVals] = useState<Record<string, string>>({});
  const [done, setDone] = useState("");

  async function suggest() {
    setBusy(true); setErr(""); setDone("");
    try {
      const r = await api<Suggestion>(`/api/admin/settings/placeholders/${encodeURIComponent(k)}/suggest`, { method: "POST" });
      setSg(r);
      setVals(Object.fromEntries(r.fields.map((f) => [f.field, r.values[f.field] !== undefined ? String(r.values[f.field]) : ""])));
    } catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  }
  async function apply() {
    if (!sg) return;
    const values: Record<string, number> = {};
    for (const [f, v] of Object.entries(vals)) if (v !== "") values[f] = Number(v);
    if (!Object.keys(values).length) return;
    setBusy(true); setErr("");
    try {
      await api(`/api/admin/settings/placeholders/${encodeURIComponent(k)}/apply`, { method: "POST", json: { values, sources: sg.sources } });
      setDone("Applied to the calculation settings. Check the result, then press “Mark confirmed”.");
      onApplied();
    } catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  }

  const cited = sg ? sg.sources.filter((s) => !sg.cite?.length || sg.cite.includes(s.n)) : [];
  return (
    <div style={{ marginTop: 6 }}>
      <button className="small secondary" disabled={busy} onClick={suggest}>{busy && !sg ? "Reading documents…" : "Suggest from documents"}</button>
      {err && <div className="err small">{err}</div>}
      {sg && (
        <div className="suggest-box">
          {!sg.found && <div className="note small">The documents do not give a clear value for this setting. Keep the current value or enter one yourself.</div>}
          <AnswerText text={sg.explanation || "-"} sources={sg.sources} />
          {sg.problems?.map((p) => <div key={p} className="warn warning small">{p}</div>)}
          {sg.fields.length > 0 && (
            <div className="row" style={{ marginTop: 6 }}>
              {sg.fields.map((f) => (
                <div key={f.field}>
                  <label className="small">{f.field.replace(/_/g, " ")} ({f.unit}) · now {String(f.current)}</label>
                  <input type="number" step="any" min={f.min} max={f.max} value={vals[f.field] ?? ""}
                    onChange={(e) => setVals({ ...vals, [f.field]: e.target.value })} />
                </div>
              ))}
              <button style={{ flex: "0 0 auto" }} disabled={busy || Object.values(vals).every((v) => v === "")} onClick={apply}>Apply values</button>
            </div>
          )}
          {done && <div className="ok small">{done}</div>}
          <SourceList sources={cited} />
        </div>
      )}
    </div>
  );
}
